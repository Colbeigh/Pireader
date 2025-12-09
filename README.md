# PiReader

A complete e-reader application for Raspberry Pi Zero 2 with 4-button navigation, E-Ink display, EPUB support, and book browser.

## Features
source ~/epubenv/bin/activate
cd ~/ereader
python3 main.py

## Features

- **EPUB Support**: Read .epub files with automatic bookmarking
- **4-Button Navigation**: Simple Prev/Next/Menu/Back controls
- **E-Paper Display**: 4.2" Waveshare e-paper display support
- **Book Browser**: Browse and select from multiple books
- **Chapter Navigation**: Jump to chapters (when available)
- **Page Navigation**: Go to specific page numbers
- **Sleep Mode**: Power-saving display sleep
- **Auto-Resume**: Automatically returns to last read page
- **Background Processing**: Fast initial load with full processing in background

## Hardware Requirements

- Raspberry Pi Zero 2 W
- Waveshare 4.2" E-Paper Display (or compatible)
- 4x Tactile buttons
- Jumper wires
- MicroSD card (16GB+ recommended)
- Power supply (5V 2A)

## GPIO Wiring (Pi Zero 2)

| Button | GPIO | Physical Pin | Color (suggested) |
|--------|------|--------------|-------------------|
| Previous | GPIO4 | Pin 7 | Yellow |
| Next | GPIO27 | Pin 13 | Green |
| Menu | GPIO22 | Pin 15 | Orange |
| Back | GPIO23 | Pin 16 | Blue |

**Wiring Instructions:**
1. Connect one side of each button to its GPIO pin
2. Connect other side to any GND pin (Pins 6, 9, 14, 20, 25, 30, 34, or 39)
3. Recommended: Use GND Pin 14 for Next/Menu/Back buttons, Pin 9 for Previous

## Quick Installation

### 1. Install System Dependencies
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3-pip python3-pil python3-rpi.gpio git

### 2. Install Python Packages
pip3 install \
    ebooklib==0.18 \
    beautifulsoup4==4.12.2 \
    Pillow==10.0.0 \
    RPi.GPIO==0.7.1

### 3. Install Waveshare E-Paper Library
cd ~
git clone https://github.com/waveshare/e-Paper
cd e-Paper/RaspberryPi_JetsonNano
sudo bash ./setup.sh

### 4. Clone or copy files
mkdir -p ~/ereader
cd ~/ereader
# Copy all .py files to this directory

### 5. Create Directories
mkdir -p ~/books
mkdir -p ~/.ebook_cache
mkdir -p ~/.ebook_reader

### 6. Add your book (EPUB FORMAT ONLY)
# Copy EPUB files to:
cp *.epub ~/books/

### 7. Run the e-reader
chmod +x setup.sh
./setup.sh
source ~/epubenv/bin/activate (NOT NEEDED DEPENDING ON OS)
cd ~/ereader
python3 main.py

### 8. OPTIONAL Virtual Environment
## - Certain Dependencies will not download without on certain OS
python3 -m venv ~/epubenv
source ~/epubenv/bin/activate
pip install -r requirements.txt

## Button Controls
### Reading Mode:
Prev/Next: Turn page
Long press Prev/Next: Jump 10 pages
Menu: Open main menu
Back: No function

### Menu Mode:
Prev/Next: Navigate menu
Menu: Select item
Back: Cancel/Go back
Main Menu Options
Resume - Return to reading
Jump Pages - Quick page jumps (+/- 5,10,50,100)
Go to Page - Enter specific page number
Skip to Chapter - Jump to specific chapter
Refresh Book - Reprocess current book
Select Book - Browse and choose different book
Sleep - Put display to sleep

Shutdown - Power off e-reader



## Quick Installation Script

You can also create a `setup.sh`:

```bash
#!/bin/bash
# setup.sh - Complete installation script

echo "📦 Installing e-reader dependencies..."

# Update system
sudo apt update
sudo apt upgrade -y

# Install system packages
sudo apt install -y python3-pip python3-pil python3-rpi.gpio git

# Install Python packages
pip3 install ebooklib beautifulsoup4 Pillow RPi.GPIO

# Install waveshare library
cd ~
if [ ! -d "e-Paper" ]; then
    git clone https://github.com/waveshare/e-Paper
    cd e-Paper/RaspberryPi_JetsonNano
    sudo bash ./setup.sh
    cd ~
fi

# Create directories
mkdir -p ~/books ~/.ebook_cache ~/.ebook_reader ~/ereader

echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Add EPUB files to ~/books/"
echo "2. Copy e-reader .py files to ~/ereader/"
echo "3. Run: cd ~/ereader && python3 main.py"
chmod +x setup.sh
./setup.sh
