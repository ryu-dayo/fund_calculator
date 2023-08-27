#!/usr/bin/python
# coding=utf-8
from function import file_path
from time import sleep
from json import loads
from tqdm import tqdm
from os import path
import configparser
import pandas as pd
import requests

def notion_create_page(json_content,config):

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
    
    # sleep(0.5)
    return(response.text)

def notion_update_page(item,json_content,config):

    url = "https://api.notion.com/v1/pages/" + item.get('page_id')
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

    sleep(0.5)
    # print(response.text)
    return response.text

def if_page_nan(config,my_fund):
    '判断page id是否为空，为空则新建page并返回id'
    nan_list = my_fund[my_fund['page_id'].isnull()].index.tolist()
    if len(nan_list)>0:
        for nan_index in nan_list:

            json_content = {
                'Name':{'title':[{'text':{'content':my_fund.loc[nan_index,'fundcode']}}]},
                '投资体系':{'relation':[{'id':config['notion_page_id'][my_fund.loc[nan_index,'parent']]}]},
                '基金名称':{'rich_text':[{'text':{'content':my_fund.loc[nan_index,'name']}}]}
            }
            if my_fund.loc[nan_index,'child']==my_fund.loc[nan_index,'child']:
                json_content['永久组合'] = {'relation':[{config['notion_page_id'][my_fund.loc[nan_index,'child']]}]}

            response_text = notion_create_page(json_content,config)
            # print(response_text)
            my_fund.loc[nan_index,'page_id'] = loads(response_text)['id']
            
        my_fund.to_csv(
            file_path("fund_data.csv"),
            index=False,
        )
    return my_fund

def different_data(column_list,my_fund):
    '补齐并对比数据'
    try:
        notion_data = pd.read_csv(
            file_path("fund_data_backup.csv"),
            dtype={"fundcode":str}
        )
    except:
        notion_data = pd.DataFrame(
            columns=column_list
        )
    my_fund,notion_data = my_fund.align(notion_data,join="outer",axis=None)
    diff_index_list = my_fund.compare(notion_data).index.tolist()
    return diff_index_list

def update_data(diff_index_list,my_fund,config):
    #   遍历基金并上传
    if len(diff_index_list)>0:
        progress_bar = tqdm(total=len(diff_index_list),desc='上传 Notion')
        update_dict = my_fund.loc[diff_index_list,:].to_dict('records')
        for item in update_dict:

            json_content = {
                'properties':{
                    '持有市值':{'number':item.get('amount')},
                    '持有收益':{'number':item.get('cysy')},
                    '持有收益率':{'number':item.get('cysyl')},
                    '累计收益':{'number':item.get('ljsy')},
                    # '更新时间':{'date':{'start':item.get('FSRQ')}},
                    # '基金名称':{'rich_text':[{'text':{'content':item.get('name')}}]}
                }
            }

            notion_update_page(item,json_content,config)
            progress_bar.update(1)

        #   备份这次数据，以便下次进行对比
        my_fund.to_csv(
            file_path("fund_data_backup.csv"),
            index=False,
        )
    else:
        print('无修改')

def update_notion():
    # 加载配置
    config = configparser.ConfigParser()
    config.read(file_path('config.ini'),encoding='UTF-8')

    try:
        my_fund = pd.read_csv(
            file_path('fund_data.csv'),
            dtype={'fundcode':str},
        )
    except:
        print('未找到数据，停止上传至 Notion')
        exit()

    column_list = my_fund.columns

    my_fund = if_page_nan(config,my_fund) # 检查是否有新购买的基金，如果有则在 Notion 新建页面
    diff_index_list = different_data(column_list,my_fund) # 和上次上传内容比较，只上传改动内容
    update_data(diff_index_list,my_fund,config) # 上传

if __name__ == '__main__':
    update_notion()