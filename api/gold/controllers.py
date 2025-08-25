from flask import request
from flask_restx import Resource, fields

from api.gold import gold_api
from api.gold.services import GoldPriceService
from util.logging_util import logger


# 금 가격 정보 응답 모델
gold_price_model = gold_api.model('GoldPriceResponse', {
    'status': fields.String(description='응답 상태'),
    'data': fields.Raw(description='금 가격 데이터'),
    'message': fields.String(description='응답 메시지'),
    'error_code': fields.String(description='오류 코드')
})



@gold_api.route('/price')
class GoldPrice(Resource):
    @gold_api.doc('get_gold_price')
    @gold_api.marshal_with(gold_price_model)
    def get(self):
        """네이버 금융에서 실시간 금 가격 정보를 조회합니다."""
        try:
            gold_info = GoldPriceService.get_gold_price_info()
            
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
