import json,re,sys,urllib.request
sys.path.insert(0,'/Users/kevinkreative/genseo/scripts')
import genseo_config as c
ua={'User-Agent':'Mozilla/5.0'}
u=f'https://{c.SHOP}/admin/api/{c.API}/blogs/104008483131/articles/635104854331.json'
a=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'X-Shopify-Access-Token':c.TOKEN}),timeout=45))['article']
assert a['published_at'], 'Unpublished article'
url='https://wellnessnest.co/blogs/news/'+a['handle']
r=urllib.request.urlopen(urllib.request.Request(url,headers=ua),timeout=45)
page=r.read().decode(); assert r.status==200
imgs=[a['image']['src']]+re.findall(r'<img[^>]+src=["\']([^"\']+)',a['body_html'])
assert len(imgs)==4, len(imgs)
for image in imgs:
 response=urllib.request.urlopen(urllib.request.Request(image,headers=ua),timeout=45)
 assert response.status==200 and response.headers.get('Content-Type','').startswith('image/'),image
 assert image.split('?')[0].rsplit('/',1)[-1] in page,image
assert 'shop-this-article' in page
assert re.search(r'data-liquid-handles=["\'][^"\']*fusiforce-creatine-gummies',page)
assert 'FAQPage' in page and ('BlogPosting' in page or '"Article"' in page)
print(json.dumps({'article_id':a['id'],'title':a['title'],'published_at':a['published_at'],'frontend_http':r.status,'cdn_images':'4/4','rendered_images':'4/4','schema':'PASS','widget':'PASS','url':url},indent=2))
