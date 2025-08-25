import logging

from contants import SingletonInstance, get_config_from_param_store


# Naver SMS
class NaverSmsConfig(SingletonInstance):
    def __init__(self):
        self.ACCESS_KEY = get_config_from_param_store('/52g/nhn/sens/access-key')
        self.SECRET_KEY = get_config_from_param_store('/52g/nhn/sens/secret-key')
        self.NAVER_URL = get_config_from_param_store('/52g/nhn/sens/url')
        self.NAVER_URI = get_config_from_param_store('/52g/nhn/sens/uri')
        self.FROM_PHONE_NUMBER = get_config_from_param_store('/52g/nhn/sens/from-phone-number')



# JWT
class JWTConfig(SingletonInstance):
    def __init__(self):
        self.SECRET_KEY = get_config_from_param_store('/52g/camp/secret-key')


# Flask Base Configuration
class BaseConfig(object):
    # Flask
    ENV = 'development'
    DEBUG = False
    BUNDLE_ERRORS = True
    PROPAGATE_EXCEPTIONS = True
    SECRET_KEY = JWTConfig.instance().SECRET_KEY
    # Restx
    RESTX_VALIDATE = True
    RESTX_MASK_SWAGGER = False
    # JWT
    JWT_ACCESS_TOKEN_EXPIRES = False
    LOG_LEVEL = logging.DEBUG

# Flask Local Configuration
class LocalConfig(BaseConfig):
    DEBUG = True

# Flask Dev Configuration
class DevConfig(BaseConfig):
    BASE_URL = 'https://finance-backend.52g.studio'


config_by_name = dict(
    local='config.LocalConfig',
    dev='config.DevConfig')
