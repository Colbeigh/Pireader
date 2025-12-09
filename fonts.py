#!/usr/bin/python3
# fonts.py - Font management with caching

from PIL import ImageFont
import os
import config

class FastFontCache:
    _cache = {}
    
    @staticmethod
    def get_font(size=config.FONT_SIZE_NORMAL):
        cache_key = (config.FONT_PATH, size)
        
        if cache_key not in FastFontCache._cache:
            if os.path.exists(config.FONT_PATH):
                try:
                    FastFontCache._cache[cache_key] = ImageFont.truetype(config.FONT_PATH, size)
                except:
                    FastFontCache._cache[cache_key] = ImageFont.load_default()
            else:
                FastFontCache._cache[cache_key] = ImageFont.load_default()
        
        return FastFontCache._cache[cache_key]