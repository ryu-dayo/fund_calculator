import os

file_path = os.path.dirname(os.path.abspath(__file__))
file_list = [
    'update_fund.py',
    'update_notion.py',
    'view_fund.py'
]

for file_item in file_list:
    os.system('python3.9 ' + os.path.join(file_path,file_item))