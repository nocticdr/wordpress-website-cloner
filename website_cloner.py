#!/usr/bin/env python3
"""
Complete WordPress Site Analyzer & Interactive Cloner with Custom URLs
Usage: python complete_wordpress_cloner.py https://example.com
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

    def is_same_domain(self, url):
        return urlparse(url).netloc == urlparse(self.base_url).netloc

    def _get_homepage_links(self):
        """Extract all internal links from the homepage"""
        links = set()
        try:
            print("🔍 Scanning homepage for internal links...")
            response = self.session.get(self.base_url, timeout=15)
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

    def _extract_internal_links(self, soup, base_url):
        """Extract all internal links from a soup object"""
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = urljoin(base_url, href)
            if (self.is_same_domain(full_url) and 
                full_url != base_url and  # Don't add the current page
                not href.startswith('#') and  # Skip anchors
                not href.startswith('mailto:') and  # Skip email links
                not href.startswith('tel:') and  # Skip phone links
                not full_url.endswith(('.jpg', '.png', '.pdf', '.zip', '.doc', '.docx'))):  # Skip files
                links.append(full_url)
        return list(set(links))  # Remove duplicates

    def _analyze_link_levels(self):
        """Analyze link structure by levels from homepage"""
        levels = {'level_1': 0, 'level_2': 0, 'level_3': 0, 'total': 1}
        
        try:
            print("🔍 Analyzing link structure...")
            
            # Get level 1 links (from homepage)
            level_1_links = self._get_homepage_links()
            levels['level_1'] = len(level_1_links)
            
            # Sample a few level 1 pages to estimate level 2
            level_2_estimate = 0
            sample_size = min(3, len(level_1_links))
            
            if sample_size > 0:
                sampled_links = list(level_1_links)[:sample_size]
                print(f"   📊 Sampling {sample_size} level 1 pages to estimate deeper levels...")
                for i, link in enumerate(sampled_links, 1):
                    try:
                        print(f"   📄 Sampling page {i}/{sample_size}...")
                        response = self.session.get(link, timeout=10)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.content, 'html.parser')
                            page_links = self._extract_internal_links(soup, link)
                            level_2_estimate += len(page_links)
                        time.sleep(0.5)  # Be respectful
                    except Exception as e:
                        print(f"   ⚠️  Could not sample {link}")
                        continue
                
                # Estimate total level 2 links
                if sample_size > 0:
                    avg_links_per_page = level_2_estimate / sample_size
                    levels['level_2'] = int(avg_links_per_page * levels['level_1'])
                    # Rough estimate for level 3 (assuming similar pattern but less)
                    levels['level_3'] = int(levels['level_2'] * 0.3)  # Conservative estimate
            
            levels['total'] = 1 + levels['level_1'] + levels['level_2'] + levels['level_3']
            
        except Exception as e:
            print(f"⚠️  Could not analyze link structure: {e}")
        
        return levels

    def analyze_quick(self):
        """Quick analysis for the interactive cloner with level breakdown"""
        print(f"🔍 Analyzing {self.base_url}...")
        content_counts = self.check_rest_api()
        
        posts = content_counts.get('posts', 0)
        pages = content_counts.get('pages', 0)
        
        print(f"📋 QUICK ANALYSIS:")
        print(f"   📝 Posts: {posts}")
        print(f"   📄 Pages: {pages}")
        print(f"   📂 Categories: {content_counts.get('categories', 0)}")
        print(f"   🏷️  Tags: {content_counts.get('tags', 0)}")
        
        # Analyze link levels for homepage crawling
        try:
            level_analysis = self._analyze_link_levels()
            if level_analysis.get('level_1', 0) > 0:
                print(f"\n🔗 LINK STRUCTURE ANALYSIS:")
                print(f"   🏠 Homepage: 1 page")
                print(f"   📊 Level 1 links: {level_analysis.get('level_1', 0)} pages")
                print(f"   📊 Level 2 links: {level_analysis.get('level_2', 0)} pages (estimated)")
                print(f"   📊 Level 3 links: {level_analysis.get('level_3', 0)} pages (estimated)")
                print(f"   📊 Total discoverable: {level_analysis.get('total', 0)} pages")
            content_counts['level_analysis'] = level_analysis
        except Exception as e:
            print(f"⚠️  Link analysis failed: {e}")
            content_counts['level_analysis'] = {'level_1': 0, 'level_2': 0, 'level_3': 0, 'total': 1}
        
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
        self.custom_urls = []
        
        # Create output directory
        Path(self.output_dir).mkdir(exist_ok=True)
        Path(f"{self.output_dir}/assets").mkdir(exist_ok=True)

        # Check for existing files
        self.existing_files = self._get_existing_files()

    def _get_existing_files(self):
        """Check for existing HTML files in the output directory"""
        existing_files = set()
        try:
            if os.path.exists(self.output_dir):
                for file in os.listdir(self.output_dir):
                    if file.endswith('.html'):
                        existing_files.add(file)
                if existing_files:
                    print(f"📁 Found {len(existing_files)} existing HTML files in {self.output_dir}")
                    print(f"   These will be skipped to avoid re-downloading")
        except Exception as e:
            print(f"⚠️  Could not check existing files: {e}")
        return existing_files

    def _get_filename_from_url(self, url):
        """Generate filename from URL"""
        parsed_url = urlparse(url)
        if parsed_url.path == '/' or parsed_url.path == '':
            return "index.html"
        else:
            filename = parsed_url.path.strip('/').replace('/', '_') + ".html"
            return self.clean_filename(filename)

    def _is_file_already_downloaded(self, url):
        """Check if a URL's corresponding file already exists"""
        filename = self._get_filename_from_url(url)
        return filename in self.existing_files

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
        
        # Clone mode - WITH OPTION 5
        print(f"\n2️⃣ What content do you want to clone?")
        print("   1. Recent posts only (quick test)")
        print("   2. Homepage + key pages only")
        print("   3. Homepage + random sample of posts")
        print("   4. All posts and pages (full clone)")
        print("   5. Custom URLs (specify exact pages/paths)")
        
        while True:
            choice = input("   Enter choice (1/2/3/4/5): ").strip()
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
            elif choice == "5":
                self.clone_mode = 'custom'
                self.custom_urls = self._get_custom_urls()
                print(f"   This will clone {len(self.custom_urls)} custom URLs")
                break
            else:
                print("   Please enter 1, 2, 3, 4, or 5")
        
        # Skip depth question for custom URLs
        if self.clone_mode != 'custom':
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
        delay_question = "4️⃣" if self.clone_mode != 'custom' else "3️⃣"
        print(f"\n{delay_question} Delay between requests (be nice to the server)")
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
        print(f"   📊 Max pages: {self.max_pages}")
        print(f"   📝 Clone mode: {self.clone_mode}")
        if self.clone_mode in ['homepage_plus_random']:
            print(f"   🎲 Random posts: {self.random_count}")
        elif self.clone_mode == 'custom':
            print(f"   📋 Custom URLs: {len(self.custom_urls)}")
        if self.clone_mode != 'custom':
            print(f"   🔍 Crawl depth: {self.max_depth}")
        print(f"   ⏱️  Request delay: {self.delay_between_requests}s")
        
        confirm = input("\n   Proceed with these settings? (y/n): ").strip().lower()
        return confirm in ['y', 'yes', '']

    def _get_custom_urls(self):
        """Get custom URLs from user input"""
        custom_urls = []
        
        print(f"\n📋 CUSTOM URL INPUT")
        print(f"   You can specify URLs in several ways:")
        print(f"   1. Full URLs: https://www.qnetturkiye.blog/about/")
        print(f"   2. Paths only: /about/ or about/")
        print(f"   3. Multiple URLs separated by commas")
        print(f"   4. One URL per line (press Enter twice when done)")
        
        print(f"\n   Examples:")
        print(f"   • /about/, /contact/, /products/")
        print(f"   • https://www.qnetturkiye.blog/specific-post/")
        print(f"   • category/electronics/")
        
        input_method = input(f"\n   Choose input method (1=single line, 2=multiple lines): ").strip()
        
        if input_method == "2":
            # Multi-line input
            print(f"\n   Enter URLs one per line (press Enter twice when done):")
            while True:
                url_input = input("   URL: ").strip()
                if url_input == "":
                    break
                processed_url = self._process_custom_url(url_input)
                if processed_url:
                    custom_urls.append(processed_url)
                    print(f"   ✅ Added: {processed_url}")
        else:
            # Single line input
            url_input = input(f"\n   Enter URLs (separated by commas): ").strip()
            url_list = [url.strip() for url in url_input.split(',')]
            
            for url in url_list:
                if url:
                    processed_url = self._process_custom_url(url)
                    if processed_url:
                        custom_urls.append(processed_url)
                        print(f"   ✅ Added: {processed_url}")
        
        # Always include homepage
        homepage = self.base_url
        if homepage not in custom_urls:
            custom_urls.insert(0, homepage)
            print(f"   🏠 Added homepage: {homepage}")
        
        print(f"\n   📊 Total custom URLs: {len(custom_urls)}")
        return custom_urls
    
    def _process_custom_url(self, url_input):
        """Process and validate a custom URL input"""
        url_input = url_input.strip()
        
        # If it's already a full URL
        if url_input.startswith(('http://', 'https://')):
            # Validate it's from the same domain
            if self.is_same_domain(url_input):
                return url_input
            else:
                print(f"   ⚠️  Skipping external URL: {url_input}")
                return None
        
        # If it's a path, convert to full URL
        if url_input.startswith('/'):
            return f"{self.base_url}{url_input}"
        else:
            # Add leading slash if missing
            return f"{self.base_url}/{url_input}"

    def get_urls_by_mode(self):
        """Get URLs based on clone mode with proper level ordering"""
        if self.clone_mode in ['minimal', 'homepage_plus_random']:
            # For options 2 and 3, use breadth-first crawling
            return self._get_urls_breadth_first()
        elif self.clone_mode == 'custom':
            # For option 5, use custom URLs
            return self._get_urls_custom()
        else:
            # For options 1 and 4, use the original API-based approach
            return self._get_urls_api_based()
    
    def _get_urls_custom(self):
        """Return custom URLs as specified by user, filtering out existing files"""
        print(f"📋 Using custom URLs:")
        filtered_urls = []
        skipped_count = 0
        
        for i, url in enumerate(self.custom_urls, 1):
            if self._is_file_already_downloaded(url):
                print(f"   {i:2d}. ⏭️  SKIPPED (already exists): {url}")
                skipped_count += 1
            else:
                print(f"   {i:2d}. ✅ {url}")
                filtered_urls.append(url)
        
        if skipped_count > 0:
            print(f"\n📊 Summary: {len(filtered_urls)} new URLs, {skipped_count} already exist")
        
        return filtered_urls
    
    def _get_urls_breadth_first(self):
        """Breadth-first crawling: homepage → level 1 → level 2 → level 3"""
        ordered_urls = []
        visited = set()
        skipped_count = 0
        
        # Level 0: Homepage
        homepage = self.base_url
        if self._is_file_already_downloaded(homepage):
            print(f"🏠 Level 0: ⏭️  SKIPPED homepage (already exists)")
            skipped_count += 1
        else:
            ordered_urls.append(homepage)
            print(f"🏠 Level 0: Added homepage")
        visited.add(homepage)
        
        # Level 1: All links from homepage
        print(f"🔍 Level 1: Scanning homepage for links...")
        level_1_links = self._get_links_from_page(homepage, visited)
        ordered_urls.extend(level_1_links)
        visited.update(level_1_links)
        print(f"✅ Level 1: Added {len(level_1_links)} pages")
        
        # Level 2: All links from level 1 pages
        if self.max_depth >= 2:
            print(f"🔍 Level 2: Scanning level 1 pages for links...")
            level_2_links = []
            for level_1_url in level_1_links:
                if len(ordered_urls) >= self.max_pages:
                    break
                page_links = self._get_links_from_page(level_1_url, visited)
                level_2_links.extend(page_links)
                visited.update(page_links)
            
            ordered_urls.extend(level_2_links)
            print(f"✅ Level 2: Added {len(level_2_links)} pages")
            
            # Level 3: All links from level 2 pages
            if self.max_depth >= 3:
                print(f"🔍 Level 3: Scanning level 2 pages for links...")
                level_3_links = []
                for level_2_url in level_2_links:
                    if len(ordered_urls) >= self.max_pages:
                        break
                    page_links = self._get_links_from_page(level_2_url, visited)
                    level_3_links.extend(page_links)
                    visited.update(page_links)
                
                ordered_urls.extend(level_3_links)
                print(f"✅ Level 3: Added {len(level_3_links)} pages")
        
        # Add additional content based on mode
        if self.clone_mode == 'homepage_plus_random':
            print(f"🎲 Adding {self.random_count} random posts...")
            random_posts = self._get_random_posts(self.random_count)
            for post in random_posts:
                if post not in visited and len(ordered_urls) < self.max_pages:
                    ordered_urls.append(post)
                    visited.add(post)
            print(f"✅ Added {len([p for p in random_posts if p in ordered_urls])} random posts")
        
        return ordered_urls
    
    def _get_links_from_page(self, url, visited):
        """Extract internal links from a single page, filtering out existing files"""
        links = []
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                page_links = self._extract_internal_links(soup, url)
                
                # Filter out already visited and existing files
                for link in page_links:
                    if (link not in visited and 
                        len(links) < 20 and  # Limit per page to avoid explosion
                        not self._is_file_already_downloaded(link)):
                        links.append(link)
        except Exception as e:
            print(f"   ⚠️  Could not scan {url}: {e}")
        
        return links
    
    def _extract_internal_links(self, soup, base_url):
        """Extract all internal links from a soup object"""
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = urljoin(base_url, href)
            if (self.is_same_domain(full_url) and 
                full_url != base_url and  # Don't add the current page
                not href.startswith('#') and  # Skip anchors
                not href.startswith('mailto:') and  # Skip email links
                not href.startswith('tel:') and  # Skip phone links
                not full_url.endswith(('.jpg', '.png', '.pdf', '.zip', '.doc', '.docx'))):  # Skip files
                links.append(full_url)
        return list(set(links))  # Remove duplicates
    
    def _get_urls_api_based(self):
        """Original API-based URL collection for options 1 and 4, filtering out existing files"""
        urls = set()
        skipped_count = 0
        
        # ALWAYS start with homepage
        if self._is_file_already_downloaded(self.base_url):
            print(f"⏭️  SKIPPED homepage (already exists)")
            skipped_count += 1
        else:
            urls.add(self.base_url)
            print(f"✅ Added homepage: {self.base_url}")
        
        if self.clone_mode == 'recent':
            # Option 1: Recent posts only (quick test)
            recent_posts = self._get_recent_posts(20)
            for post in recent_posts:
                if self._is_file_already_downloaded(post):
                    skipped_count += 1
                else:
                    urls.add(post)
            print(f"✅ Added {len(urls) - (1 if self.base_url in urls else 0)} recent posts")
            if skipped_count > 0:
                print(f"⏭️  Skipped {skipped_count} posts (already exist)")
        
        elif self.clone_mode == 'all':
            # Option 4: All posts and pages (full clone)
            all_posts = self._get_all_posts()
            all_pages = self._get_all_pages()
            
            for post in all_posts:
                if not self._is_file_already_downloaded(post):
                    urls.add(post)
                else:
                    skipped_count += 1
            
            for page in all_pages:
                if not self._is_file_already_downloaded(page):
                    urls.add(page)
                else:
                    skipped_count += 1
            
            print(f"✅ Added {len(urls) - (1 if self.base_url in urls else 0)} posts + pages")
            if skipped_count > 0:
                print(f"⏭️  Skipped {skipped_count} posts/pages (already exist)")
        
        return list(urls)
    
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
        """Update HTML to use local asset paths"""
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

    def save_page(self, url):
        """Download and save a single page"""
        if url in self.visited_urls:
            return set()
        
        # Check if file already exists
        if self._is_file_already_downloaded(url):
            filename = self._get_filename_from_url(url)
            print(f"⏭️  SKIPPED (already exists): {url} -> {filename}")
            self.visited_urls.add(url)
            return set()
        
        try:
            print(f"🌐 Processing: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Download assets and update their links
            assets = self.download_assets(soup, url)
            self.update_asset_links(soup, assets)
            
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
        """Main method to clone the WordPress site"""
        print(f"\n🚀 Starting clone of {self.base_url}")
        
        # Get URLs to process
        urls_to_process = self.get_urls_by_mode()
        print(f"\n📋 Found {len(urls_to_process)} URLs to process")
        
        if len(urls_to_process) > self.max_pages:
            urls_to_process = urls_to_process[:self.max_pages]
            print(f"🎯 Limited to {self.max_pages} pages")
        
        # Show processing order for custom URLs
        if self.clone_mode == 'custom':
            print(f"\n📋 PROCESSING ORDER:")
            for i, url in enumerate(urls_to_process, 1):
                parsed = urlparse(url)
                if parsed.path == '/':
                    page_type = "🏠 Homepage"
                else:
                    page_type = "📄 Custom Page"
                print(f"   {i:2d}. {page_type}: {url}")
        
        # Process pages
        processed = 0
        print(f"\n🔄 PROCESSING PAGES:")
        
        for i, url in enumerate(urls_to_process, 1):
            if processed >= self.max_pages:
                break
            
            print(f"\n[{i:2d}/{len(urls_to_process)}] ", end="")
            self.save_page(url)
            processed += 1
            
            if processed < len(urls_to_process):
                time.sleep(self.delay_between_requests)
        
        # Final summary
        print(f"\n🎉 CLONING COMPLETED!")
        print(f"📊 Pages processed: {processed}")
        print(f"📁 Output directory: {self.output_dir}")
        print(f"🌐 Open {self.output_dir}/index.html to view")
        
        # Show existing files info
        if len(self.existing_files) > 0:
            print(f"\n📋 BATCH SUMMARY:")
            print(f"   📄 New pages downloaded: {processed}")
            print(f"   ⏭️  Pages already existed: {len(self.existing_files)}")
            print(f"   📊 Total pages in directory: {processed + len(self.existing_files)}")
        
        # Show structure summary
        if self.clone_mode == 'custom':
            print(f"\n📋 CUSTOM URLS CLONED:")
            print(f"   📄 Total custom pages: {processed}")
            print(f"   🏠 Homepage included: {'Yes' if self.base_url in self.visited_urls else 'No'}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python new_combined.py <wordpress_site_url>")
        print("Example: python new_combined.py https://example.com")
        sys.exit(1)
    
    site_url = sys.argv[1]
    
    # Validate URL
    if not site_url.startswith(('http://', 'https://')):
        site_url = 'https://' + site_url
    
    print(f"🔍 Complete WordPress Site Analyzer & Cloner")
    print(f"🎯 Target: {site_url}")
    
    # Quick analysis
    try:
        analyzer = WordPressSiteAnalyzer(site_url)
        content_counts = analyzer.analyze_quick()
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        content_counts = {}
    
    # Create output directory name based on domain
    domain = urlparse(site_url).netloc.replace('.', '_')
    output_dir = f"cloned_{domain}"
    
    # Create cloner instance
    cloner = InteractiveWordPressCloner(site_url, output_dir)
    
    # Get user preferences
    if cloner.get_user_preferences(content_counts):
        try:
            cloner.clone_site()
        except KeyboardInterrupt:
            print(f"\n⏹️  Cloning interrupted by user")
            print(f"📁 Partial results saved in: {output_dir}")
        except Exception as e:
            print(f"\n❌ Error during cloning: {e}")
            print(f"📁 Partial results may be saved in: {output_dir}")
    else:
        print("❌ Cloning cancelled by user")


if __name__ == "__main__":
    main()