#!/usr/bin/env python3
"""
repair_schema.py — Self-healing schema fixer. Works on the LIVE article HTML, so it repairs
any article regardless of how it was published (python publisher, MCP, GraphQL, curl).

For the given article(s): if the live body is missing Article JSON-LD or FAQPage schema,
build them FROM THE RENDERED HTML (not the markdown draft) and inject via the Shopify API.
Also fixes a generic author field/schema when a named /pages/ byline exists in the body.

Usage:
  python3 repair_schema.py <ARTICLE_ID> [BLOG_ID]      # one article
  python3 repair_schema.py --sweep <id1,id2,...>        # many (comma-sep), blog 104008483131
Idempotent: re-running a healthy article changes nothing.
"""
import sys, json, re, urllib.request, urllib.error, datetime, time

from genseo_config import SHOP, TOKEN, API
from genseo_roster import NAMES as ROSTER  # single source: roster.json

def api(url, data=None, method="GET"):
    req=urllib.request.Request(url, data=(json.dumps(data).encode() if data else None), method=method,
        headers={"X-Shopify-Access-Token":TOKEN,"Content-Type":"application/json"})
    for attempt in range(5):
        try:
            res = urllib.request.urlopen(req)
            return json.loads(res.read()) if method!="DELETE" else {}
        except urllib.error.HTTPError as e:
            if e.code in (500, 502, 503, 504, 429) and attempt < 4:
                time.sleep(2 ** attempt)
                continue
            raise

def clean(s): return re.sub(r'\s+',' ',re.sub(r'<[^>]*>','',s)).strip()

def extract_faqs(body):
    """Find a visible FAQ section and pull Q (h3/strong) + answer (following text) pairs."""
    # locate FAQ heading
    m=re.search(r'<h2[^>]*>[^<]*(?:FAQ|Frequently Asked Questions)[^<]*</h2>(.*)$', body, re.S|re.I)
    seg = m.group(1) if m else body
    pairs=[]
    # questions as <h3>...?</h3> then answer until next <h3>/<h2>
    for qm in re.finditer(r'<h3[^>]*>(.*?)</h3>(.*?)(?=<h3|<h2|$)', seg, re.S|re.I):
        q=clean(qm.group(1)); ans=clean(qm.group(2))
        if q.endswith('?') and len(ans.split())>=8 and 'about the author' not in q.lower():
            pairs.append((q,ans))
    return pairs[:8]

def repair(aid, blog="104008483131"):
    a=api(f"https://{SHOP}/admin/api/{API}/blogs/{blog}/articles/{aid}.json")["article"]
    body=a.get("body_html") or ""; title=a.get("title","")
    changed=[]
    # canary: an untitled post means a publish slipped past the fail-loud guard — flag for manual fix
    if title.strip() in ("","Generated Article"):
        print(f"  [{aid}] ⚠ UNTITLED ('Generated Article') — needs manual title fix | {a.get('handle')}")
        return
    # named author from byline
    am=re.search(r'/pages/([a-z-]+)', body)
    handle=am.group(1) if am and am.group(1) in ROSTER else None

    # Fallback: look up author name in ROSTER values if no link exists in body
    if not handle:
        author_field = (a.get("author") or "").strip()
        for h, name in ROSTER.items():
            if name.lower() in author_field.lower():
                handle = h
                break

    author_name=ROSTER.get(handle)
    if not author_name:
        current=(a.get("author") or "").strip()
        if current in ROSTER.values():
            author_name=current
        else:
            # Never stamp a default person onto someone else's article — the donor
            # system silently attributed unknown articles to one staffer. Skip instead.
            print(f"  [{aid}] ⚠ SKIP author repair — byline '{current or '(empty)'}' not in roster.json | {a.get('handle')}")
            author_name=None

    # Clean up old invalid Article schema to force a rebuild if it was Organization but we resolved a Person handle
    for m_json in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', body, re.S):
        try:
            js = json.loads(m_json.group(1).strip())
            if js.get("@type") == "Article":
                author_type = js.get("author", {}).get("@type")
                if author_type != "Person" and handle:
                    body = body.replace(m_json.group(0), "")
                    changed.append("Reset-Article")
        except Exception:
            pass

    add=""
    if "application/ld+json" not in body or '"@type": "Article"' not in body:
        art={"@context":"https://schema.org","@type":"Article","headline":title,
             "author":({"@type":"Person","name":author_name,"url":f"https://wellnessnest.co/pages/{handle}"} if handle and author_name else {"@type":"Organization","name":"Wellness Nest"}),
             "publisher":{"@type":"Organization","name":"Wellness Nest","logo":{"@type":"ImageObject","url":"https://wellnessnest.co/cdn/shop/files/WNN_Main_Logo_eb77747f-0bd5-4316-a9ba-92349ddbe5cc.png"}},
             "dateModified":datetime.date.today().isoformat()}
        add+=f'\n<script type="application/ld+json">\n{json.dumps(art,indent=2)}\n</script>\n'
        changed.append("Article")
    if "FAQPage" not in body:
        faqs=extract_faqs(body)
        if faqs:
            fp={"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
                {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":ans}} for q,ans in faqs]}
            add+=f'\n<script type="application/ld+json">\n{json.dumps(fp,indent=2)}\n</script>\n'
            changed.append(f"FAQPage({len(faqs)})")
        else:
            changed.append("FAQPage-SKIPPED(no visible FAQ found)")

    payload={"article":{"id":aid}}
    do_put=False
    if add:
        payload["article"]["body_html"]=body+add; do_put=True
    if (a.get("author") or "").strip() in ("","Wellness Nest Editorial Team","Your Brand Research Team","Your Brand Staff") and handle and author_name:
        payload["article"]["author"]=author_name; do_put=True; changed.append(f"author→{author_name}")
    if do_put:
        api(f"https://{SHOP}/admin/api/{API}/blogs/{blog}/articles/{aid}.json", payload, "PUT")
        print(f"  [{aid}] REPAIRED: {', '.join(changed)} | {a.get('handle')}")
    else:
        print(f"  [{aid}] healthy (schema+author present) | {a.get('handle')}")

def recent_article_ids(hours, blogs=("104008483131",)):  # was the same id twice -> double check/repair (fixed 2026-10-03)
    """Article IDs updated within the last `hours`, across the given blogs."""
    since=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(hours=hours)).strftime('%Y-%m-%dT%H:%M:%SZ')
    out=[]
    for blog in blogs:
        url=f"https://{SHOP}/admin/api/{API}/blogs/{blog}/articles.json?limit=250&updated_at_min={urllib.parse.quote(since)}&fields=id,updated_at,published_at"
        while url:
            req=urllib.request.Request(url, headers={"X-Shopify-Access-Token":TOKEN})
            res=urllib.request.urlopen(req); d=json.loads(res.read())
            out+=[(a['id'],blog) for a in d['articles'] if a.get('published_at')]
            url=None
            for p in res.headers.get('Link','').split(','):
                if 'rel="next"' in p: url=p[p.find('<')+1:p.find('>')]
    return out

def main():
    if sys.argv[1]=="--recent":
        hours=int(sys.argv[2]) if len(sys.argv)>2 else 24
        ids=recent_article_ids(hours)
        print(f"Articles updated in last {hours}h: {len(ids)} — checking schema…")
        # capture repaired/untitled counts by tapping stdout lines repair() prints
        import io, contextlib
        repaired=untitled=healthy=0
        for aid,blog in ids:
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf): repair(aid, blog)
            line=buf.getvalue(); print(line, end="")
            if "REPAIRED" in line: repaired+=1
            elif "UNTITLED" in line: untitled+=1
            elif "healthy" in line: healthy+=1
        # GROUND-TRUTH LOG so the daily run is auditable (who/when/what)
        try:
            ts=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
            with open("/Users/kevinkreative/genseo/repair_runs.log","a") as lg:
                lg.write(f"{ts}\t--recent {hours}h\tchecked={len(ids)}\trepaired={repaired}\tuntitled={untitled}\thealthy={healthy}\n")
        except Exception: pass
        print(f"Done. checked={len(ids)} repaired={repaired} untitled={untitled} healthy={healthy} (logged to repair_runs.log)")
    elif sys.argv[1]=="--sweep":
        ids=[x.strip() for x in sys.argv[2].split(",") if x.strip()]
        for i in ids: repair(i)
    else:
        repair(sys.argv[1], sys.argv[2] if len(sys.argv)>2 else "104008483131")

if __name__=="__main__": main()
