"""Cross-store isolation and compatibility checks. No network or Shopify writes."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'scripts'))
from store_profiles import Profile, StoreGuardError
from run_store import duplicate_guard, main
from store_article import prepare_html, article_fragment, validate_schema, scope_css
from store_publisher import Shopify


class StoreIsolationTests(unittest.TestCase):
    def test_context_rejected_both_directions(self):
        for store, foreign in [('cherish','wellnessnest'), ('wellnessnest','cherish')]:
            selected, other = Profile(store), Profile(foreign)
            for source in other.data['context'] + other.data['templates'] + [other.data['calendar']]:
                with self.subTest(store=store,source=source), self.assertRaises(StoreGuardError):
                    selected.read_context(source)

    def test_unlisted_secret_context_rejected(self):
        for store in ('cherish','wellnessnest'):
            with self.assertRaises(StoreGuardError):
                Profile(store).read_context(ROOT/'.env')

    def test_foreign_product_links_and_handles_fail(self):
        wn, ch = Profile('wellnessnest'), Profile('cherish')
        for profile, content in [(ch,'https://wellnessnest.co/products/fusiforce-creatine-gummies'),
                                 (wn,'https://thecherishcompany.com/products/alticoddle-six-layer-muslin-cotton-blanket'),
                                 (ch,'/products/fusiforce-creatine-gummies'),
                                 (wn,'/products/alticoddle-six-layer-muslin-cotton-blanket'),
                                 (ch,'https://foreign.example/products/alticoddle-six-layer-muslin-cotton-blanket')]:
            with self.subTest(store=profile.store,content=content), self.assertRaises(StoreGuardError):
                profile.check_text(content)

    def test_profile_cannot_load_foreign_or_secret_source(self):
        original = Path.read_text
        for source in [str(ROOT/'brand/wellnessnest.json'), str(Path.home()/'PATI/LLM-Wiki/.env')]:
            def read(path, *a, **kw):
                text = original(path,*a,**kw)
                if path == ROOT/'stores/cherish/profile.json':
                    data = json.loads(text); data['context'].append(source)
                    return json.dumps(data)
                return text
            with patch.object(Path,'read_text',read), self.assertRaises(StoreGuardError):
                Profile('cherish')

    def test_credential_namespace_rejected(self):
        p=Profile('cherish'); p.data['credential']['prefix']='SHOPIFY_CHERISH_'
        with self.assertRaises(StoreGuardError): p.validate_credentials_metadata()

    def test_competitor_product_link_is_not_an_own_handle(self):
        p = Profile('cherish')
        text = ('<a href="/products/alticoddle-six-layer-muslin-cotton-blanket">a</a> <a href="https://thecherishcompany.com/products/lumibliss-cotton-waffle-weave-blanket">b</a> '
                '<a href="https://www.brooklinen.com/products/classic-core-sheet-set">c</a>')
        self.assertEqual(p.linked_handles(text), {'alticoddle-six-layer-muslin-cotton-blanket', 'lumibliss-cotton-waffle-weave-blanket'})
        p.check_text(text)   # the citation itself stays legal

    def test_write_payload_is_checked_as_decoded_json(self):
        # A JSON-encoded body holds href=\\"/products/<handle>\\"; the escaped quote must not become part of the handle.
        p = Profile('cherish')
        own = json.dumps({'article': {'body_html': '<a href="/products/alticoddle-six-layer-muslin-cotton-blanket">x</a>'}})
        foreign = json.dumps({'article': {'body_html': '<a href="/products/fusiforce-creatine-gummies">x</a>'}})
        with patch.object(p, 'credential_domain', return_value=p.data['shop']):
            p.assert_write(p.data['shop'], own)
            with self.assertRaises(StoreGuardError):
                p.assert_write(p.data['shop'], foreign)

    def test_wrong_domain_write_stops_before_auth_or_network(self):
        p=Profile('cherish')
        api=object.__new__(Shopify); api.profile=p; api.domain='wellnessnest1.myshopify.com'
        with patch.object(p,'credential_domain',return_value=p.data['shop']), patch('urllib.request.urlopen') as request:
            with self.assertRaises(StoreGuardError): api.request('/admin/api/2026-04/blogs/1/articles.json', {'article':{'title':'Test'}})
            request.assert_not_called()

    def test_calendar_and_first_21(self):
        p=Profile('cherish'); rows=list(__import__('csv').DictReader(p.read_context(p.data['calendar']).splitlines()))
        self.assertEqual(len(rows),int(p.data['calendar_rows']))
        self.assertTrue(all(r['approval']=='kevin' for r in rows[:21]))
        self.assertEqual(len(p.calendar('2026-10-28')),7)
        self.assertEqual(len(p.data['templates']),7)

    def test_prompt_contains_only_selected_store(self):
        p=Profile('cherish'); row=p.calendar('2026-10-28')[0]
        prompt=json.loads(p.prompt(row))
        self.assertEqual(prompt['store'],'cherish')
        self.assertTrue(all('/23-new-bedding-brand/' in c['path'] for c in prompt['context']))
        self.assertNotIn('access_token',prompt)
        self.assertNotIn('SHOPIFY_CHERISH_LIVE_CLIENT_SECRET',p.prompt(row))

    def test_duplicate_includes_unpublished(self):
        with self.assertRaises(StoreGuardError):
            duplicate_guard({'handle':'test','title':'How to wash muslin'}, {'primary_keyword':'muslin wash'},
                            [{'handle':'test','title':'Old title','published_at':None}])


    def test_approved_template_css_cannot_be_changed_by_writer(self):
        p=Profile('cherish'); template,_=p.template('1')
        changed=template.replace('--milk:#FBF8F5','--milk:#000000')
        prepared=prepare_html(changed,template)
        self.assertIn('--milk:#FBF8F5',prepared)
        self.assertNotIn('--milk:#000000',prepared)
        self.assertNotIn('Template preview',prepared)
        self.assertNotIn('class="spec"',prepared)

    def test_shopify_fragment_has_scoped_css_and_no_store_chrome(self):
        p=Profile('cherish'); template,_=p.template('1')
        fragment=article_fragment(prepare_html(template,template))
        self.assertNotIn('<html',fragment)
        self.assertNotIn('<header',fragment)
        self.assertNotIn('class="preview"',fragment)
        self.assertIn('id="genseo-cherish"',fragment)
        self.assertIn('#genseo-cherish h1',fragment)
        self.assertIn('application/ld+json',fragment)
        self.assertIn('@font-face',fragment)

    def test_faq_schema_answers_must_match_visible_answers(self):
        p=Profile('cherish'); template,_=p.template('1')
        prepared=prepare_html(template,template)
        package={'title':'Bedding for Night Sweats: How to Set Up a Bed That Copes','handle':'bedding-for-night-sweats'}
        validate_schema(prepared,package,p)
        changed=prepared.replace('"text": "Cotton, linen and wool absorb', '"text": "Invented fact. Cotton, linen and wool absorb',1)
        self.assertNotEqual(changed,prepared)
        with self.assertRaises(StoreGuardError): validate_schema(changed,package,p)

    def test_legacy_every_write_rejects_foreign_domain_and_token(self):
        import genseo_config
        import urllib.request
        for domain, token in [('uxfaue-s1.myshopify.com',genseo_config.TOKEN),
                              (genseo_config.SHOP,'not-the-selected-credential')]:
            req=urllib.request.Request('https://'+domain+'/admin/api/2026-04/blogs/1/articles.json',
                data=b'{"article":{"title":"A draft"}}',headers={'X-Shopify-Access-Token':token})
            with self.assertRaises(StoreGuardError): genseo_config.assert_legacy_request(req)

    def test_approval_controls_unpublished_and_live_payloads(self):
        p=Profile('cherish'); template,_=p.template('1')
        p.data.pop('article_contract')  # legacy fragment path; journal-v1 is covered in test_journal_fields.py
        package={'body_html':prepare_html(template,template),'title':'A store article',
                 'handle':'a-store-article','meta_description':'A description'}
        for live in (False,True):
            api=object.__new__(Shopify);api.profile=p;api.domain=p.data['shop']
            calls=[]
            state={'published':False}
            package['title']='Bedding for Night Sweats: How to Set Up a Bed That Copes'
            package['handle']='bedding-for-night-sweats'
            def request(path,payload=None,method=None):
                if payload is not None:
                    calls.append(payload)
                    state['published']=payload['article']['published']
                return {'article':{'id':123,'handle':package['handle'],
                    'published_at':'2026-10-28' if state['published'] else None,
                    'body_html':article_fragment(package['body_html'])}}
            with patch.object(api,'identity'), patch.object(api,'request',side_effect=request):
                api.publish(package,1,live)
            self.assertIs(calls[0]['article']['published'],False)
            self.assertIs(calls[-1]['article']['published'],live)
            self.assertNotIn('<html',calls[0]['article']['body_html'])

    def test_bad_shopify_readback_never_publishes_live(self):
        p=Profile('cherish');template,_=p.template('1')
        p.data.pop('article_contract')  # legacy fragment path; journal-v1 is covered in test_journal_fields.py
        package={'title':'Bedding for Night Sweats: How to Set Up a Bed That Copes',
                 'handle':'bedding-for-night-sweats','body_html':prepare_html(template,template),
                 'meta_description':'A description'}
        api=object.__new__(Shopify);api.profile=p;api.domain=p.data['shop']
        from store_article import soup
        broken=soup(article_fragment(package['body_html']))
        broken.style.decompose()
        response={'article':{'id':123,'handle':package['handle'],'published_at':None,'body_html':str(broken)}}
        with patch.object(api,'identity'), patch.object(api,'request',return_value=response) as request:
            with self.assertRaises(StoreGuardError): api.publish(package,1,True)
            self.assertFalse(any(c.kwargs.get('method')=='PUT' for c in request.call_args_list))

    def test_auth_adapter_loads_on_the_system_python(self):
        p=Profile('cherish')
        api=Shopify(p)
        self.assertEqual(api.domain,p.data['shop'])
        self.assertTrue(callable(api.auth.token))

    def test_dry_run_refuses_foreign_credential_domain_at_start(self):
        with patch.object(Profile,'credential_domain',side_effect=StoreGuardError('Credential store domain mismatch')):
            with self.assertRaises(StoreGuardError): main(['--store','cherish','--day','2026-10-28','--dry-run'])

    def test_store_required(self):
        result=subprocess.run([sys.executable,str(ROOT/'scripts/run_store.py'),'--dry-run'],capture_output=True)
        self.assertEqual(result.returncode,2)

    def test_preview_and_apply_cannot_mix(self):
        with self.assertRaises(StoreGuardError): main(['--store','cherish','--dry-run','--apply'])

    def test_legacy_refuses_cherish_selection(self):
        env=dict(os.environ,GENSEO_STORE='cherish')
        result=subprocess.run([sys.executable,'-c',f"import sys;sys.path.insert(0,{str(ROOT/'scripts')!r});import genseo_config"], env=env,capture_output=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn(b'Wellness Nest only',result.stderr)


class CherishRecoveryTests(unittest.TestCase):
    """Lane A 2026-11-04: a renamed source stopped Cherish for days with no report."""
    def test_renamed_source_fails_before_generation_and_reports(self):
        import cherish_auto
        original = Path.read_text
        def read(path, *a, **kw):
            text = original(path, *a, **kw)
            if path == ROOT/'stores/cherish/profile.json':
                return text.replace('20-8b-cherish-copy-pdp-core-three.md', '8b-cherish-copy-pdp-core-three.md')
            return text
        with patch.object(Path, 'read_text', read), self.assertRaisesRegex(StoreGuardError, 'Missing approved input') as caught:
            Profile('cherish')
        with patch.object(cherish_auto, 'incident') as sent:
            self.assertEqual(cherish_auto.blocked(caught.exception), 1)
        self.assertEqual(sent.call_args[0][0], 'missing-source')

    def test_second_run_after_a_publish_does_not_exceed_the_daily_allowance(self):
        import cherish_auto
        with tempfile.TemporaryDirectory() as tmp:
            day = cherish_auto.dt.datetime.now(cherish_auto.ICT).date().isoformat()
            (Path(tmp)/'daily').mkdir()
            (Path(tmp)/'daily'/f'{day}.md').write_text('Calendar day x · approval=auto rows: 7 · published: 3 · job\n')
            with patch.object(cherish_auto, 'WORK', Path(tmp)), patch.object(cherish_auto.subprocess, 'run') as run, \
                 patch.object(cherish_auto.subprocess, 'call') as call:
                self.assertEqual(cherish_auto.main([]), 0)
            run.assert_not_called(); call.assert_not_called()

    def test_eligible_rows_skip_published_past_and_manual_rows(self):
        import cherish_auto
        class Fake:
            data = {'calendar': 'c'}
            def read_context(self, _):
                return ('day,slot,approval,uniqueness_key\n2026-11-03,1,auto,a\n2026-11-04,1,auto,b\n'
                        '2026-11-04,2,auto,c\n2026-11-05,1,manual,d\n2026-11-05,2,auto,e\n')
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp)/'articles.json').write_text(json.dumps({'b': {'published': True}}))
            with patch.object(cherish_auto, 'STATE', Path(tmp)):
                keys = [r['uniqueness_key'] for r in cherish_auto.eligible_rows(Fake(), today='2026-11-04')]
                self.assertEqual(keys, ['c', 'e'])
                with patch.object(cherish_auto, 'incident') as sent:
                    self.assertEqual(cherish_auto.queue_check(Fake()), 2)
                self.assertEqual(sent.call_args[0][0], 'queue-low')


if __name__=='__main__': unittest.main()
