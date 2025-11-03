#!/usr/bin/env python3
"""
Example script showing how to download and analyze images from online sources.
This demonstrates the enhanced image processor with real-world images.
"""

import json
import logging
import urllib.request
from pathlib import Path
from src.image_processor import ImageProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def download_image(url: str, save_path: str) -> bool:
    """
    Download an image from a URL.
    
    Args:
        url: URL of the image
        save_path: Local path to save the image
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logging.info(f"Downloading image from: {url}")
        urllib.request.urlretrieve(url, save_path)
        logging.info(f"Image saved to: {save_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to download image: {e}")
        return False


def analyze_and_display(processor: ImageProcessor, image_path: str):
    """
    Analyze an image and display key information.
    
    Args:
        processor: ImageProcessor instance
        image_path: Path to the image file
    """
    print("\n" + "="*80)
    print(f"Analyzing: {Path(image_path).name}")
    print("="*80)
    
    try:
        analysis = processor.analyze_image(image_path)
        
        # Display content classification
        content = analysis.get('content_classification', {})
        print(f"\n📋 WHAT IT IS:")
        print(f"   {content.get('description', 'Unknown')}")
        
        # Display key features
        print(f"\n🔑 KEY FEATURES:")
        features = analysis.get('key_features', {}).get('key_features', [])
        for feature in features[:5]:  # Show top 5 features
            print(f"   • {feature}")
        
        # Display what it displays/contains
        print(f"\n📸 WHAT IT DISPLAYS:")
        
        # Faces
        faces = analysis.get('face_detection', {})
        if faces.get('has_faces'):
            print(f"   • {faces.get('description')}")
        
        # Text
        text = analysis.get('text_extraction', {})
        if text.get('has_text'):
            print(f"   • {text.get('description')}")
            if text.get('word_count', 0) > 0:
                preview = text.get('text_content', '')[:100]
                if preview:
                    print(f"     Text preview: \"{preview}...\"")
        
        # Shapes
        shapes = analysis.get('shape_detection', {})
        if shapes.get('total_shapes', 0) > 0:
            print(f"   • {shapes.get('description')}")
        
        # Patterns
        patterns = analysis.get('pattern_detection', {})
        if patterns.get('has_codes'):
            print(f"   • {patterns.get('description')}")
        
        # Visual characteristics
        print(f"\n🎨 VISUAL CHARACTERISTICS:")
        
        # Brightness
        brightness = analysis.get('brightness', {})
        brightness_pct = brightness.get('brightness_percentage', 0)
        if brightness_pct < 30:
            print(f"   • Dark image ({brightness_pct}% brightness)")
        elif brightness_pct > 70:
            print(f"   • Bright image ({brightness_pct}% brightness)")
        else:
            print(f"   • Medium brightness ({brightness_pct}%)")
        
        # Dominant color
        dominant = analysis.get('dominant_color', {}).get('most_dominant', {})
        if dominant:
            hex_color = dominant.get('hex', '#000000')
            percentage = dominant.get('percentage', 0)
            print(f"   • Dominant color: {hex_color} ({percentage}% of image)")
        
        # Texture
        texture = analysis.get('texture_analysis', {})
        print(f"   • {texture.get('description', 'Unknown texture')}")
        
        # Edge complexity
        edges = analysis.get('edge_detection', {})
        print(f"   • {edges.get('description', 'Unknown complexity')}")
        
        print("\n" + "="*80)
        
       
        output_file = Path(image_path).stem + "_detailed_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        print(f"✅ Detailed analysis saved to: {output_file}\n")
        
    except Exception as e:
        print(f"❌ Error analyzing image: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function demonstrating online image analysis."""
    print("Enhanced Image Processor - Online Image Analysis Demo")
    print("="*80)
    
   
    processor = ImageProcessor()
    

    example_images = [
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/1200px-Cat03.jpg",
            "name": "cat_photo.jpg",
            "description": "A cat photo"
        },
        
    ]
    
    print("\nThis script can download and analyze images from URLs.")
    print("\nOptions:")
    print("1. Use example image (cat photo from Wikimedia)")
    print("2. Enter your own image URL")
    print("3. Analyze a local image file")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
       
        img = example_images[0]
        local_path = f"downloaded_{img['name']}"
        
        if download_image(img['url'], local_path):
            analyze_and_display(processor, local_path)
        else:
            print("Failed to download example image.")
    
    elif choice == "2":
       
        url = input("\nEnter image URL: ").strip()
        if not url:
            print("No URL provided.")
            return
        
        
        filename = url.split('/')[-1]
        if not any(filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png']):
            filename = "downloaded_image.jpg"
        
        local_path = f"downloaded_{filename}"
        
        if download_image(url, local_path):
            analyze_and_display(processor, local_path)
        else:
            print("Failed to download image.")
    
    elif choice == "3":
        
        file_path = input("\nEnter path to local image: ").strip()
        if not file_path or not Path(file_path).exists():
            print("Invalid file path.")
            return
        
        analyze_and_display(processor, file_path)
    
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()
