from flask import request
from flask_restx import Resource, fields
from pynamodb.exceptions import DoesNotExist

from api.company import company_api
from api.company.models import CompanyModel
from api.company.services import CompanyService
from util.logging_util import logger
from exceptions import CoreException, BadRequestException, EntityNotFoundException



company_response_model = company_api.model('CompanyResponse', {
    'company_id': fields.String(description='회사 ID'),
    'company_name': fields.String(description='회사명'),
    'company_type': fields.String(description='회사 유형')
})

# 금 가격 정보 응답 모델
gold_price_model = company_api.model('GoldPriceResponse', {
    'status': fields.String(description='응답 상태'),
    'data': fields.Raw(description='금 가격 데이터'),
    'message': fields.String(description='응답 메시지'),
    'error_code': fields.String(description='오류 코드')
})



@company_api.route('/gold-price')
class GoldPrice(Resource):
    @company_api.doc('get_gold_price')
    @company_api.marshal_with(gold_price_model)
    def get(self):
        """네이버 금융에서 현재 금 가격 정보 조회"""
        try:
            gold_info = CompanyService.get_gold_price_info()
            
            if gold_info['status'] == 'success':
                return gold_info, 200
            else:
                return gold_info, 400
                
        except Exception as e:
            logger.error(f"Unexpected error getting gold price: {str(e)}")
            return {
                'status': 'error',
                'data': None,
                'message': '금 가격 조회 중 예상치 못한 오류가 발생했습니다',
                'error_code': 'UNEXPECTED_ERROR'
            }, 500
