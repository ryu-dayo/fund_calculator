#!/usr/bin/python
# coding=utf-8
from function import file_path
import configparser
import pandas as pd
import requests
import json
import re

def get_name_page():
    '从网页获取数据'

    config = configparser.ConfigParser()
    config.read(file_path('config.ini'),encoding='UTF-8')
    
    url = config['url_get']['name_url']
    try:
        fund_content = requests.get(url).text
    except:
        print("网络无法连接，请检查配置或者网络")
        exit()
    return fund_content

def parse_name_page(html):
    '解析数据'
    name_str = re.findall('\[".*?"\]',html)
    name_dict = {}
    for item_str in name_str:
        item_info = json.loads(item_str)
        # print(item_info)
        name_dict[item_info[0]]=[item_info[2],item_info[3]]
    return name_dict

def get_name_info():
    html = get_name_page()
    name_dict = parse_name_page(html)
    name_df = pd.DataFrame.from_dict(name_dict,orient='index').reset_index()
    name_df.columns = ['fundcode','name','type']
    name_df.to_csv(
        file_path('fund_name.csv'),
        encoding='utf_8_sig',
        index=False,
    )
    return name_dict

if __name__=='__main__':
    get_name_info()
