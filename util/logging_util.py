import logging


class __LoggingWrapper:
    def __init__(self):
        # 만약 기본 콘솔 로깅이 아닌 파일 로깅들이 필요하면 여거서 설정 추가
        # 설정과 관련된 정보는 요 링크 참조
        # https://docs.python.org/ko/3/howto/logging.html
        self.__default_logger_name = None
        self.__set_config()

    def set_default_logger_level(self, logger_name, level):
        self.__default_logger_name = logger_name
        self.set_level(self.__default_logger_name, level)

    # noinspection PyMethodMayBeStatic
    def __set_config(self, **kwargs):
        logging.basicConfig(**kwargs)

    # noinspection PyMethodMayBeStatic
    def set_level(self,  logger_name: str, level: int):
        print('New Logger Registered :', logger_name, level)
        _logger = logging.getLogger(logger_name)
        _logger.setLevel(level)
        _logger.propagate = True

    # noinspection PyMethodMayBeStatic
    # 명시적인 로거 이름으로 남길때 사용하는 메소드
    def get_logger(self, logger_name):
        return logging.getLogger(logger_name)

    # set_default_logger_level(기본 로거 이름) 으로 로깅을 남길때 사용하는 메소드들
    def debug(self, msg, *args, **kwargs):
        if msg is not None:
            logging.getLogger(self.__default_logger_name).debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        if msg is not None:
            logging.getLogger(self.__default_logger_name).info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        if msg is not None:
            logging.getLogger(self.__default_logger_name).warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        if msg is not None:
            logging.getLogger(self.__default_logger_name).error(msg, *args, **kwargs)

    def fatal(self, msg, *args, **kwargs):
        if msg is not None:
            logging.getLogger(self.__default_logger_name).fatal(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        if msg is not None:
            logging.getLogger(self.__default_logger_name).exception(msg, *args, **kwargs)


logger = __LoggingWrapper()

