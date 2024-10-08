#!/usr/bin/python
# coding=utf-8
from function import file_path
from update_name import get_name_info
from update_nav import get_nav
from datetime import datetime
from time import time
from os import path
import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)

def trans_filter(my_trans: pd.DataFrame, fundcode: str, parent_type: str, info=['Buy','Sell','Income'], star_index=0):
    '''
    在交易数据中筛选 my_fund 中的基金
    info: 交易类型，列表类型
    star_index: 起始索引
    '''
    return my_trans.query(
        "fundcode == @fundcode and parent == @parent_type and "
        "info in @info and index >= @star_index"
    )

def if_liquidation(my_trans: pd.DataFrame, fundcode: str, parent_type: str):
    """
    判断是否有过清仓，返回最后一次清仓交易的行索引+1
    """
    fund_trans = trans_filter(my_trans, fundcode, parent_type).copy()
    fund_trans['remaining_shares'] = np.cumsum(fund_trans['number_shares']).round(2)

    liquidation_rows = fund_trans['remaining_shares'] == 0
    if not fund_trans[liquidation_rows].empty:
        star_index = fund_trans[liquidation_rows].index.values[-1] + 1
    else:
        star_index = 0

    return star_index

def calculate_fund_data(my_trans: pd.DataFrame, fundcode: str, parent_type: str, star_index: int):
    """
    计算基金交易数据
    """
    # 获取包含所有相关交易类型的完整数据集（从star_index开始）
    trans_liquidation_df = trans_filter(my_trans,fundcode, parent_type, star_index=star_index)

    trans_buy_df = trans_liquidation_df[trans_liquidation_df['info'] == 'Buy']
    trans_sell_df = trans_liquidation_df[trans_liquidation_df['info'] == 'Sell']
    trans_income_df = trans_liquidation_df[trans_liquidation_df['info'] == 'Income']
    
    # 获取包含所有相关交易类型的完整数据集（不考虑star_index）
    trans_all_df = trans_filter(my_trans, fundcode, parent_type)

    trans_buy_all = trans_all_df[trans_all_df['info'] == 'Buy']
    trans_income_all = trans_all_df[trans_all_df['info'] == 'Income']
    trans_sell_all = trans_all_df[trans_all_df['info'] == 'Sell']
    
    sell_shares = trans_sell_df['number_shares'].sum()
    jjfh = round(trans_income_df['total_price'].sum(), 2)
    cyfe = round(
        trans_buy_df['number_shares'].sum()
        + trans_income_df['number_shares'].sum()
        + sell_shares,
        2
    )
    jjbj = round(trans_buy_df[['total_price','commission']].sum().sum(), 2)
    cccb = jjbj / (cyfe-sell_shares) if cyfe > 0 else 0
    
    lj_cyfe = round(
        trans_buy_all['number_shares'].sum()
        + trans_income_all['number_shares'].sum()
        + trans_sell_all['number_shares'].sum(),
        2
    )
    lj_mcje = trans_sell_all["total_price"].sum()
    lj_jjbj = round(trans_buy_all[['total_price', 'commission']].sum().sum(), 2)
    lj_jjfh = round(trans_income_all['total_price'].sum(), 2)
    child = trans_all_df.loc[trans_all_df.index[-1], 'child']
    
    data_info = [fundcode, cyfe, parent_type, child, jjfh, jjbj, cccb, lj_cyfe, lj_jjfh, lj_jjbj, lj_mcje]
    return data_info

def fundcode_unique(df, parent_type):
    trans_fund_list = df.loc[df['parent']==parent_type, 'fundcode'].unique()
    return trans_fund_list

def calculate_base_data(my_trans):
    """
    计算每个基金的基础数据
    """
    data_info_list = []
    for parent_type in my_trans['parent'].unique():  # 遍历所有的基金策略
        trans_fund_list = fundcode_unique(my_trans, parent_type)  # 获得每种策略中的基金
        # 对交易过的基金进行基础计算
        for fundcode in trans_fund_list:  # 遍历基金
            star_index = if_liquidation(my_trans, fundcode, parent_type)
            data_info = calculate_fund_data(my_trans, fundcode, parent_type, star_index)
            data_info_list.append(data_info)
            
    trans_data = pd.DataFrame(
        data_info_list,
        columns=['fundcode', 'cyfe', 'parent', 'child', 'jjfh', 'jjbj', 'cccb', 'lj_cyfe', 'lj_jjfh', 'lj_jjbj', 'lj_mcje']
    )
    return trans_data

def merge_data(my_fund: pd.DataFrame, trans_data: pd.DataFrame):
    """
    合并基金基础数据和交易数据
    """
    columns_to_drop = ['cyfe', 'child', 'jjfh', 'jjbj', 'cccb', 'lj_cyfe', 'lj_jjfh', 'lj_jjbj', 'lj_mcje']
    my_fund_cleaned = my_fund.drop(columns=columns_to_drop, errors='ignore')
    
    my_fund_data = pd.merge(my_fund_cleaned, trans_data, on=['fundcode', 'parent'], how='right')
    return my_fund_data

def add_fund_name(my_fund_data: pd.DataFrame):
    """
    为新基金添加名称
    """
    if my_fund_data['name'].isnull().any():
        try:
            name_df = pd.read_csv(file_path('fund_name.csv'), dtype={'fundcode':str})
            name_dict = name_df.set_index('fundcode').T.to_dict('list')
        except FileNotFoundError:
            name_dict = get_name_info()

        my_fund_data['name'] = my_fund_data['fundcode'].map(lambda x: name_dict.get(x, [None,None])[0])
        my_fund_data['type'] = my_fund_data['fundcode'].map(lambda x: name_dict.get(x, [None,None])[1])

def update_fund_nav(my_fund_data: pd.DataFrame):
    """
    更新基金净值
    """
    date_today = datetime.now().strftime('%Y-%m-%d')
    
    fund_need_update = my_fund_data[
        (my_fund_data['FSRQ'] != date_today) & 
        (my_fund_data['cyfe'] > 0)
    ]
    fund_list = fund_need_update['fundcode'].unique()
    
    if fund_list.size > 0:
        dwjz_dict = get_nav(fund_list)
        not_today_index = fund_need_update.index
        dwjz_values = my_fund_data.loc[not_today_index, 'fundcode'].map(dwjz_dict)

        my_fund_data.loc[not_today_index, 'DWJZ'] = dwjz_values.str[1].astype(float)
        my_fund_data.loc[not_today_index, 'FSRQ'] = dwjz_values.str[0]

    # 处理为空的净值，一般为新录入且已清仓的基金
    my_fund_data['DWJZ'] = my_fund_data['DWJZ'].fillna(0)

def calculate_revenue(my_fund_data: pd.DataFrame):
    """
    计算累计收益，持有收益，持有收益率，持有市值
    """
    my_fund_data["ljsy"] = (
        my_fund_data["lj_cyfe"] * my_fund_data["DWJZ"]
        + my_fund_data["lj_mcje"]
        - my_fund_data["lj_jjbj"]
        + my_fund_data["lj_jjfh"]
    ).round(2)
    
    condition = my_fund_data["cyfe"] > 0
    cysy_calculate = (my_fund_data["DWJZ"] - my_fund_data["cccb"]) * my_fund_data["cyfe"] + my_fund_data["jjfh"]
    cysyl_calculate = cysy_calculate / (my_fund_data["cccb"] * my_fund_data['cyfe'])

    my_fund_data['cysy'] = np.where(condition, cysy_calculate.round(2), 0)
    my_fund_data['cysyl'] = np.where(condition, cysyl_calculate.round(4), 0)

    my_fund_data['cccb'] = my_fund_data['cccb'].round(4)
    my_fund_data['amount'] = (my_fund_data['cyfe'] * my_fund_data['DWJZ']).round(2) # 计算每个基金的总金额

def update_fund():
    """
    更新基金数据的主流程
    """
    start_time = time()

    try:
        my_trans = pd.read_csv(file_path('trans_data.csv'), dtype={'fundcode': str}, comment='#')
    except FileNotFoundError:
        logging.error("交易数据文件未找到，无法更新基金")
        return
    
    my_trans = my_trans.sort_values(by='date').reset_index(drop=True)
    my_trans.loc[my_trans['info'] == 'Sell','number_shares'] *= -1  # 将卖出的份额变为负数
    
    if path.isfile(file_path('fund_data.csv')):
        my_fund = pd.read_csv(file_path('fund_data.csv'), dtype={'fundcode':str})
    else:
        my_fund = pd.DataFrame(columns=['fundcode', 'name', 'page_id', 'parent', 'cysy', 'cysyl', 'ljsy', 'FSRQ', 'DWJZ', 'cyfe', 'child', 'jjfh', 'jjbj', 'cccb'])

    trans_data = calculate_base_data(my_trans)
    my_fund_data = merge_data(my_fund, trans_data)
    add_fund_name(my_fund_data)
    update_fund_nav(my_fund_data)
    calculate_revenue(my_fund_data)

    my_fund_data.to_csv(file_path('fund_data.csv'), index=False)

    end_time = time()
    logging.info(f'数据计算完成，运行时长：{round(end_time - start_time, 2)}s')

if __name__ == '__main__':
    update_fund()