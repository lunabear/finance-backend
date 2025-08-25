"""
  파일에 관련된 유틸리티 모듈
"""
import os
from pathlib import Path
from logging_util import logger


def create_directory(path: str) -> None:
    """
    디렉토리를 생성한다.
    :param path: 디렉토리를 생성할 경로
    :return:
    """
    try:
        if not os.path.exists(path):
            os.makedirs(path)
        else:
            logger.warning('Warn: the directory already exists.')
    except OSError:
        logger.error('Error: Failed to create the directory.')


def get_sorted_file_list(path: str) -> list:
    """
    생성일 순서로 경로에 있는 파일 및 디렉토리 목록(1단계)을 얻는다.
    :param path: 파일 목록을 얻을 경로
    :return:
    """
    return list(sorted(os.listdir(path), key=lambda f: os.stat(os.path.join(path, f)).st_mtime))


def get_all_file_list_in_directory(path: str) -> list:
    """
    해당 경로 하위의 모든 파일 리스트(PosixPath)를 (하위 디렉토리 포함, 파일 만) 얻는다.
    :param path: 파일 목록을 얻을 경로
    :return:
    """
    path_list = Path(path).glob('**/*')
    file_list = [path for path in path_list if path.is_file()]
    return file_list


if __name__ == '__main__':
    # 해당 디렉토리의 하위의 모든(리커시브) 파일 리스트를 얻는다.
    print(get_all_file_list_in_directory('../api'))

    # 해당 디렉토리 하위의 파일 및 디렉토리(1단계) 의 파일 리스트를 생성일 순서로 얻는다.
    print(get_sorted_file_list('../api'))



