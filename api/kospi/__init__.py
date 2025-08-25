from flask_restx import Namespace

kospi_api = Namespace(name='kospi', path='/kospi', description='KOSPI 지수 정보 조회 API')
