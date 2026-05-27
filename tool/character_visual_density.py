import lib.font
from PIL import Image, ImageDraw, ImageFont
import json

sample_font = lib.font.UBUNTU_MONO

fonts = [
    (ImageFont.truetype(sample_font.r, 16), "r"),
    (ImageFont.truetype(sample_font.ri, 16), "ri"),
    (ImageFont.truetype(sample_font.b, 16), "b"),
    (ImageFont.truetype(sample_font.bi, 16), "bi"),
]

printable_chars = [chr(i) for i in range(32, 127)]

char_fill_levels = []

for font, style in fonts:
    for char in printable_chars:
        bbox = font.getbbox(char)
        left, top, right, bottom = bbox

        width = right - left
        height = bottom - top

        image = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(image)
        draw.text((-left, -top), char, font=font, fill=255)

        fill_count = sum(image.getdata()) // 255

        char_fill_levels.append((char, fill_count, style))

max_fill_level = max(char_fill_levels, key=lambda x: x[1])[1]
count_list = [[] for i in range(0, max_fill_level + 1)]

for char, fill, style in char_fill_levels:
    count_list[fill].append((char, style))

final_list = [item for item in count_list if item]

with open("visual_density.json", "w") as f:
    json.dump({"visual_density": final_list, "max_level": max_fill_level}, f)
