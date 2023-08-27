import shutil
import configparser
from json import loads
from function import file_path

def export_data():
    # 加载配置文件
    config = configparser.ConfigParser()
    config.read(file_path('config.ini'),encoding='UTF-8')

    # 获得需要备份的文件和目标地址
    file_name_list = loads(config['export']['file_list'])
    target_folder = config['export']['path']

    # 如果目标地址不为空则执行备份
    if target_folder != '':

        for file_name in file_name_list:
            try:
                current_file = file_path(file_name)
                target_file = target_folder + file_name
                shutil.copy(current_file, target_file)
            except:
                continue

        print(f'文件已成功备份至 {target_folder}')

if __name__ == '__main__':
    export_data()