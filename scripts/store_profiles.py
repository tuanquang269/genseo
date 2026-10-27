"""Store identity and explicit context boundaries. No credentials in prompt context."""
import csv
import hashlib
import json
import os
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent


class StoreGuardError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise StoreGuardError(message)


class Profile:
    def __init__(self, store):
        require(store in ('wellnessnest', 'cherish'), 'Unknown store')
        self.store = store
        self.path = ROOT / 'stores' / store / 'profile.json'
        self.data = json.loads(self.path.read_text())
        require(self.data['id'] == store, 'Profile identity mismatch')
        expected = {'wellnessnest': ('wellnessnest.co', 'wellnessnest1.myshopify.com'),
                    'cherish': ('thecherishcompany.com', 'uxfaue-s1.myshopify.com')}[store]
        require((self.data['domain'], self.data['shop']) == expected, 'Store domain mismatch')
        self.other = 'cherish' if store == 'wellnessnest' else 'wellnessnest'
        self.other_data = json.loads((ROOT / 'stores' / self.other / 'profile.json').read_text())
        self.allowed = {Path(p).expanduser().resolve() for key in ('context', 'templates', 'gates')
                        for p in self.data[key]}
        self.allowed.add(Path(self.data['calendar']).resolve())
        if 'registry' in self.data:
            self.allowed.add(Path(self.data['registry']).resolve())
        foreign = {Path(p).expanduser().resolve() for key in ('context', 'templates', 'gates')
                   for p in self.other_data[key]}
        foreign.add(Path(self.other_data['calendar']).resolve())
        if 'registry' in self.other_data:
            foreign.add(Path(self.other_data['registry']).resolve())
        require(not self.allowed.intersection(foreign), 'Cross-store context in profile')
        # Profile edits cannot grant access to the vault root, another store, or a secret file.
        home = Path.home()
        vault = home/'PATI/LLM-Wiki'
        work = home/'PATI/work'
        if store == 'cherish':
            ownership = [vault/'20-brands/23-new-bedding-brand', work/'cherish-seo', work/'cherish-ids']
        else:
            ownership = [ROOT/'brand', ROOT/'scripts', home/'.claude/skills/genseo-auto-publish/references']
        for p in self.allowed:
            own = any(p == base.resolve() or base.resolve() in p.parents for base in ownership)
            own = own or (store == 'wellnessnest' and p in (ROOT/'daily-tickets.md', vault/'20-brands/1-wellnessnest.md'))
            require(own and p.suffix in ('.md', '.json', '.html', '.csv', '.py'), 'Input does not belong to selected store')
            require(p.name not in ('credentials.json', 'shopify_token.json'), 'Credentials cannot enter writer context')
        for p in self.allowed:
            require(p.is_file(), f'Missing approved input: {p}')
        self.validate_credentials_metadata()

    def validate_credentials_metadata(self):
        c = self.data['credential']
        if self.store == 'cherish':
            require(c['prefix'] == 'SHOPIFY_CHERISH_LIVE_', 'Wrong credential namespace')
            require(Path(c['env_file']).resolve() == Path.home()/'PATI/LLM-Wiki/.env', 'Wrong credential file')
            require(all(k.startswith(c['prefix']) for k in c['keys']), 'Cross-store credential key')
            require(Path(c['adapter']).resolve() == Path('/Users/kevinkreative/PATI/work/cherish-launch-tools/t3_store.py'), 'Unapproved credential adapter')
        else:
            require(c['kind'] == 'legacy-json', 'Wrong credential source')
            require(Path(c['path']).expanduser().resolve() == Path.home()/'.genseo/shopify_token.json', 'Wrong credential path')

    def read_context(self, path):
        p = Path(path).expanduser().resolve()
        require(p in self.allowed, 'Context is outside the selected store allowlist')
        return p.read_text()

    @property
    def handles(self):
        if 'registry' not in self.data:
            return set(self.data['product_handles'])
        return {r['product_handle'] for r in csv.DictReader(self.read_context(self.data['registry']).splitlines())}

    def check_handle(self, handle):
        require(handle in self.handles, 'Product handle is outside the selected store catalog')

    def check_text(self, text):
        # Apply to generated content, not approved history which can mention other brands.
        foreign = (self.other_data['domain'], self.other_data['shop'])
        require(not any(d in text.lower() for d in foreign), 'Cross-store domain in content')
        names = ('wellness nest', 'wellnessnest', 'shilasource', 'florafresh', 'fusiforce', 'ageaura', 'turkesterone') if self.store == 'cherish' else ('the cherish company', 'thecherishcompany')
        require(not any(n in text.lower() for n in names), 'Cross-store brand context in content')
        for match in re.finditer(r'(?:https?://[^\s<>"\')]+)?/products/([^\s<>"\')?#/|]+)', text, re.I):
            url = match.group(0)
            host = (urlsplit(url).hostname or '').removeprefix('www.')
            own = (self.data['domain'], self.data['shop'])
            handle = unquote(match.group(1))
            require(host not in foreign, 'Cross-store product link')
            if host and host not in own:
                # A third-party page (a competitor citation) is fine. A foreign host that reuses OUR handle is not.
                require(handle not in self.handles, 'Cross-store product link')
                continue
            self.check_handle(handle)

    def credential_domain(self):
        c = self.data['credential']
        if self.store == 'wellnessnest':
            path = Path(os.environ.get('GENSEO_CONFIG', c['path'])).expanduser()
            cfg = json.loads(path.read_text())
            domain = cfg['shop']
        else:
            env = {}
            for line in Path(c['env_file']).read_text().splitlines():
                if '=' in line and not line.lstrip().startswith('#'):
                    k, v = line.split('=', 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
            domain = env.get(c['prefix']+'STORE')
        require(domain == self.data['shop'], 'Credential store domain mismatch')
        return domain

    def assert_write(self, domain, body):
        require(domain == self.data['shop'], 'Shopify write domain mismatch')
        require(self.credential_domain() == domain, 'Credential identity changed')
        self.check_text(body)

    def template(self, style):
        matches = [p for p in self.data['templates'] if Path(p).name.startswith('style-'+style+'-')]
        require(len(matches) == 1, 'Unapproved template style')
        html = self.read_context(matches[0])
        m = re.search(r'<script[^>]*id="rules-machine"[^>]*>(.*?)</script>', html, re.S)
        require(m is not None, 'Template has no rules-machine block')
        return html, json.loads(m.group(1))

    def calendar(self, day):
        rows = list(csv.DictReader(self.read_context(self.data['calendar']).splitlines()))
        require(len(rows) == int(self.data['calendar_rows']), 'Calendar row count changed: review the store profile')
        seen = set()
        for r in rows:
            require(r['approval'] in ('kevin', 'auto'), 'Invalid calendar approval')
            self.check_handle(r['target_product_handle'])
            self.check_text(r['internal_links'])
            self.check_text(' '.join(r[k] for k in ('angle','primary_keyword','secondary_keywords')))
            require(r['uniqueness_key'] and r['uniqueness_key'] not in seen, 'Duplicate calendar topic')
            seen.add(r['uniqueness_key'])
            self.template(r['style'])
        selected = [r for r in rows if r['day'] == day]
        require(len(selected) <= self.data['daily_volume'], 'Daily volume exceeds profile')
        require(all(r['approval'] == 'kevin' for r in rows[:self.data['review_first']]), 'First 21 posts must require Kevin review')
        return selected

    def prompt(self, row):
        template, rules = self.template(row['style'])
        context = [{'path': p, 'content': self.read_context(p)} for p in self.data['context']]
        # Only this product's registry rows. No secret files or shared vault context.
        products = [r for r in csv.DictReader(self.read_context(self.data['registry']).splitlines())
                    if r['product_handle'] == row['target_product_handle']]
        return json.dumps({'store': self.store, 'domain': self.data['domain'], 'voice': self.data['voice'],
                           'task': row, 'context': context, 'product_facts': products, 'allowed_product_handles': sorted(self.handles),
                           'approved_template': re.sub(r'<style\b[^>]*>.*?</style>', '<!-- Approved CSS is inserted by the runner. -->', template, flags=re.S), 'rules_machine': rules,
                           'output_contract': 'Return an article package with store, day, slot, title, handle, meta_description, body_html, and facts. Preserve approved CSS and structure. Include rules-machine exactly. Each facts item needs claim and source (an approved path, evidence URL, or shopify://<shop>/products/<handle> from the supplied live product facts) and quote. Do not invent claims. Do not read global GenSEO skills. Use a style- prefixed HTML filename for the render gate. Publishing is performed by the guarded runner only.' + self.journal_contract()}, ensure_ascii=False, indent=2)

    def journal_contract(self):
        if self.data.get('article_contract') != 'journal-v1':
            return ''
        from journal_fields import CHIP_TAGS
        return (' The package also needs "tags": 1 to 3 values chosen only from ' + json.dumps(CHIP_TAGS) +
                '. The runner writes the article body and journal.* metafields from your page; it adds no CSS or JSON-LD to the body.')

    def fingerprint(self):
        return hashlib.sha256(self.path.read_bytes()).hexdigest()
