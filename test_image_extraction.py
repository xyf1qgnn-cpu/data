#!/usr/bin/env python3
"""
Simple test script for PDF image extraction without API calls
"""

import os
import sys
from pdf2image import convert_from_path
from PIL import Image

# Test PDF path
PDF_PATH = "/mnt/e/Documents/data_unextracted/Behaviour-and-design-of-stainless-steel-recycled-aggregate-co_2025_Engineeri.pdf"

def test_pdf_extraction():
    """Test PDF to image extraction"""
    print(f"Testing PDF extraction: {os.path.basename(PDF_PATH)}")
    print("-" * 60)

    if not os.path.exists(PDF_PATH):
        print(f"Error: PDF file not found at {PDF_PATH}")
        return False

    try:
        # Convert PDF to images
        print("Step 1: Converting PDF to images...")
        images = convert_from_path(PDF_PATH, dpi=150)
        print(f"✓ Successfully extracted {len(images)} pages")

        # Test saving first few images
        cache_dir = "./cache_test"
        os.makedirs(cache_dir, exist_ok=True)

        print("\nStep 2: Saving images to cache...")
        saved_count = 0
        for i, image in enumerate(images[:min(5, len(images))], 1):  # Save first 5 images
            img_path = os.path.join(cache_dir, f"{i}.jpg")
            image.save(img_path, "JPEG", quality=95)
            print(f"  Saved: {img_path} (Size: {image.size})")
            saved_count += 1

        if len(images) > 5:
            print(f"  ... and {len(images) - 5} more images")

        print("\n" + "-" * 60)
        print(f"✅ SUCCESS: PDF image extraction works!")
        print(f"  - Total pages: {len(images)}")
        print(f"  - Sample images saved to: {cache_dir}")
        print(f"  - Image quality: 95% JPEG")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pdf_extraction()
    sys.exit(0 if success else 1)
