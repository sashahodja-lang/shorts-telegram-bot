import os
from PIL import Image, ImageDraw

def create_bot_icon():
    size = (256, 256)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Telegram blue background
    padding = 16
    draw.rounded_rectangle(
        [(padding, padding), (256 - padding, 256 - padding)],
        radius=48,
        fill="#2AABEE"
    )

    # White Paper Plane
    plane = [(60, 125), (195, 65), (135, 195), (115, 145)]
    draw.polygon(plane, fill="#FFFFFF")

    # Paper Plane fold
    draw.polygon([(115, 145), (145, 130), (135, 195)], fill="#D0EAF8")

    # Down arrow badge (download)
    arrow_circle = [(145, 145), (225, 225)]
    draw.ellipse(arrow_circle, fill="#FF0050", outline="#FFFFFF", width=3)
    
    # White Down Arrow
    draw.line([(185, 165), (185, 200)], fill="#FFFFFF", width=6)
    draw.polygon([(170, 190), (200, 190), (185, 210)], fill="#FFFFFF")

    icon_path = os.path.join(os.path.dirname(__file__), "bot_icon.ico")
    img.save(icon_path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print(f"Bot icon created: {icon_path}")

if __name__ == "__main__":
    create_bot_icon()
