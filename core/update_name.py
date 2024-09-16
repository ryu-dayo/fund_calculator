#!/usr/bin/python
# coding=utf-8
from requests.exceptions import RequestException
from function import file_path, load_config
import pandas as pd
import requests
import logging
import json
import re

logging.basicConfig(level=logging.INFO)

def get_name_page() -> str:
    """
    从网页获取数据
    """
    try:
        config = load_config()
        url = config['url_get']['name_url']
    except KeyError as e:
        logging.error("配置文件中缺少必要的键： %s", e)
        return None
    except Exception as e:
        logging.error("加载配置文件时发生错误： %s", e)
        return None
        
    try:
        fund_content = requests.get(url, timeout=10).text
    except RequestException as e:
        logging.error("网络无法连接，请检查配置或者网络: %s", e)
        return None
    return fund_content

def parse_name_page(html: str) -> dict:
    """
    解析数据
    """
    if not html:
        logging.error("传入的 HTML 数据为空")
        return {}
    
    try:
        name_str = re.findall(r'\[".*?"\]',html)
        name_dict = {}
        for item in name_str:
            item_info = json.loads(item)
            # print(item_info)
            name_dict[item_info[0]] = [item_info[2], item_info[3]]
    except (json.JSONDecodeError, IndexError) as e:
        logging.error("数据解析错误: %s", e)
        return {}
    
    return name_dict

def get_name_info():
    html = get_name_page()
    if not html:
        logging.error("未能获取网页数据")
        return
    
    name_dict = parse_name_page(html)
    if not name_dict:
        logging.error("未获取到有效的基金名称信息")
        return
    
    name_df = pd.DataFrame.from_dict(name_dict, orient='index').reset_index()
    name_df.columns = ['fundcode', 'name', 'type']
    
    try:
        name_df.to_csv(file_path('fund_name.csv'), encoding='utf_8_sig', index=False)
        logging.info("基金名称信息已保存成功")
    except Exception as e:
        logging.error("文件保存失败： %s", e)
        
    return name_dict

if __name__ == '__main__':
    get_name_info()
