import sys, re, json, urllib.request, collections
UA={"User-Agent":"Mozilla/5.0 GenSEO-verify"}
def get(u):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=40); return r.status, r.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e: return e.code,""
    except Exception as e: return str(e),""
seen={}; bad=0
for h in sys.argv[1:]:
    url="https://wellnessnest.co/blogs/news/"+h
    st,html=get(url); errs=[]
    if st!=200: errs.append("page %s"%st)
    tags=re.findall(r'<a[^>]*data-genseo-cluster-link[^>]*>',html)
    hrefs=[re.search(r'href="([^"]+)"',t).group(1) for t in tags if 'href="' in t]
    dup=[k for k,v in collections.Counter(hrefs).items() if v>2]
    if dup: errs.append("dup %s"%dup)
    if not hrefs: errs.append("no markers")
    for x in set(hrefs):
        full=x if x.startswith("http") else "https://wellnessnest.co"+x
        if full not in seen: seen[full]=get(full)[0]
        if seen[full]!=200: errs.append("link %s %s"%(x,seen[full]))
    types=[]
    for blk in re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>',html,re.S):
        try: d=json.loads(blk)
        except Exception: errs.append("jsonld parse"); continue
        for it in (d if isinstance(d,list) else d.get("@graph",[d])):
            t=it.get("@type") if isinstance(it,dict) else None
            types+= t if isinstance(t,list) else [t]
    a=sum(1 for t in types if t in("Article","BlogPosting")); f=types.count("FAQPage")
    if a!=1: errs.append("Article blocks %d"%a)
    if f>1: errs.append("FAQPage %d"%f)
    if "</html>" not in html: errs.append("render")
    bad+=bool(errs)
    print(("OK  " if not errs else "FAIL")+" %s links=%d uniq=%d article=%d faq=%d %s"%(h,len(hrefs),len(set(hrefs)),a,f,"; ".join(errs)))
print("VERIFY_DONE bad=%d"%bad); sys.exit(1 if bad else 0)
