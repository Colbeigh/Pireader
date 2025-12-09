#!/usr/bin/python3
# main.py - Main e-reader application

import sys
import os
import time
import datetime
import subprocess

# Import modules
import config
from fonts import FastFontCache
from book import extract_text_fast
from bookmarks import BookmarkManager
from controls import FourButtonControls
from display import EReaderDisplay
from book_manager import BookManager

# ============================================================================
# MAIN E-READER APPLICATION
# ============================================================================
class CompleteEReader:
    def __init__(self):
        self.display = EReaderDisplay()
        self.controls = FourButtonControls()
        self.bookmark_manager = BookmarkManager()
        self.book_manager = BookManager()
        self.font = FastFontCache.get_font(config.FONT_SIZE_NORMAL)
        
        # Book state
        self.current_page = 0
        self.pages = []
        self.book_path = ""
        self.chapters = []
        self.chapter_page_map = {}
        
        # Books list
        self.all_books = []
        self.book_filenames = []
        
        # Setup controls
        self.setup_controls()
        self.load_books_list()
    
    def setup_controls(self):
        """Setup button callbacks"""
        self.controls.register_callback('state_changed', self.on_state_changed)
        self.controls.register_callback('page_change', self.on_page_change)
        self.controls.register_callback('menu_action', self.on_menu_action)
        self.controls.register_callback('chapter_select', self.on_chapter_select)
        self.controls.register_callback('book_select', self.on_book_select)
    
    def load_books_list(self):
        """Load list of all books"""
        self.all_books, self.book_filenames = self.book_manager.get_all_books()
        print(f"📚 Found {len(self.all_books)} books")
        self.controls.set_books(self.book_filenames)
    
    def load_book(self, book_path=None):
        """Load a book with chapters"""
        if not book_path:
            # Try to load last book
            book_path = self.book_manager.get_last_book()
            if not book_path:
                print("❌ No books found!")
                self.show_no_books_message()
                return False
        
        if not os.path.exists(book_path):
            print(f"❌ Book not found: {book_path}")
            return False
        
        self.book_path = os.path.abspath(book_path)
        
        # Save as last book
        self.book_manager.save_last_book(self.book_path)
        
        # Load from cache or process (includes chapters)
        text, pages, chapters = extract_text_fast(book_path)
        self.pages = pages
        self.chapters = chapters
        
        # Set chapters in controls
        self.controls.set_chapters(chapters)
        
        # Load bookmark
        saved_page = self.bookmark_manager.load_bookmark(book_path)
        self.current_page = saved_page - 1
        self.current_page = max(0, min(self.current_page, len(pages)-1))
        
        print(f"📖 {len(pages)} pages, {len(chapters)} chapters, resuming at page {self.current_page+1}")
        
        if not chapters:
            print("⚠️ No chapters detected in this book")
        
        # Display first page
        self.display.init_display()
        self.display.clear_display()
        self.render_current_state()
        
        return True
    
    def show_no_books_message(self):
        """Show message when no books are found"""
        img = self.display.render_confirmation(
            "NO BOOKS",
            "No books found!\n\nPlease add EPUB files to:\n~/books/",
            ["OK"],
            0
        )
        self.display.display_page(img, force_full=True)
        time.sleep(3)
    
    def check_background_processing(self):
        """Check if background book processing has completed"""
        from book import check_processing_complete
        result = check_processing_complete()
        
        if result and result['book_path'] == self.book_path:
            print(f"🔄 Background processing complete: {len(result['pages'])} pages")
            self.pages = result['pages']
            self.chapters = result['chapters']
            self.controls.set_chapters(self.chapters)
            
            # Adjust current page if needed
            if self.current_page >= len(self.pages):
                self.current_page = len(self.pages) - 1
            
            # Force refresh display
            self.display.needs_clear = True
            self.render_current_state(force_full=True)
            
            print(f"✅ Updated to full book: {len(self.pages)} pages")
            return True
        
        return False

    def refresh_current_book(self):
        """Force refresh current book (reprocess)"""
        if not self.book_path:
            return
        
        print(f"🔄 Refreshing book: {os.path.basename(self.book_path)}")
        
        # Clear cache for this book
        import hashlib
        book_hash = hashlib.md5(self.book_path.encode()).hexdigest()[:16]
        cache_file = os.path.join(config.CACHE_DIR, f"{book_hash}.pkl.gz")
        if os.path.exists(cache_file):
            os.remove(cache_file)
            print("🧹 Cleared cache")
        
        # Reload book
        from book import extract_text_fast
        text, pages, chapters = extract_text_fast(self.book_path)
        self.pages = pages
        self.chapters = chapters
        self.controls.set_chapters(chapters)
        
        # Reset to page 1
        self.current_page = 0
        self.display.needs_clear = True
        self.render_current_state(force_full=True)
        
        print(f"✅ Refreshed: {len(pages)} initial pages (full processing in background)")
    
    def render_current_state(self, force_full=False):
        """Render based on current state"""
        if self.controls.current_state == "READING":
            img = self.display.render_reading_page(self.font, self.pages, self.current_page)
        
        elif self.controls.current_state == "MAIN_MENU":
            img = self.display.render_menu(
                "MAIN MENU",
                self.controls.main_menu,
                self.controls.menu_index
            )
        
        elif self.controls.current_state == "JUMP_MENU":
            img = self.display.render_menu(
                "JUMP PAGES",
                self.controls.jump_menu,
                self.controls.submenu_index
            )
        
        elif self.controls.current_state == "CHAPTER_MENU":
            if self.chapters:
                img = self.display.render_chapter_menu(
                    self.chapters,
                    self.controls.chapter_menu_index
                )
            else:
                # No chapters, show message
                img = self.display.render_confirmation(
                    "NO CHAPTERS",
                    "No chapters found\nin this book.",
                    ["OK"],
                    0
                )
        
        elif self.controls.current_state == "BROWSER_MENU":
            img = self.display.render_browser_menu(
                self.controls.browser_menu,
                self.controls.browser_index,
                self.controls.browser_page
            )
        
        elif self.controls.current_state == "SLEEP_MENU":
            img = self.display.render_confirmation(
                "SLEEP",
                "Put display to sleep?",
                self.controls.sleep_menu,
                self.controls.submenu_index
            )
        
        elif self.controls.current_state == "SHUTDOWN_CONFIRM":
            img = self.display.render_confirmation(
                "SHUTDOWN",
                "Shutdown the e-reader?",
                self.controls.shutdown_menu,
                self.controls.submenu_index
            )
        
        else:
            # Fallback to reading
            img = self.display.render_reading_page(self.font, self.pages, self.current_page)
        
        # Display the image
        used_partial = self.display.display_page(img, force_full=force_full)
        return used_partial
    
    def on_state_changed(self, new_state, selected_index):
        """Handle state change from controls"""
        print(f"🔄 State: {new_state}")
        self.render_current_state()
    
    def on_page_change(self, delta):
        """Handle page change request"""
        if not self.pages:
            return
        
        new_page = self.current_page + delta
        new_page = max(0, min(new_page, len(self.pages) - 1))
        
        if new_page != self.current_page:
            page_diff = abs(new_page - self.current_page)
            if page_diff > 3:
                self.display.needs_clear = True
            
            self.current_page = new_page
            
            if delta > 0:
                print(f"⏩ Forward {abs(delta)} pages to {self.current_page+1}")
            else:
                print(f"⏪ Back {abs(delta)} pages to {self.current_page+1}")
            
            self.render_current_state()
            
            # Auto-save bookmark
            self.bookmark_manager.save_bookmark_async(self.book_path, self.current_page + 1)
    
    def on_chapter_select(self, chapter_index):
        """Handle chapter selection"""
        if not self.chapters or chapter_index >= len(self.chapters):
            return
        
        chapter_name = self.chapters[chapter_index]
        print(f"📖 Jumping to chapter: {chapter_name}")
        
        # Estimate page based on chapter index
        # This is simplified - in a real implementation, you'd have exact page mapping
        if self.pages:
            estimated_page = int((chapter_index / len(self.chapters)) * len(self.pages))
            estimated_page = max(0, min(estimated_page, len(self.pages) - 1))
            
            old_page = self.current_page
            self.current_page = estimated_page
            
            print(f"📄 Jumped from page {old_page+1} to page {self.current_page+1}")
            
            # Force full refresh for large jumps
            self.display.needs_clear = True
            self.render_current_state()
            
            # Save bookmark
            self.bookmark_manager.save_bookmark_async(self.book_path, self.current_page + 1)
    
    def on_book_select(self, book_index):
        """Handle book selection from browser"""
        if book_index < len(self.all_books):
            new_book_path = self.all_books[book_index]
            print(f"📚 Switching to: {os.path.basename(new_book_path)}")
            
            # Save current bookmark before switching
            if self.book_path and self.pages:
                self.bookmark_manager.save_bookmark_async(self.book_path, self.current_page + 1)
            
            # Load new book
            if self.load_book(new_book_path):
                self.controls.current_state = "READING"
                self.render_current_state(force_full=True)
            else:
                # Failed to load, go back to browser
                self.controls.current_state = "BROWSER_MENU"
                self.render_current_state()
    
    def on_menu_action(self, action):
        """Handle menu actions"""
        if action == 'sleep':
            print("💤 Putting display to sleep...")
            
            # Clear display first
            self.display.clear_display()
            
            # Show sleep message
            img = self.display.render_confirmation(
                "SLEEPING",
                "Display is sleeping\n\nPress any button\nto wake",
                ["", ""],
                0
            )
            self.display.display_page(img, force_full=True)
            time.sleep(0.5)
            
            # Put display to sleep
            self.display.sleep()
            
            # Wait for button press to wake
            print("Press any button to wake...")
            self.wait_for_wake()
            
            # Wake display
            self.display.wake()
            self.controls.current_state = "READING"
            self.render_current_state(force_full=True)
        
        elif action == 'refresh':
            self.refresh_current_book()
        
        elif action == 'shutdown':
            print("🛑 Shutting down...")
            self.shutdown()
    
    def wait_for_wake(self):
        """Wait for any button press to wake"""
        import RPi.GPIO as GPIO
        
        # Set up GPIO for polling
        buttons = [
            self.controls.BTN_PREV,
            self.controls.BTN_NEXT,
            self.controls.BTN_MENU,
            self.controls.BTN_BACK
        ]
        
        # Poll for button press
        for _ in range(1000):  # Wait up to 10 seconds
            for pin in buttons:
                if GPIO.input(pin) == GPIO.LOW:
                    print("Button pressed, waking...")
                    time.sleep(0.2)  # Debounce
                    return
            time.sleep(0.01)
        
        # If no button pressed, wake anyway after timeout
        print("Timeout, waking automatically...")
    
    def shutdown(self):
        """Shutdown the e-reader"""
        print("\n💾 Saving bookmark...")
        if self.book_path and self.pages:
            self.bookmark_manager.save_bookmark_async(self.book_path, self.current_page + 1)
        time.sleep(0.5)  # Give time to save
        
        print("🛑 Shutting down display...")
        self.display.clear_display()
        
        # Show shutdown message
        img = self.display.render_confirmation(
            "SHUTDOWN",
            "Goodbye!\n\nShutting down...",
            ["", ""],
            0
        )
        self.display.display_page(img, force_full=True)
        time.sleep(1)
        
        self.display.sleep()
        self.controls.cleanup()
        
        print(f"✅ Done! Returning to page {self.current_page + 1}")
        
        # Actual system shutdown
        print("🚀 Executing system shutdown...")
        try:
            os.system("sudo shutdown -h now")
        except:
            print("Could not execute shutdown command")
        
        sys.exit(0)
    
    def run(self):
        """Main run loop"""
        print("="*60)
        print("📱 E-READER WITH BOOK BROWSER")
        print("="*60)
        print("\nButton Controls:")
        print("  Reading Mode:")
        print("    Prev/Next: Page turn")
        print("    Long press Prev/Next: Jump 10 pages")
        print("    Menu: Open main menu")
        print("    Back: No function")
        print("\n  Menu Mode:")
        print("    Prev/Next: Navigate")
        print("    Menu: Select")
        print("    Back: Cancel/Go back")
        print("="*60)
        print(f"Found {len(self.all_books)} books in {config.BOOKS_DIR}")
        if self.chapters:
            print(f"Found {len(self.chapters)} chapters in current book")
        print("="*60)
        
        # Check if we're starting with partial book
        if self.pages and len(self.pages) < 50:  # If less than 50 pages, likely partial
            print("⚠️ Starting with partial book. Full processing in background...")
        
        try:
            # Keep program alive
            last_page = -1
            last_save_time = time.time()
            last_processing_check = time.time()
            
            while True:
                # Auto-save every minute
                current_time = time.time()
                if current_time - last_save_time > 60:  # 60 seconds
                    if self.book_path and self.pages:
                        self.bookmark_manager.save_bookmark_async(self.book_path, self.current_page + 1)
                    last_save_time = current_time
                
                # Check for background processing completion every 5 seconds
                if current_time - last_processing_check > 5:
                    if self.check_background_processing():
                        print(f"✅ Book now has {len(self.pages)} pages")
                    last_processing_check = current_time
                
                # Show page change notification
                if (self.current_page != last_page and 
                    self.controls.current_state == "READING" and 
                    self.pages):
                    pages_until_refresh = self.display.full_refresh_interval - self.display.page_counter
                    print(f"📄 Page {self.current_page+1}/{len(self.pages)} (Next full: {pages_until_refresh})")
                    last_page = self.current_page
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n⏹️  Shutting down...")
        finally:
            self.shutdown()

# ============================================================================
# MAIN FUNCTION
# ============================================================================
def main():
    # Check if books directory exists
    if not os.path.exists(config.BOOKS_DIR):
        print(f"📁 Creating books directory: {config.BOOKS_DIR}")
        os.makedirs(config.BOOKS_DIR, exist_ok=True)
        print(f"✅ Please add EPUB files to: {config.BOOKS_DIR}")
    
    # Create and run e-reader
    reader = CompleteEReader()
    
    # Try to load last book or any book
    print(f"\n📖 Loading last book...")
    if not reader.load_book():
        # No books found, show browser
        reader.load_books_list()
        if reader.all_books:
            print("📚 Found books, showing browser...")
            reader.controls.current_state = "BROWSER_MENU"
            reader.render_current_state(force_full=True)
        else:
            print("❌ No books found!")
            time.sleep(3)
            return
    
    # Run
    reader.run()

if __name__ == "__main__":
    main()