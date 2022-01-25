from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 
img = Image.open("./NumberImgGrenerator/RawNumberBG.jpg")
font = ImageFont.truetype(r'./NumberImgGrenerator/FZZJ-LongYTJW.TTF', 200)
# font = ImageFont.truetype(r'Osake.ttf', 330)

for i in range(1, 300+1):
    tmpImg = img.copy()
    draw = ImageDraw.Draw(tmpImg)
    draw_str = '{0:03}'.format(i)

    px = 180
    py = 320

    draw.text((px, py), draw_str, (0,0,0), font=font)
    tmpImg.save('./RawImgs/CharaImages/NumberImgs/Number_{}.jpg'.format(draw_str))