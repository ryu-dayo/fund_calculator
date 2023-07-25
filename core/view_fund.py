#!/usr/bin/python
# coding=utf-8
from function import file_path,mac_notification
from json import loads
from time import time
import configparser
import pandas as pd
import platform

def fund_percent(df,type_name):
    """
    根据不同类型合并数据并计算占比
    """
    if type_name!='parent':
        percent_df = df[df['parent']==type_name].copy()
        type_name = 'child'
    else:
        percent_df = df.copy()
    percent_df['percent'] = percent_df['amount']/percent_df['amount'].sum()
    percent_df = percent_df.groupby(type_name,as_index=False)[['amount','percent']].sum()
    percent_df['percent'] = percent_df['percent'].apply(lambda x:'%.2f%%'%(x*100)) 
    return percent_df

def merge_data(origin_fund,fake_data):
    my_fund = pd.concat([origin_fund,fake_data])
    my_fund['child'].fillna(my_fund['fundcode'],inplace=True) # 如果子分类为空则替换为基金编号
    
    # 筛选当前持有的基金
    my_fund = my_fund[my_fund['amount']>0]
    return my_fund

def df_to_str(df):
    df_str = df.to_string(index=False,header=False)
    return df_str

def print_data(config,fake_data,origin_fund,my_fund):
    str_line = '-'*30
    print_list = []

    #   统计子类型占比
    for name, group in my_fund.groupby('parent'):
        if name not in loads(config['view']['hidden_type']):
            print_list.extend(
                [name,df_to_str(fund_percent(my_fund,name)),str_line]
            )

    #   统计账户收益
    cal_1 = ['账户资产（元）',round(sum(origin_fund['amount']),2)]
    cal_2 = ['持有收益（元）',round(sum(origin_fund['cysy']),2)]
    cal_3 = ['累计收益（元）',round(sum(origin_fund['ljsy']),2)]
    cal_df = pd.DataFrame([cal_1,cal_2,cal_3])

    #   转换成字符串并打印
    cal_df_str = df_to_str(cal_df)
    parent_data_str = df_to_str(fund_percent(origin_fund,'parent'))
    fake_data_str = df_to_str(fake_data[['parent','child','amount']])
    content_text = '\n'.join(
        [cal_df_str,str_line,'组合比例',parent_data_str,str_line] + 
        print_list + 
        ['占位数据',fake_data_str,str_line]
    )
    print(content_text)

    #   如果是 mac 则发送通知
    sys_platform = platform.platform().lower()
    if 'macos' in sys_platform:
        mac_notification('',content_text)

def view_fund():
    start = time()

    config = configparser.ConfigParser()
    config.read(file_path('config.ini'),encoding='UTF-8')

    #   加载原始基金数据和占位数据
    origin_fund = pd.read_csv(
        file_path('fund_data.csv'),
        dtype={'fundcode':str},
    )
    fake_data = pd.DataFrame(
        loads(config['view']['fake_data']),
        columns=['fundcode','parent','child','amount']
    )
    
    my_fund = merge_data(origin_fund,fake_data)
    print_data(config,fake_data,origin_fund,my_fund)

    end = time()
    print('运行时长：',round(end-start,2),'s')

if __name__ == '__main__':
    view_fund()