#!/usr/bin/python
# coding=utf-8
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.exceptions import RequestException
from function import load_config
from json import loads
from re import findall
from tqdm import tqdm
from time import time
import requests
import logging

logging.basicConfig(level=logging.INFO)

def get_one_page(fund_code: str, pageSize: int, startDate: str, endDate: str, pageIndex: int) -> str:
    '''
    网络请求获取基金净值数据
    '''
    config = load_config()

    url = config['url_get']['nav_url']
    headers = {
        'Referer': 'http://fundf10.eastmoney.com/',
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
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.text
    except RequestException as e:
        logging.error(f"获取基金 {fund_code} 数据失败： {e}")
        return None  # 失败时返回 None，让调用方处理

def parse_one_page(html: str) -> str:
    '''
    解析网页内容
    '''
    try:
        content = findall(r'\((.*?)\)', html)
        if content:
            return content[0]
        else:
            logging.error("解析网页内容失败")
            return None
    except Exception as e:
        logging.error(f"解析网页内容失败： {e}")
        return None

def get_fund_info(fund_code: str, pageSize=1, startDate='', endDate='', pageIndex=1):
    '''
    组合需要的信息
    '''
    html = get_one_page(fund_code, pageSize, startDate, endDate, pageIndex)
    if html is not None:
        parsed_content = parse_one_page(html)
        if parsed_content is not None:
            try:
                lsjz_json = loads(parsed_content)
                return lsjz_json
            except ValueError as e:
                logging.error(f"JSON 解析失败： {e}")
                return None
        else:
            logging.error(f"解析失败，基金 {fund_code} 没有可用的内容")
    else:
        logging.error(f"基金 {fund_code} 网页内容为空")
        
    return None

def get_one_fund_nav(fund_code):
    '''
    获取单个基金的净值
    '''
    fund_info = get_fund_info(fund_code)
    if fund_info is not None:
        try:
            lsjz_json = fund_info['Data']['LSJZList'][0]  # 访问数据前先检查
            return {
                "FSRQ": lsjz_json['FSRQ'],  # 日期
                "DWJZ": lsjz_json['DWJZ'],  # 净值
            }
        except (KeyError, IndexError) as e:
            logging.error(f"处理基金 {fund_code} 时出错: {e}")
            return None
    else:
        logging.error(f"基金 {fund_code} 没有获取到有效的数据")
        return None

def get_nav(fund_list):
    '''
    获取基金列表的最新净值
    '''
    dwjz_dict = {}
    progress_bar = tqdm(total=len(fund_list), desc='更新净值')

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(get_one_fund_nav, fund_code): fund_code for fund_code in fund_list}
        
    for future in as_completed(futures):
        fund_code = futures[future]
        try:
            result = future.result()
            if result is not None:
                dwjz_dict[fund_code] = [result['FSRQ'], result['DWJZ']]
        except Exception as e:
            logging.error(f"处理基金 {fund_code} 时发生异常: {e}")
        
        progress_bar.update(1)

    progress_bar.close()
    return dwjz_dict

if __name__ == '__main__':
    fund_list = ['000001']
    
    dwjz_dict = get_nav(fund_list)
    print(dwjz_dict)
