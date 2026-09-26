import os
import time
from sqlalchemy.orm import Session
import models
from PIL import Image, ImageDraw, ImageFilter

def create_marketing_image(screenshot_path: str, output_filename: str):
    try:
        if not os.path.exists(screenshot_path):
            return None
            
        # Open original screenshot
        screenshot = Image.open(screenshot_path)
        
        # Calculate new dimensions for marketing asset (e.g. 1200x800 for LinkedIn/Twitter)
        bg_width, bg_height = 1200, 800
        
        # Create a beautiful gradient background (for simplicity, using a solid stylish color)
        bg_color = (20, 25, 40) # Dark sleek blue
        canvas = Image.new("RGB", (bg_width, bg_height), bg_color)
        
        # Resize screenshot to fit nicely inside with padding
        target_width = 900
        aspect_ratio = screenshot.height / screenshot.width
        target_height = int(target_width * aspect_ratio)
        
        # Crop if too tall
        if target_height > 600:
            target_height = 600
            screenshot = screenshot.crop((0, 0, screenshot.width, int(screenshot.width * (600/900))))
            
        screenshot = screenshot.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # Create mock browser window frame
        frame_padding = 20
        frame_width = target_width + frame_padding*2
        frame_height = target_height + frame_padding + 40 # extra space for top bar
        
        # Position in center
        paste_x = (bg_width - frame_width) // 2
        paste_y = (bg_height - frame_height) // 2 + 30 # slight offset downwards
        
        # Draw frame shadow
        draw = ImageDraw.Draw(canvas)
        draw.rounded_rectangle(
            [paste_x-10, paste_y-10, paste_x+frame_width+10, paste_y+frame_height+10],
            radius=20,
            fill=(10, 12, 20)
        )
        
        # Draw main browser frame
        draw.rounded_rectangle(
            [paste_x, paste_y, paste_x+frame_width, paste_y+frame_height],
            radius=15,
            fill=(245, 245, 245) # Light grey frame
        )
        
        # Draw mock macOS buttons
        btn_y = paste_y + 15
        draw.ellipse([paste_x+20, btn_y, paste_x+32, btn_y+12], fill=(255, 95, 86))  # Red
        draw.ellipse([paste_x+40, btn_y, paste_x+52, btn_y+12], fill=(255, 189, 46)) # Yellow
        draw.ellipse([paste_x+60, btn_y, paste_x+72, btn_y+12], fill=(39, 201, 63))  # Green
        
        # Paste the actual screenshot
        canvas.paste(screenshot, (paste_x + frame_padding, paste_y + 40))
        
        output_path = os.path.join("media_assets", output_filename)
        canvas.save(output_path, quality=95)
        
        return f"media_assets/{output_filename}"
    except Exception as e:
        print(f"Error generating marketing image: {e}")
        return None

def generate_marketing_media(product_id: str, db: Session):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        return []
        
    # Get up to 3 screenshots
    evidence = db.query(models.PageScreenshot).filter(models.PageScreenshot.product_id == product_id).limit(3).all()
    
    generated_assets = []
    
    for idx, ev in enumerate(evidence):
        original_path = ev.storage_key # e.g. screenshots/xxx.png
        output_filename = f"marketing_{product_id}_{idx}.png"
        
        # Generate the beautiful composite
        asset_path = create_marketing_image(original_path, output_filename)
        if asset_path:
            generated_assets.append(asset_path)
            
    time.sleep(2) # Simulate rendering time
    return generated_assets
