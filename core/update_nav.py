#!/usr/bin/python
# coding=utf-8
import function
import pandas as pd
import numpy as np
import time

start = time.time()

my_fund = pd.read_csv(
    function.file_path('fund_data.csv'),
    dtype={'fundcode':str}
)

dwjz_list = []
fund_list = my_fund["fundcode"].unique()

for fund_code in fund_list:
    dwjz_info = function.get_fund_info(fund_code)
    dwjz_info["fundcode"] = fund_code
    dwjz_list.append(np.array(dwjz_info.iloc[0].tolist()))

fund_value = pd.DataFrame(
    dwjz_list,
    columns=["FSRQ","DWJZ","fundcode"],
)

#   组装数据
for repeat_columns in ["FSRQ","DWJZ"]:
    if repeat_columns in my_fund.columns:
        my_fund = my_fund.drop(repeat_columns,axis=1)
my_fund_data = pd.merge(
    my_fund,
    fund_value,
    on=["fundcode"],
    how='left'
)

my_fund_data.to_csv(
    function.file_path("fund_data.csv"),
    index=False,
)

end = time.time()
print('获取最新净值，运行时长：',round(end-start,2),'s')