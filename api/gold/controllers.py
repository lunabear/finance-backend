from flask import request
from flask_restx import Resource, fields, reqparse

from api.gold import gold_api
from api.gold.services import GoldPriceService
from util.logging_util import logger
from exceptions import CoreException


# 금 가격 정보 응답 모델
gold_price_model = gold_api.model('GoldPriceResponse', {
    'status': fields.String(description='응답 상태'),
    'data': fields.Raw(description='금 가격 데이터'),
    'message': fields.String(description='응답 메시지'),
    'error_code': fields.String(description='오류 코드')
})

# 일별 시세 응답 모델
daily_price_model = gold_api.model('DailyPriceData', {
    'date': fields.String(description='날짜'),
    'closing_price': fields.String(description='종가'),
    'change': fields.String(description='전일 대비'),
    'change_rate': fields.String(description='등락율')
})

# 전체 일별 시세 응답 모델
all_prices_model = gold_api.model('AllDailyPricesResponse', {
    'current_price': fields.String(description='현재가'),
    'daily_prices': fields.List(fields.Nested(daily_price_model), description='일별 시세 목록'),
    'total_count': fields.Integer(description='총 데이터 개수'),
    'last_updated': fields.String(description='마지막 업데이트 시간')
})

# 요청 파라미터 파서
price_parser = reqparse.RequestParser()
price_parser.add_argument('date', 
                         type=str, 
                         required=False, 
                         help='조회할 날짜 (YYYY-MM-DD 형식, 미입력시 전체 데이터)',
                         location='args')

# 날짜 범위 파라미터 파서
date_range_parser = reqparse.RequestParser()
date_range_parser.add_argument('start_date', 
                              type=str, 
                              required=True, 
                              help='시작 날짜 (YYYY-MM-DD 형식)',
                              location='args')
date_range_parser.add_argument('end_date', 
                              type=str, 
                              required=True, 
                              help='종료 날짜 (YYYY-MM-DD 형식)',
                              location='args')


@gold_api.route('/price')
class GoldPrice(Resource):
    @gold_api.doc('get_gold_price')
    @gold_api.expect(price_parser)
    @gold_api.marshal_with(gold_price_model)
    def get(self):
        """네이버 금융에서 금 가격 정보를 조회합니다.
        
        파라미터:
        - date: 조회할 날짜 (YYYY-MM-DD 형식, 선택사항)
                미입력시 전체 일별 시세 데이터를 조회합니다.
        """
        try:
            args = price_parser.parse_args()
            date = args.get('date')
            
            logger.info(f"금 가격 정보 조회 요청 - date: {date}")
            
            # 서비스 호출
            result = GoldPriceService.get_gold_price_info(date)
            
            return {
                'status': 'success',
                'data': result,
                'message': '금 가격 정보를 성공적으로 조회했습니다.',
                'error_code': None
            }
            
        except CoreException as e:
            logger.error(f"금 가격 조회 중 비즈니스 오류: {e.error_code} - {e.message}")
            return {
                'status': 'error',
                'data': None,
                'message': e.message,
                'error_code': e.error_code
            }, 400
            
        except Exception as e:
            logger.error(f"금 가격 조회 중 예상치 못한 오류: {str(e)}")
            return {
                'status': 'error',
                'data': None,
                'message': '서버 내부 오류가 발생했습니다.',
                'error_code': 'INTERNAL_SERVER_ERROR'
            }, 500


@gold_api.route('/price/daily')
class GoldDailyPrices(Resource):
    @gold_api.doc('get_all_daily_prices')
    @gold_api.marshal_with(gold_price_model)
    def get(self):
        """네이버 금융에서 전체 일별 금 시세 데이터를 조회합니다."""
        try:
            logger.info("전체 일별 금 시세 조회 요청")
            
            # 전체 일별 시세 조회
            result = GoldPriceService._get_all_daily_prices()
            
            return {
                'status': 'success',
                'data': result,
                'message': '전체 일별 금 시세를 성공적으로 조회했습니다.',
                'error_code': None
            }
            
        except CoreException as e:
            logger.error(f"전체 일별 시세 조회 중 비즈니스 오류: {e.error_code} - {e.message}")
            return {
                'status': 'error',
                'data': None,
                'message': e.message,
                'error_code': e.error_code
            }, 400
            
        except Exception as e:
            logger.error(f"전체 일별 시세 조회 중 예상치 못한 오류: {str(e)}")
            return {
                'status': 'error',
                'data': None,
                'message': '서버 내부 오류가 발생했습니다.',
                'error_code': 'INTERNAL_SERVER_ERROR'
            }, 500


@gold_api.route('/price/range')
class GoldPriceRange(Resource):
    @gold_api.doc('get_price_range')
    @gold_api.expect(date_range_parser)
    @gold_api.marshal_with(gold_price_model)
    def get(self):
        """지정된 날짜 범위의 금 시세 데이터를 조회합니다.
        
        파라미터:
        - start_date: 시작 날짜 (YYYY-MM-DD 형식, 필수)
        - end_date: 종료 날짜 (YYYY-MM-DD 형식, 필수)
        """
        try:
            args = date_range_parser.parse_args()
            start_date = args.get('start_date')
            end_date = args.get('end_date')
            
            logger.info(f"날짜 범위 금 시세 조회 요청 - start: {start_date}, end: {end_date}")
            
            # 날짜 범위 조회
            result = GoldPriceService.get_date_range_prices(start_date, end_date)
            
            return {
                'status': 'success',
                'data': result,
                'message': f'{start_date}부터 {end_date}까지의 금 시세를 성공적으로 조회했습니다.',
                'error_code': None
            }
            
        except CoreException as e:
            logger.error(f"날짜 범위 조회 중 비즈니스 오류: {e.error_code} - {e.message}")
            return {
                'status': 'error',
                'data': None,
                'message': e.message,
                'error_code': e.error_code
            }, 400
            
        except Exception as e:
            logger.error(f"날짜 범위 조회 중 예상치 못한 오류: {str(e)}")
            return {
                'status': 'error',
                'data': None,
                'message': '서버 내부 오류가 발생했습니다.',
                'error_code': 'INTERNAL_SERVER_ERROR'
            }, 500


@gold_api.route('/price/latest')
class GoldLatestPrice(Resource):
    @gold_api.doc('get_latest_price')
    @gold_api.marshal_with(gold_price_model)
    def get(self):
        """가장 최근 거래일의 금 시세 데이터를 조회합니다."""
        try:
            logger.info("최신 금 시세 조회 요청")
            
            # 전체 데이터를 가져온 후 첫 번째(최신) 데이터만 반환
            all_data = GoldPriceService._get_all_daily_prices()
            
            if all_data['daily_prices']:
                latest_price = all_data['daily_prices'][0]  # 첫 번째가 가장 최신
                result = {
                    'current_price': all_data['current_price'],
                    'latest_trading_day': latest_price,
                    'last_updated': all_data['last_updated']
                }
            else:
                raise CoreException("NO_DATA_FOUND", "최신 시세 데이터를 찾을 수 없습니다.")
            
            return {
                'status': 'success',
                'data': result,
                'message': '최신 금 시세를 성공적으로 조회했습니다.',
                'error_code': None
            }
            
        except CoreException as e:
            logger.error(f"최신 시세 조회 중 비즈니스 오류: {e.error_code} - {e.message}")
            return {
                'status': 'error',
                'data': None,
                'message': e.message,
                'error_code': e.error_code
            }, 400
            
        except Exception as e:
            logger.error(f"최신 시세 조회 중 예상치 못한 오류: {str(e)}")
            return {
                'status': 'error',
                'data': None,
                'message': '서버 내부 오류가 발생했습니다.',
                'error_code': 'INTERNAL_SERVER_ERROR'
            }, 500
       