import json
import random
import io
from PIL import Image, ImageDraw, ImageFont


PALLETE: dict = None
PALLETE_COUNT: int

with open("visual_density.json", "r") as f:
    PALLETE = json.load(f)
PALLETE_COUNT = len(PALLETE["visual_density"])


def reduce_size(image: Image, max_file_size=10 * 1024 * 1024):
    width, height = image.size

    while True:
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        size_in_bytes = buffer.tell()

        if size_in_bytes <= max_file_size:
            buffer.seek(0)
            return buffer, size_in_bytes

        width = int(width * 0.9)
        height = int(height * 0.9)
        image = image.resize((width, height), Image.Resampling.LANCZOS)

        if width < 100 or height < 100:
            break

    buffer.seek(0)
    return buffer, size_in_bytes


def text(text: str, size: int, bg: str, fg: str, bold: bool):
    font = None
    if not bold:
        font = ImageFont.truetype("ubuntu-font-family/UbuntuMono-R.ttf", size=size)
    else:
        font = ImageFont.truetype("ubuntu-font-family/UbuntuMono-B.ttf", size=size)

    width, height = int(font.getlength(text)), size
    image = Image.new('RGBA', (width, height), color=bg)
    draw = ImageDraw.Draw(image)
    draw.text((0, 0), text, fill=fg, font=font)

    return image


def asciify(src_image: Image, character_size: int, bg_influence: float, no_color: bool, chars_only: bool):
    pixels = src_image.load()

    font_map = {
        "r": ImageFont.truetype("ubuntu-font-family/UbuntuMono-R.ttf", size=character_size),
        "ri": ImageFont.truetype("ubuntu-font-family/UbuntuMono-RI.ttf", size=character_size),
        "b": ImageFont.truetype("ubuntu-font-family/UbuntuMono-B.ttf", size=character_size),
        "bi": ImageFont.truetype("ubuntu-font-family/UbuntuMono-BI.ttf", size=character_size),
    }

    cwidth, cheight = int(font_map["bi"].getlength("w")), character_size

    dst_width, dst_height = src_image.size
    dst_width = int(dst_width / cwidth)
    dst_height = int(dst_height / cheight)

    dst_image: Image = None
    if not chars_only:
        dst_image = Image.new('RGB', (dst_width * cwidth, dst_height * cheight), color='black')
    else:
        dst_image = Image.new('RGBA', (dst_width * cwidth, dst_height * cheight), color='#00000000')

    draw = ImageDraw.Draw(dst_image)

    for cx in range(0, dst_width):
        for cy in range(0, dst_height):
            x = cx * cwidth
            y = cy * cheight

            avg_color = [0, 0, 0]
            for i in range(x, x + cwidth):
                for j in range(y, y + cheight):
                    if i < src_image.size[0] and j < src_image.size[1]:
                        color = pixels[i, j]
                        for n in range(0, 3):
                            avg_color[n] += color[n]

            for n in range(0, 3):
                avg_color[n] /= cwidth * cheight
            rate = (avg_color[0] + avg_color[1] + avg_color[2]) / 3 / 255 * PALLETE_COUNT

            visual_density = min(int(rate + 0.5), PALLETE_COUNT-1)

            pallete = PALLETE["visual_density"][visual_density]
            draw_set = random.choice(pallete)

            if no_color:
                avg_color = [255, 255, 255]

            if not chars_only:
                # bg
                draw.rectangle(
                    [(x, y), (x + cwidth, y + cheight)],
                    fill=tuple(int(x * bg_influence) for x in avg_color),
                )

            # fg
            draw.text(
                (x, y),
                draw_set[0],
                fill=tuple(int(x) for x in avg_color),
                font=font_map[draw_set[1]]
            )

    return dst_image
