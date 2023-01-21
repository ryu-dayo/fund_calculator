import os

def file_path(file_name):
    file_path = os.path.join(
        os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            ),
            'data'
        ),
        file_name
    )
    return file_path
