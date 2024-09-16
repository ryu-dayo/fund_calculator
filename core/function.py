from os import system, path
import json

def file_path(file_name):
    file_path = path.join(
        path.join(
            path.dirname(
                path.dirname(
                    path.abspath(__file__)
                )
            ),
            'data'
        ),
        file_name
    )
    return file_path

def load_config():
    config_path = file_path('config.json')

    with open(config_path, 'r', encoding='utf-8') as file:
        config = json.load(file)

    return config

def mac_notification(title, text):
    system(
        """
        osascript -e 'display notification "{}" with title "{}"'
        """.format(text, title)
    )