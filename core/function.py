from os import system,path

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

def mac_notification(title,text):
    system(
        """
        osascript -e 'display notification "{}" with title "{}"'
        """.format(text,title)
    )