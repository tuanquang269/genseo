import sys
import os
import time
import urllib.request
import urllib.error
import urllib.parse
from xml.etree import ElementTree as ET
import csv
import subprocess

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--user", "--break-system-packages", "--quiet"])

try:
    from bs4 import BeautifulSoup
except ImportError:
    install('beautifulsoup4')
    from bs4 import BeautifulSoup

def get_xml_urls(sitemap_url):
    urls = []
    try:
        req = urllib.request.Request(sitemap_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        res = urllib.request.urlopen(req)
        xml_data = res.read()
        root = ET.fromstring(xml_data)
        
        # Parse nested sitemaps
        if root.tag.endswith('sitemapindex'):
            for sitemap in root.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap'):
                loc = sitemap.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text
                # Prioritize blogs for testing
                if 'blog' in loc: 
                    urls.extend(get_xml_urls(loc))
        elif root.tag.endswith('urlset'):
            for url in root.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                loc = url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text
                urls.append(loc)
    except Exception as e:
        print(f"Failed to parse sitemap {sitemap_url}: {e}")
    return urls

def check_link(url, cache):
    if url in cache:
        return cache[url]
    
    try:
        req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
        urllib.request.urlopen(req, timeout=5)
        cache[url] = 200
        return 200
    except urllib.error.HTTPError as e:
        cache[url] = e.code
        return e.code
    except Exception as e:
        cache[url] = 500
        return 500

def crawl_site(base_url, max_urls=50):
    sitemap_url = f"{base_url.rstrip('/')}/sitemap.xml"
    print(f"🤖 Fetching sitemaps from {sitemap_url}...")
    urls = get_xml_urls(sitemap_url)
    
    if not urls:
        print("No URLs extracted. Sitemap might be blocking bots.")
        return
        
    urls = urls[:max_urls] 
    
    results = []
    link_cache = {}
    
    for i, url in enumerate(urls):
        print(f"[{i+1}/{len(urls)}] Crawling: {url} (Sleeping 2s for Safety...)")
        time.sleep(2) 
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            res = urllib.request.urlopen(req, timeout=10)
            html = res.read()
            soup = BeautifulSoup(html, 'html.parser')
            
            h1s = soup.find_all('h1')
            h1_status = "OK" if len(h1s) == 1 else ("Missing" if len(h1s) == 0 else "Multiple")
            
            images = soup.find_all('img')
            missing_alts = sum(1 for img in images if not img.get('alt'))
            
            links = soup.find_all('a')
            broken_links = []
            for a in links:
                href = a.get('href')
                if href and href.startswith('/'):
                    full_link = urllib.parse.urljoin(base_url, href)
                    status = check_link(full_link, link_cache)
                    if status == 404:
                        broken_links.append(href)
                        
            results.append({
                "url": url,
                "h1_status": h1_status,
                "missing_alts": missing_alts,
                "broken_links": "|".join(broken_links)
            })
            
        except Exception as e:
            print(f"Failed to scan {url}: {e}")
            
    csv_path = os.path.expanduser("~/genseo/CRAWL_REPORT.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["url", "h1_status", "missing_alts", "broken_links"])
        writer.writeheader()
        writer.writerows(results)
        
    print(f"\n✅ Done! Report saved to {csv_path}")

    issues_count = sum(1 for r in results if r['broken_links'] or r['h1_status'] != 'OK' or r['missing_alts'] > 0)
    create_optimizer_ticket(issues_count, csv_path)

def create_optimizer_ticket(issues_count, csv_path):
    ticket_path = os.path.expanduser("~/genseo/OPTIMIZER_ACTION.md")
    content = f"# 🛠️ Optimizer Protocol Triggered\n\n"
    content += f"Crawler found anomalies in {issues_count} pages.\n"
    content += f"Run `/genseo-seo-optimizer` and pass it this CSV: `{csv_path}`\n\n"
    
    with open(ticket_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
if __name__ == '__main__':
    domain = "https://yourdomain.com"
    if len(sys.argv) > 1:
        domain = sys.argv[1]
    crawl_site(domain, max_urls=10) # 10 urls limit for testing
