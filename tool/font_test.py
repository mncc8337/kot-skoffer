from PIL import Image, ImageDraw, ImageFont

width, height = 50, 50
image = Image.new('RGB', (width, height), color='white')

draw = ImageDraw.Draw(image)

font = ImageFont.truetype("ubuntu-font-family/UbuntuMono-R.ttf", size=50)

text = "Hello, Pillow!"
position = (0, 0)

draw.text(position, text, fill='black', font=font)

image.show()
