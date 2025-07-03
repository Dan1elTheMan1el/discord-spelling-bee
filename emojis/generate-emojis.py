from PIL import Image, ImageDraw, ImageFont

letters = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]

for letter in letters:
    # Create mid and out images
    mid = Image.open("resources/hexmid.png")
    draw = ImageDraw.Draw(mid)
    font = ImageFont.truetype("resources/helvmn.ttf", 120)
    draw.text((101, 110), letter, font=font, fill=(0, 0, 0), anchor="mm", stroke_width=2)
    mid.save(f"emojis/mid_{letter.lower()}.png")

    out = Image.open("resources/hexout.png")
    draw = ImageDraw.Draw(out)
    draw.text((101, 110), letter, font=font, fill=(0, 0, 0), anchor="mm", stroke_width=2)
    out.save(f"emojis/out_{letter.lower()}.png")