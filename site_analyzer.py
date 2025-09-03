#!/usr/bin/env python3
"""
WordPress Site Analyzer - Check site size before cloning
Usage: python site_analyzer.py https://example.com
"""

import requests
from bs4 import BeautifulSoup
import sys
from urllib.parse import urlparse, urljoin
import json

class SiteAnalyzer:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def check_sitemap(self):
        """Check sitemap for URL count"""
        sitemap_urls = [
            f"{self.base_url}/sitemap.xml",
            f"{self.base_url}/sitemap_index.xml", 
            f"{self.base_url}/wp-sitemap.xml",
            f"{self.base_url}/sitemap-index.xml"
        ]
        
        total_urls = 0
        found_sitemaps = []
        
        for sitemap_url in sitemap_urls:
            try:
                response = self.session.get(sitemap_url, timeout=10)
                if response.status_code == 200:
                    print(f"✅ Found sitemap: {sitemap_url}")
                    found_sitemaps.append(sitemap_url)
                    
                    soup = BeautifulSoup(response.content, 'xml')
                    urls = soup.find_all('loc')
                    print(f"   📄 URLs in this sitemap: {len(urls)}")
                    total_urls += len(urls)
                    
                    # Show some example URLs
                    for i, url in enumerate(urls[:5]):
                        print(f"      • {url.text}")
                    if len(urls) > 5:
                        print(f"      ... and {len(urls) - 5} more")
                    print()
                    
            except Exception as e:
                continue
        
        if not found_sitemaps:
            print("❌ No sitemaps found")
        
        return total_urls

    def check_rest_api(self):
        """Check WordPress REST API for content count"""
        endpoints = [
            ('/wp-json/wp/v2/posts', 'Posts'),
            ('/wp-json/wp/v2/pages', 'Pages'),
            ('/wp-json/wp/v2/categories', 'Categories'),
            ('/wp-json/wp/v2/tags', 'Tags')
        ]
        
        total_content = 0
        
        print("📡 Checking WordPress REST API...")
        for endpoint, content_type in endpoints:
            try:
                url = f"{self.base_url}{endpoint}?per_page=1"
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    # Get total count from headers
                    total_items = response.headers.get('X-WP-Total', 0)
                    print(f"   📊 {content_type}: {total_items}")
                    total_content += int(total_items)
                else:
                    print(f"   ❌ {content_type}: Not accessible")
            except Exception as e:
                print(f"   ❌ {content_type}: Error ({e})")
        
        if total_content == 0:
            print("❌ WordPress REST API not accessible or no content found")
        
        return total_content

    def check_feeds(self):
        """Check RSS feeds for post count"""
        feed_urls = [
            f"{self.base_url}/feed/",
            f"{self.base_url}/?feed=rss2",
            f"{self.base_url}/rss/"
        ]
        
        print("📰 Checking RSS feeds...")
        for feed_url in feed_urls:
            try:
                response = self.session.get(feed_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'xml')
                    items = soup.find_all('item')
                    print(f"✅ Feed found: {feed_url}")
                    print(f"   📄 Recent items: {len(items)} (feeds usually show latest 10-20)")
                    return True
            except:
                continue
        
        print("❌ No RSS feeds found")
        return False

    def estimate_size(self):
        """Provide size estimation and recommendations"""
        print("=" * 60)
        print("📊 SITE SIZE ANALYSIS COMPLETE")
        print("=" * 60)
        
        sitemap_count = self.check_sitemap()
        api_count = self.check_rest_api()
        self.check_feeds()
        
        print("\n🎯 RECOMMENDATIONS:")
        
        max_count = max(sitemap_count, api_count)
        
        if max_count == 0:
            print("⚠️  Could not determine site size automatically")
            print("   • Try running the cloner with max_pages=20 first")
            print("   • Monitor the output to see how many pages it finds")
            
        elif max_count <= 50:
            print("🟢 SMALL SITE (≤50 pages)")
            print("   • Safe to clone with default settings")
            print("   • Estimated time: 2-5 minutes")
            print("   • Use: max_pages=100 (default)")
            
        elif max_count <= 200:
            print("🟡 MEDIUM SITE (50-200 pages)")
            print("   • Moderate cloning time expected")
            print("   • Estimated time: 5-15 minutes")
            print("   • Use: max_pages=250")
            
        elif max_count <= 500:
            print("🟠 LARGE SITE (200-500 pages)")
            print("   • Consider running in smaller batches")
            print("   • Estimated time: 15-45 minutes")
            print("   • Use: max_pages=100 first, then increase")
            
        else:
            print("🔴 VERY LARGE SITE (>500 pages)")
            print("   • Definitely run in batches")
            print("   • Consider which sections you actually need")
            print("   • Estimated time: 1+ hours")
            print("   • Use: max_pages=50 for testing")
        
        print(f"\n📈 Estimated total pages: {max_count}")
        print(f"💾 Estimated disk space needed: {max_count * 0.5:.1f}-{max_count * 2:.1f} MB")

def main():
    if len(sys.argv) != 2:
        print("Usage: python site_analyzer.py <wordpress_site_url>")
        print("Example: python site_analyzer.py https://example.com")
        sys.exit(1)
    
    site_url = sys.argv[1]
    
    if not site_url.startswith(('http://', 'https://')):
        site_url = 'https://' + site_url
    
    print(f"🔍 Analyzing WordPress site: {site_url}")
    print("=" * 60)
    
    analyzer = SiteAnalyzer(site_url)
    analyzer.estimate_size()

if __name__ == "__main__":
    main()
