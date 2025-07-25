#!/usr/bin/python
# coding=utf-8
from concurrent.futures import ThreadPoolExecutor, as_completed
from function import file_path, load_config
from time import sleep
from tqdm import tqdm
import pandas as pd
import requests
import logging
import json

logging.basicConfig(level=logging.INFO)

def notion_create_page(json_content,config):
    """
    创建 Notion 页面
    """
    url = "https://api.notion.com/v1/pages"
    token = config['notion']['token']
    
    payload = {
        "parent":{
            "type": "database_id",
            "database_id": config['notion']['database_id'],
        },
        "properties":json_content
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"创建 Notion 页面时出错：{e}")
        return None

def notion_update_page(item, json_content, config):
    """
    更新 Notion 页面
    """
    url = f"https://api.notion.com/v1/pages/{item.get('page_id')}"
    token = config['notion']['token']

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "content-type":"application/json"
    }
    
    try:
        response = requests.patch(url, json=json_content, headers=headers)
        response.raise_for_status()
        sleep(0.5)
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"更新 Notion 页面时出错：{e}")
        return None

def if_page_nan(config, my_fund):
    """
    检查 page_id 是否为空，为空则新建页面并返回 ID
    """
    nan_list = my_fund[my_fund['page_id'].isnull()].index.tolist()
    if nan_list:
        for nan_index in nan_list:
            json_content = {
                'Name': {'title': [{'text': {'content': my_fund.loc[nan_index, 'fundcode']}}]},
                '投资体系': {'relation': [{'id': config['notion']['notion_page_id'][my_fund.loc[nan_index, 'parent']]}]},
                '基金名称': {'rich_text': [{'text': {'content': my_fund.loc[nan_index, 'name']}}]}
            }
            if pd.notna(my_fund.loc[nan_index, 'child']):
                json_content['永久组合'] = {'relation': [{config['notion']['notion_page_id'][my_fund.loc[nan_index, 'child']]}]}

            response_text = notion_create_page(json_content, config)
            if response_text:
                my_fund.loc[nan_index, 'page_id'] = json.loads(response_text).get('id')
            
        my_fund.to_csv(file_path("fund_data.csv"), index=False)
        
    return my_fund

def different_data(column_list, my_fund):
    """
    补齐并对比数据，返回有差异的索引列表
    """
    try:
        notion_data = pd.read_csv(file_path("fund_data_backup.csv"), dtype={"fundcode": str})
    except FileNotFoundError:
        logging.warning("备份文件不存在，创建新文件")
        notion_data = pd.DataFrame(columns=column_list)
        
    my_fund, notion_data = my_fund.align(notion_data, join="outer", axis=None)
    diff_index_list = my_fund.compare(notion_data).index.tolist()
    return diff_index_list

def update_data(diff_index_list, my_fund, config):
    """
    上传差异数据到 Notion
    """
    if diff_index_list:
        progress_bar = tqdm(total=len(diff_index_list), desc='上传 Notion')
        update_dict = my_fund.loc[diff_index_list, :].to_dict('records')
        
        # 使用线程池加速网络请求
        with ThreadPoolExecutor(max_workers=5) as executor: # 可调节线程数
            futures = []
            for item in update_dict:
                json_content = {
                    'properties':{
                        '持有市值': {'number': item.get('amount')},
                        '持有收益': {'number': item.get('cysy')},
                        '持有收益率': {'number': item.get('cysyl')},
                        '累计收益': {'number': item.get('ljsy')},
                        # '更新时间': {'date': {'start': item.get('FSRQ')}},
                        # '基金名称': {'rich_text': [{'text': {'content': item.get('name')}}]}
                    }
                }
                futures.append(executor.submit(notion_update_page, item, json_content, config))
            
            success = True
            for future in as_completed(futures):
                try:
                    future.result()  # 获取结果，抛出异常则记录
                    progress_bar.update(1)
                except Exception as e:
                    logging.error(f"Error updating page: {e}")
                    success = False

        progress_bar.close()
        
        if success:   
            # 备份这次数据
            my_fund.to_csv(file_path("fund_data_backup.csv"), index=False)
            logging.info("Data successfully backed up.")
        else:
            logging.error("Some updates failed. Data not backed up.")
            
    else:
        logging.info("无修改需要上传")

def update_notion():
    """
    更新 Notion 数据库
    """
    config = load_config()

    if config['notion']['upload_enabled'] == False:
        return

    try:
        my_fund = pd.read_csv(file_path('fund_data.csv'), dtype={'fundcode': str})
    except FileNotFoundError:
        logging.error("未找到 fund_data.csv 数据，停止上传至 Notion")
        return

    column_list = my_fund.columns.tolist()

    # 检查是否有新基金，如果有则在 Notion 中新建页面
    my_fund = if_page_nan(config, my_fund)
    
    # 对比数据并只上传有修改的内容
    diff_index_list = different_data(column_list, my_fund)
    update_data(diff_index_list, my_fund, config) # 上传

if __name__ == '__main__':
    update_notion()