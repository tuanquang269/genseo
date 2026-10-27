"""Build the approved preview and a scoped Shopify article fragment."""
import json
import re
from store_profiles import require


def soup(text):
    from bs4 import BeautifulSoup
    return BeautifulSoup(text, 'html.parser')


def prepare_html(body, template):
    doc, approved = soup(body), soup(template)
    require(doc.head is not None and doc.body is not None, 'A complete HTML document is required')
    for node in doc.select('style, script:not([type="application/ld+json"]):not(#rules-machine), .preview, .spec, .spec-sec'):
        node.decompose()
    for node in approved.select('style'):
        doc.head.append(node)
    # Store chrome is owned by the live theme. It is absent from the article gate.
    for node in doc.select('header.site, footer.foot, .topbar, .stick'):
        node.decompose()
    require(doc.select_one('.layout article') is not None, 'Approved layout is missing')
    return str(doc)


def scope_css(css):
    # Approved templates use ordinary selectors and media rules. Process leaf
    # blocks so media conditions remain intact and font-face definitions survive.
    require('@keyframes' not in css and '@import' not in css, 'Unsupported template CSS rule')
    def leaf(match):
        selectors, declarations = match.groups()
        if selectors.strip().startswith('@'):
            return match.group(0)
        out = []
        for selector in selectors.split(','):
            selector = selector.strip()
            selector = re.sub(r'^(?::root|html|body)(?=\b|\s|:|$)', '#genseo-cherish', selector)
            if not selector.startswith('#genseo-cherish'):
                selector = '#genseo-cherish ' + selector
            out.append(selector)
        return ','.join(out)+'{'+declarations+'}'
    return re.sub(r'([^{}]+)\{([^{}]*)\}', leaf, css)


def article_fragment(body):
    doc = soup(body)
    layout = doc.select_one('.layout')
    require(layout is not None, 'Article layout is missing')
    sections = ''.join(str(node) for node in doc.select('section.band'))
    css = '\n'.join(scope_css(node.get_text()) for node in doc.select('style'))
    schema = ''.join(str(node) for node in doc.select('script[type="application/ld+json"]'))
    return '<style>'+css+'</style><div id="genseo-cherish">'+str(layout)+sections+'</div>'+schema


def validate_schema(body, package, profile):
    doc = soup(body)
    require(doc.h1 is not None and doc.h1.get_text(' ',strip=True) == package['title'], 'Title and H1 differ')
    schemas = doc.select('script[type="application/ld+json"]')
    require(len(schemas) == 1, 'Exactly one JSON-LD graph is required')
    graph = json.loads(schemas[0].get_text())['@graph']
    types = {node['@type'] for node in graph}
    require({'BlogPosting','BreadcrumbList','FAQPage'} <= types, 'Required schema types are missing')
    require(not types.intersection({'Product','Review','AggregateRating'}), 'Product and review schema do not belong in a post')
    post = next(n for n in graph if n['@type']=='BlogPosting')
    url = f"https://{profile.data['domain']}/blogs/{profile.data['blog_handle']}/{package['handle']}"
    require(post.get('headline') == package['title'] and str(post.get('@id','')).startswith(url+'#'), 'Blog schema identity mismatch')
    for key in ('author','publisher'):
        require(post.get(key,{}).get('name') == profile.data['name'], 'Unapproved schema author or publisher')
    faq = next(n for n in graph if n['@type']=='FAQPage')['mainEntity']
    visible = doc.select('.faq details')
    require(len(faq) == len(visible) and len(faq) >= 3, 'FAQ schema count mismatch')
    normalize = lambda text: ' '.join(text.split())
    for item, node in zip(faq,visible):
        question = node.select_one('summary h3')
        answer = node.select_one('div')
        require(question is not None and answer is not None, 'Visible FAQ structure missing')
        require(normalize(item['name']) == normalize(question.get_text(' ',strip=True)), 'FAQ schema question mismatch')
        require(normalize(item['acceptedAnswer']['text']) == normalize(answer.get_text(' ',strip=True)), 'FAQ schema answer mismatch')
