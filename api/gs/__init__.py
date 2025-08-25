from flask_restx import Namespace

gs_api = Namespace(name='gs', path='/gs', description='GS 종목 정보 조회 API')
