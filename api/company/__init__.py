from flask_restx import Namespace

company_api = Namespace(name='company', path='/company', description='폐기물 관리 시스템 업체 관리 API')
