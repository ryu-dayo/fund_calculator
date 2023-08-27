#!/usr/bin/python
# coding=utf-8
from function import file_path
from json import loads
from re import findall
from tqdm import tqdm
from time import time
from sys import exit
import configparser
import requests

def get_one_page(fund_code,pageSize,startDate,endDate,pageIndex):
    '''
    网络请求
    '''
    config = configparser.ConfigParser()
    config.read(file_path('config.ini'),encoding='UTF-8')

    url = config['url_get']['nav_url']
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Referer': 'http://fundf10.eastmoney.com/',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) \
            AppleWebKit/537.36 (KHTML, like Gecko) \
                Chrome/89.0.4389.114 Safari/537.36',
    }
    params = {
        'callback': 'jQuery183023310064964236155_1618410538700',
        'fundCode': fund_code,
        'pageIndex': pageIndex,
        'pageSize': pageSize,
        'startDate': startDate,
        'endDate': endDate,
        '_=': str(int(time()))
    }
    try:
        r = requests.get(url=url,headers=headers,params=params)
    except:
        print("网络无法连接，请检查配置或者网络")
        exit()
    return r.text

def parse_one_page(html):
    '''
    解析网页内容
    '''
    content = findall('\((.*?)\)',html)[0]
    return content

def get_fund_info(fund_code,pageSize=1,startDate='',endDate='',pageIndex=1):
    '''
    组合需要的信息
    '''
    html = get_one_page(fund_code,pageSize,startDate,endDate,pageIndex)
    if html is not None:
        lsjz_json = loads(parse_one_page(html))
        return lsjz_json
    return None

def get_nav(fund_list):
    dwjz_dict = {}

    progress_bar = tqdm(total=len(fund_list),desc='更新净值')
    for fund_code in fund_list:
        lsjz_json = get_fund_info(fund_code)['Data']['LSJZList'][0]
        dwjz_dict[fund_code] = [
            lsjz_json['FSRQ'],
            lsjz_json['DWJZ'],
        ]
        progress_bar.update(1)
    return dwjz_dict
