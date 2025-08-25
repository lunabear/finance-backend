from flask import request
from flask_restx import Resource, fields, reqparse

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

# 요청 파라미터 파서
price_parser = reqparse.RequestParser()
price_parser.add_argument('date', 
                         type=str, 
                         required=False, 
                         help='조회할 날짜 (YYYY-MM-DD 형식, 미입력시 실시간 데이터)',
                         location='args')



@gold_api.route('/price')
class GoldPrice(Resource):
    @gold_api.doc('get_gold_price')
    @gold_api.expect(price_parser)
    @gold_api.marshal_with(gold_price_model)
    def get(self):
        """네이버 금융에서 금 가격 정보를 조회합니다.
        
        파라미터:
        - date: 조회할 날짜 (YYYYMMDD 형식, 선택사항)
                미입력시 실시간 데이터를 조회합니다.
        """
       