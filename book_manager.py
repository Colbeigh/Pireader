#!/usr/bin/python3
# book_manager.py - Manage books and last opened book

import os
import json
import glob
from datetime import datetime
import config

class BookManager:
    def __init__(self, books_dir=config.BOOKS_DIR):
        self.books_dir = books_dir
        self.last_book_file = os.path.join(config.BOOKMARK_DIR, "last_book.json")
        os.makedirs(self.books_dir, exist_ok=True)
        os.makedirs(config.BOOKMARK_DIR, exist_ok=True)
    
    def get_all_books(self):
        """Get all EPUB books in the books directory"""
        books = []
        patterns = ['*.epub', '*.EPUB', '*.mobi', '*.MOBI', '*.pdf', '*.PDF']
        
        for pattern in patterns:
            books.extend(glob.glob(os.path.join(self.books_dir, pattern)))
        
        # Sort by modification time (newest first)
        books.sort(key=os.path.getmtime, reverse=True)
        
        # Get just the filenames
        book_names = [os.path.basename(book) for book in books]
        return books, book_names
    
    def save_last_book(self, book_path):
        """Save the last opened book"""
        try:
            last_book_data = {
                'path': book_path,
                'filename': os.path.basename(book_path),
                'last_opened': datetime.now().isoformat()
            }
            with open(self.last_book_file, 'w') as f:
                json.dump(last_book_data, f)
        except Exception as e:
            print(f"Error saving last book: {e}")
    
    def get_last_book(self):
        """Get the last opened book"""
        if os.path.exists(self.last_book_file):
            try:
                with open(self.last_book_file, 'r') as f:
                    data = json.load(f)
                # Check if the book still exists
                if os.path.exists(data['path']):
                    return data['path']
            except:
                pass
        
        # If no last book, try to find any book
        books, _ = self.get_all_books()
        if books:
            return books[0]
        
        return None
    
    def get_book_path(self, book_filename):
        """Get full path for a book filename"""
        return os.path.join(self.books_dir, book_filename)