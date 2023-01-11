#!/usr/bin/python
# coding=utf-8

from function import file_path
import pandas as pd
import numpy as np
import requests
import time
import json
import re

start = time.time()

# 从网页获取数据
url = 'http://fund.eastmoney.com/js/fundcode_search.js'
fund_content = requests.get(url).text
fund_str = re.findall('\[".*?"\]',fund_content)

# 解析数据
fund_list = []
for info_str in fund_str:
    info_data = json.loads(info_str)
    fund_list.append(info_data)
fund_data = pd.DataFrame(
    fund_list,
    columns=['fundcode','基金简拼','name','基金类型','基金全拼'],
)
fund_data.iloc[-1] = [np.nan,'','假数据','','']

# 保存数据
fund_data.to_csv(
    file_path('fund_name.csv'),
    encoding='utf_8_sig',
    index=False,
)

#   组装数据
my_fund = pd.read_csv(
    file_path('fund_data.csv'),
    dtype={'fundcode':str}
)
for repeat_columns in ["name"]:
    if repeat_columns in my_fund.columns:
        my_fund = my_fund.drop(repeat_columns,axis=1)
my_fund_data = pd.merge(
    fund_data[['fundcode','name']],
    my_fund,
    on=['fundcode'],
    how='right'
)

my_fund_data.to_csv(
    file_path('fund_data.csv'),
    index=False,
)

end = time.time()
print('获取基金名称，运行时长：',round(end-start,2),'s')