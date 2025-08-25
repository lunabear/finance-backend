from flask import request
from flask_restx import Resource, fields, reqparse
from datetime import datetime

from api.gs import gs_api
from api.gs.services import GsStockService
from util.logging_util import logger
from exceptions import CoreException


# GS 종목 정보 응답 모델
gs_stock_model = gs_api.model('GsStockResponse', {
    'status': fields.String(description='응답 상태'),
    'data': fields.Raw(description='GS 종목 데이터'),
    'message': fields.String(description='응답 메시지'),
    'error_code': fields.String(description='오류 코드')
})

# 일별 시세 응답 모델
daily_price_model = gs_api.model('DailyPriceData', {
    'date': fields.String(description='날짜'),
    'closing_price': fields.String(description='종가'),
    'change_value': fields.String(description='전일비'),
    'direction': fields.String(description='등락 방향'),
    'open_price': fields.String(description='시가'),
    'high_price': fields.String(description='고가'),
    'low_price': fields.String(description='저가'),
    'volume': fields.String(description='거래량')
})

# 실시간 데이터 모델
realtime_data_model = gs_api.model('RealtimeData', {
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
all_prices_model = gs_api.model('AllDailyPricesResponse', {
    'stock_code': fields.String(description='종목코드'),
    'stock_name': fields.String(description='종목명'),
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

# 페이지네이션 파라미터 파서
pagination_parser = reqparse.RequestParser()
pagination_parser.add_argument('page', 
                              type=int, 
                              required=False, 
                              default=1,
                              help='페이지 번호 (기본값: 1)',
                              location='args')


@gs_api.route('/price')
class GsStockResource(Resource):
    @gs_api.expect(price_parser)
    @gs_api.marshal_with(gs_stock_model)
    @gs_api.doc('get_gs_stock')
    @gs_api.doc(description='GS 종목 정보를 조회합니다.')
    def get(self):
        """GS 종목 정보 조회"""
        try:
            args = price_parser.parse_args()
            date = args.get('date')
            
            # GS 종목 정보 조회
            stock_info = GsStockService.get_gs_stock_info(date)
            
            logger.info(f"GS 종목 정보 조회 완료 - 날짜: {date or '전체'}")
            
            return {
                'status': 'success',
                'message': 'GS 종목 정보를 성공적으로 조회했습니다.',
                'data': stock_info,
                'error_code': None
            }
            
        except CoreException as e:
            logger.error(f"GS 종목 조회 중 오류: {e.message}")
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


@gs_api.route('/stock/range')
class GsStockRangeResource(Resource):
    @gs_api.expect(date_range_parser)
    @gs_api.marshal_with(gs_stock_model)
    @gs_api.doc('get_gs_stock_range')
    @gs_api.doc(description='날짜 범위의 GS 종목 정보를 조회합니다.')
    def get(self):
        """날짜 범위 GS 종목 정보 조회"""
        try:
            args = date_range_parser.parse_args()
            start_date = args.get('start_date')
            end_date = args.get('end_date')
            
            # 날짜 범위 GS 종목 정보 조회
            stock_info = GsStockService.get_date_range_prices(start_date, end_date)
            
            logger.info(f"GS 종목 날짜 범위 조회 완료 - {start_date} ~ {end_date}")
            
            return {
                'status': 'success',
                'message': f'GS 종목 정보를 성공적으로 조회했습니다. ({start_date} ~ {end_date})',
                'data': stock_info,
                'error_code': None
            }
            
        except CoreException as e:
            logger.error(f"GS 종목 날짜 범위 조회 중 오류: {e.message}")
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


@gs_api.route('/stock/realtime')
class GsStockRealtimeResource(Resource):
    @gs_api.marshal_with(gs_stock_model)
    @gs_api.doc('get_gs_stock_realtime')
    @gs_api.doc(description='실시간 GS 종목 정보를 조회합니다.')
    def get(self):
        """실시간 GS 종목 정보 조회"""
        try:
            # 실시간 GS 종목 정보 조회
            stock_info = GsStockService.get_realtime_price()
            
            logger.info("실시간 GS 종목 정보 조회 완료")
            
            return {
                'status': 'success',
                'message': '실시간 GS 종목 정보를 성공적으로 조회했습니다.',
                'data': stock_info,
                'error_code': None
            }
            
        except CoreException as e:
            logger.error(f"실시간 GS 종목 조회 중 오류: {e.message}")
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


@gs_api.route('/health')
class GsHealthResource(Resource):
    @gs_api.marshal_with(gs_stock_model)
    @gs_api.doc('gs_health_check')
    @gs_api.doc(description='GS API 서비스 상태를 확인합니다.')
    def get(self):
        """GS API 헬스체크"""
        try:
            # 간단한 실시간 데이터 조회로 서비스 상태 확인
            GsStockService.get_realtime_price()
            
            return {
                'status': 'success',
                'message': 'GS API 서비스가 정상적으로 작동하고 있습니다.',
                'data': {
                    "status": "healthy",
                    "service": "GS Stock API",
                    "stock_code": "078930",
                    "stock_name": "GS",
                    "timestamp": datetime.now().isoformat()
                },
                'error_code': None
            }
            
        except Exception as e:
            logger.error(f"GS API 헬스체크 실패: {str(e)}")
            return {
                'status': 'error',
                'message': 'GS API 서비스에 문제가 있습니다.',
                'data': {
                    "status": "unhealthy",
                    "service": "GS Stock API",
                    "stock_code": "078930",
                    "stock_name": "GS",
                    "error": str(e)
                },
                'error_code': 'SERVICE_UNHEALTHY'
            }, 503


@gs_api.route('/info')
class GsInfoResource(Resource):
    @gs_api.marshal_with(gs_stock_model)
    @gs_api.doc('get_gs_info')
    @gs_api.doc(description='GS 종목 기본 정보를 조회합니다.')
    def get(self):
        """GS 종목 기본 정보 조회"""
        try:
            return {
                'status': 'success',
                'message': 'GS 종목 기본 정보입니다.',
                'data': {
                    "stock_code": GsStockService.STOCK_CODE,
                    "stock_name": GsStockService.STOCK_NAME,
                    "company_name": "GS",
                    "market": "KOSPI",
                    "api_endpoints": {
                        "all_prices": "/api/gs/stock",
                        "specific_date": "/api/gs/stock?date=YYYY-MM-DD",
                        "date_range": "/api/gs/stock/range?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD",
                        "realtime": "/api/gs/stock/realtime",
                        "pagination": "/api/gs/stock/pages?page=1",
                        "health": "/api/gs/health"
                    },
                    "data_source": f"https://finance.naver.com/item/sise_day.naver?code={GsStockService.STOCK_CODE}",
                    "last_updated": datetime.now().isoformat()
                },
                'error_code': None
            }
            
        except Exception as e:
            logger.error(f"GS 종목 정보 조회 중 오류: {str(e)}")
            return {
                'status': 'error',
                'message': '서버 내부 오류가 발생했습니다.',
                'data': None,
                'error_code': 'INTERNAL_SERVER_ERROR'
            }, 500
