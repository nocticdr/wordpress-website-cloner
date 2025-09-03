#!/usr/bin/env python3
"""
Fixed Combined WordPress Site Analyzer & Interactive Cloner
Usage: python fixed_combined_cloner.py https://example.com
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
import random

class WordPressSiteAnalyzer:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def check_rest_api(self):
        """Check WordPress REST API for content count"""
        endpoints = [
            ('/wp-json/wp/v2/posts', 'Posts'),
            ('/wp-json/wp/v2/pages', 'Pages'),
            ('/wp-json/wp/v2/categories', 'Categories'),
            ('/wp-json/wp/v2/tags', 'Tags')
        ]
        
        content_counts = {}
        
        print("📡 Checking WordPress REST API...")
        for endpoint, content_type in endpoints:
            try:
                url = f"{self.base_url}{endpoint}?per_page=1"
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    total_items = int(response.headers.get('X-WP-Total', 0))
                    print(f"   📊 {content_type}: {total_items}")
                    content_counts[content_type.lower()] = total_items
                else:
                    content_counts[content_type.lower()] = 0
            except Exception as e:
                content_counts[content_type.lower()] = 0
        
        return content_counts

    def analyze_quick(self):
        """Quick analysis for the interactive cloner"""
        print(f"🔍 Analyzing {self.base_url}...")
        content_counts = self.check_rest_api()
        
        posts = content_counts.get('posts', 0)
        pages = content_counts.get('pages', 0)
        
        print(f"📋 QUICK ANALYSIS:")
        print(f"   📝 Posts: {posts}")
        print(f"   📄 Pages: {pages}")
        print(f"   📂 Categories: {content_counts.get('categories', 0)}")
        print(f"   🏷️  Tags: {content_counts.get('tags', 0)}")
        
        total_pages = posts + pages
        
        if total_pages <= 50:
            recommendation = "🟢 SMALL SITE - Safe to clone fully"
        elif total_pages <= 200:
            recommendation = "🟡 MEDIUM SITE - Consider batching"
        elif total_pages <= 500:
            recommendation = "🟠 LARGE SITE - Definitely use batches"
        else:
            recommendation = "🔴 VERY LARGE SITE - Clone selectively"
        
        print(f"   {recommendation}")
        
        return content_counts


class InteractiveWordPressCloner:
    def __init__(self, base_url, output_dir="cloned_site"):
        self.base_url = base_url.rstrip('/')
        self.output_dir = output_dir
        self.visited_urls = set()
        self.downloaded_assets = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        # Default settings
        self.max_pages = 50
        self.max_depth = 2
        self.clone_mode = 'minimal'
        self.random_count = 50
        self.delay_between_requests = 1
        
        # Create output directory
        Path(self.output_dir).mkdir(exist_ok=True)
        Path(f"{self.output_dir}/assets").mkdir(exist_ok=True)

    def get_user_preferences(self, content_counts=None):
        """Interactive setup for cloning preferences"""
        print("\n" + "="*60)
        print("🛠️  CLONING CONFIGURATION")
        print("="*60)
        
        if content_counts:
            posts = content_counts.get('posts', 0)
            pages = content_counts.get('pages', 0)
            print(f"Site has {posts} posts and {pages} pages")
        
        # Max pages
        print(f"\n1️⃣ How many pages maximum do you want to clone?")
        print(f"   Current default: {self.max_pages}")
        print("   Recommended for testing: 20-50")
        print("   For larger clones: 200-500+")
        
        while True:
            try:
                user_input = input("   Enter max pages (or press Enter for default): ").strip()
                if user_input == "":
                    break
                self.max_pages = int(user_input)
                if self.max_pages > 0:
                    break
                print("   Please enter a positive number")
            except ValueError:
                print("   Please enter a valid number")
        
        # Clone mode - CORRECTED ORDER AND LOGIC
        print(f"\n2️⃣ What content do you want to clone?")
        print("   1. Recent posts only (quick test)")
        print("   2. Homepage + key pages only")
        print("   3. Homepage + random sample of posts")
        print("   4. All posts and pages (full clone)")
        
        while True:
            choice = input("   Enter choice (1/2/3/4): ").strip()
            if choice == "1":
                self.clone_mode = 'recent'
                print(f"   This will clone recent posts up to {self.max_pages} total pages")
                break
            elif choice == "2":
                self.clone_mode = 'minimal'
                print(f"   This will clone homepage + key pages up to {self.max_pages} total pages")
                break
            elif choice == "3":
                self.clone_mode = 'homepage_plus_random'
                while True:
                    try:
                        default_random = min(self.max_pages - 10, 30)  # Leave room for homepage + key pages
                        user_input = input(f"   How many random posts? (default {default_random}): ").strip()
                        if user_input == "":
                            self.random_count = default_random
                            break
                        self.random_count = int(user_input)
                        if self.random_count > 0:
                            break
                        print("   Please enter a positive number")
                    except ValueError:
                        print("   Please enter a valid number")
                print(f"   This will clone homepage + key pages + {self.random_count} random posts")
                break
            elif choice == "4":
                self.clone_mode = 'all'
                print(f"   This will attempt to clone all content up to {self.max_pages} pages")
                break
            else:
                print("   Please enter 1, 2, 3, or 4")
        
        # Crawl depth
        print(f"\n3️⃣ How deep should the crawler go?")
        print("   1 = Only direct links")
        print("   2 = Two levels deep (recommended)")
        print("   3 = Three levels deep")
        
        while True:
            try:
                user_input = input(f"   Enter depth (1-3, default {self.max_depth}): ").strip()
                if user_input == "":
                    break
                depth = int(user_input)
                if 1 <= depth <= 3:
                    self.max_depth = depth
                    break
                print("   Please enter 1, 2, or 3")
            except ValueError:
                print("   Please enter a valid number")
        
        # Request delay
        print(f"\n4️⃣ Delay between requests (be nice to the server)")
        print(f"   Current: {self.delay_between_requests} seconds")
        
        while True:
            try:
                user_input = input("   Enter delay in seconds (or press Enter): ").strip()
                if user_input == "":
                    break
                delay = float(user_input)
                if delay >= 0.5:
                    self.delay_between_requests = delay
                    break
                print("   Please enter at least 0.5 seconds")
            except ValueError:
                print("   Please enter a valid number")
        
        # Summary
        print(f"\n✅ CONFIGURATION SUMMARY:")
        print(f"   📊 Max pages: {self.max_pages}")  # This should show your input, not be overridden
        print(f"   📝 Clone mode: {self.clone_mode}")
        if self.clone_mode in ['homepage_plus_random']:
            print(f"   🎲 Random posts: {self.random_count}")
        print(f"   🔍 Crawl depth: {self.max_depth}")
        print(f"   ⏱️  Request delay: {self.delay_between_requests}s")
        
        confirm = input("\n   Proceed with these settings? (y/n): ").strip().lower()
        return confirm in ['y', 'yes', '']

    def get_urls_by_mode(self):
        """Get URLs based on clone mode - always includes homepage and its linked pages"""
        urls = set()
        
        # ALWAYS start with homepage
        urls.add(self.base_url)
        print(f"✅ Added homepage: {self.base_url}")
        
        # Get all links from homepage (this is what you want for all modes)
        homepage_links = self._get_homepage_links()
        urls.update(homepage_links)
        print(f"✅ Added {len(homepage_links)} links found on homepage")
        
        if self.clone_mode == 'recent':
            # Option 1: Recent posts only (quick test)
            recent_posts = self._get_recent_posts(20)
            urls.update(recent_posts)
            print(f"✅ Added {len(recent_posts)} recent posts")
        
        elif self.clone_mode == 'minimal':
            # Option 2: Homepage + key pages only
            key_pages = self._get_key_pages()
            urls.update(key_pages)
            print(f"✅ Added {len(key_pages)} key pages (About, Contact, etc.)")
        
        elif self.clone_mode == 'homepage_plus_random':
            # Option 3: Homepage + random sample of posts
            key_pages = self._get_key_pages()  # Include key pages too
            urls.update(key_pages)
            random_posts = self._get_random_posts(self.random_count)
            urls.update(random_posts)
            print(f"✅ Added {len(key_pages)} key pages + {len(random_posts)} random posts")
        
        elif self.clone_mode == 'all':
            # Option 4: All posts and pages (full clone)
            all_posts = self._get_all_posts()
            all_pages = self._get_all_pages()
            urls.update(all_posts)
            urls.update(all_pages)
            print(f"✅ Added {len(all_posts)} posts + {len(all_pages)} pages")
        
        return list(urls)
    
    def _get_homepage_links(self):
        """Extract all internal links from the homepage"""
        links = set()
        try:
            print("🏠 Scanning homepage for internal links...")
            response = self.session.get(self.base_url, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    full_url = urljoin(self.base_url, href)
                    if (self.is_same_domain(full_url) and 
                        full_url != self.base_url and  # Don't add homepage twice
                        not href.startswith('#') and  # Skip anchors
                        not href.startswith('mailto:') and  # Skip email links
                        not full_url.endswith(('.jpg', '.png', '.pdf', '.zip'))):  # Skip file downloads
                        links.add(full_url)
        except Exception as e:
            print(f"⚠️  Could not scan homepage: {e}")
        
        return links
    
    def _get_recent_posts(self, count=20):
        """Get recent posts via API"""
        posts = set()
        try:
            api_url = f"{self.base_url}/wp-json/wp/v2/posts?per_page={count}&orderby=date"
            response = self.session.get(api_url, timeout=30)
            if response.status_code == 200:
                post_data = response.json()
                for post in post_data:
                    if 'link' in post:
                        posts.add(post['link'])
        except Exception as e:
            print(f"⚠️  Could not get recent posts: {e}")
        return posts
    
    def _get_key_pages(self):
        """Get key WordPress pages (About, Contact, etc.)"""
        pages = set()
        try:
            api_url = f"{self.base_url}/wp-json/wp/v2/pages?per_page=20"
            response = self.session.get(api_url, timeout=30)
            if response.status_code == 200:
                page_data = response.json()
                for page in page_data:
                    if 'link' in page:
                        pages.add(page['link'])
        except Exception as e:
            print(f"⚠️  Could not get pages: {e}")
        return pages
    
    def _get_random_posts(self, count):
        """Get random sample of posts"""
        posts = set()
        try:
            # Get total count first
            api_url = f"{self.base_url}/wp-json/wp/v2/posts?per_page=1"
            response = self.session.get(api_url, timeout=30)
            total_posts = int(response.headers.get('X-WP-Total', 0))
            
            if total_posts > 0:
                # Collect posts from multiple pages for better randomization
                all_posts = []
                pages_to_fetch = min(5, (total_posts // 100) + 1)
                
                for page in range(1, pages_to_fetch + 1):
                    api_url = f"{self.base_url}/wp-json/wp/v2/posts?per_page=100&page={page}"
                    response = self.session.get(api_url, timeout=30)
                    if response.status_code == 200:
                        page_posts = response.json()
                        all_posts.extend(page_posts)
                
                # Random sample
                if all_posts:
                    sample_size = min(count, len(all_posts))
                    random_posts = random.sample(all_posts, sample_size)
                    for post in random_posts:
                        if 'link' in post:
                            posts.add(post['link'])
        except Exception as e:
            print(f"⚠️  Could not get random posts: {e}")
        return posts
    
    def _get_all_posts(self):
        """Get all posts via API"""
        posts = set()
        try:
            page = 1
            while len(posts) < 500:  # Reasonable limit
                api_url = f"{self.base_url}/wp-json/wp/v2/posts?per_page=100&page={page}"
                response = self.session.get(api_url, timeout=30)
                if response.status_code == 200:
                    page_posts = response.json()
                    if not page_posts:  # No more posts
                        break
                    for post in page_posts:
                        if 'link' in post:
                            posts.add(post['link'])
                    page += 1
                else:
                    break
        except Exception as e:
            print(f"⚠️  Could not get all posts: {e}")
        return posts
    
    def _get_all_pages(self):
        """Get all pages via API"""
        pages = set()
        try:
            api_url = f"{self.base_url}/wp-json/wp/v2/pages?per_page=100"
            response = self.session.get(api_url, timeout=30)
            if response.status_code == 200:
                page_data = response.json()
                for page in page_data:
                    if 'link' in page:
                        pages.add(page['link'])
        except Exception as e:
            print(f"⚠️  Could not get all pages: {e}")
        return pages

    def is_same_domain(self, url):
        return urlparse(url).netloc == urlparse(self.base_url).netloc

    def clean_filename(self, filename):
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        return filename[:200] if len(filename) > 200 else filename

    def download_file(self, url, local_path):
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(response.content)
            return True
        except:
            return False

    def get_local_asset_path(self, asset_url):
        parsed = urlparse(asset_url)
        path = parsed.path.lstrip('/')
        if parsed.query:
            path += f"_{parsed.query.replace('&', '_').replace('=', '_')}"
        return os.path.join(self.output_dir, "assets", path)

    def download_assets(self, soup, page_url):
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
        """Update asset links to use local paths"""
        for original_url, local_path in assets:
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
        
        return soup

    def convert_to_relative_links(self, soup, current_url):
        """Convert all internal links to relative links"""
        base_domain = urlparse(self.base_url).netloc
        current_path = urlparse(current_url).path
        
        # Convert all anchor links
        for a in soup.find_all('a', href=True):
            href = a['href']
            
            # Skip external links, anchors, mailto, tel, etc.
            if (href.startswith('#') or 
                href.startswith('mailto:') or 
                href.startswith('tel:') or 
                href.startswith('javascript:') or
                href.startswith('data:')):
                continue
            
            # Convert internal absolute links to relative
            parsed_href = urlparse(href)
            if parsed_href.netloc == base_domain or not parsed_href.netloc:
                # Make it relative
                full_url = urljoin(self.base_url, href)
                parsed_full = urlparse(full_url)
                
                # Generate a relative filename
                if parsed_full.path == '/' or parsed_full.path == '':
                    relative_file = 'index.html'
                else:
                    relative_file = parsed_full.path.strip('/').replace('/', '_') + '.html'
                
                # Clean the filename
                relative_file = self.clean_filename(relative_file)
                a['href'] = relative_file
                
                # Add title attribute for better UX
                if not a.get('title') and a.get_text(strip=True):
                    a['title'] = f"Internal link: {a.get_text(strip=True)[:50]}"
        
        return soup

    def convert_to_relative_links(self, soup, current_url):
        """Convert all internal links to relative links"""
        base_domain = urlparse(self.base_url).netloc
        
        # Convert all anchor links
        for a in soup.find_all('a', href=True):
            href = a['href']
            
            # Skip external links, anchors, mailto, tel, etc.
            if (href.startswith('#') or 
                href.startswith('mailto:') or 
                href.startswith('tel:') or 
                href.startswith('javascript:') or
                href.startswith('data:')):
                continue
            
            # Convert internal absolute links to relative
            parsed_href = urlparse(href)
            if parsed_href.netloc == base_domain or not parsed_href.netloc:
                # Make it relative
                full_url = urljoin(self.base_url, href)
                parsed_full = urlparse(full_url)
                
                # Generate a relative filename
                if parsed_full.path == '/' or parsed_full.path == '':
                    relative_file = 'index.html'
                else:
                    relative_file = parsed_full.path.strip('/').replace('/', '_') + '.html'
                
                # Clean the filename
                relative_file = self.clean_filename(relative_file)
                a['href'] = relative_file
                
                # Add title attribute for better UX
                if not a.get('title') and a.get_text(strip=True):
                    a['title'] = f"Internal link: {a.get_text(strip=True)[:50]}"
        
        # Convert form actions
        for form in soup.find_all('form', action=True):
            action = form['action']
            parsed_action = urlparse(action)
            if parsed_action.netloc == base_domain or not parsed_action.netloc:
                # For forms, point to original site with warning
                if not action.startswith('http'):
                    form['action'] = urljoin(self.base_url, action)
                # Add a note that forms won't work in static version
                form_note = soup.new_tag('div', style='background: #fff3cd; padding: 10px; margin: 5px 0; border: 1px solid #ffeaa7; border-radius: 4px; font-size: 14px;')
                form_note.string = '⚠️ Note: This form points to the original website and may not work in this static version.'
                form.insert_before(form_note)
        
        return soup

    def save_page(self, url):
        if url in self.visited_urls:
            return set()
        
        try:
            print(f"🌐 Processing: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Download assets and update their links
            assets = self.download_assets(soup, url)
            soup = self.update_asset_links(soup, assets)
            
            # Convert all internal links to relative links
            soup = self.convert_to_relative_links(soup, url)
            
            # Add a note at the top indicating this is a static clone
            if url == self.base_url:  # Only add to homepage
                clone_note = soup.new_tag('div', style='background: #e3f2fd; padding: 15px; margin: 10px 0; border-left: 4px solid #2196f3; font-family: Arial, sans-serif;')
                clone_note.string = f'📋 Static clone of {self.base_url} - Some dynamic features may not work. Original site: '
                original_link = soup.new_tag('a', href=self.base_url, target='_blank', style='color: #2196f3; text-decoration: none; font-weight: bold;')
                original_link.string = 'Visit Original'
                clone_note.append(original_link)
                
                # Insert after body tag or at the beginning
                body = soup.find('body')
                if body and body.contents:
                    body.insert(0, clone_note)
                else:
                    # Fallback: add after head
                    head = soup.find('head')
                    if head:
                        head.insert_after(clone_note)
            
            # Save HTML
            parsed_url = urlparse(url)
            if parsed_url.path == '/' or parsed_url.path == '':
                filename = "index.html"
            else:
                filename = parsed_url.path.strip('/').replace('/', '_') + ".html"
            
            filename = self.clean_filename(filename)
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(soup.prettify()))
            
            self.visited_urls.add(url)
            print(f"   ✅ Saved: {filename}")
            
            # Extract internal links
            internal_links = set()
            for a in soup.find_all('a', href=True):
                link_url = urljoin(url, a['href'])
                if (self.is_same_domain(link_url) and 
                    link_url not in self.visited_urls and
                    not link_url.endswith(('.jpg', '.png', '.pdf', '.zip'))):
                    internal_links.add(link_url)
            
            return internal_links
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return set()

    def clone_site(self):
        print(f"\n🚀 Starting clone of {self.base_url}")
        
        # Get URLs to process
        urls_to_process = self.get_urls_by_mode()
        print(f"\n📋 Found {len(urls_to_process)} URLs")
        
        if len(urls_to_process) > self.max_pages:
            urls_to_process = urls_to_process[:self.max_pages]
            print(f"🎯 Limited to {self.max_pages} pages")
        
        # Process pages
        processed = 0
        for url in urls_to_process:
            if processed >= self.max_pages:
                break
            
            self.save_page(url)
            processed += 1
            time.sleep(self.delay_between_requests)
        
        # Final summary
        print(f"\n🎉 CLONING COMPLETED!")
        print(f"📊 Pages processed: {processed}")
        print(f"📁 Output directory: {self.output_dir}")
        print(f"🌐 Open {self.output_dir}/index.html to view")


def main():
    if len(sys.argv) != 2:
        print("Usage: python fixed_combined_cloner.py <wordpress_site_url>")
        sys.exit(1)
    
    site_url = sys.argv[1]
    if not site_url.startswith(('http://', 'https://')):
        site_url = 'https://' + site_url
    
    print(f"🔍 Combined WordPress Analyzer & Cloner")
    print(f"🎯 Target: {site_url}")
    
    # Quick analysis
    try:
        analyzer = WordPressSiteAnalyzer(site_url)
        content_counts = analyzer.analyze_quick()
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        content_counts = {}
    
    # Create output directory
    domain = urlparse(site_url).netloc.replace('.', '_')
    output_dir = f"cloned_{domain}"
    
    # Interactive cloning
    cloner = InteractiveWordPressCloner(site_url, output_dir)
    
    if cloner.get_user_preferences(content_counts):
        try:
            cloner.clone_site()
        except KeyboardInterrupt:
            print(f"\n⏹️  Interrupted - partial results in {output_dir}")
    else:
        print("❌ Cancelled")


if __name__ == "__main__":
    main()