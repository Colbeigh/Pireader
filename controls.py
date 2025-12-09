#!/usr/bin/python3
# controls.py - Button controls with state management

import time
import threading
import RPi.GPIO as GPIO
import config

class FourButtonControls:
    def __init__(self):
        # GPIO assignments
        self.BTN_PREV = config.GPIO_PREV
        self.BTN_NEXT = config.GPIO_NEXT
        self.BTN_MENU = config.GPIO_MENU
        self.BTN_BACK = config.GPIO_BACK
        
        # Button tracking
        self.press_times = {}
        self.last_states = {}
        self.running = True
        
        # Application state
        self.current_state = "READING"  # READING, MAIN_MENU, JUMP_MENU, CHAPTER_MENU, BROWSER_MENU, SLEEP_MENU, SHUTDOWN_CONFIRM
        self.menu_index = 0
        self.submenu_index = 0
        self.chapter_menu_index = 0
        self.browser_index = 0
        self.browser_page = 0
        
        # Menu structures
        self.main_menu = config.MAIN_MENU
        self.jump_menu = config.JUMP_MENU
        self.sleep_menu = config.SLEEP_MENU
        self.shutdown_menu = config.SHUTDOWN_MENU
        self.browser_menu = []  # Will be populated with books
        self.chapter_menu = []  # Will be populated with chapters
        self.chapter_page_map = {}  # Maps chapter index to page number
        
        # Callbacks
        self.callbacks = {
            'state_changed': None,
            'menu_action': None,
            'page_change': None,
            'chapter_select': None,
            'book_select': None
        }
        
        self.setup_gpio()
        self.start_monitoring()
    
    def setup_gpio(self):
        """Setup GPIO pins"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup buttons with pull-up resistors
        buttons = [self.BTN_PREV, self.BTN_NEXT, self.BTN_MENU, self.BTN_BACK]
        for pin in buttons:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self.last_states[pin] = True
        
        print("✅ Buttons: Prev(GPIO4), Next(GPIO27), Menu(GPIO22), Back(GPIO23)")
    
    def set_chapters(self, chapters, chapter_page_map=None):
        """Set available chapters for skipping"""
        self.chapter_menu = chapters
        if chapter_page_map:
            self.chapter_page_map = chapter_page_map
        else:
            for i in range(len(chapters)):
                self.chapter_page_map[i] = i
    
    def set_books(self, books):
        """Set available books for browser"""
        self.browser_menu = ["Back to Reading"] + books
        self.browser_index = 0
        self.browser_page = 0
    
    def start_monitoring(self):
        """Start button monitoring thread"""
        thread = threading.Thread(target=self._monitor_buttons, daemon=True)
        thread.start()
    
    def _monitor_buttons(self):
        """Monitor button presses"""
        while self.running:
            current_time = time.time()
            
            # Check each button
            for pin, name in [
                (self.BTN_PREV, 'prev'),
                (self.BTN_NEXT, 'next'),
                (self.BTN_MENU, 'menu'),
                (self.BTN_BACK, 'back')
            ]:
                current_state = GPIO.input(pin) == GPIO.LOW  # LOW = pressed
                last_state = self.last_states[pin]
                
                # Button just pressed
                if current_state and not last_state:
                    self.press_times[pin] = current_time
                
                # Button just released
                elif not current_state and last_state:
                    if pin in self.press_times:
                        duration = current_time - self.press_times[pin]
                        self._handle_button(name, duration)
                        del self.press_times[pin]
                
                self.last_states[pin] = current_state
            
            time.sleep(0.02)
    
    def _handle_button(self, button, duration):
        """Handle button press with duration"""
        is_long_press = duration >= 0.5
        
        # Handle based on current state
        if self.current_state == "READING":
            self._handle_reading_mode(button, is_long_press)
        
        elif self.current_state == "MAIN_MENU":
            self._handle_main_menu(button, is_long_press)
        
        elif self.current_state == "JUMP_MENU":
            self._handle_jump_menu(button, is_long_press)
        
        elif self.current_state == "CHAPTER_MENU":
            self._handle_chapter_menu(button, is_long_press)
        
        elif self.current_state == "BROWSER_MENU":
            self._handle_browser_menu(button, is_long_press)
        
        elif self.current_state == "SLEEP_MENU":
            self._handle_sleep_menu(button, is_long_press)
        
        elif self.current_state == "SHUTDOWN_CONFIRM":
            self._handle_shutdown_menu(button, is_long_press)
    
    def _handle_reading_mode(self, button, long_press):
        """Handle buttons in reading mode"""
        if button == 'prev':
            if long_press:
                # Quick jump back
                if self.callbacks.get('page_change'):
                    self.callbacks['page_change'](-10)
            else:
                # Normal page back
                if self.callbacks.get('page_change'):
                    self.callbacks['page_change'](-1)
        
        elif button == 'next':
            if long_press:
                # Quick jump forward
                if self.callbacks.get('page_change'):
                    self.callbacks['page_change'](10)
            else:
                # Normal page forward
                if self.callbacks.get('page_change'):
                    self.callbacks['page_change'](1)
        
        elif button == 'menu':
            # Open main menu
            self.current_state = "MAIN_MENU"
            self.menu_index = 0
            if self.callbacks.get('state_changed'):
                self.callbacks['state_changed'](self.current_state, self.menu_index)
        
        elif button == 'back':
            # No function in reading mode
            pass
    
    def _handle_main_menu(self, button, long_press):
        """Handle buttons in main menu"""
        if button == 'prev':
            # Navigate up
            self.menu_index = (self.menu_index - 1) % len(self.main_menu)
            if self.callbacks.get('state_changed'):
                self.callbacks['state_changed'](self.current_state, self.menu_index)
        
        elif button == 'next':
            # Navigate down
            self.menu_index = (self.menu_index + 1) % len(self.main_menu)
            if self.callbacks.get('state_changed'):
                self.callbacks['state_changed'](self.current_state, self.menu_index)
        
        elif button == 'menu':
            # Select menu item
            selected = self.main_menu[self.menu_index]
            
            if selected == "Resume":
                self.current_state = "READING"
                if self.callbacks.get('state_changed'):
                    self.callbacks['state_changed'](self.current_state, 0)
            
            elif selected == "Jump Pages":
                self.current_state = "JUMP_MENU"
                self.submenu_index = 0
                if self.callbacks.get('state_changed'):
                    self.callbacks['state_changed'](self.current_state, self.submenu_index)
            
            elif selected == "Skip to Chapter":
                if self.chapter_menu:
                    self.current_state = "CHAPTER_MENU"
                    self.chapter_menu_index = 0
                    if self.callbacks.get('state_changed'):
                        self.callbacks['state_changed'](self.current_state, self.chapter_menu_index)
                else:
                    print("⚠️ No chapters found in this book")
                    # Stay in main menu
            
            elif selected == "Refresh Book":
                if self.callbacks.get('menu_action'):
                    self.callbacks['menu_action']('refresh')
            
            elif selected == "Select Book":
                self.current_state = "BROWSER_MENU"
                self.browser_index = 0
                if self.callbacks.get('state_changed'):
                    self.callbacks['state_changed'](self.current_state, self.browser_index)
            
            elif selected == "Sleep":
                self.current_state = "SLEEP_MENU"
                self.submenu_index = 0
                if self.callbacks.get('state_changed'):
                    self.callbacks['state_changed'](self.current_state, self.submenu_index)
            
            elif selected == "Shutdown":
                self.current_state = "SHUTDOWN_CONFIRM"
                self.submenu_index = 0
                if self.callbacks.get('state_changed'):
                    self.callbacks['state_changed'](self.current_state, self.submenu_index)
        
        elif button == 'back':
            # Back to reading
            self.current_state = "READING"
            if self.callbacks.get('state_changed'):
                self.callbacks['state_changed'](self.current_state, 0)
    
    def _handle_jump_menu(self, button, long_press):
        """Handle buttons in jump menu"""
        if button == 'prev':
            # Navigate up
            self.submenu_index = (self.submenu_index - 1) % len(self.jump_menu)
            if self.callbacks.get('state_changed'):
                self.callbacks['state_changed'](self.current_state, self.submenu_index)
        
        elif button == 'next':
            # Navigate down
            self.submenu_index = (self.submenu_index + 1) % len(self.jump_menu)
            if self.callbacks.get('state_changed'):
                self.callbacks['state_changed'](self.current_state, self.submenu_index)
        
        elif button == 'menu':
            # Execute jump
            selected = self.jump_menu[self.submenu_index]
            
            if selected == "Back":
                self.current_state = "MAIN_MENU"
                self.menu_index = 1  # Go back to Jump Pages in main menu
                if self.callbacks.get('state_changed'):
                    self.callbacks['state_changed'](self.current_state, self.menu_index)
            
            else:
                # Parse jump amount
                if selected.startswith("+"):
                    pages = int(selected[1:].split()[0])
                    if self.callbacks.get('page_change'):
                        self.callbacks['page_change'](pages)
                elif selected.startswith("-"):
                    pages = -int(selected[1:].split()[0])
                    if self.callbacks.get('page_change'):
                        self.callbacks['page_change'](pages)
                
                # Return to reading
                self.current_state = "READING"
                if self.callbacks.get('state_changed'):
                    self.callbacks['state_changed'](self.current_state, 0)
        
        elif button == 'back':
            # Back to main menu
            self.current_state = "MAIN_MENU"
            self.menu_index = 1  # Jump Pages position
            if self.callbacks.get('state_changed'):
                self.callbacks['state_changed'](self.current_state, self.menu_index)
    
    def _handle_chapter_menu(self, button, long_press):
        """Handle buttons in chapter selection menu"""
        if not self.chapter_menu:
            self.current_state = "MAIN_MENU"
            if self.callbacks.get('state_changed'):
                self.callbacks['state_changed'](self.current_state, self.menu_index)
            return
        
        if button == 'prev':
            # Navigate up
            self.chapter_menu_index = (self.chapter_menu_index - 1) % len(self.chapter_menu)
            if self.callbacks.get('state_changed'):
                self.callbacks['state_changed'](self.current_state, self.chapter_menu_index)
        
        elif button == 'next':
            # Navigate down
            self.chapter_menu_index = (self.chapter_menu_index + 1) % len(self.chapter_menu)
            if self.callbacks.get('state_changed'):
                self.callbacks['state_changed'](self.current_state, self.chapter_menu_index)
        
        elif button == 'menu':
            # Select chapter
            if self.callbacks.get('chapter_select'):
                self.callbacks['chapter_select'](self.chapter_menu_index)
            
            # Return to reading
            self.current_state = "READING"
            if self.callbacks.get('state_changed'):
                self.callbacks['state_changed'](self.current_state, 0)
        
        elif button == 'back':
            # Back to main menu
            self.current_state = "MAIN_MENU"
            self.menu_index = 2  # Skip to Chapter position
            if self.callbacks.get('state_changed'):
                self.callbacks['state_changed'](self.current_state, self.menu_index)
    
    def _handle_browser_menu(self, button, long_press):
        """Handle buttons in book browser menu"""
        if not self.browser_menu:
            self.current_state = "MAIN_MENU"
            if self.callbacks.get('state_changed'):
                self.callbacks['state_changed'](self.current_state, self.menu_index)
            return
        
        items_per_page = 6
        total_items = len(self.browser_menu)
        total_pages = (total_items + items_per_page - 1) // items_per_page
        
        if button == 'prev':
            # Navigate up
            self.browser_index = (self.browser_index - 1) % total_items
            # Update page if needed
            self.browser_page = self.browser_index // items_per_page
            if self.callbacks.get('state_changed'):
                self.callbacks['state_changed'](self.current_state, self.browser_index)
        
        elif button == 'next':
            # Navigate down
            self.browser_index = (self.browser_index + 1) % total_items
            # Update page if needed
            self.browser_page = self.browser_index // items_per_page
            if self.callbacks.get('state_changed'):
                self.callbacks['state_changed'](self.current_state, self.browser_index)
        
        elif button == 'menu':
            # Select book
            if self.browser_index == 0:
                # "Back to Reading" selected
                self.current_state = "READING"
                if self.callbacks.get('state_changed'):
                    self.callbacks['state_changed'](self.current_state, 0)
            else:
                # Book selected
                if self.callbacks.get('book_select'):
                    book_index = self.browser_index - 1  # Adjust for "Back to Reading"
                    if book_index < len(self.browser_menu) - 1:
                        self.callbacks['book_select'](book_index)
        
        elif button == 'back':
            # Back to main menu
            self.current_state = "MAIN_MENU"
            self.menu_index = 3  # Select Book position
            if self.callbacks.get('state_changed'):
                self.callbacks['state_changed'](self.current_state, self.menu_index)
    
    def _handle_sleep_menu(self, button, long_press):
        """Handle buttons in sleep menu"""
        if button == 'prev':
            # Navigate up
            self.submenu_index = (self.submenu_index - 1) % len(self.sleep_menu)
            if self.callbacks.get('state_changed'):
                self.callbacks['state_changed'](self.current_state, self.submenu_index)
        
        elif button == 'next':
            # Navigate down
            self.submenu_index = (self.submenu_index + 1) % len(self.sleep_menu)
            if self.callbacks.get('state_changed'):
                self.callbacks['state_changed'](self.current_state, self.submenu_index)
        
        elif button == 'menu':
            selected = self.sleep_menu[self.submenu_index]
            
            if selected == "Sleep Now":
                if self.callbacks.get('menu_action'):
                    self.callbacks['menu_action']('sleep')
            elif selected == "Cancel":
                self.current_state = "MAIN_MENU"
                self.menu_index = 4  # Sleep position
                if self.callbacks.get('state_changed'):
                    self.callbacks['state_changed'](self.current_state, self.menu_index)
        
        elif button == 'back':
            # Back to main menu
            self.current_state = "MAIN_MENU"
            self.menu_index = 4  # Sleep position
            if self.callbacks.get('state_changed'):
                self.callbacks['state_changed'](self.current_state, self.menu_index)
    
    def _handle_shutdown_menu(self, button, long_press):
        """Handle buttons in shutdown menu"""
        if button == 'prev':
            # Navigate up
            self.submenu_index = (self.submenu_index - 1) % len(self.shutdown_menu)
            if self.callbacks.get('state_changed'):
                self.callbacks['state_changed'](self.current_state, self.submenu_index)
        
        elif button == 'next':
            # Navigate down
            self.submenu_index = (self.submenu_index + 1) % len(self.shutdown_menu)
            if self.callbacks.get('state_changed'):
                self.callbacks['state_changed'](self.current_state, self.submenu_index)
        
        elif button == 'menu':
            selected = self.shutdown_menu[self.submenu_index]
            
            if selected == "Shutdown Now":
                if self.callbacks.get('menu_action'):
                    self.callbacks['menu_action']('shutdown')
            elif selected == "Cancel":
                self.current_state = "MAIN_MENU"
                self.menu_index = 5  # Shutdown position
                if self.callbacks.get('state_changed'):
                    self.callbacks['state_changed'](self.current_state, self.menu_index)
        
        elif button == 'back':
            # Back to main menu
            self.current_state = "MAIN_MENU"
            self.menu_index = 5  # Shutdown position
            if self.callbacks.get('state_changed'):
                self.callbacks['state_changed'](self.current_state, self.menu_index)
    
    def register_callback(self, event, callback):
        """Register a callback function"""
        self.callbacks[event] = callback
    
    def cleanup(self):
        """Cleanup GPIO"""
        self.running = False
        time.sleep(0.1)
        GPIO.cleanup()