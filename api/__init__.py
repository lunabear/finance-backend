import os

from flask import Flask
from flask_cors import CORS
from flask_restx import Api
from werkzeug.utils import import_string

from api.gold import gold_api
from api.common import jwt
from config import config_by_name
from util.logging_util import logger


authorizations = {
    'user_token': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': 'JWT for user'
    },
    'admin_token': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': 'JWT for Waste Admin system'
    },

}


def create_app():
    # SonarQube: S4502 - CSRF protection is not necessary for JWT-based authentication
    app = Flask(__name__)
    # for zappa health check;
    app.add_url_rule('/', endpoint='ping', view_func=lambda: 'Pong!')

    api = Api(app,
              authorizations=authorizations,
              security='user_token',
              doc='/swagger',
              title='finance-backend',
              version='1.0',
              description='금융 정보 서비스 백엔드 API')

    config_name = os.getenv('FINANCE_BACKEND_ENV', 'local')
    print(f'config_env:{config_name}')
    config_object = import_string(config_by_name[config_name])()
    app.config.from_object(config_object)

    # finance backend logger 설정
    logger.set_default_logger_level(app.name, app.config['LOG_LEVEL'])

    # jwt
    jwt.init_app(app)
    
    # register namespace
    api.add_namespace(gold_api)
    
    # register controllers
    from api.gold import controllers

    # enable CORS for all origins (전체 허용)
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # 애플리케이션 시작 시 테이블 초기화
    initialize_tables()

    return app


def initialize_tables():
    """
    애플리케이션 시작 시 필요한 DynamoDB 테이블들을 초기화
    현재는 금 가격 서비스가 DynamoDB를 사용하지 않으므로 빈 함수
    """
    try:
        logger.info("애플리케이션 초기화 완료")
        
    except Exception as e:
        logger.error(f"애플리케이션 초기화 실패: {str(e)}")
