from flask import request
from flask_restx import Resource, fields, reqparse

from api.kospi import kospi_api
from api.kospi.services import KospiPriceService
from util.logging_util import logger
from exceptions import CoreException


# KOSPI 가격 정보 응답 모델
kospi_price_model = kospi_api.model('KospiPriceResponse', {
    'status': fields.String(description='응답 상태'),
    'data': fields.Raw(description='KOSPI 가격 데이터'),
    'message': fields.String(description='응답 메시지'),
    'error_code': fields.String(description='오류 코드')
})

# 일별 시세 응답 모델
daily_price_model = kospi_api.model('DailyPriceData', {
    'date': fields.String(description='날짜'),
    'closing_price': fields.String(description='종가'),
    'change_value': fields.String(description='전일비'),
    'change_rate': fields.String(description='등락률'),
    'direction': fields.String(description='등락 방향'),
    'volume': fields.String(description='거래량'),
    'trading_value': fields.String(description='거래대금')
})

# 실시간 데이터 모델
realtime_data_model = kospi_api.model('RealtimeData', {
    'current_price': fields.String(description='현재가'),
    'change_value': fields.String(description='전일비'),
    'change_rate': fields.String(description='등락률'),
    'direction': fields.String(description='등락 방향'),
    'open_price': fields.String(description='시가'),
    'high_price': fields.String(description='고가'),
    'low_price': fields.String(description='저가'),
    'volume': fields.String(description='거래량'),
    'trading_value': fields.String(description='거래대금'),
    'market_status': fields.String(description='장 상태')
})

# 전체 일별 시세 응답 모델
all_prices_model = kospi_api.model('AllDailyPricesResponse', {
    'current_price_info': fields.Nested(realtime_data_model, description='현재가 정보'),
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


@kospi_api.route('/price')
class KospiPriceResource(Resource):
    @kospi_api.expect(price_parser)
    @kospi_api.marshal_with(kospi_price_model)
    @kospi_api.doc('get_kospi_price')
    @kospi_api.doc(description='KOSPI 가격 정보를 조회합니다.')
    def get(self):
        """KOSPI 가격 정보 조회"""
        try:
            args = price_parser.parse_args()
            date = args.get('date')
            
            # KOSPI 가격 정보 조회
            price_info = KospiPriceService.get_kospi_price_info(date)
            
            logger.info(f"KOSPI 가격 정보 조회 완료 - 날짜: {date or '전체'}")
            
            return {
                'status': 'success',
                'message': 'KOSPI 가격 정보를 성공적으로 조회했습니다.',
                'data': price_info,
                'error_code': None
            }
            
        except CoreException as e:
            logger.error(f"KOSPI 가격 조회 중 오류: {e.message}")
            return {
                'status': 'error',
                'message': e.message,
                'data': None,
                'error_code': e.error_code
            }, 500
        except Exception as e:
            logger.error(f"예상치 못한 오류 발생: {str(e)}")
            return {
                'status': 'error',
                'message': '서버 내부 오류가 발생했습니다.',
                'data': None,
                'error_code': 'INTERNAL_SERVER_ERROR'
            }, 500


@kospi_api.route('/price/range')
class KospiPriceRangeResource(Resource):
    @kospi_api.expect(date_range_parser)
    @kospi_api.marshal_with(kospi_price_model)
    @kospi_api.doc('get_kospi_price_range')
    @kospi_api.doc(description='날짜 범위의 KOSPI 가격 정보를 조회합니다.')
    def get(self):
        """날짜 범위 KOSPI 가격 정보 조회"""
        try:
            args = date_range_parser.parse_args()
            start_date = args.get('start_date')
            end_date = args.get('end_date')
            
            # 날짜 범위 KOSPI 가격 정보 조회
            price_info = KospiPriceService.get_date_range_prices(start_date, end_date)
            
            logger.info(f"KOSPI 날짜 범위 조회 완료 - {start_date} ~ {end_date}")
            
            return {
                'status': 'success',
                'message': f'KOSPI 가격 정보를 성공적으로 조회했습니다. ({start_date} ~ {end_date})',
                'data': price_info,
                'error_code': None
            }
            
        except CoreException as e:
            logger.error(f"KOSPI 날짜 범위 조회 중 오류: {e.message}")
            return {
                'status': 'error',
                'message': e.message,
                'data': None,
                'error_code': e.error_code
            }, 500
        except Exception as e:
            logger.error(f"예상치 못한 오류 발생: {str(e)}")
            return {
                'status': 'error',
                'message': '서버 내부 오류가 발생했습니다.',
                'data': None,
                'error_code': 'INTERNAL_SERVER_ERROR'
            }, 500


@kospi_api.route('/price/realtime')
class KospiRealtimePriceResource(Resource):
    @kospi_api.marshal_with(kospi_price_model)
    @kospi_api.doc('get_kospi_realtime_price')
    @kospi_api.doc(description='실시간 KOSPI 가격 정보를 조회합니다.')
    def get(self):
        """실시간 KOSPI 가격 정보 조회"""
        try:
            # 실시간 KOSPI 가격 정보 조회
            price_info = KospiPriceService.get_realtime_price()
            
            logger.info("실시간 KOSPI 가격 정보 조회 완료")
            
            return {
                'status': 'success',
                'message': '실시간 KOSPI 가격 정보를 성공적으로 조회했습니다.',
                'data': price_info,
                'error_code': None
            }
            
        except CoreException as e:
            logger.error(f"실시간 KOSPI 가격 조회 중 오류: {e.message}")
            return {
                'status': 'error',
                'message': e.message,
                'data': None,
                'error_code': e.error_code
            }, 500
        except Exception as e:
            logger.error(f"예상치 못한 오류 발생: {str(e)}")
            return {
                'status': 'error',
                'message': '서버 내부 오류가 발생했습니다.',
                'data': None,
                'error_code': 'INTERNAL_SERVER_ERROR'
            }, 500


@kospi_api.route('/health')
class KospiHealthResource(Resource):
    @kospi_api.marshal_with(kospi_price_model)
    @kospi_api.doc('kospi_health_check')
    @kospi_api.doc(description='KOSPI API 서비스 상태를 확인합니다.')
    def get(self):
        """KOSPI API 헬스체크"""
        try:
            # 간단한 실시간 데이터 조회로 서비스 상태 확인
            KospiPriceService.get_realtime_price()
            
            return {
                'status': 'success',
                'message': 'KOSPI API 서비스가 정상적으로 작동하고 있습니다.',
                'data': {
                    "status": "healthy",
                    "service": "KOSPI Price API",
                    "timestamp": "2025-08-25T16:30:00"
                },
                'error_code': None
            }
            
        except Exception as e:
            logger.error(f"KOSPI API 헬스체크 실패: {str(e)}")
            return {
                'status': 'error',
                'message': 'KOSPI API 서비스에 문제가 있습니다.',
                'data': {
                    "status": "unhealthy",
                    "service": "KOSPI Price API",
                    "error": str(e)
                },
                'error_code': 'SERVICE_UNHEALTHY'
            }, 503