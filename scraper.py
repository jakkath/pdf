import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import re
import csv

# Configuration
max_depth = 3
domain = "e-kalvi.com"
save_folder = "downloaded_pdfs"
details_file = "pdf_details.csv"
delay = 1  # Seconds between requests

visited_urls = set()
downloaded_file_ids = set()  # Track downloaded Google Drive file IDs

def setup():
    """Create download folder and details file if needed"""
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
    if not os.path.exists(details_file):
        with open(details_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Title", "Grade", "Subject", "Topic", "Medium", "Source", "Published On", "File Type", "No. of Pages", "Download Link"])

def get_file_id(url):
    """Extract Google Drive file ID from different URL formats"""
    try:
        if '/uc?id=' in url:
            return url.split('/uc?id=')[1].split('&')[0]
        if 'export=download&id=' in url:
            return url.split('export=download&id=')[1].split('&')[0]
        if '/d/' in url:
            return url.split('/d/')[1].split('/')[0]
        return None
    except IndexError:
        return None

def sanitize_filename(title):
    """Sanitize the title to create a valid filename"""
    return re.sub(r'[\\/*?:"<>|]', "_", title).strip()

def download_pdf(drive_url, title):
    """Handle Google Drive PDF downloads with duplicate checks"""
    global downloaded_file_ids  # Access the global set of downloaded IDs
    
    try:
        file_id = get_file_id(drive_url)
        if not file_id:
            print(f"⚠️ Unsupported Google Drive URL: {drive_url}")
            return

        # Check for duplicate file ID
        if file_id in downloaded_file_ids:
            print(f"⏩ Skipping duplicate file: {title}")
            return
        downloaded_file_ids.add(file_id)

        direct_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        response = requests.get(direct_url, stream=True)
        response.raise_for_status()

        # Generate unique filename
        base_name = sanitize_filename(title)
        filename = f"{base_name}.pdf"
        filepath = os.path.join(save_folder, filename)
        
        # Handle filename duplicates
        counter = 1
        while os.path.exists(filepath):
            filename = f"{base_name} {counter}.pdf"
            filepath = os.path.join(save_folder, filename)
            counter += 1

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)
        print(f"✅ Downloaded: {filename}")

    except Exception as e:
        print(f"❌ Failed to download {drive_url}: {str(e)}")

def extract_details(soup, url):
    """Extract details from the HTML content"""
    details = {
        "Title": None,
        "Grade": None,
        "Subject": None,
        "Topic": None,
        "Medium": None,
        "Source": None,
        "Published On": None,
        "File Type": None,
        "No. of Pages": None,
        "Download Link": None
    }

    # Extract title
    title_tag = soup.find('h1', class_='entry-title')
    if title_tag:
        details["Title"] = title_tag.text.strip()

    # Extract details from the table
    table = soup.find('table')
    if table:
        for row in table.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) == 2:
                key = cells[0].text.strip().replace(':', '')
                value = cells[1].text.strip()
                if key in details:
                    details[key] = value

    # Extract download link
    download_link = soup.find('a', href=True, text=re.compile(r'Download PDF', re.IGNORECASE))
    if download_link:
        details["Download Link"] = urljoin(url, download_link['href'])

    return details

def save_details(details):
    """Save extracted details to a CSV file"""
    with open(details_file, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            details["Title"],
            details["Grade"],
            details["Subject"],
            details["Topic"],
            details["Medium"],
            details["Source"],
            details["Published On"],
            details["File Type"],
            details["No. of Pages"],
            details["Download Link"]
        ])

def is_article_page(soup):
    """Check if the page is an article page by looking for specific elements"""
    return soup.find('article') is not None

def crawl_site(start_url):
    """Main crawling function"""
    queue = [(start_url, 0)]
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    while queue:
        url, depth = queue.pop(0)
        
        if depth > max_depth or url in visited_urls:
            continue
            
        try:
            print(f"🌐 Checking: {url} (Depth: {depth})")
            visited_urls.add(url)
            
            # Get page content
            time.sleep(delay)
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check if the page is an article page
            if is_article_page(soup):
                # Extract details from the HTML
                details = extract_details(soup, url)
                if details["Title"]:  # Only save details if the title is found
                    save_details(details)
                
                # Check for Google Drive links first
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if 'drive.google.com' in href:
                        full_url = urljoin(url, href)
                        print(f"🔗 Found Google Drive link: {full_url}")
                        download_pdf(full_url, details["Title"])
            
            # Add internal links to queue
            if depth < max_depth:
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(url, href)
                    if is_same_domain(full_url) and full_url not in visited_urls:
                        queue.append((full_url, depth + 1))
                        
        except Exception as e:
            print(f"⚠️ Error processing {url}: {str(e)}")

def is_same_domain(url):
    """Check if URL belongs to our target domain"""
    parsed = urlparse(url)
    return parsed.netloc == domain

if __name__ == "__main__":
    setup()
    start_url = "https://e-kalvi.com/"
    print("🚀 Starting PDF crawler...")
    crawl_site(start_url)
    print("✅ Crawling completed!")