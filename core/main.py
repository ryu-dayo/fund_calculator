from update_fund import update_fund
from update_notion import update_notion
from view_fund import view_fund
from export_data import export_data

update_fund()
try:
    update_notion()
except:
    print('Notion 配置可能有问题，已跳过上传')
view_fund()
export_data()