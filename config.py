#!/usr/bin/python3
# config.py - Configuration constants

import os

# Display dimensions
DISPLAY_WIDTH = 300
DISPLAY_HEIGHT = 400
DISPLAY_MARGIN = 4

# GPIO Pin assignments (Pi Zero 2)
GPIO_PREV = 4    # GPIO4, Pin 7
GPIO_NEXT = 27   # GPIO27, Pin 13
GPIO_MENU = 22   # GPIO22, Pin 15
GPIO_BACK = 23   # GPIO23, Pin 16

# Font paths and sizes
FONT_PATH = "/home/colbeigh/e-Paper/RaspberryPi_JetsonNano/python/pic/Font.ttc"
FONT_SIZE_NORMAL = 18
FONT_SIZE_TITLE = 22
FONT_SIZE_MENU = 20
FONT_SIZE_SMALL = 14

# Directories
BOOKS_DIR = os.path.expanduser("~/books")  # Default books directory
CACHE_DIR = os.path.expanduser("~/.ebook_cache")
BOOKMARK_DIR = os.path.expanduser("~/.ebook_reader")

# Display settings
FULL_REFRESH_INTERVAL = 100  # Pages between full refreshes

# Menu structures
MAIN_MENU = ["Resume", "Jump Pages", "Skip to Chapter", "Refresh Book", "Select Book", "Sleep", "Shutdown"]
JUMP_MENU = ["+5 pages", "+10 pages", "+50 pages", "+100 pages", 
             "-5 pages", "-10 pages", "-50 pages", "-100 pages", "Back"]
SLEEP_MENU = ["Sleep Now", "Cancel"]
SHUTDOWN_MENU = ["Shutdown Now", "Cancel"]
BROWSER_MENU = ["Back to Reading"]  # Will be populated with books