#!/usr/bin/python
# coding=utf-8
from function import file_path
import pandas as pd
import requests
import json
import re

def get_name_page():
    '从网页获取数据'
    url = 'http://fund.eastmoney.com/js/fundcode_search.js'
    fund_content = requests.get(url).text
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
