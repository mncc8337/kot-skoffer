from PIL import Image, ImageDraw, ImageFont
import json

fonts = [
    (ImageFont.truetype("ubuntu-font-family/UbuntuMono-R.ttf", 16), "r"),
    (ImageFont.truetype("ubuntu-font-family/UbuntuMono-RI.ttf", 16), "ri"),
    (ImageFont.truetype("ubuntu-font-family/UbuntuMono-B.ttf", 16), "b"),
    (ImageFont.truetype("ubuntu-font-family/UbuntuMono-BI.ttf", 16), "bi"),
]

printable_chars = [chr(i) for i in range(32, 127)]

char_fill_levels = []

for font, style in fonts:
    for char in printable_chars:
        width, height = font.getbbox(char)[2:]
        image = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(image)
        draw.text((0, 0), char, font=font, fill=255)

        pixel_data = image.getdata()
        fill_count = sum(1 for pixel in pixel_data if pixel > 0)

        char_fill_levels.append((char, fill_count, style))

char_fill_levels.sort(key=lambda x: x[1])
max_fill_level = max(char_fill_levels, key=lambda x: x[1])[1]
count_list = [[] for i in range(0, max_fill_level + 1)]

for char, fill, style in char_fill_levels:
    count_list[fill].append((char, style))

final_list = [item for item in count_list if item]

with open("visual_density.json", "w") as f:
    json.dump({"visual_density": final_list, "max_level": max_fill_level}, f)
