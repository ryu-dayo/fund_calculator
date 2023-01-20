import configparser
import pandas as pd
import requests
import time
import json
import sys
import re
import os

def file_path(file_name):
    file_path = os.path.join(
        os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            ),
            'data'
        ),
        file_name
    )
    return file_path

def get_one_page(fund_code,pageSize,startDate,endDate,pageIndex):
    '''
    网络请求
    '''
    url = 'http://api.fund.eastmoney.com/f10/lsjz'
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
        '_=': str(int(time.time()))
    }
    try:
        r = requests.get(url=url,headers=headers,params=params)
        return r.text
    except requests.exceptions.ConnectionError:
        print("网络无法连接")
        sys.exit()

def parse_one_page(html):
    '''
    解析网页内容
    '''
    content = re.findall('\((.*?)\)',html)[0]
    return content

def get_fund_info(fund_code,pageSize=1,startDate='',endDate='',pageIndex=1):
    '''
    组合需要的信息
    '''
    html = get_one_page(fund_code,pageSize,startDate,endDate,pageIndex)
    if html is not None:
        lsjz_json = json.loads(parse_one_page(html))
        return lsjz_json
    return None

def notion_create_page(json_content):

    config = configparser.ConfigParser()
    config.read(file_path('config.ini'),encoding='UTF-8')

    url = "https://api.notion.com/v1/pages"
    token = config['notion']['token']
    
    payload = {
        "parent":{
            "type":"database_id",
            "database_id":config['notion']['database_id'],
        },
        "properties":json_content
    }
    headers = {
        "Authorization":"Bearer "+token,
        "Notion-Version": "2022-06-28"
    }

    response = requests.post(url, json=payload, headers=headers)
    
    time.sleep(0.5)
    return(response.text)

def notion_update_page(row,json_content):

    config = configparser.ConfigParser()
    config.read(file_path('config.ini'),encoding='UTF-8')

    url = "https://api.notion.com/v1/pages/" + getattr(row,"page_id")
    token = config['notion']['token']

    payload = json_content
    headers = {
        "accept":"application/json",
        "Authorization": "Bearer "+ token,
        "Notion-Version": "2022-06-28",
        "content-type":"application/json"
    }

    s = requests.session()
    s.keep_alive = False
    response = requests.patch(url, json=payload,headers=headers)

    time.sleep(0.5)
    # print(response.text)
    return(response.text)