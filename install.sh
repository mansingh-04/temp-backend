#!/bin/bash
set -e

echo "Installing dependencies..."
pip install --no-cache-dir -r requirements.txt

echo "Checking for Tesseract OCR..."
if ! command -v tesseract &> /dev/null
then
    echo "Tesseract OCR not found. Attempting to install..."
    apt-get update && apt-get install -y tesseract-ocr
fi

echo "Installation complete." 