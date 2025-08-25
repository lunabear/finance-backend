import os

from flask import Flask
from flask_cors import CORS
from flask_restx import Api
from werkzeug.utils import import_string

from api.company import company_api
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
              title='waste-admin',
              version='1.0',
              description='폐기물 관리 시스템 백엔드 API')

    config_name = os.getenv('WASTE_ADMIN_ENV', 'local')
    print(f'config_env:{config_name}')
    config_object = import_string(config_by_name[config_name])()
    app.config.from_object(config_object)

    # waste admin logger 설정
    logger.set_default_logger_level(app.name, app.config['LOG_LEVEL'])

    # jwt
    jwt.init_app(app)
    
    # register namespace
    api.add_namespace(company_api)
    
    # register controllers
    from api.company import controllers

    # enable CORS for all origins (전체 허용)
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # 애플리케이션 시작 시 테이블 초기화
    initialize_tables()

    return app


def initialize_tables():
    """
    애플리케이션 시작 시 필요한 DynamoDB 테이블들을 초기화
    """
    try:
        from api.company.services import CompanyService
        logger.info("Initializing database tables...")
        
        # Company 테이블 초기화
        CompanyService.create_table_if_not_exists()
        
        # User 테이블 초기화
        logger.info("Database tables initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {str(e)}")
        # 테이블 생성 실패가 애플리케이션 시작을 막지 않도록 함
        # 실제 운영 환경에서는 이 부분을 더 엄격하게 처리할 수 있음
