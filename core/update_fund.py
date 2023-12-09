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

def trans_filter(my_trans,fundcode,parent_type,info=['Buy','Sell','Income'],star_index=0):
    '''
    在交易数据中筛选my_fund中的基金
    info: 交易类型，列表类型
    star_index: 起始索引
    '''
    trans_info = my_trans[
        (my_trans['fundcode']==fundcode)&
        (my_trans['parent']==parent_type)&
        (my_trans['info'].isin(info))&
        (my_trans.index>=star_index)
    ]
    return trans_info

def if_liquidation(my_trans,fundcode,parent_type):
    '判断是否有过清仓，返回最后一次清仓交易的行索引+1'
    fund_trans = trans_filter(my_trans,fundcode,parent_type).copy()
    fund_trans['remaining_shares'] = np.cumsum(fund_trans['number_shares']).round(2)
    if 0.00 in list(fund_trans['remaining_shares']):
        star_index = fund_trans[fund_trans['remaining_shares']==0].index.values[-1]+1
    else:
        star_index = 0
    return star_index

def calculate_fund_data(my_trans,fundcode,parent_type,star_index):
    '计算基金各项数据'
    trans_sell_df = trans_filter(my_trans,fundcode,parent_type,['Sell'],star_index)
    trans_income_df = trans_filter(my_trans,fundcode,parent_type,['Income'],star_index)
    trans_buy_df = trans_filter(my_trans,fundcode,parent_type,['Buy'],star_index)
    trans_buy_all = trans_filter(my_trans,fundcode,parent_type,['Buy'])
    trans_income_all = trans_filter(my_trans,fundcode,parent_type,['Income'])
    trans_sell_all = trans_filter(my_trans,fundcode,parent_type,['Sell'])
    trans_all_df = trans_filter(my_trans,fundcode,parent_type)
    
    sell_shares = trans_sell_df['number_shares'].sum()
    jjfh = round(trans_income_df['total_price'].sum(),2)
    cyfe = round(
        trans_buy_df['number_shares'].sum()+
        trans_income_df['number_shares'].sum()+
        sell_shares,
        2
    )
    jjbj = round(
        trans_buy_df['total_price'].sum()+
        trans_buy_df['commission'].sum(),
        2
    )
    if cyfe > 0:
        cccb = jjbj/(cyfe-sell_shares)
    else:
        cccb = 0
    lj_cyfe = round(
        trans_buy_all['number_shares'].sum()+
        trans_income_all['number_shares'].sum()+
        trans_sell_all['number_shares'].sum(),
        2
    )
    lj_mcje = trans_sell_all["total_price"].sum()
    lj_jjbj = round(
        trans_buy_all['total_price'].sum()+
        trans_buy_all['commission'].sum(),
        2
    )
    lj_jjfh = round(trans_income_all['total_price'].sum(),2)
    child = trans_all_df.loc[trans_all_df.index[-1],'child']
    data_info = [fundcode,cyfe,parent_type,child,jjfh,jjbj,cccb,lj_cyfe,lj_jjfh,lj_jjbj,lj_mcje]
    return data_info

def fundcode_unique(df,parent_type):
    trans_fund_list = df.loc[df['parent']==parent_type,'fundcode'].unique()
    return trans_fund_list

def calculate_base_data(my_trans):
    data_info_list = []
    for parent_type in my_trans['parent'].unique(): #遍历所有的基金策略
        trans_fund_list = fundcode_unique(my_trans,parent_type) #获得每种策略中的基金
        # 对交易过的基金进行基础计算
        for fundcode in trans_fund_list:   #遍历基金
            
            star_index = if_liquidation(my_trans,fundcode,parent_type)
            data_info = calculate_fund_data(my_trans,fundcode,parent_type,star_index)

            data_info_list.append(data_info)
    trans_data = pd.DataFrame(
        data_info_list,
        columns=['fundcode','cyfe','parent','child','jjfh','jjbj','cccb','lj_cyfe','lj_jjfh','lj_jjbj','lj_mcje']
    )
    # print(trans_data)
    return trans_data

def merge_data(my_fund,trans_data):
    '组装数据'
    for repeat_columns in ['cyfe','child','jjfh','jjbj','cccb','lj_cyfe','lj_jjfh','lj_jjbj','lj_mcje']:
        if repeat_columns in my_fund.columns:
            my_fund = my_fund.drop(repeat_columns,axis=1)
    my_fund_data = pd.merge(
        my_fund,
        trans_data,
        on=['fundcode','parent'],
        how='right'
    )
    return my_fund_data

def add_fund_name(my_fund_data):
    '新基金添加名称'
    if my_fund_data['name'].isnull().any():
        try:
            name_df = pd.read_csv(
                file_path('fund_name.csv'),
                dtype={'fundcode':str},
            )
            name_dict = name_df.set_index('fundcode').T.to_dict('list')
        except:
            name_dict = get_name_info()
        my_fund_data['name'] = my_fund_data['fundcode'].apply(lambda x:name_dict.get(x)[0])
        my_fund_data['type'] = my_fund_data['fundcode'].apply(lambda x:name_dict.get(x)[1])

def update_fund_nav(my_fund_data):
    '若净值更新日期不是今天，则更新净值'
    date_today = datetime.now().strftime('%Y-%m-%d')
    # date_today = '2023-02-03' #测试用
    fund_list = my_fund_data[
        (my_fund_data['FSRQ']!=date_today)&(my_fund_data['cyfe']>0)
    ]['fundcode'].unique()
    if len(fund_list)>0:
        dwjz_dict = get_nav(fund_list)
        not_today_index = my_fund_data[
            (my_fund_data['FSRQ']!=date_today)&(my_fund_data['cyfe']>0)
        ].index
        my_fund_data.loc[not_today_index,'DWJZ'] = my_fund_data.loc[
            not_today_index,'fundcode'
        ].apply(lambda x:dwjz_dict.get(x)[1]).astype(float)
        my_fund_data.loc[not_today_index,'FSRQ'] = my_fund_data.loc[
            not_today_index,'fundcode'
        ].apply(lambda x:dwjz_dict.get(x)[0])

    # 处理为空的净值，一般为新录入且已清仓的基金
    my_fund_data['DWJZ'] = my_fund_data['DWJZ'].fillna(0)

def calculate_revenue(my_fund_data):
    '计算累计收益，持有收益，持有收益率，持有市值'
    my_fund_data["ljsy"] = (my_fund_data["lj_cyfe"]*my_fund_data["DWJZ"]+my_fund_data["lj_mcje"]-my_fund_data["lj_jjbj"]+my_fund_data["lj_jjfh"]).round(2)
    
    my_fund_data[["cysy","cysyl"]] = 0.0
    my_fund_data.loc[my_fund_data["cyfe"]>0,"cysy"] = (my_fund_data["DWJZ"]-my_fund_data["cccb"])*my_fund_data["cyfe"]+my_fund_data["jjfh"]
    my_fund_data.loc[my_fund_data["cyfe"]>0,"cysyl"] = (my_fund_data["cysy"]/(my_fund_data["cccb"]*my_fund_data['cyfe'])).round(4)

    my_fund_data['cccb'] = my_fund_data['cccb'].round(4)
    my_fund_data['cysy'] = my_fund_data['cysy'].round(2)

    my_fund_data['amount'] = (my_fund_data['cyfe']*my_fund_data['DWJZ']).round(2) # 计算每个基金的总金额
    # print(my_fund_data)

def update_fund():
    start = time()

    my_trans = pd.read_csv(
        file_path('trans_data.csv'),
        dtype={'fundcode':str},
        comment='#'
    ).sort_values(by='date').reset_index(drop=True)
    
    if path.isfile(file_path('fund_data.csv')):
        my_fund = pd.read_csv(
            file_path('fund_data.csv'),
            dtype={'fundcode':str},
        )
    else:
        my_fund = pd.DataFrame(
            columns=['fundcode','name','page_id','parent','cysy','cysyl','ljsy','FSRQ','DWJZ','cyfe','child','jjfh','jjbj','cccb']
        )

    # 处理数据，将卖出的份额变为负数
    my_trans.loc[(my_trans['info']=='Sell'),'number_shares'] = -my_trans.loc[
        (my_trans['info']=='Sell'),'number_shares'
    ]

    trans_data = calculate_base_data(my_trans)
    my_fund_data = merge_data(my_fund,trans_data)
    add_fund_name(my_fund_data)
    update_fund_nav(my_fund_data)
    calculate_revenue(my_fund_data)

    my_fund_data.to_csv(
        file_path('fund_data.csv'),
        index=False,
    )

    end = time()
    print('数据计算完成，运行时长：',round(end-start,2),'s')

if __name__ == '__main__':
    update_fund()