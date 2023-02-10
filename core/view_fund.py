#!/usr/bin/python
# coding=utf-8
from function import file_path
from time import time
import configparser
import pandas as pd
import json

def fund_percent(df,type_name,child_name=''):
    if type_name!='parent':
        percent_df = df.loc[child_name].copy()
    else:
        percent_df = df.copy()
    percent_df['percent'] = percent_df['amount']/percent_df['amount'].sum()
    percent_df = percent_df.groupby(type_name)[['amount','percent']].sum()
    percent_df['percent'] = percent_df['percent'].apply(lambda x:'%.2f%%'%(x*100))
    return percent_df

def merge_data(config):

    my_fund = pd.read_csv(
        file_path('fund_data.csv'),
        dtype={'fundcode':str},
    )

    fake_data = pd.DataFrame(
        json.loads(config['view']['fake_data']),
        columns=['fundcode','parent','child','amount']
    )
    my_fund = pd.concat([my_fund,fake_data])
    print('-'*30,'\n占位数据\n',fake_data,'\n','-'*30)
    my_fund['child'].fillna(my_fund['fundcode'],inplace=True) # 如果子分类为空则替换为基金编号

    my_fund = my_fund[
        my_fund['amount']>0
    ].set_index(['parent','child'])
    return my_fund

def print_data(config,my_fund):
    for name, group in my_fund.groupby('parent'):
        if name not in json.loads(config['view']['hidden_type']):
            print(name)
            # print(group)
            print(fund_percent(my_fund,'child',name))
            print('-'*30)
    #计算组合占比
    print('组合比例')
    print(fund_percent(my_fund,'parent'))
    print('-'*30)
    # print(my_fund)

def view_fund():
    start = time()

    config = configparser.ConfigParser()
    config.read(file_path('config.ini'),encoding='UTF-8')
    
    my_fund = merge_data(config)
    print_data(config,my_fund)

    end = time()
    print('运行时长：',round(end-start,2),'s')

if __name__ == '__main__':
   view_fund()