#!/usr/bin/python3
# book.py - Text extraction, pagination, and chapter detection

import os
import re
import gzip
import pickle
import hashlib
import threading
import time
import queue
import config
from fonts import FastFontCache

# Try to import ebooklib, but provide fallback
try:
    from ebooklib import epub, ITEM_DOCUMENT
    from bs4 import BeautifulSoup
    EBOOKLIB_AVAILABLE = True
except ImportError:
    EBOOKLIB_AVAILABLE = False
    print("⚠️ Warning: ebooklib or beautifulsoup4 not installed. EPUB processing disabled.")

# Global queue for processing completion notifications
processing_queue = queue.Queue()

def clean_text(text):
    """Clean text to fix spacing issues"""
    text = re.sub(r"(\w)'\s+(\w)", r"\1'\2", text)
    text = re.sub(r"(\w)'\s+([tsmd])\b", r"\1'\2", text, flags=re.IGNORECASE)
    text = re.sub(r':\s+', ': ', text)
    text = re.sub(r'\.\s{2,}', '. ', text)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    return text

def extract_chapters_from_epub(book_path):
    """Extract chapter titles from EPUB"""
    if not EBOOKLIB_AVAILABLE:
        return []
    
    try:
        book = epub.read_epub(book_path)
        chapters = []
        
        # Method 1: Look for table of contents
        if book.toc:
            for item in book.toc:
                if hasattr(item, 'title'):
                    title = item.title
                    if title and title.strip():
                        chapters.append(title.strip())
        
        # Method 2: Look for headings in documents
        if not chapters or len(chapters) < 5:
            for item in book.get_items():
                if item.get_type() == ITEM_DOCUMENT:
                    try:
                        html = item.get_content().decode("utf-8", errors="ignore")
                        soup = BeautifulSoup(html, "html.parser")
                        # Look for h1-h3 tags
                        for heading in soup.find_all(['h1', 'h2', 'h3']):
                            heading_text = heading.text.strip()
                            if heading_text and len(heading_text) < 100:
                                chapters.append(heading_text)
                    except:
                        pass
        
        # Clean up and deduplicate
        seen = set()
        cleaned_chapters = []
        for chapter in chapters:
            clean_chapter = chapter.strip()
            if clean_chapter and clean_chapter not in seen:
                seen.add(clean_chapter)
                cleaned_chapters.append(clean_chapter)
        
        # Limit to 20 chapters
        return cleaned_chapters[:20]
        
    except Exception as e:
        print(f"Error extracting chapters: {e}")
        return []

def extract_text_fast(path, cache_dir=config.CACHE_DIR, callback=None):
    """Fast text extraction with caching and chapter detection"""
    if not EBOOKLIB_AVAILABLE:
        print("❌ ebooklib not installed. Cannot process EPUB files.")
        return "Please install ebooklib: pip3 install ebooklib beautifulsoup4", [["Install ebooklib"]], []
    
    cache_dir = os.path.expanduser(cache_dir)
    os.makedirs(cache_dir, exist_ok=True)
    
    book_stat = os.stat(path)
    cache_key = f"{path}_{book_stat.st_mtime}_{book_stat.st_size}"
    cache_hash = hashlib.md5(cache_key.encode()).hexdigest()[:16]
    cache_file = os.path.join(cache_dir, f"{cache_hash}.pkl.gz")
    
    # Try cache first
    if os.path.exists(cache_file):
        try:
            with gzip.open(cache_file, 'rb') as f:
                cached_data = pickle.load(f)
                if not cached_data.get('partial', False):
                    print("📂 Loaded from cache")
                    return cached_data['text'], cached_data['pages'], cached_data.get('chapters', [])
                else:
                    print("⚠️ Found partial cache, continuing processing...")
        except:
            print("⚠️ Cache corrupted, re-processing...")
    
    print(f"📖 Processing book: {os.path.basename(path)}")
    
    try:
        book = epub.read_epub(path)
        
        # Extract chapters first
        chapters = extract_chapters_from_epub(path)
        
        # Count total documents
        total_items = sum(1 for item in book.get_items() if item.get_type() == ITEM_DOCUMENT)
        print(f"📄 Found {total_items} documents in EPUB")
        
        # Process enough for good initial reading (at least 50 pages worth)
        print("📖 Processing initial content...")
        parts = []
        items_processed = 0
        target_words = 10000  # Enough for ~40-50 pages
        
        for item in book.get_items():
            if item.get_type() == ITEM_DOCUMENT:
                try:
                    html = item.get_content().decode("utf-8", errors="ignore")
                    text = BeautifulSoup(html, "html.parser").get_text(separator="\n")
                    parts.append(text.strip())
                    items_processed += 1
                    
                    # Check if we have enough content
                    current_words = len("\n".join(parts).split())
                    if current_words >= target_words or items_processed >= 30:
                        break
                except Exception as e:
                    print(f"⚠️ Error processing item: {e}")
                    continue
        
        initial_text = "\n".join(parts)
        text = clean_text(initial_text)
        
        # Paginate initial
        font = FastFontCache.get_font(config.FONT_SIZE_NORMAL)
        pages = paginate_initial(text, font)
        
        print(f"📄 Initial: {len(pages)} pages (full: {total_items} documents)")
        
        # Cache initial
        cache_data = {
            'text': text,
            'pages': pages,
            'chapters': chapters,
            'partial': True,
            'timestamp': time.time(),
            'book_path': path
        }
        with gzip.open(cache_file, 'wb') as f:
            pickle.dump(cache_data, f)
        
        # Process full in background
        def process_full():
            print(f"🔄 Background processing: {os.path.basename(path)}")
            full_parts = []
            processed_count = 0
            
            # Re-read the book for full processing
            full_book = epub.read_epub(path)
            
            for item in full_book.get_items():
                if item.get_type() == ITEM_DOCUMENT:
                    try:
                        html = item.get_content().decode("utf-8", errors="ignore")
                        text = BeautifulSoup(html, "html.parser").get_text(separator="\n")
                        full_parts.append(text.strip())
                        processed_count += 1
                        
                        # Progress indicator for large books
                        if processed_count % 20 == 0:
                            print(f"🔄 Processed {processed_count}/{total_items} documents")
                    except Exception as e:
                        print(f"⚠️ Error in background processing: {e}")
                        continue
            
            full_text = "\n".join(full_parts)
            full_text_clean = clean_text(full_text)
            full_pages = paginate_full(full_text_clean, font)
            
            # Update cache with full data
            cache_data.update({
                'text': full_text_clean,
                'pages': full_pages,
                'partial': False
            })
            with gzip.open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            
            print(f"✅ Full book processed: {len(full_pages)} pages")
            
            # Notify that processing is complete
            if callback:
                callback(path, full_pages, chapters)
            else:
                # Put in queue for main thread to check
                processing_queue.put({
                    'book_path': path,
                    'pages': full_pages,
                    'chapters': chapters
                })
        
        # Start background processing
        threading.Thread(target=process_full, daemon=True).start()
        
        return text, pages, chapters
        
    except Exception as e:
        print(f"❌ Error processing {os.path.basename(path)}: {e}")
        import traceback
        traceback.print_exc()
        return f"Error loading book: {str(e)}", [["Error loading book"]], []

def check_processing_complete():
    """Check if any book processing has completed"""
    try:
        return processing_queue.get_nowait()
    except queue.Empty:
        return None

def paginate_initial(text, font, W=config.DISPLAY_WIDTH, H=config.DISPLAY_HEIGHT, margin=config.DISPLAY_MARGIN):
    """Paginate initial text"""
    bbox = font.getbbox("Hg")
    line_height = bbox[3] + 1
    footer_height = line_height * 1.5
    usable_height = H - (2 * margin) - footer_height
    max_lines_per_page = int(usable_height / line_height)
    
    paragraphs = text.split("\n")
    all_lines = []
    lines_collected = 0
    max_initial_lines = max_lines_per_page * 50  # Enough for 50 pages
    
    for para in paragraphs:
        if lines_collected >= max_initial_lines:
            break
        
        para = para.strip()
        if not para:
            if all_lines and all_lines[-1] != "":
                all_lines.append("")
                lines_collected += 1
            continue
        
        words = para.split()
        current_line = ""
        
        for word in words:
            if lines_collected >= max_initial_lines:
                break
            
            test_line = f"{current_line} {word}".strip() if current_line else word
            line_width = font.getlength(test_line)
            
            if line_width <= (W - 2 * margin):
                current_line = test_line
            else:
                if current_line:
                    all_lines.append(current_line)
                    lines_collected += 1
                current_line = word
        
        if current_line and lines_collected < max_initial_lines:
            all_lines.append(current_line)
            lines_collected += 1
    
    # Split into pages
    pages = []
    current_page_lines = []
    
    for line in all_lines:
        if len(current_page_lines) >= max_lines_per_page:
            if current_page_lines:
                pages.append(current_page_lines)
                current_page_lines = []
            if line == "":
                continue
        current_page_lines.append(line)
    
    if current_page_lines:
        pages.append(current_page_lines)
    
    if not pages:
        pages = [["Loading..."]]
    
    return pages

def paginate_full(text, font, W=config.DISPLAY_WIDTH, H=config.DISPLAY_HEIGHT, margin=config.DISPLAY_MARGIN):
    """Full pagination"""
    bbox = font.getbbox("Hg")
    line_height = bbox[3] + 1
    footer_height = line_height * 1.5
    usable_height = H - (2 * margin) - footer_height
    max_lines_per_page = int(usable_height / line_height)
    
    paragraphs = text.split("\n")
    all_lines = []
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            if all_lines and all_lines[-1] != "":
                all_lines.append("")
            continue
        
        words = para.split()
        current_line = ""
        
        for word in words:
            test_line = f"{current_line} {word}".strip() if current_line else word
            line_width = font.getlength(test_line)
            
            if line_width <= (W - 2 * margin):
                current_line = test_line
            else:
                if current_line:
                    all_lines.append(current_line)
                current_line = word
        
        if current_line:
            all_lines.append(current_line)
    
    # Split into pages
    pages = []
    current_page_lines = []
    
    for line in all_lines:
        if len(current_page_lines) >= max_lines_per_page:
            if current_page_lines:
                pages.append(current_page_lines)
                current_page_lines = []
            if line == "":
                continue
        current_page_lines.append(line)
    
    if current_page_lines:
        pages.append(current_page_lines)
    
    # Clean up
    cleaned_pages = []
    for page in pages:
        while page and page[-1] == "":
            page.pop()
        if page:
            cleaned_pages.append(page)
    
    print(f"📄 Full pagination: {len(cleaned_pages)} pages")
    return cleaned_pages