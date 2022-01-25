
import datetime
import json
import random

import os
import pandas as pd

from exceptions import *

from ut_Loging import log_err, log_info, log_warnning

def read_data_from_file(file_path_list):
    last_component = file_path_list[-1].split('.')[-1]
    if last_component == "csv":
        try:
            raw_df = pd.read_csv(os.path.join(*file_path_list), encoding='utf-8', dtype=str, na_filter=False)
            raw_df = raw_df.applymap(lambda cell: str(cell).strip(" ").strip("\t"))         # handle the space at the prefix or suffix
            return raw_df
        except FileNotFoundError as e:
            return pd.DataFrame()    
    else:
        try:
            raw_df = pd.read_excel(os.path.join(*file_path_list), dtype=str, na_filter=False)
            raw_df = raw_df.applymap(lambda cell: str(cell).strip(" ").strip("\t"))         # handle the space at the prefix or suffix
            return raw_df
        except FileNotFoundError as e:
            return pd.DataFrame()


def read_players_from_file(player_pool_file_name):
    raw_df = read_data_from_file(["MainData", player_pool_file_name])
    raw_df =  raw_df.rename(columns={
        "姓名": "player_name",
        "工号": "player_no",
        "照片名称": "image_url",
    })
    if raw_df.empty:
        raise PoolDataFileError(player_pool_file_name)
    # handle the no prefix name. Default using the *.jpg
    raw_df["image_url"] = raw_df["image_url"].apply(lambda x: x if len(x.split('.')) > 1 else "{}.jpg".format(x))
    raw_dict = raw_df.to_dict("records")
    return raw_df, raw_dict

def read_award_info_from_file():
    raw_df = read_data_from_file(["MainData", 'awards.csv'])
    raw_df["奖品数目"] = raw_df["奖品数目"].astype(int)
    raw_dict = raw_df.to_dict()
    return raw_df, raw_dict

def save_info_to_file(df:pd.DataFrame, filename:str="awards.csv"):
    df.to_csv(os.path.join(*["MainData", filename]), index=False, encoding='utf-8-sig')


def create_payload(payload_name, payload_value, code_str="1000", msg_str="success"):
    result_dict = {
        "code": str(code_str), 
        "msg": str(msg_str)
        }
    if payload_name != None or payload_value != None:
        result_dict[payload_name] = payload_value
    payload = json.dumps(result_dict, ensure_ascii=False)
    log_info("create_payload: {}".format(payload))
    return payload

def check_file_exist(filepath, filename):
    fp = os.path.join(*[filepath, filename])
    return os.path.exists(fp)

def check_award_img_file_exist(filename):
    return check_file_exist(os.path.join(*["MainData", "AwardImages"]), filename)