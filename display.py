#!/usr/bin/python3
# display.py - E-Paper display management

import sys
import os
import datetime
import textwrap
sys.path.append("/home/colbeigh/e-Paper/RaspberryPi_JetsonNano/python/lib")

from waveshare_epd import epd4in2_V2
from PIL import Image, ImageDraw
import config
from fonts import FastFontCache

class EReaderDisplay:
    def __init__(self):
        self.epd = epd4in2_V2.EPD()
        self.current_image = None
        self.use_partial = True
        self.show_time = True
        self.needs_clear = False
        self.page_counter = 0
        self.full_refresh_interval = config.FULL_REFRESH_INTERVAL
        self._display_initialized = False
        
        # Fonts
        self.title_font = FastFontCache.get_font(config.FONT_SIZE_TITLE)
        self.menu_font = FastFontCache.get_font(config.FONT_SIZE_MENU)
        self.normal_font = FastFontCache.get_font(config.FONT_SIZE_NORMAL)
        self.small_font = FastFontCache.get_font(config.FONT_SIZE_SMALL)
        
    def init_display(self):
        """Initialize display"""
        if not self._display_initialized:
            self.epd.init()
            self._display_initialized = True
    
    def clear_display(self):
        """Clear display completely"""
        self.epd.init()
        self.epd.Clear()
        self.needs_clear = False
        self.page_counter = 0
    
    def check_full_refresh_needed(self):
        """Check if we need a full refresh"""
        self.page_counter += 1
        if self.page_counter >= self.full_refresh_interval:
            print(f"🔄 Full refresh after {self.page_counter} pages")
            self.page_counter = 0
            return True
        return False
    
    def render_reading_page(self, font, pages, page_index, margin=config.DISPLAY_MARGIN):
        """Render a normal reading page"""
        W, H = config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT
        img = Image.new("1", (W, H), 255)
        draw = ImageDraw.Draw(img)
        
        bbox = font.getbbox("Hg")
        line_height = bbox[3] + 1
        font_height = bbox[3]
        
        # Draw text content
        y = margin
        footer_margin = font_height * 2.5
        text_area_height = H - margin - footer_margin
        
        page_content = pages[page_index] if page_index < len(pages) else ["Page not found"]
        
        for line in page_content:
            if y + font_height > text_area_height:
                break
            if line:
                draw.text((margin, y), line, font=font, fill=0)
                y += line_height
        
        # Draw footer
        footer_y = H - margin - font_height
        
        # Time (left)
        if self.show_time:
            current_time = datetime.datetime.now().strftime("%H:%M")
            draw.text((margin, footer_y - 2), current_time, font=font, fill=0)
        
        # Page number (right)
        page_info = f"{page_index+1}/{len(pages)}"
        page_width = font.getlength(page_info)
        draw.text((W - margin - page_width, footer_y - 2), page_info, font=font, fill=0)
        
        # Progress bar
        progress = (page_index + 1) / len(pages)
        bar_width = 200
        bar_x = (W - bar_width) // 2
        bar_y = H - margin - font_height - 8
        bar_filled = int(bar_width * progress)
        draw.rectangle((bar_x, bar_y, bar_x + bar_width, bar_y + 2), outline=0, fill=255)
        if bar_filled > 0:
            draw.rectangle((bar_x, bar_y, bar_x + bar_filled, bar_y + 2), fill=0)
        
        self.current_image = img
        return img
    
    def render_menu(self, title, items, selected_index, margin=10):
        """Render a generic menu"""
        W, H = config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT
        img = Image.new("1", (W, H), 255)
        draw = ImageDraw.Draw(img)
        
        # Title
        title_width = self.title_font.getlength(title)
        draw.text((W//2 - title_width//2, margin), title, font=self.title_font, fill=0)
        draw.line((margin, margin + 30, W - margin, margin + 30), fill=0, width=2)
        
        # Menu items
        y = margin + 50
        for i, item in enumerate(items):
            # Truncate long items
            display_item = item
            if len(item) > 30:
                display_item = item[:27] + "..."
            
            # Highlight selected item
            if i == selected_index:
                # Draw selection background
                draw.rectangle((margin-5, y-5, W-margin+5, y+25), fill=0)
                draw.text((margin, y), f"▶ {display_item}", font=self.menu_font, fill=255)
            else:
                draw.text((margin + 20, y), display_item, font=self.menu_font, fill=0)
            
            y += 35
        
        # Instructions at bottom
        instructions = "Prev/Next: Navigate  Menu: Select  Back: Cancel"
        inst_width = self.small_font.getlength(instructions)
        draw.text((W//2 - inst_width//2, H - 30), instructions, font=self.small_font, fill=0)
        
        self.current_image = img
        return img
    
    def render_chapter_menu(self, chapters, selected_index, margin=10):
        """Render chapter selection menu"""
        W, H = config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT
        img = Image.new("1", (W, H), 255)
        draw = ImageDraw.Draw(img)
        
        # Title
        title = "CHAPTERS"
        title_width = self.title_font.getlength(title)
        draw.text((W//2 - title_width//2, margin), title, font=self.title_font, fill=0)
        draw.line((margin, margin + 30, W - margin, margin + 30), fill=0, width=2)
        
        # Chapter items
        y = margin + 50
        items_per_page = 6
        start_index = (selected_index // items_per_page) * items_per_page
        
        for i in range(start_index, min(start_index + items_per_page, len(chapters))):
            chapter = chapters[i]
            # Truncate long chapter titles
            display_chapter = chapter
            if len(chapter) > 25:
                display_chapter = chapter[:22] + "..."
            
            # Add numbering
            display_text = f"{i+1}. {display_chapter}"
            
            # Highlight selected item
            if i == selected_index:
                draw.rectangle((margin-5, y-5, W-margin+5, y+25), fill=0)
                draw.text((margin, y), display_text, font=self.menu_font, fill=255)
            else:
                draw.text((margin, y), display_text, font=self.menu_font, fill=0)
            
            y += 35
        
        # Page indicator
        total_pages = (len(chapters) + items_per_page - 1) // items_per_page
        current_page = start_index // items_per_page + 1
        if total_pages > 1:
            page_indicator = f"Page {current_page}/{total_pages}"
            page_width = self.small_font.getlength(page_indicator)
            draw.text((W//2 - page_width//2, H - 50), page_indicator, font=self.small_font, fill=0)
        
        # Instructions
        instructions = "Menu: Select  Back: Cancel"
        inst_width = self.small_font.getlength(instructions)
        draw.text((W//2 - inst_width//2, H - 30), instructions, font=self.small_font, fill=0)
        
        self.current_image = img
        return img
    
    def render_browser_menu(self, books, selected_index, current_page, margin=10):
        """Render book browser menu"""
        W, H = config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT
        img = Image.new("1", (W, H), 255)
        draw = ImageDraw.Draw(img)
        
        # Title
        title = "SELECT BOOK"
        title_width = self.title_font.getlength(title)
        draw.text((W//2 - title_width//2, margin), title, font=self.title_font, fill=0)
        draw.line((margin, margin + 30, W - margin, margin + 30), fill=0, width=2)
        
        # Book items (paginated)
        y = margin + 50
        items_per_page = 6
        start_index = current_page * items_per_page
        end_index = min(start_index + items_per_page, len(books))
        
        for i in range(start_index, end_index):
            book_name = books[i]
            # Truncate long book names
            display_book = book_name
            if len(book_name) > 25:
                display_book = book_name[:22] + "..."
            
            # Highlight selected item
            if i == selected_index:
                draw.rectangle((margin-5, y-5, W-margin+5, y+25), fill=0)
                draw.text((margin, y), f"▶ {display_book}", font=self.menu_font, fill=255)
            else:
                draw.text((margin + 20, y), display_book, font=self.menu_font, fill=0)
            
            y += 35
        
        # Page indicator
        total_pages = (len(books) + items_per_page - 1) // items_per_page
        if total_pages > 1:
            page_indicator = f"Page {current_page + 1}/{total_pages}"
            page_width = self.small_font.getlength(page_indicator)
            draw.text((W//2 - page_width//2, H - 50), page_indicator, font=self.small_font, fill=0)
        
        # Instructions
        instructions = "Menu: Select  Back: Cancel"
        inst_width = self.small_font.getlength(instructions)
        draw.text((W//2 - inst_width//2, H - 30), instructions, font=self.small_font, fill=0)
        
        self.current_image = img
        return img
    
    def render_confirmation(self, title, message, options, selected_index, margin=10):
        """Render confirmation dialog"""
        W, H = config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT
        img = Image.new("1", (W, H), 255)
        draw = ImageDraw.Draw(img)
        
        # Title
        title_width = self.title_font.getlength(title)
        draw.text((W//2 - title_width//2, margin), title, font=self.title_font, fill=0)
        
        # Message
        y = margin + 50
        msg_lines = textwrap.wrap(message, width=30)
        for line in msg_lines:
            draw.text((W//2 - self.menu_font.getlength(line)//2, y), line, font=self.menu_font, fill=0)
            y += 30
        
        # Options
        y += 20
        for i, option in enumerate(options):
            option_x = W//2 - 100 if i == 0 else W//2 + 20
            
            if i == selected_index:
                draw.rectangle((option_x-5, y-5, option_x+95, y+25), fill=0)
                draw.text((option_x, y), option, font=self.menu_font, fill=255)
            else:
                draw.rectangle((option_x-5, y-5, option_x+95, y+25), outline=0, width=1)
                draw.text((option_x, y), option, font=self.menu_font, fill=0)
        
        self.current_image = img
        return img
    
    def display_page(self, img, force_full=False):
        """Display page with appropriate refresh"""
        periodic_full = self.check_full_refresh_needed()
        needs_full = self.needs_clear or force_full or periodic_full
        
        if needs_full:
            if periodic_full:
                print("🔄 Periodic full refresh")
            self.clear_display()
            self.epd.display(self.epd.getbuffer(img))
            return False
        
        if self.use_partial:
            try:
                self.epd.display_Partial(self.epd.getbuffer(img))
                return True
            except:
                self.epd.display(self.epd.getbuffer(img))
                return False
        else:
            self.epd.display(self.epd.getbuffer(img))
            return False
    
    def sleep(self):
        """Put display to sleep"""
        self.epd.sleep()
    
    def wake(self):
        """Wake display from sleep"""
        self.epd.init()