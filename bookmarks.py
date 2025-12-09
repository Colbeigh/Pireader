#!/usr/bin/python3
# bookmarks.py - Bookmark management

import os
import json
import datetime
import threading
import hashlib
import config

class BookmarkManager:
    def __init__(self, bookmark_dir=config.BOOKMARK_DIR):
        self.bookmark_dir = bookmark_dir
        os.makedirs(self.bookmark_dir, exist_ok=True)
        self._cache = {}
    
    def get_bookmark_path(self, book_path):
        book_hash = hashlib.md5(book_path.encode()).hexdigest()[:16]
        return os.path.join(self.bookmark_dir, f"bookmark_{book_hash}.json")
    
    def load_bookmark(self, book_path):
        """Load saved page"""
        if book_path in self._cache:
            return self._cache[book_path]
        
        bookmark_path = self.get_bookmark_path(book_path)
        if os.path.exists(bookmark_path):
            try:
                with open(bookmark_path, 'r') as f:
                    data = json.load(f)
                if data.get('book_path') == book_path:
                    page = data['page_num']
                    self._cache[book_path] = page
                    return page
            except:
                pass
        
        return 1
    
    def save_bookmark_async(self, book_path, page_num):
        """Save bookmark in background"""
        def save():
            bookmark_path = self.get_bookmark_path(book_path)
            bookmark_data = {
                'book_path': book_path,
                'page_num': page_num,
                'last_accessed': datetime.datetime.now().isoformat()
            }
            try:
                with open(bookmark_path, 'w') as f:
                    json.dump(bookmark_data, f)
                self._cache[book_path] = page_num
            except:
                pass
        
        threading.Thread(target=save, daemon=True).start()