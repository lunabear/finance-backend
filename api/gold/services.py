import urllib.request
import urllib.parse
import re
from typing import Dict
from bs4 import BeautifulSoup
from datetime import datetime

from util.logging_util import logger
from exceptions import CoreException


class GoldPriceService:

    @staticmethod
    def crawl_gold_price() -> Dict:
        """
        네이버 금융에서 실시간 금 가격 정보를 크롤링합니다.
        
        Returns:
            Dict: 금 가격 정보
                - current_price: 현재 금 가격 (USD/Troy Ounce)
                - change_amount: 전일 대비 변동액
                - change_rate: 전일 대비 변동률 (%)
                - currency: 통화 단위 (USD)
                - last_updated: 마지막 업데이트 시간
                - market: 거래소 정보 (COMEX)
        """
        try:
            # 네이버 금융 금 시세 URL
            url = "https://finance.naver.com/marketindex/worldGoldDetail.naver?marketindexCd=CMDT_GC&fdtc=2"
            
            # User-Agent 헤더 설정 (브라우저로 위장)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # HTTP 요청 생성
            req = urllib.request.Request(url, headers=headers)
            
            # 웹페이지 요청 및 응답 받기
            with urllib.request.urlopen(req, timeout=10) as response:
                # 여러 인코딩 시도 (네이버는 주로 EUC-KR 사용)
                raw_html = response.read()
                html = None
                
                for encoding in ['euc-kr', 'utf-8', 'cp949']:
                    try:
                        html = raw_html.decode(encoding)
                        logger.info(f"Successfully decoded with {encoding}")
                        break
                    except UnicodeDecodeError:
                        continue
                
                if html is None:
                    # 모든 인코딩 실패시 에러 무시하고 디코딩
                    html = raw_html.decode('utf-8', errors='ignore')
                    logger.warning("Decoded with error ignoring")
            
            # BeautifulSoup으로 HTML 파싱
            soup = BeautifulSoup(html, 'html.parser')
            
            # 금 가격 정보 추출
            gold_data = {}
            
            # 현재 가격 추출 - 여러 방법으로 시도
            current_price = None
            
            # 방법 1: 특정 클래스로 찾기
            price_selectors = [
                'span.value',
                'em.no_up', 'em.no_down', 'em.no_cha',
                '.num', '.price', '.current'
            ]
            
            for selector in price_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    text = elem.get_text().strip()
                    # 3000대 금 가격 패턴 찾기
                    price_match = re.search(r'3[0-9]{3}\.[0-9]{2}', text.replace(',', ''))
                    if price_match:
                        current_price = float(price_match.group())
                        logger.info(f"Found gold price via selector {selector}: {current_price}")
                        break
                if current_price:
                    break
            
            # 방법 2: 정규식으로 HTML 전체에서 3000대 가격 패턴 찾기
            if not current_price:
                price_patterns = [
                    r'>([3][0-9]{3}\.[0-9]{2})<',  # >3378.00< 형태
                    r'([3][0-9]{3}\.[0-9]{2})\s*달러',  # 3378.00 달러 형태
                    r'([3][0-9]{3}\.[0-9]{2})\s*USD',  # 3378.00 USD 형태
                    r'([3][0-9]{3}\.[0-9]{2})',  # 단순 3378.00 형태
                ]
                
                for pattern in price_patterns:
                    matches = re.findall(pattern, html)
                    if matches:
                        current_price = float(matches[0])
                        logger.info(f"Found gold price via regex: {current_price}")
                        break
            
            gold_data['current_price'] = current_price
            
            # 변동액 추출 - 여러 방법으로 시도
            change_amount = 0.0
            
            # HTML에서 변동액 패턴 찾기
            change_patterns = [
                r'전일대비.*?([+-]?[0-9]+\.[0-9]+)',  # 전일대비 +4.60 형태
                r'([+-][0-9]+\.[0-9]+).*?달러',  # +4.60 달러 형태
                r'>([+-][0-9]+\.[0-9]+)<',  # >+4.60< 형태
                r'([+-]?[0-9]+\.[0-9]+)\s*\(',  # 4.60 ( 형태
            ]
            
            for pattern in change_patterns:
                matches = re.findall(pattern, html)
                if matches:
                    try:
                        change_amount = float(matches[0])
                        logger.info(f"Found change amount: {change_amount}")
                        break
                    except ValueError:
                        continue
            
            gold_data['change_amount'] = change_amount
            
            # 변동률 추출
            change_rate = 0.0
            rate_patterns = [
                r'([+-]?[0-9]+\.[0-9]+)%',  # 0.13% 형태
                r'\(\s*([+-]?[0-9]+\.[0-9]+)\s*%\s*\)',  # ( -0.13% ) 형태
            ]
            
            for pattern in rate_patterns:
                matches = re.findall(pattern, html)
                if matches:
                    try:
                        change_rate = float(matches[0])
                        logger.info(f"Found change rate: {change_rate}%")
                        break
                    except ValueError:
                        continue
            
            gold_data['change_rate'] = change_rate
            
            # 추가 정보 설정
            gold_data['currency'] = 'USD'
            gold_data['unit'] = 'Troy Ounce'
            gold_data['market'] = 'COMEX'
            gold_data['last_updated'] = datetime.now().isoformat()
            
            # 크롤링 성공 로그
            logger.info(f"Gold price crawling successful: {gold_data['current_price']} USD/oz")
            
            return gold_data
            
        except urllib.error.URLError as e:
            logger.error(f"URL Error during gold price crawling: {str(e)}")
            raise CoreException("네트워크 오류로 금 가격 조회에 실패했습니다", "NETWORK_ERROR")
        except urllib.error.HTTPError as e:
            logger.error(f"HTTP Error during gold price crawling: {str(e)}")
            raise CoreException("웹사이트 접근 오류로 금 가격 조회에 실패했습니다", "HTTP_ERROR")
        except Exception as e:
            logger.error(f"Unexpected error during gold price crawling: {str(e)}")
            raise CoreException("금 가격 크롤링 중 오류가 발생했습니다", "CRAWLING_ERROR")

    @staticmethod 
    def get_gold_price_info() -> Dict:
        """
        실시간 금 가격 정보를 조회하는 메인 함수입니다.
        
        Returns:
            Dict: API 응답 형식으로 포맷된 금 가격 정보
                - status: 'success' 또는 'error'
                - data: 금 가격 데이터 (성공시)
                - message: 응답 메시지
                - error_code: 오류 코드 (실패시)
        """
        try:
            raw_data = GoldPriceService.crawl_gold_price()
            
            # 데이터 포맷팅
            formatted_data = {
                'status': 'success',
                'data': {
                    'price': raw_data.get('current_price'),
                    'change': raw_data.get('change_amount'),
                    'change_rate': raw_data.get('change_rate'),
                    'currency': raw_data.get('currency'),
                    'unit': raw_data.get('unit'),
                    'market': raw_data.get('market'),
                    'updated_at': raw_data.get('last_updated')
                },
                'message': '금 가격 정보 조회 성공'
            }
            
            return formatted_data
            
        except CoreException as e:
            return {
                'status': 'error',
                'data': None,
                'message': e.message,
                'error_code': e.error_code
            }
        except Exception as e:
            logger.error(f"Error getting gold price info: {str(e)}")
            return {
                'status': 'error',
                'data': None,
                'message': '금 가격 정보 조회 중 오류가 발생했습니다',
                'error_code': 'UNKNOWN_ERROR'
            }

