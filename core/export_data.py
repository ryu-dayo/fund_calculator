import os
import shutil
import logging
from function import file_path, load_config

logging.basicConfig(level=logging.INFO)

def export_data():
    """
    备份指定的文件到目标文件夹
    """
    # 加载配置文件
    config = load_config()

    # 获得需要备份的文件和目标地址
    file_name_list = config['export']['file_list']
    target_folder = config['export']['path']
    
    # 检查目标地址是否存在，如果不存在则提示错误
    if not target_folder:
        logging.error("目标文件夹为空，请在配置文件中指定目标文件夹")
        return

    if not os.path.exists(target_folder):
        try:
            os.makedirs(target_folder)  # 如果目标目录不存在，则创建它
            logging.info(f"目标文件夹 {target_folder} 已创建")
        except Exception as e:
            logging.error(f"无法创建目标文件夹 {target_folder}: {e}")
            return

    # 备份文件
    for file_name in file_name_list:
        try:
            current_file = file_path(file_name)
            target_file = os.path.join(target_folder, file_name)
            
            shutil.copy(current_file, target_file)
            logging.info(f"已备份文件: {current_file}")
            
        except FileNotFoundError:
            logging.warning(f"未找到文件: {current_file}")
        except PermissionError:
            logging.error(f"没有权限复制文件: {current_file}")
        except Exception as e:
            logging.error(f"备份文件 {current_file} 时出错: {e}")

    logging.info(f"文件已成功备份至 {target_folder}")

if __name__ == '__main__':
    export_data()