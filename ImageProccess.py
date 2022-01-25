import os
from PIL import Image

g_chara_path = "CharaImages"
g_award_path = "AwardImages"
g_result_chara_path = os.path.join('MainData', g_chara_path)
g_result_award_path = os.path.join('MainData', g_award_path)

g_belong_replace = {
    "财务部": "财务",
    "港台运营中心": "港台",
    "韩国运营中心": "韩国",
    "韩国办公室": "韩国",
    "日本运营中心": "日本",
    "亚欧运营中心": "亚欧",
    "中国运营中心": "中国",
    "人事行政中心": "人事行政",
    "商务发展中心": "商发",
    "技术中心": "技术",
    "市场中心": "市场",
    "运维部": "运维",
    "总经办": "总经办",
}

def __compress_image(is_chara_path, is_to_jpg, result_path, filename, file_path):
    img = Image.open(file_path)
    org_w, org_h = img.size
    org_astio = org_w/org_h

    tmp_result_width = 256
    
    if is_to_jpg:
        img = img.convert("RGB")
    else:
        img = img.convert("RGBA")
    img = img.resize((tmp_result_width, int(tmp_result_width/org_astio)), Image.ANTIALIAS)

    save_file_name = filename.split('.')[0]
    if is_chara_path:
        tmp_belong = save_file_name.split("-")[0]
        try:
            tmp_belong = g_belong_replace[tmp_belong]
            tmp_real_name = save_file_name.split("-")[-1]
            save_file_name = "{}-{}".format(tmp_belong, tmp_real_name)
        except KeyError:
            pass

    if is_to_jpg:
        img.save(os.path.join(result_path, "{}.jpg".format(save_file_name)), format="JPEG", quality=60, optimize=True)
    else:        
        img.save(os.path.join(result_path, "{}.png".format(save_file_name)), format="PNG", compress_level=5, optimize=True)


def __compress_all_imgs(chara_path, award_path, result_chara_path, result_award_path, compress_image):
    for root, dirs, files in os.walk(os.path.join("RawImgs", chara_path), topdown=True):
        for file in files:
            tmp_file_path = os.path.join(root, file)        
            __compress_image(True, True, result_chara_path, file, tmp_file_path)
        
    for root, dirs, files in os.walk(os.path.join("RawImgs", award_path), topdown=True):
        for file in files:
            tmp_file_path = os.path.join(root, file)        
            __compress_image(False, False, result_award_path, file, tmp_file_path)

def compress_all_imgs():
    __compress_all_imgs(g_chara_path, g_award_path, g_result_chara_path, g_result_award_path, __compress_image)

# def __change_img_alpha():
#     from PIL import Image 

#     img = Image.open('org_bg.png')
#     img = img.convert("RGBA")
#     datas = img.getdata()

#     newData = []
#     for item in datas:
#         if item[3] < 250:      # is alpha
#             newData.append((item[0], item[1], item[2], int(item[3]*0.4)))
#         else:
#             newData.append(item)

#     img.putdata(newData)
#     img.save("BG_draw_end.png", format="PNG", compress_level=5, optimize=True)
# __change_img_alpha()