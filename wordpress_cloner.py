#!/usr/bin/env python3
"""
WordPress Website Cloner - Converts WordPress content to static HTML
Usage: python wordpress_cloner.py https://example.com
"""

import requests
from bs4 import BeautifulSoup
import os
import sys
import urllib.parse
from urllib.parse import urljoin, urlparse
import time
import re
from pathlib import Path
import json

class WordPressCloner:
    def __init__(self, base_url, output_dir="cloned_site"):
        self.base_url = base_url.rstrip('/')
        self.output_dir = output_dir
        self.visited_urls = set()
        self.downloaded_assets = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Create output directory
        Path(self.output_dir).mkdir(exist_ok=True)
        Path(f"{self.output_dir}/assets").mkdir(exist_ok=True)
        
    def is_same_domain(self, url):
        """Check if URL belongs to the same domain"""
        return urlparse(url).netloc == urlparse(self.base_url).netloc
    
    def clean_filename(self, filename):
        """Clean filename for filesystem compatibility"""
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = filename.strip()
        return filename[:200] if len(filename) > 200 else filename
    
    def download_file(self, url, local_path):
        """Download a file and save it locally"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(response.content)
            print(f"Downloaded: {url}")
            return True
        except Exception as e:
            print(f"Failed to download {url}: {e}")
            return False
    
    def get_local_asset_path(self, asset_url):
        """Generate local path for an asset"""
        parsed = urlparse(asset_url)
        path = parsed.path.lstrip('/')
        
        # Handle query parameters for dynamic assets
        if parsed.query:
            path += f"_{parsed.query.replace('&', '_').replace('=', '_')}"
        
        return os.path.join(self.output_dir, "assets", path)
    
    def download_assets(self, soup, page_url):
        """Download CSS, JS, images, and other assets"""
        assets = []
        
        # CSS files
        for link in soup.find_all('link', {'rel': 'stylesheet'}):
            href = link.get('href')
            if href:
                full_url = urljoin(page_url, href)
                if self.is_same_domain(full_url) and full_url not in self.downloaded_assets:
                    local_path = self.get_local_asset_path(full_url)
                    if self.download_file(full_url, local_path):
                        self.downloaded_assets.add(full_url)
                        assets.append((full_url, local_path))
        
        # JavaScript files
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src:
                full_url = urljoin(page_url, src)
                if self.is_same_domain(full_url) and full_url not in self.downloaded_assets:
                    local_path = self.get_local_asset_path(full_url)
                    if self.download_file(full_url, local_path):
                        self.downloaded_assets.add(full_url)
                        assets.append((full_url, local_path))
        
        # Images
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                full_url = urljoin(page_url, src)
                if self.is_same_domain(full_url) and full_url not in self.downloaded_assets:
                    local_path = self.get_local_asset_path(full_url)
                    if self.download_file(full_url, local_path):
                        self.downloaded_assets.add(full_url)
                        assets.append((full_url, local_path))
        
        return assets
    
    def update_asset_links(self, soup, assets):
        """Update HTML to use local asset paths"""
        for original_url, local_path in assets:
            # Make path relative to HTML file
            relative_path = os.path.relpath(local_path, self.output_dir)
            
            # Update CSS links
            for link in soup.find_all('link', href=True):
                if urljoin(self.base_url, link['href']) == original_url:
                    link['href'] = relative_path
            
            # Update script sources
            for script in soup.find_all('script', src=True):
                if urljoin(self.base_url, script['src']) == original_url:
                    script['src'] = relative_path
            
            # Update image sources
            for img in soup.find_all('img', src=True):
                if urljoin(self.base_url, img['src']) == original_url:
                    img['src'] = relative_path
    
    def get_wordpress_content(self):
        """Get WordPress content through various methods"""
        urls_to_process = set()
        
        # Start with homepage
        urls_to_process.add(self.base_url)
        
        # Try to get sitemap URLs
        sitemap_urls = [
            f"{self.base_url}/sitemap.xml",
            f"{self.base_url}/sitemap_index.xml",
            f"{self.base_url}/wp-sitemap.xml"
        ]
        
        for sitemap_url in sitemap_urls:
            try:
                response = self.session.get(sitemap_url, timeout=30)
                if response.status_code == 200:
                    print(f"Found sitemap: {sitemap_url}")
                    sitemap_soup = BeautifulSoup(response.content, 'xml')
                    
                    # Extract URLs from sitemap
                    for loc in sitemap_soup.find_all('loc'):
                        url = loc.text.strip()
                        if self.is_same_domain(url):
                            urls_to_process.add(url)
            except:
                continue
        
        # Try WordPress REST API
        try:
            api_posts_url = f"{self.base_url}/wp-json/wp/v2/posts"
            response = self.session.get(api_posts_url, timeout=30)
            if response.status_code == 200:
                posts = response.json()
                for post in posts:
                    if 'link' in post:
                        urls_to_process.add(post['link'])
                print(f"Found {len(posts)} posts via REST API")
        except:
            pass
        
        # Try WordPress RSS feeds
        feed_urls = [
            f"{self.base_url}/feed/",
            f"{self.base_url}/?feed=rss2",
            f"{self.base_url}/rss/"
        ]
        
        for feed_url in feed_urls:
            try:
                response = self.session.get(feed_url, timeout=30)
                if response.status_code == 200:
                    feed_soup = BeautifulSoup(response.content, 'xml')
                    for link in feed_soup.find_all('link'):
                        url = link.text.strip()
                        if self.is_same_domain(url):
                            urls_to_process.add(url)
                    break
            except:
                continue
        
        return list(urls_to_process)
    
    def save_page(self, url):
        """Download and save a single page"""
        if url in self.visited_urls:
            return
        
        try:
            print(f"Processing: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Download assets
            assets = self.download_assets(soup, url)
            
            # Update asset links in HTML
            self.update_asset_links(soup, assets)
            
            # Generate filename
            parsed_url = urlparse(url)
            if parsed_url.path == '/' or parsed_url.path == '':
                filename = "index.html"
            else:
                filename = parsed_url.path.strip('/').replace('/', '_') + ".html"
            
            filename = self.clean_filename(filename)
            filepath = os.path.join(self.output_dir, filename)
            
            # Save HTML
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(soup.prettify()))
            
            self.visited_urls.add(url)
            print(f"Saved: {filename}")
            
            # Extract internal links for further processing
            internal_links = set()
            for a in soup.find_all('a', href=True):
                link_url = urljoin(url, a['href'])
                if self.is_same_domain(link_url) and link_url not in self.visited_urls:
                    internal_links.add(link_url)
            
            return internal_links
            
        except Exception as e:
            print(f"Error processing {url}: {e}")
            return set()
    
    def clone_site(self, max_pages=100):
        """Main method to clone the WordPress site"""
        print(f"Starting to clone {self.base_url}")
        
        # Get initial URLs
        urls_to_process = self.get_wordpress_content()
        all_urls = set(urls_to_process)
        
        processed_count = 0
        
        while urls_to_process and processed_count < max_pages:
            current_url = urls_to_process.pop()
            
            if current_url in self.visited_urls:
                continue
            
            # Process the page
            new_links = self.save_page(current_url)
            
            if new_links:
                # Add new links to process
                for link in new_links:
                    if link not in all_urls:
                        urls_to_process.append(link)
                        all_urls.add(link)
            
            processed_count += 1
            
            # Be nice to the server
            time.sleep(1)
        
        print(f"\nCloning completed!")
        print(f"Pages processed: {processed_count}")
        print(f"Assets downloaded: {len(self.downloaded_assets)}")
        print(f"Output directory: {self.output_dir}")
        
        # Save a log of processed URLs
        with open(f"{self.output_dir}/processed_urls.txt", 'w') as f:
            for url in sorted(self.visited_urls):
                f.write(f"{url}\n")

def main():
    if len(sys.argv) != 2:
        print("Usage: python wordpress_cloner.py <wordpress_site_url>")
        print("Example: python wordpress_cloner.py https://example.com")
        sys.exit(1)
    
    site_url = sys.argv[1]
    
    # Validate URL
    if not site_url.startswith(('http://', 'https://')):
        site_url = 'https://' + site_url
    
    # Create output directory name based on domain
    domain = urlparse(site_url).netloc.replace('.', '_')
    output_dir = f"cloned_{domain}"
    
    cloner = WordPressCloner(site_url, output_dir)
    
    try:
        cloner.clone_site(max_pages=100)  # Adjust max_pages as needed
    except KeyboardInterrupt:
        print("\nCloning interrupted by user")
    except Exception as e:
        print(f"Error during cloning: {e}")

if __name__ == "__main__":
    main()
