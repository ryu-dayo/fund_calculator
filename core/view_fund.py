#!/usr/bin/python
# coding=utf-8
import function
import pandas as pd
import time

def fund_percent(type_name,child_name=''):
    if type_name!='parent':
        percent_df = my_fund.loc[child_name].copy()
    else:
        percent_df = my_fund.copy()
    percent_df['percent'] = percent_df['amount']/percent_df['amount'].sum()
    percent_df = percent_df.groupby(type_name)[['amount','percent']].sum()
    percent_df['percent'] = percent_df['percent'].apply(lambda x:'%.2f%%'%(x*100))
    return percent_df

start = time.time()

my_fund = pd.read_csv(
    function.file_path('fund_data.csv'),
    dtype={'fundcode':str},
)
fake_data = pd.DataFrame(
    [['','','永久组合',10000,1,'货币',0,10000,1,'1993-07-26',0],
    ['','','永久组合',10000,1,'黄金',0,10000,1,'1993-07-26',0],],
    columns=['fundcode','page_id','parent','cyfe','cccb','child','jjfh','jjbj','DWJZ','FSRQ','cysy']
)
my_fund = pd.concat([my_fund,fake_data])
print('-'*30,'\n占位数据\n',fake_data,'\n','-'*30)
my_fund['child'].fillna(my_fund['fundcode'],inplace=True) # 如果子分类为空则替换为基金编号
my_fund['amount'] = round((my_fund['cyfe']*my_fund['DWJZ']),2) # 计算每个基金的总金额
my_fund = my_fund[
    my_fund['amount']>0
].set_index(['parent','child'])

for name, group in my_fund.groupby('parent'):
    if name!="长赢指数":
        print(name)
        # print(group)
        print(fund_percent('child',name))
        print('-'*30)
#计算组合占比
print('组合比例')
print(fund_percent('parent'))
print('-'*30)
# print(my_fund)

end = time.time()
print('运行时长：',round(end-start,2),'s')