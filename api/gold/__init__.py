from flask_restx import Namespace

gold_api = Namespace(name='gold', path='/gold', description='금 가격 정보 조회 API')
