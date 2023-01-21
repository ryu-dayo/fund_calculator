#!/usr/bin/python
# coding=utf-8
from function import file_path
from update_name import get_name_info
from update_nav import get_nav
from datetime import datetime
import pandas as pd
import time

def trans_filter(info):
    '''
    在交易数据中筛选my_fund中的基金
    info: 交易类型
    '''
    trans_info = my_trans[
        (my_trans['fundcode']==fundcode)&
        (my_trans['parent']==parent_type)&
        (my_trans['info']==info)
    ]
    return trans_info

star = time.time()

my_trans = pd.read_csv(
    file_path('trans_data.csv'),
    dtype={'fundcode':str},
)
my_fund = pd.read_csv(
    file_path('fund_data.csv'),
    dtype={'fundcode':str},
)

data_info_list = []

for parent_type in my_trans['parent'].unique(): #遍历所有的基金策略
    trans_fund_list = my_trans[my_trans['parent']==parent_type]['fundcode'].unique() #获得每种策略中的基金
    # 对交易过的基金进行基础计算
    for fundcode in trans_fund_list:   #遍历基金
        buy_shares = trans_filter('Buy')['number_shares'].sum()
        income_shares = trans_filter('Income')['number_shares'].sum()
        sell_shares = trans_filter('Sell')['number_shares'].sum()
        buy_price = trans_filter('Buy')['total_price'].sum()
        buy_commission = trans_filter('Buy')['commission'].sum()
        child = trans_filter("Buy").reset_index().loc[0,"child"]
        jjfh = round(trans_filter('Income')['total_price'].sum(),2)
        sell_total_price = trans_filter("Sell")["total_price"].sum()
        cyfe = round(buy_shares+income_shares-sell_shares,2)
        jjbj = round(buy_price+buy_commission,2)
        cccb = round(jjbj/(cyfe+sell_shares),4)

        # trans_num = my_trans[(my_trans.values==0].index.values[-1])
        # print(trans_num)

        if (cyfe>0) & (sell_shares>0):
            mcsy = sum(
                (trans_filter("Sell")["price_share"]*(cyfe+sell_shares)-jjbj+jjfh)/jjbj
                *(trans_filter("Sell")["number_shares"]*cccb)
            )
        else:
            mcsy = 0
        
        data_info = [fundcode,cyfe,parent_type,child,jjfh,jjbj,sell_total_price,cccb,mcsy]
        data_info_list.append(data_info)

trans_data = pd.DataFrame(
    data_info_list,
    columns=["fundcode","cyfe","parent","child","jjfh","jjbj","mcje","cccb","mcsy"]
)

#   组装数据
for repeat_columns in ["cyfe","child","jjfh","jjbj","mcje","cccb","mcsy"]:
    if repeat_columns in my_fund.columns:
        my_fund = my_fund.drop(repeat_columns,axis=1)
my_fund_data = pd.merge(
    my_fund,
    trans_data,
    on=['fundcode','parent'],
    how='right'
)

#   新基金添加名称
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

#   若净值更新日期不是今天，则更新
date_today = datetime.now().strftime('%Y-%m-%d')
# date_today = '2023-01-20' #测试用
fund_list = my_fund_data[my_fund_data['FSRQ']!=date_today]['fundcode'].unique()
if len(fund_list)>0:
    dwjz_dict = get_nav(fund_list)
    my_fund_data.loc[my_fund_data[my_fund_data['FSRQ']!=date_today].index,'DWJZ'] = my_fund_data.loc[my_fund_data[my_fund_data['FSRQ']!=date_today].index,'fundcode'].apply(lambda x:dwjz_dict.get(x)[1]).astype(float)
    my_fund_data.loc[my_fund_data[my_fund_data['FSRQ']!=date_today].index,'FSRQ'] = my_fund_data.loc[my_fund_data[my_fund_data['FSRQ']!=date_today].index,'fundcode'].apply(lambda x:dwjz_dict.get(x)[0])

#   计算持有收益，持有收益率，累计收益
my_fund_data[["cysy","cysyl"]] = 0
my_fund_data.loc[my_fund_data["cyfe"]==0,"cccb"] = 0
my_fund_data["ljsy"] = round(my_fund_data["cyfe"] * my_fund_data["DWJZ"] + my_fund_data["mcje"] - my_fund_data["jjbj"] + my_fund_data["jjfh"],2)
my_fund_data.loc[my_fund_data["cyfe"]>0,"cysy"] = round(my_fund_data["DWJZ"]*my_fund_data["cyfe"]-my_fund_data["jjbj"]+my_fund_data["jjfh"],2)
my_fund_data.loc[my_fund_data["mcsy"]>0,"cysy"] = round(my_fund_data["ljsy"]-my_fund_data["mcsy"],2)
my_fund_data.loc[my_fund_data["cyfe"]>0,"cysyl"] = round(my_fund_data["cysy"]/my_fund_data["jjbj"],4)
my_fund_data.loc[my_fund_data["mcsy"]>0,"cysyl"] = round(my_fund_data["cysy"]/(my_fund_data["jjbj"]-my_fund_data["mcfe"]*my_fund_data["cccb"]),4)

my_fund_data.to_csv(
    file_path('fund_data.csv'),
    index=False,
)

end = time.time()
print('数据计算完成，运行时长：',round(end-star,2),'s')