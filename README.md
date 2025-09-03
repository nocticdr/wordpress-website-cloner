# WordPress Website Cloner

A Python tool for creating static copies of WordPress websites with intelligent crawling and batch download capabilities.

## Features

- **WordPress Site Analysis**: Analyzes site structure and content via REST API
- **Multiple Cloning Modes**: 
  - Recent posts only
  - Homepage + key pages
  - Homepage + random posts
  - Full site clone
  - Custom URL specification
- **Batch Download Support**: Skip existing files to continue downloads incrementally
- **Asset Download**: Downloads CSS, JavaScript, and images with local path conversion
- **Respectful Crawling**: Configurable delays and limits

## Installation

1. Clone this repository
2. Create a virtual environment:
   ```bash
   python3 -m venv wordpress-cloner-env
   source wordpress-cloner-env/bin/activate  # On Windows: wordpress-cloner-env\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install requests beautifulsoup4 lxml
   ```

## Usage

```bash
python3 website_cloner.py https://example.com
```

The script will:
1. Analyze the WordPress site structure
2. Present interactive configuration options
3. Download and save pages with assets
4. Create a static copy in the `cloned_[domain]` directory

## Configuration Options

- **Max Pages**: Limit the number of pages to download
- **Clone Mode**: Choose from 5 different cloning strategies
- **Crawl Depth**: Control how deep the crawler goes (1-3 levels)
- **Request Delay**: Set delays between requests to be respectful to servers

## Batch Downloads

The tool supports incremental downloads:
- Automatically detects existing HTML files
- Skips already downloaded pages
- Perfect for large sites that need to be downloaded in batches

## Output Structure

```
cloned_example_com/
├── index.html (homepage)
├── assets/
│   ├── css/
│   ├── js/
│   └── images/
├── page1.html
├── page2.html
└── ...
```

## Requirements

- Python 3.7+
- requests
- beautifulsoup4
- lxml

## License

This project is open source. Use responsibly and respect website terms of service and robots.txt files.

## Disclaimer

This tool is for educational and legitimate backup purposes only. Always ensure you have permission to clone websites and respect copyright laws.
