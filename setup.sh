#!/bin/bash
# setup.sh - Install dependencies and setup e-reader

echo "📦 Setting up e-reader..."

# Update system
echo "🔄 Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install Python packages
echo "📦 Installing Python packages..."
sudo apt install -y python3-pip python3-pil python3-rpi.gpio

# Install Python libraries
echo "📚 Installing ebooklib and dependencies..."
pip3 install ebooklib beautifulsoup4

# Check if waveshare library exists
echo "🔍 Checking for waveshare e-paper library..."
if [ ! -d "/home/colbeigh/e-Paper/RaspberryPi_JetsonNano" ]; then
    echo "⚠️ Waveshare e-paper library not found."
    echo "Please install it from: https://github.com/waveshare/e-Paper"
    echo "Or run:"
    echo "  cd ~"
    echo "  git clone https://github.com/waveshare/e-Paper"
    echo "  cd e-Paper/RaspberryPi_JetsonNano"
    echo "  sudo bash ./setup.sh"
fi

# Create directories
echo "📁 Creating cache directories..."
mkdir -p ~/.ebook_cache
mkdir -p ~/.ebook_reader
mkdir -p ~/books
mkdir -p ~/ereader

# Copy Python files if they exist in current directory
if [ -f "main.py" ]; then
    echo "📄 Copying Python files..."
    cp *.py ~/ereader/
fi

# Make main script executable
if [ -f "~/ereader/main.py" ]; then
    chmod +x ~/ereader/main.py
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the e-reader:"
echo "  cd ~/ereader"
echo "  python3 main.py"
echo ""
echo "Add EPUB files to: ~/books/"
echo ""
echo "If you haven't installed the waveshare library yet:"
echo "  cd ~"
echo "  git clone https://github.com/waveshare/e-Paper"
echo "  cd e-Paper/RaspberryPi_JetsonNano"
echo "  sudo bash ./setup.sh"