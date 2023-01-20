#!/usr/bin/python
# coding=utf-8

from function import notion_update_page
from function import notion_create_page
from function import file_path
from tqdm import tqdm
import configparser
import pandas as pd
import json

config = configparser.ConfigParser()
config.read(file_path('config.ini'),encoding='UTF-8')

my_fund = pd.read_csv(
    file_path('fund_data.csv'),
    dtype={'fundcode':str},
)
column_list = my_fund.columns

#   判断page id是否为空，为空则新建page并返回id
nan_list = my_fund[my_fund['page_id'].isnull()].index.tolist()

if len(nan_list)>0:
    for item in nan_list:

        json_content = {
            "Name":{"title":[{"text":{"content":my_fund.loc[item,"fundcode"]}}]},
            "投资体系":{"relation":[{"id":config['notion_page_id'][my_fund.loc[item,"parent"]]}]},
        }
        if my_fund.loc[item,"child"]==my_fund.loc[item,"child"]:
            json_content["永久组合"] = {"relation":[{config['notion_page_id'][my_fund.loc[item,"child"]]}]}

        response_text = notion_create_page(json_content)
        print(response_text)
        my_fund.loc[item,"page_id"] = json.loads(response_text)["id"]
        
    my_fund.to_csv(
        file_path("fund_data.csv"),
        index=False,
    )

#   补齐并对比数据
notion_data = pd.read_csv(
    file_path("fund_data_backup.csv"),
    dtype={"fundcode":str}
)
my_fund,notion_data = my_fund.align(notion_data,join="outer",axis=None)
diff_index_list = my_fund.compare(notion_data).index.tolist()

#   遍历基金并上传
if len(diff_index_list)>0:
    progress_bar = tqdm(total=len(diff_index_list))
    for row in my_fund.loc[diff_index_list,:].itertuples():

        json_content = {
            'properties':{
                '份额':{'number':getattr(row,'cyfe')},
                '持有单价':{'number':getattr(row,'cccb')},
                '净值':{'number':getattr(row,'DWJZ')},
                '持有收益':{'number':getattr(row,'cysy')},
                '持有收益率':{'number':getattr(row,'cysyl')},
                '累计收益':{'number':getattr(row,'ljsy')},
                # '更新时间':{'date':{'start':getattr(row,'FSRQ')}},
                # '基金名称':{'rich_text':[{'text':{'content':getattr(row,'name')}}]}
            }
        }

        response_text = notion_update_page(row,json_content)
        progress_bar.update(1)

    #   备份这次数据，以便下次进行对比
    my_fund.to_csv(
        file_path("fund_data_backup.csv"),
        index=False,
    )
else:
    print('无修改')