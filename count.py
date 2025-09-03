#!/usr/bin/env python3
import sys, re, time, argparse, xml.etree.ElementTree as ET
from collections import deque
from urllib.parse import urljoin, urlparse, urldefrag
import requests
from bs4 import BeautifulSoup

UA = "SiteCounter/1.0 (+https://example.org)"
HEADERS = {"User-Agent": UA}
TIMEOUT = 8

def host_key(url):
    host = urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host

def is_html(resp):
    ctype = resp.headers.get("Content-Type","").lower()
    return "text/html" in ctype or "application/xhtml" in ctype

def normalize_url(base, href):
    if not href:
        return None
    href = href.strip()
    # ignore mailto:, tel:, javascript:
    if re.match(r"^(mailto:|tel:|javascript:|data:)", href, re.I):
        return None
    full = urljoin(base, href)
    full, _frag = urldefrag(full)
    # drop obvious binaries
    if re.search(r"\.(jpg|jpeg|png|gif|webp|svg|pdf|zip|gz|rar|7z|mp4|mp3|mov|avi|wmv|css|js)(\?|$)", full, re.I):
        return None
    return full

def fetch(url):
    return requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)

def sitemap_urls(start_url, max_urls=50000):
    # Try /sitemap.xml (and recurse if it’s a sitemap index)
    base = f"{urlparse(start_url).scheme}://{urlparse(start_url).netloc}"
    sm_url = urljoin(base, "/sitemap.xml")
    try:
        r = fetch(sm_url)
        if r.status_code != 200:
            return set()
        urls = set()
        root = ET.fromstring(r.content)
        # namespaces are optional; handle both
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        # detect if it's an index
        sitemaps = root.findall(".//sm:sitemap/sm:loc", ns) or root.findall(".//sitemap/loc")
        if sitemaps:
            for loc in sitemaps:
                try:
                    r2 = fetch(loc.text.strip())
                    if r2.status_code != 200:
                        continue
                    sub = ET.fromstring(r2.content)
                    for u in (sub.findall(".//sm:url/sm:loc", ns) or sub.findall(".//url/loc")):
                        urls.add(urldefrag(u.text.strip())[0])
                        if len(urls) >= max_urls: return urls
                except Exception:
                    continue
            return urls
        # plain urlset
        for u in (root.findall(".//sm:url/sm:loc", ns) or root.findall(".//url/loc")):
            urls.add(urldefrag(u.text.strip())[0])
            if len(urls) >= max_urls: break
        return urls
    except Exception:
        return set()

def crawl(start_url, max_pages=500, delay=0.5):
    base_host = host_key(start_url)
    base_origin = f"{urlparse(start_url).scheme}://{urlparse(start_url).netloc}"
    q = deque([start_url])
    seen = set()

    while q and len(seen) < max_pages:
        url = q.popleft()
        if url in seen: 
            continue
        try:
            r = fetch(url)
        except Exception:
            continue
        if r.status_code >= 400:
            continue
        seen.add(url)
        if not is_html(r): 
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        # follow <a> and rel=next
        for a in soup.find_all(["a", "link"], href=True):
            nxt = normalize_url(url, a.get("href"))
            if not nxt: 
                continue
            if host_key(nxt) != base_host: 
                continue
            if nxt not in seen:
                q.append(nxt)
        time.sleep(delay)
    return seen

def main():
    ap = argparse.ArgumentParser(description="Count webpages on a site (sitemap first, then crawl).")
    ap.add_argument("url", help="Start URL, e.g., https://www.example.com")
    ap.add_argument("--max", type=int, default=500, help="Max pages to crawl (default 500)")
    ap.add_argument("--no-sitemap", action="store_true", help="Skip sitemap and crawl only")
    args = ap.parse_args()

    start = args.url if re.match(r"^https?://", args.url) else "https://" + args.url

    pages = set()
    if not args.no_sitemap:
        sm = sitemap_urls(start)
        # keep only same-site
        pages |= {u for u in sm if host_key(u) == host_key(start)}

    if not pages:
        pages = crawl(start, max_pages=args.max)

    print(f"Discovered {len(pages)} pages{' (crawl-capped)' if len(pages)>=args.max else ''}")
    for u in sorted(pages):
        print(u)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage: python3 count.py https://www.example.com")
        sys.exit(1)
    main()