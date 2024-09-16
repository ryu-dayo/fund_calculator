#!/usr/bin/python
# coding=utf-8
from function import file_path, mac_notification, load_config
from time import time
from os import path
import pandas as pd
import platform
import logging

logging.basicConfig(level=logging.INFO)

def fund_percent(df, type_name: str) -> pd.DataFrame:
    """
    根据不同类型合并数据并计算占比
    """
    percent_df = df.copy() if type_name == 'parent' else df[df['parent']==type_name].copy()
    type_name = 'child' if type_name != 'parent' else type_name
    
    percent_df['percent'] = percent_df['amount'] / percent_df['amount'].sum()
    percent_df = percent_df.groupby(type_name, as_index=False)[['amount', 'percent']].sum()
    percent_df['percent'] = percent_df['percent'].apply(lambda x:f'{x * 100:.2f}%') 
    return percent_df

def merge_data(origin_fund: pd.DataFrame, fake_data: pd.DataFrame) -> pd.DataFrame:
    """
    合并原始基金数据与占位数据，并处理子分类为空的情况
    """
    my_fund = pd.concat([origin_fund, fake_data], ignore_index=True)
    my_fund['child'].fillna(my_fund['fundcode'], inplace=True) # 如果子分类为空则替换为基金编号
    
    # 筛选当前持有的基金
    return my_fund[my_fund['amount'] > 0]

def df_to_str(df: pd.DataFrame) -> str:
    """
    将 DataFrame 转为字符串
    """
    return df.to_string(index=False, header=False)

def print_data(config: dict, fake_data: pd.DataFrame, origin_fund: pd.DataFrame, my_fund: pd.DataFrame):
    """
    打印基金数据，并在 macOS 发送通知
    """
    str_line = '-' * 30
    print_list = []

    # 统计子类型占比
    for name, group in my_fund.groupby('parent'):
        if name not in config['view']['hidden_type']:
            print_list.extend(
                [name, df_to_str(fund_percent(my_fund, name)), str_line]
            )

    # 统计账户收益
    cal_df = pd.DataFrame([
        ['账户资产（元）', round(sum(origin_fund['amount']), 2)],
        ['持有收益（元）', round(sum(origin_fund['cysy']), 2)],
        ['累计收益（元）', round(sum(origin_fund['ljsy']), 2)]
    ])

    # 转换成字符串并打印
    content_text = '\n'.join([
        df_to_str(cal_df),
        str_line,
        '组合比例',
        df_to_str(fund_percent(origin_fund, 'parent')),
        str_line
    ] + print_list + [
        '占位数据',
        df_to_str(fake_data[['parent', 'child', 'amount']]),
        str_line
    ])
    
    print(content_text)

    # 如果是 mac 则发送通知
    if 'macos' in platform.platform().lower():
        mac_notification('基金', content_text)

def view_fund():
    """
    查看基金数据
    """
    start_time = time()
    config = load_config()

    # 加载原始基金数据
    if path.isfile(file_path('fund_data.csv')):
        try:
            origin_fund = pd.read_csv(
                file_path('fund_data.csv'),
                dtype={'fundcode': str},
            )
        except Exception as e:
            logging.error(f"读取 fund_data.csv 文件失败：{e}")
            origin_fund = pd.DataFrame()
    else:
        origin_fund = pd.DataFrame(columns=[
            'fundcode', 'name', 'page_id', 'parent', 'cysy', 'cysyl', 'ljsy', 'FSRQ',
            'DWJZ', 'cyfe', 'child', 'jjfh', 'jjbj', 'mcje', 'cccb', 'mcsy' 
        ])

    # 加载占位数据
    try:
        fake_data = pd.DataFrame(
            config['view']['fake_data'],
            columns=['fundcode', 'parent', 'child', 'amount']
        )
    except Exception as e:
        logging.error(f"加载占位数据失败：{e}")
        fake_data = pd.DataFrame(columns=['fundcode', 'parent', 'child', 'amount'])
    
    # 合并并打印数据
    my_fund = merge_data(origin_fund, fake_data)
    print_data(config, fake_data, origin_fund, my_fund)

    end_time = time()
    print(f'运行时长：{round(end_time - start_time, 2)}s')

if __name__ == '__main__':
    view_fund()