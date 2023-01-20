#!/usr/bin/python
# coding=utf-8
from function import get_fund_info
from tqdm import tqdm

def get_nav(fund_list):
    dwjz_dict = {}

    progress_bar = tqdm(total=len(fund_list),desc='更新净值')
    for fund_code in fund_list:
        lsjz_json = get_fund_info(fund_code)
        dwjz_dict[fund_code] = [
            lsjz_json['Data']['LSJZList'][0]['FSRQ'],
            lsjz_json['Data']['LSJZList'][0]['DWJZ'],
        ]
        progress_bar.update(1)
    return dwjz_dict
