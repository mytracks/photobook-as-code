"""
Generate sample test photos.
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# Create sample photos for testing
fixtures_dir = Path(__file__).parent / "fixtures" / "sample-photos"
fixtures_dir.mkdir(parents=True, exist_ok=True)

colors = [
    ("#FF6B6B", "Red"),
    ("#4ECDC4", "Teal"),
    ("#45B7D1", "Blue"),
    ("#FFA07A", "Orange"),
    ("#98D8C8", "Mint"),
    ("#F7DC6F", "Yellow"),
    ("#BB8FCE", "Purple"),
    ("#85C1E2", "Sky"),
]

for i, (color, name) in enumerate(colors, 1):
    # Create image
    img = Image.new('RGB', (1600, 1200), color)
    draw = ImageDraw.Draw(img)
    
    # Draw text
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 100)
    except:
        font = ImageFont.load_default()
    
    text = f"Photo {i}\n{name}"
    
    # Get text bbox for centering
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    position = ((1600 - text_width) // 2, (1200 - text_height) // 2)
    
    # Draw text with black outline
    for offset_x in [-2, 0, 2]:
        for offset_y in [-2, 0, 2]:
            draw.text(
                (position[0] + offset_x, position[1] + offset_y),
                text,
                fill='black',
                font=font,
                align='center'
            )
    
    draw.text(position, text, fill='white', font=font, align='center')
    
    # Save
    filename = fixtures_dir / f"photo_{i:02d}.jpg"
    img.save(filename, 'JPEG', quality=90)
    print(f"Created {filename}")

print(f"\n✓ Created {len(colors)} sample photos in {fixtures_dir}")
