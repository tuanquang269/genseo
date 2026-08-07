#!/usr/bin/env python3
"""Add/replace an SEO content block on a Shopify COLLECTION page (descriptionHtml).

The block is written as a markdown draft, validated mechanically, converted to HTML,
and appended AFTER the collection's existing description between marker comments —
so re-running replaces our block and never destroys the original description.
Also builds FAQPage JSON-LD from the draft's `### question` FAQ entries.

Usage: python3 collection_seo.py <collection_id> <draft.md>

Gates (exit 1, nothing written): 250-900 words · >=3 FAQs (### under a FAQ heading) ·
mentions {{MARKET}} · has an {{CURRENCY}} price (S$) · >=2 internal links · no out-of-stock brands.
Logs to collection_seo_runs.log.
"""
import json, os, re, sys, urllib.request, datetime
import markdown

CONFIG_PATH = os.path.expanduser('~/.genseo/shopify_token.json')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(BASE_DIR, 'collection_seo_runs.log')
START, END = '<!-- genseo-block-start -->', '<!-- genseo-block-end -->'


def gql(shop, token, query, variables=None):
    r = urllib.request.Request(f"https://{shop}/admin/api/2026-04/graphql.json",
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={"X-Shopify-Access-Token": token, "Content-Type": "application/json"})
    out = json.loads(urllib.request.urlopen(r).read())
    if out.get('errors'):
        print("✗ GraphQL:", out['errors']); sys.exit(1)
    return out['data']


def main():
    if len(sys.argv) != 3:
        print(__doc__); sys.exit(1)
    cid, draft_path = sys.argv[1], sys.argv[2]
    md_text = open(draft_path, encoding='utf-8').read()

    # ── mechanical gates ──
    errs = []
    words = len(re.findall(r'\w+', md_text))
    if not (250 <= words <= 900): errs.append(f"{words} words (need 250-900)")
    faq_m = re.search(r'##\s+(?:Frequently Asked Questions|FAQs?)[^\n]*\n(.*)', md_text, re.S | re.I)
    faqs = re.findall(r'###\s+(.*?)\s*\n(.*?)(?=\n###|\Z)', faq_m.group(1), re.S) if faq_m else []
    if len(faqs) < 3: errs.append(f"{len(faqs)} FAQs (need >=3 `### question` under a `## FAQ` heading)")
    if '{{market}}' not in md_text.lower(): errs.append("no '{{MARKET}}' mention")
    if not re.search(r'S\$\s?\d|{{CURRENCY}}\s?\d', md_text): errs.append("no {{CURRENCY}} price (S$xx)")
    links = re.findall(r'\]\((/(?:products|collections|blogs)/[^)]+)\)', md_text)
    if len(links) < 2: errs.append(f"{len(links)} internal links (need >=2, relative /products/ /collections/ /blogs/ paths)")
    for b in ('bronson', 'transparent labs'):
        if b in md_text.lower(): errs.append(f'out-of-stock brand "{b}"')
    if errs:
        for e in errs: print(f"✗ {e}")
        sys.exit(1)

    auth = json.load(open(CONFIG_PATH))
    shop, token = auth['shop'], auth['access_token']
    gid = f"gid://shopify/Collection/{cid}"
    cur = gql(shop, token, "query($id:ID!){collection(id:$id){title handle descriptionHtml}}", {"id": gid})['collection']
    if cur is None:
        print(f"✗ collection {cid} not found"); sys.exit(1)

    existing = cur['descriptionHtml'] or ''
    if START in existing:  # replace our previous block, keep everything else
        existing = re.sub(re.escape(START) + '.*?' + re.escape(END), '', existing, flags=re.S).rstrip()

    faq_schema = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q.strip(),
         "acceptedAnswer": {"@type": "Answer", "text": markdown.markdown(a.strip())}} for q, a in faqs]}
    block_html = markdown.markdown(md_text, extensions=['extra'])
    new_desc = (existing + f"\n{START}\n{block_html}\n"
                f'<script type="application/ld+json">\n{json.dumps(faq_schema, indent=2)}\n</script>\n{END}')

    res = gql(shop, token,
        "mutation($input:CollectionInput!){collectionUpdate(input:$input){collection{id} userErrors{field message}}}",
        {"input": {"id": gid, "descriptionHtml": new_desc}})
    ue = res['collectionUpdate']['userErrors']
    if ue:
        print("✗ update failed:", ue); sys.exit(1)

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a') as f:
        f.write(f"{stamp} | collection {cid} ({cur['handle']}) | +{words}w block, {len(faqs)} FAQs, {len(links)} links\n")
    print(f"✓ collection {cid} ({cur['handle']}) updated: {words}-word SEO block, {len(faqs)} FAQs + FAQPage schema")
    print(f"  live: https://yourdomain.com/collections/{cur['handle']}")


if __name__ == '__main__':
    main()
