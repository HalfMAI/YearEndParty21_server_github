#!/usr/bin/env python  
# encoding: utf-8  
import json
import os
import sys
import web
import urllib
from exceptions import PoolDataFileError

import utilities as ut
from ImageProccess import compress_all_imgs
from Drawer import g_save_data, g_load_from_saved_data, g_remove_save_data
import Drawer


render = web.template.render('templates/')

urls = (
    "/cancle_draw_to_init_stage", "CancleDrawStage",
    "/set_stop_animation", "SetStopAnimation",
    "/check_draw_stage", "CheckDrawStage",
    "/selected_award_player_info", "SelectedAwardPlayerInfo",
    "/export_all_award_info", "ExportAllAwardInfo",
    "/init_all_status", "InitAllStatus",
    "/reproccess_all_images_format", "ProccessImagesFormat",
    "/update_award_info", "UpdateAwardInfo",
    "/cur_award_info", "AwardInfo",
    "/beforedrawing", "BeforeDrawing",
    "/startdrawing", "StartDrawing",
    "/pool_info", "PoolInfo",
    "/check_can_do", "CheckCanDo",
    "/(AwardImages|CharaImages)/(.*)", "ReadFile",
    "/(.*)\.html", "Page",
)
g_memory_file_dict = {}


class CancleDrawStage:
    def GET(self):
        web.header('Content-Type', 'application/json;charset=UTF-8')
        ut.log_info("CancleDrawStage called;")
        Drawer.g_drawer.reset_last_draw_info(Drawer.g_drawer.DRAW_STATE_INIT)
        return ut.create_payload(None, None, code_str="1000", msg_str="OK")
class SetStopAnimation:
    def GET(self):
        web.header('Content-Type', 'application/json;charset=UTF-8')
        ut.log_info("SetStopAnimation called;")
        Drawer.g_drawer.reset_last_draw_info(Drawer.g_drawer.DRAW_STATE_END_DRAW_ANIMATION)
        return ut.create_payload(None, None, code_str="1000", msg_str="OK")

class CheckDrawStage:
    def GET(self):
        web.header('Content-Type', 'application/json;charset=UTF-8')
        ut.log_info("CheckDrawStage called;")
        last_draw_info = Drawer.g_drawer.last_draw_info
        return ut.create_payload("payload", last_draw_info, code_str="1000", msg_str="OK")

class ExportAllAwardInfo:
    def GET(self):
        web.header('Content-Type', 'application/json;charset=UTF-8')
        ut.log_info("ExportAllAwardInfo called;")
        
        try:
            result_df = Drawer.g_drawer.get_all_pool_status()    
            
            result_byte = bytes(result_df.to_csv(line_terminator='\r\n', index=False, encoding='utf-8-sig'), encoding='utf-8-sig')
            web.header('Content-Type','text/csv')
            web.header('Content-Disposition', 'attachment;filename="pool_result.csv"')
            return result_byte
        except Exception as e:
            return ut.create_payload(None, None, code_str="9999", msg_str="未知错误,FOR DEBUG:{}".format(str(e)))

class SelectedAwardPlayerInfo:
    def GET(self):
        web.header('Content-Type', 'application/json;charset=UTF-8')
        ut.log_info("SelectedAwardPlayerInfo called")
        data = web.input()
        pool_id = data.get("pool_id", "").strip(" ")
        award_name = data.get("award_name", "").strip(" ")

        try:
            result_df, result_dict = Drawer.g_drawer.get_selected_award_player_info(pool_id, award_name)
            if result_df.empty:
                return ut.create_payload(None, None, code_str="1001", msg_str="当前奖品没有人抽中到")
            else:
                return ut.create_payload("payload", result_dict, code_str="1000", msg_str="OK")                
        except PoolDataFileError as e:
            return ut.create_payload(None, None, code_str="9001", msg_str="用户池:【{}】 或文件: 【{}】不存在!!!".format(pool_id, award_name))
        except Exception as e:
            return ut.create_payload(None, None, code_str="9999", msg_str="未知错误,FOR DEBUG:{}".format(str(e)))

class InitAllStatus:
    def GET(self):
        global g_memory_file_dict
        web.header('Content-Type', 'application/json;charset=UTF-8')
        ut.log_info("InitAllStatus called;")
        g_memory_file_dict = {}
        g_remove_save_data()
        return ut.create_payload(None, None, code_str="1000", msg_str="OK")
        
class ProccessImagesFormat:
    def GET(self):
        global g_memory_file_dict
        web.header('Content-Type', 'application/json;charset=UTF-8')
        ut.log_info("ProccessImagesFormat called;")        
        compress_all_imgs()
        return ut.create_payload(None, None, code_str="1000", msg_str="OK")

class UpdateAwardInfo:
    def POST(self):
        web.header('Content-Type', 'application/json;charset=UTF-8')
        json_str = web.data()
        json_str = urllib.parse.unquote(json_str.decode('utf-8'))
        ut.log_info("UpdateAwardInfo called; data:{}".format(json_str))
        raw_dict = json.loads(json_str)
        df_dict = raw_dict["award_dict"]
        save_filename = raw_dict["save_filename"]

        # fix the save file name
        save_filename = 'awards.csv'
        try:
            Drawer.g_drawer.update_award_df(df_dict, save_filename)
            return ut.create_payload(None, None, code_str="1000", msg_str="OK")
        except ut.AwardIDDuplicate as e:            
            return ut.create_payload(None, None, code_str="9001", msg_str="用户池+奖品名字 有重复，请检查对应修改项目。")
        except ut.PoolIDMultiplyFile as e:
            return ut.create_payload(None, None, code_str="9002", msg_str="用户池+用户池文件列表 有重复，请检查对应修改项目。 同一用户池只能匹配同一个用户池文件列表")
        except ut.AwardFormateError as e:            
            return ut.create_payload(None, None, code_str="9003", msg_str="请求内容格式有问题，只能是以下列:{}".format(e))            
        except ut.AwardEmptyError as e:            
            return ut.create_payload(None, None, code_str="9003", msg_str="请求内容格式有问题:{}".format(e))   
        except ut.PoolDataFileError as e:
                return ut.create_payload(None, None, code_str="9004", msg_str="请检查参数;用户池文件不存在:{}".format(e)) 
        except ut.ImageNotExistError as e:
                return ut.create_payload(None, None, code_str="9005", msg_str="请检查参数;图片文件不存在:{}".format(e)) 
        except Exception as e:
            return ut.create_payload(None, None, code_str="9999", msg_str="未知错误,FOR DEBUG:{}".format(str(e)))


class AwardInfo:
    def GET(self):        
        web.header('Content-Type', 'application/json;charset=UTF-8')
        ut.log_info("AwardInfo called")
        
        code_str="1000"
        msg_str = "OK"
        try:
            raw_df, result_dict, is_other_error, error_info = Drawer.g_drawer.get_cur_award_df()
        except FileNotFoundError as e:
            return ut.create_payload(None, None, code_str="9004", msg_str="请检查配置;配置文件不存在")
        
        if is_other_error:
            code_str = "1001"
            msg_str = error_info
        return ut.create_payload(payload_name="payload", payload_value=result_dict, code_str=code_str, msg_str=msg_str)

class StartDrawing:
    def POST(self):
        web.header('Content-Type', 'application/json;charset=UTF-8')
        json_str = web.data()
        json_str = urllib.parse.unquote(json_str.decode('utf-8'))
        ut.log_info("StartDrawing called; data:{}".format(json_str))
        raw_dict = json.loads(json_str)

        draw_pool_id = raw_dict.get("draw_pool_id", None)
        draw_award_name = raw_dict.get("draw_award_name", None)
        draw_num = raw_dict.get("draw_num", None)

        draw_stage = raw_dict.get("draw_stage", None)

        if draw_pool_id == None or draw_award_name == None or draw_num == None:
            return ut.create_payload(None, None, code_str="9001", msg_str="参数异常")
        
        # handle space
        draw_pool_id = str(draw_pool_id).strip(" ")
        draw_award_name = str(draw_award_name).strip(" ")
        draw_num = str(draw_num).strip(" ")
        draw_stage = str(draw_stage).strip(" ")
        
        try:
            draw_num = int(draw_num)
        except ValueError as e:
            return ut.create_payload(None, None, code_str="9006", msg_str="请检查参数;抽奖数目不能转换为数字")

        if draw_num <= 0:
            return ut.create_payload(None, None, code_str="9005", msg_str="请检查参数;抽奖数目不能为负数或0")

        try:
            payload_name, payload_value, opt_code, opt_msg = Drawer.g_drawer.start_draw(draw_pool_id, draw_award_name, draw_num, draw_stage)
        except ut.PoolDataFileError as e:
                return ut.create_payload(None, None, code_str="9001", msg_str="请检查参数;用户池文件不存在:{}".format(e))
        except ut.AwardDataError as e:
            return ut.create_payload(None, None, code_str="9002", msg_str="请检查参数;奖品 或 用户池不存在")
        except ut.AwardMultiplyRow as e:            
            return ut.create_payload(None, None, code_str="9003", msg_str="请检查配置;奖品名字+用户池重复.此值需要唯一")
        except FileNotFoundError as e:
            return ut.create_payload(None, None, code_str="9004", msg_str="请检查配置;配置文件不存在")
        except ut.DrawStatgeError as e:
            return ut.create_payload(None, None, code_str="9005", msg_str="抽奖阶段错误,当前阶段:[{}]. {}".format(draw_stage, e))
        except Exception as e:
            return ut.create_payload(None, None, code_str="9999", msg_str="未知错误,FOR DEBUG:{}".format(str(e)))
                
        return ut.create_payload(payload_name="payload", payload_value=payload_value, code_str=opt_code, msg_str=opt_msg)

class PoolInfo:
    def GET(self):
        web.header('Content-Type', 'application/json;charset=UTF-8')
        ut.log_info("PoolInfo called")
        data = web.input()
        pool_id = data.get("pool_id", "").lower()
        raw_df, result_dict = Drawer.g_drawer.get_cur_pool_status_df(pool_id=pool_id)
        if raw_df.empty:
            return ut.create_payload(None, None, code_str="9001", msg_str="用户池不存在")
        else:
            return ut.create_payload(payload_name="payload", payload_value=result_dict)

class CheckCanDo:
    def GET(self):
        web.header('Content-Type', 'application/json;charset=UTF-8')
        data = web.input()
        password = data.get("validationPassword", "").lower()
        if password != "efun666":
            return ut.create_payload(None, None, code_str="1000", msg_str="OK")        
        return ut.create_payload(None, None, code_str="9000", msg_str="NOT OK")

class ReadFile:
    def GET(self, media, file):
        global g_memory_file_dict
        try:            
            file_path = os.path.join("MainData", media, file)
            result_file = g_memory_file_dict.get(file_path, None)
            if result_file == None:
                f = open(file_path, 'rb')
                result_file = f.read()
                g_memory_file_dict[file_path] = result_file
            return result_file
        except:
            return web.notfound("File Not found")

class Page:
    def GET(self, page):
        # for static page
        try:
            return render._template(page)()
        except Exception:
            return ""


if __name__ == "__main__":    
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 10801
    app = web.application(urls, globals())
    app.internalerror = web.debugerror
    # app.run()
    web.httpserver.runsimple(app.wsgifunc(), ("0.0.0.0", port))
