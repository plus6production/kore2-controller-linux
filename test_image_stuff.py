from PIL import Image, ImageDraw, ImageFont


img = Image.new('1', (128, 64), 1)
draw = ImageDraw.Draw(img)

font = ImageFont.truetype("/usr/share/fonts/liberation/LiberationMono-Bold.ttf", size=20)
draw.text((0, 0), "Plus 6\nwuz\nhere!", 0, font=font, align="center")
img.save('test.png')

print(img)
#print(list(img_1b.tobytes()))