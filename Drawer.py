from io import RawIOBase
import json
import pickle
import os
import pandas as pd
import numpy as np

import utilities as ut

class AwardStatus:
    def __init__(self, pool_id:str, award_name:str, award_num:str, pool_src:str, award_image:str) -> None:
        self.pool_id = pool_id
        self.award_name = award_name
        self.award_num = award_num
        self.pool_src = pool_src
        self.award_image = award_image
        pass

class Drawer:
    def __init__(self) -> None:
        self.UNDRAW_AWARD_NAME = "未抽中"
        
        self.DRAW_STATE_INIT = "Stage_Init"
        self.DRAW_STATE_BEFORE_DRAW = "Stage_BeforeDraw"
        self.DRAW_STATE_START_DRAW_AND_PLAY_ANIMATIOIN = "Stage_StartDrawAnimation"
        self.DRAW_STATE_END_DRAW_ANIMATION = "Stage_EndDrawAnimation"
        self.DRAW_STATE_LIST = [
            self.DRAW_STATE_INIT,
            self.DRAW_STATE_BEFORE_DRAW,
            self.DRAW_STATE_START_DRAW_AND_PLAY_ANIMATIOIN,
            self.DRAW_STATE_END_DRAW_ANIMATION
        ]
        
        self.draw_times = 0
        self.draw_info = {
            "award_status":pd.DataFrame(),
            "pool_status":{}
        }
        
        self.last_draw_info = {
            "draw_stage": self.DRAW_STATE_INIT,
            "last_draw_award_info": {
                "drawed_award_info":{},
                "drawed_player_info":{}
            }
        }
        pass

    def update_draw_info_data(self) -> None:
        award_df, _ = ut.read_award_info_from_file()
        if award_df.empty:
            raise FileNotFoundError("读取奖品文件失败")

        award_df["award_id"] = award_df["用户池"].map(str) + award_df["奖品名字"].map(str)
        award_df["max_award_num"] = award_df["奖品数目"].astype(int)
        
        if award_df['award_id'].duplicated().any():
            raise ut.AwardIDDuplicate()            
        award_df = award_df.set_index("award_id")   # set to ID after check duplicated

        cur_old_award_status = self.draw_info.get("award_status", pd.DataFrame())
        if cur_old_award_status.empty:
            award_df["award_num_left"] = award_df["max_award_num"].astype(int)
            self.draw_info['award_status'] = award_df
        else:
            # handle the old award which not in the new award_list
            # Just delete the award which never drawed
            never_draw_award_df = cur_old_award_status[cur_old_award_status["award_num_left"] - cur_old_award_status["max_award_num"] == 0 ]
            cur_old_award_status = cur_old_award_status.drop(never_draw_award_df.index)

            # add new award
            old_award_id_list = cur_old_award_status.index.to_list()
            tmp_award_id_list = award_df.index.to_list()
            new_award_id_list = [f for f in tmp_award_id_list if f not in old_award_id_list]            
            new_award_df = award_df.query("award_id in @new_award_id_list")
            if new_award_df.empty == False:
                new_award_df["award_num_left"] = new_award_df["max_award_num"]
                cur_old_award_status = cur_old_award_status.append(new_award_df)
            
            # update award info
            for tmp_id in old_award_id_list:                
                tmp_award_df = award_df.query("award_id == @tmp_id")
                tmp_award_num_left = cur_old_award_status.loc[tmp_award_df.index, "max_award_num"] - cur_old_award_status.loc[tmp_award_df.index, "award_num_left"]
                cur_old_award_status.loc[tmp_award_df.index, tmp_award_df.columns] = tmp_award_df
                cur_old_award_status.loc[tmp_award_df.index, "award_num_left"] = (tmp_award_df["max_award_num"] - tmp_award_num_left).apply(self.__check_num_format)
                
            self.draw_info['award_status'] = cur_old_award_status
        self.update_pool_status()

    def update_pool_status(self):
        is_other_error = False
        error_info = ""

        tmp_current_award_status = self.draw_info['award_status']
        for index, row in tmp_current_award_status.iterrows():
            pool_name_id = row["用户池"]
            pool_name_filename = row["用户池列表名字"]

            is_should_refresh_pool_info = False
            if (pool_name_id in self.draw_info["pool_status"]) == False:   #init pool_df
                is_should_refresh_pool_info = True
            else:
                # Let check the pool had been drawed, if havn't drawed, CAT update 
                old_pool_status_df = self.draw_info["pool_status"][pool_name_id]
                if old_pool_status_df['抽中奖品'].apply(lambda award: False if award==self.UNDRAW_AWARD_NAME else True).any() == False:     #check if any award has been drawed
                    is_should_refresh_pool_info = True
            if is_should_refresh_pool_info:                
                try:
                    init_player_status_df = self.__read_init_player_status_df_with_award(pool_name_filename)
                    self.draw_info["pool_status"][pool_name_id] = init_player_status_df
                except ut.PoolDataFileError as e:
                    is_other_error = True
                    error_info = "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!请检查参数;用户池文件不存在:【{}】!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!".format(e)
        return is_other_error, error_info
    

    def update_award_df(self, df_dict, filename) -> None:
        if self.last_draw_info["draw_stage"] not in (
            self.DRAW_STATE_INIT,
            self.DRAW_STATE_END_DRAW_ANIMATION
        ):
            raise ut.DrawStatgeError("当前阶段是播放动画或准备抽奖中,想进行修改奖品信息或用户列表信息,请先进行结束抽奖动画:/set_stop_animation")

        new_award_df = pd.DataFrame(df_dict)
        new_award_df = new_award_df.applymap(lambda cell: str(cell).strip(" ").strip("\t"))         # handle the space at the prefix or suffix
        new_award_df = new_award_df.replace("", np.nan).dropna(how="all")               # handle the giving empty row

        must_have_column_list = ["用户是否可抽中多奖品","用户池","用户池列表名字","奖品名字","奖品数目","奖品图片名字"]
        if any(True for cur_col in new_award_df.columns if cur_col not in must_have_column_list) == True:
            raise ut.AwardFormateError()
        
        # check if any cell is empty string, as it's already replace to nan
        if  new_award_df[must_have_column_list].isna().any().any()== True:  
            raise ut.AwardEmptyError()

        for index, row in new_award_df.iterrows():
            pool_name_filename = row["用户池列表名字"]            
            # check all pool file is exist by do nothing, If error will raise error
            self.__read_init_player_status_df_with_award(pool_name_filename)        # will raise error

            award_img_name = row["奖品图片名字"]
            if ut.check_award_img_file_exist(award_img_name) == False:
                raise ut.ImageNotExistError(award_img_name)

        
        new_award_df["award_id"] = new_award_df["用户池"].map(str) + new_award_df["奖品名字"].map(str)        
        if new_award_df['award_id'].duplicated().any():
            raise ut.AwardIDDuplicate()

        if new_award_df.groupby(by="用户池")["用户池列表名字"].nunique().ge(2).any().any():       # Check is there any poolId >= 2 files?
            raise ut.PoolIDMultiplyFile()             

        #handle the error formate
        new_award_df["奖品数目"] = new_award_df["奖品数目"].apply(self.__check_num_format)
        new_award_df["用户是否可抽中多奖品"] = new_award_df["用户是否可抽中多奖品"].apply(self.__check_can_draw_type_format)

        drop_column = ["award_id", "max_award_num", "award_num_left"]
        drop_column = new_award_df.filter(regex="|".join(drop_column)).columns
        new_award_df.drop(drop_column, axis=1, inplace=True)
        ut.save_info_to_file(new_award_df, filename=filename)

        # only update the info after we edit the award info updated
        self.update_draw_info_data()

    def __check_num_format(self, x):        
        try:
            x = int(x)
        except ValueError as e:
            x = 0
        return 0 if x <0 else x

    def __check_can_draw_type_format(self, x):        
        if x in (["是", "否"]):
            return x
        else:
            return "否"

    def __holding_award_filter(self, holding_award_list_str, award_name):
        is_holding_that_award = False
        holding_award_list = holding_award_list_str.split(',')
        for cur_hold_award in holding_award_list:
            if award_name.lower() == cur_hold_award.lower():
                is_holding_that_award = True
                break
        return is_holding_that_award

    def get_cur_award_df(self) -> pd.DataFrame:
        # self.update_draw_info_data()
        raw_df = self.draw_info["award_status"]

        # is_other_error, error_info = self.update_pool_status()
        is_other_error, error_info = False, ""

        return raw_df, raw_df.to_dict("records"), is_other_error, error_info

    def get_selected_award_player_info(self, pool_id, award_name):        
        cur_pool_info_df, _ = self.get_cur_pool_status_df(pool_id)

        if cur_pool_info_df.empty:
            raise ut.PoolDataFileError()

        tmp_is_hold_award_series = cur_pool_info_df["抽中奖品"].apply(lambda x: self.__holding_award_filter(x, award_name))
        had_that_award_df = cur_pool_info_df[tmp_is_hold_award_series]
        return had_that_award_df, had_that_award_df.to_dict("records") 

    def get_cur_pool_status_df(self, pool_id) -> pd.DataFrame:
        # self.update_draw_info_data()

        if pool_id not in self.draw_info["pool_status"]:
            return pd.DataFrame(), {}
        
        raw_df = self.draw_info["pool_status"][pool_id]
        return raw_df, raw_df.to_dict("records")

    def get_all_pool_status(self) ->pd.DataFrame:
        self.update_draw_info_data()

        tmp_df_list = []
        for key, val in self.draw_info["pool_status"].items():
            val["用户池"] = key
            tmp_df_list.append(val)
        result_df = pd.concat(tmp_df_list)

        # def __concat_awards(x):
        #     return pd.Series(dict(
        #         抽中奖品=  '|'.join(x["抽中奖品"]),
        #         所属用户池=  '|'.join(x["用户池"])
        #     ))
        # result_df = result_df.groupby(by=["player_name","player_no"]).apply(__concat_awards).reset_index()
        result_df =  result_df.rename(columns={
            "player_name": "姓名",
            "player_no": "工号",
        })
        
        return result_df


    def reset_last_draw_info(self, draw_stage):
        self.last_draw_info["draw_stage"] = draw_stage
        g_save_data()


    def __read_init_player_status_df_with_award(self, player_pool_file_name) -> pd.DataFrame:
        player_status_df, _ = ut.read_players_from_file(player_pool_file_name)
        player_status_df["抽中奖品"] = self.UNDRAW_AWARD_NAME
        if player_status_df.empty:
            raise ut.PoolDataFileError(player_pool_file_name)
        return player_status_df

    def __get_can_draw_player_df_from_player_status_df(self, pool_df) -> pd.DataFrame:
        return pool_df.query("抽中奖品 == '{}'".format(self.UNDRAW_AWARD_NAME))


    def __update_draw_info(self, draw_pool_id, cur_single_award_df, cur_player_status_df, draw_end_num) -> None:
        self.draw_info["pool_status"][draw_pool_id] = cur_player_status_df
        cur_single_award_df['award_num_left'] = draw_end_num
        self.draw_info["award_status"].loc[cur_single_award_df.index, :] = cur_single_award_df


    def start_draw(self, draw_pool_id:str, draw_award_name:str, draw_num:int, draw_stage) -> None:
        if draw_stage == self.DRAW_STATE_START_DRAW_AND_PLAY_ANIMATIOIN:
            if self.last_draw_info["draw_stage"] == self.DRAW_STATE_BEFORE_DRAW:     # override with the last draw stage info
                tmp_last_draw_info = self.last_draw_info['last_draw_award_info']['drawed_award_info']
                draw_pool_id = tmp_last_draw_info['draw_pool_id']
                draw_award_name = tmp_last_draw_info['draw_award_name']
                # draw_num = tmp_last_draw_info['draw_num']                         # the draw num can be chaged now
            elif self.last_draw_info["draw_stage"] == self.DRAW_STATE_START_DRAW_AND_PLAY_ANIMATIOIN:
                raise ut.DrawStatgeError("当前阶段是播放动画中,想进行下一次抽奖,请先进行结束抽奖动画:/set_stop_animation")

        draw_num = int(draw_num)

        self.update_draw_info_data()
        cur_single_award_df = self.draw_info["award_status"].query("用户池 == '{}' and 奖品名字 == '{}'".format(draw_pool_id, draw_award_name)).copy()
        if cur_single_award_df.empty:
            raise ut.AwardDataError()

        cur_pool_player_status_df = None
        cur_can_draw_num = 0
        
        cur_pool_player_status_df = self.draw_info["pool_status"][draw_pool_id]
        cur_can_draw_num = cur_single_award_df["award_num_left"].values[0]
        cur_draw_type = cur_single_award_df["用户是否可抽中多奖品"].values[0]

        opt_code = 1000
        opt_msg = ""
        payload_name = ""
        payload_value = ""

        if cur_draw_type == "是":
            tmp_is_hold_award_series = cur_pool_player_status_df["抽中奖品"].apply(lambda x: self.__holding_award_filter(x, draw_award_name))
            can_draw_player = cur_pool_player_status_df.loc[ ~tmp_is_hold_award_series]
        elif cur_draw_type == "否":
            can_draw_player = self.__get_can_draw_player_df_from_player_status_df(cur_pool_player_status_df)
        else:            
            raise ut.AwardDataError()

        all_player_len = len(cur_pool_player_status_df)
        can_draw_player_len = len(can_draw_player)
        if can_draw_player_len <= 0:   # all player has award        
            opt_code = 1001
            opt_msg = "当前用户池所有人均已有奖品"
            payload_name = "payload"
            payload_value = {
                "cur_pool_status": cur_pool_player_status_df.to_dict("records"),
                "cur_award_status": cur_single_award_df.to_dict("records")
            }
            return payload_name, payload_value, opt_code, opt_msg

        # get the this time draw num
        this_draw_num = min(can_draw_player_len, cur_can_draw_num, draw_num)
        if this_draw_num <= 0: #no award left         
            opt_code = 1002
            opt_msg = "所有奖品已经抽完"
            payload_name = "payload"
            payload_value = {
                "cur_pool_status": cur_pool_player_status_df.to_dict("records"),
                "cur_award_status": cur_single_award_df.to_dict("records")
            }
            return payload_name, payload_value, opt_code, opt_msg

        if draw_stage == self.DRAW_STATE_START_DRAW_AND_PLAY_ANIMATIOIN:
            #Drawing some player
            opt_code, opt_msg, payload_name, payload_value = self.__draw_players(draw_pool_id, draw_award_name, draw_num, cur_single_award_df, cur_pool_player_status_df, cur_can_draw_num, can_draw_player, all_player_len, can_draw_player_len, this_draw_num)
        elif draw_stage == self.DRAW_STATE_BEFORE_DRAW:
            opt_code = 2000
            opt_msg = "开始播放抽奖前动画"
            payload_name = None
            payload_value = None
        else:
            raise ut.DrawStatgeError("只可接受 Stage_BeforeDraw 与 Stage_StartDrawAnimation")

        # Setup the draw info
        self.last_draw_info = {
            "draw_stage": draw_stage,
            "last_draw_award_info": {
                "drawed_award_info":{
                    "draw_pool_id": draw_pool_id,
                    "draw_award_name": draw_award_name,
                    "draw_num": draw_num,
                },
                "drawed_player_info": payload_value
            }
        }
        # save the draw status
        g_save_data()

        return payload_name, payload_value, opt_code, opt_msg

    def __draw_players(self, draw_pool_id, draw_award_name, draw_num, cur_single_award_df, cur_pool_player_status_df, cur_can_draw_num, can_draw_player, all_player_len, can_draw_player_len, this_draw_num):
        get_players_df = can_draw_player.sample(this_draw_num).sort_index()     #Drawing some player

        def ___add_award_to_player(cur_hold_award, award_name):            
            result = cur_hold_award
            if cur_hold_award == self.UNDRAW_AWARD_NAME:
                result = award_name
            else:
                result = cur_hold_award + ",{}".format(award_name)
            return result
        get_players_df["抽中奖品"] = get_players_df["抽中奖品"].apply(___add_award_to_player, award_name=draw_award_name)

        # get_players_df["抽中奖品"] = draw_award_name
        cur_pool_player_status_df.loc[get_players_df.index, :] = get_players_df

        draw_end_num = cur_can_draw_num - this_draw_num
        self.__update_draw_info(draw_pool_id, cur_single_award_df, cur_pool_player_status_df, draw_end_num)
                
        opt_code = 1000
        opt_msg = "正常抽取; 奖品名字: {}; 抽前数目: {}, 操作抽取数目: {}, 实际抽取数目: {}, 抽后数目: {}; 当池总抽奖用户数: {}, 已抽过数目: {}, 剩余可抽用户数: {}, 抽后未抽用户数目: {}".format(
            draw_award_name, cur_can_draw_num, draw_num, this_draw_num, draw_end_num,
            all_player_len, all_player_len-can_draw_player_len, can_draw_player_len, can_draw_player_len-this_draw_num
            )
        payload_name = "payload"
        payload_value = get_players_df.to_dict("records")
        return opt_code,opt_msg,payload_name,payload_value
    

#######################
_old_file_floder = os.path.join(*[os.getcwd(), 'SaveData'])
_old_file_path = os.path.join(*[_old_file_floder,  'Drawer.sav'])

def g_load_from_saved_data():
    global g_drawer
    if os.path.exists(_old_file_path):
        with open(_old_file_path, 'rb') as f:
            g_drawer = pickle.load(f)

def g_save_data():
    global g_drawer    
    os.makedirs(_old_file_floder, exist_ok=True)
    with open(_old_file_path, 'wb+') as f:
        pickle.dump(g_drawer, f)

def g_remove_save_data():
    global g_drawer
    try:
        os.remove(_old_file_path)
    except OSError:
        pass    
    g_drawer = Drawer()
    g_drawer.update_draw_info_data()

#######################
g_drawer = Drawer()
g_load_from_saved_data()
g_drawer.update_draw_info_data()