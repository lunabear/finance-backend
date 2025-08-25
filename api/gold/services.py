import urllib.request
import urllib.parse
import re
import requests
from typing import Dict, Optional, List
from bs4 import BeautifulSoup
from datetime import datetime, date

from util.logging_util import logger
from exceptions import CoreException


class GoldPriceService:
    BASE_URL = "https://finance.naver.com/marketindex/worldGoldDetail.naver"
    
    @staticmethod
    def get_gold_price_info(date: Optional[str] = None) -> Dict:
        """
        네이버 금융에서 금 가격 정보를 조회합니다.
        
        Args:
            date: 조회할 날짜 (YYYY-MM-DD 형식, 선택사항)
                미입력시 실시간 데이터를 조회합니다.
        
        Returns:
            Dict: 금 가격 정보
        """
        try:
            if date:
                # 특정 날짜 조회
                return GoldPriceService._get_gold_price_by_date(date)
            else:
                # 전체 일별 시세 조회
                return GoldPriceService._get_all_daily_prices()
        except Exception as e:
            logger.error(f"금 가격 정보 조회 중 오류 발생: {str(e)}")
            raise CoreException("GOLD_PRICE_FETCH_ERROR", f"금 가격 정보를 가져올 수 없습니다: {str(e)}")
    
    @staticmethod
    def _get_all_daily_prices() -> Dict:
        """
        네이버 금융에서 전체 일별 금 시세를 크롤링합니다.
        
        Returns:
            Dict: 전체 일별 시세 데이터
        """
        try:
            # 일별 시세 데이터는 별도 URL에서 가져옴
            daily_quote_url = "https://finance.naver.com/marketindex/worldDailyQuote.naver?marketindexCd=CMDT_GC&fdtc=2&page=1"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # 일별 시세 데이터 크롤링
            response = requests.get(daily_quote_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 일별 시세 테이블 찾기 - 더 정확한 셀렉터 사용
            daily_prices = []
            
            # 테이블의 tbody에서 데이터 행들을 찾기
            table = soup.find('table')
            if table:
                # 헤더 행을 제외한 데이터 행들
                rows = table.find_all('tr')[1:]  # 첫 번째 행(헤더) 제외
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        try:
                            date_text = cells[0].get_text(strip=True)
                            closing_price = cells[1].get_text(strip=True)
                            change_cell = cells[2].get_text(strip=True)
                            change_rate = cells[3].get_text(strip=True)
                            
                            # 날짜 형식 확인 (YYYY.MM.DD 형식)
                            if re.match(r'\d{4}\.\d{2}\.\d{2}', date_text):
                                daily_prices.append({
                                    'date': date_text,
                                    'closing_price': closing_price,
                                    'change': change_cell,
                                    'change_rate': change_rate
                                })
                        except (IndexError, ValueError) as e:
                            logger.warning(f"테이블 행 파싱 중 오류: {str(e)}")
                            continue
            
            # 현재가 정보는 메인 페이지에서 가져오기
            current_price = GoldPriceService._get_current_price()
            
            return {
                'current_price': current_price,
                'daily_prices': daily_prices,
                'last_updated': datetime.now().isoformat(),
                'total_count': len(daily_prices)
            }
            
        except requests.RequestException as e:
            logger.error(f"네이버 금융 페이지 요청 중 오류: {str(e)}")
            raise CoreException("NETWORK_ERROR", f"네트워크 오류가 발생했습니다: {str(e)}")
        except Exception as e:
            logger.error(f"금 시세 크롤링 중 오류: {str(e)}")
            raise CoreException("CRAWLING_ERROR", f"데이터 파싱 중 오류가 발생했습니다: {str(e)}")
    
    @staticmethod
    def _get_current_price() -> str:
        """
        네이버 금융 메인 페이지에서 현재가 정보를 가져옵니다.
        
        Returns:
            str: 현재가
        """
        try:
            url = f"{GoldPriceService.BASE_URL}?marketindexCd=CMDT_GC&fdtc=2"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 현재가 찾기 - 여러 셀렉터 시도
            current_price_selectors = [
                '.num',
                '.blind em',
                'em.num',
                'span.num',
                'strong em'
            ]
            
            current_price = "N/A"
            for selector in current_price_selectors:
                element = soup.select_one(selector)
                if element:
                    price_text = element.get_text(strip=True)
                    # 숫자와 콤마, 점이 포함된 가격 패턴 확인
                    if re.match(r'[\d,]+\.?\d*', price_text):
                        current_price = price_text
                        break
                        
            # 현재가를 찾지 못한 경우 페이지 전체에서 금액 패턴 검색
            if current_price == "N/A":
                text_content = soup.get_text()
                # 3,000대 숫자 패턴 검색 (금 시세는 보통 3,000대)
                price_match = re.search(r'3,\d{3}\.\d{2}', text_content)
                if price_match:
                    current_price = price_match.group()
                    
            return current_price
            
        except Exception as e:
            logger.warning(f"현재가 조회 중 오류: {str(e)}")
            return "N/A"
    
    @staticmethod
    def _get_gold_price_by_date(target_date: str) -> Dict:
        """
        특정 날짜의 금 시세를 조회합니다.
        
        Args:
            target_date: 조회할 날짜 (YYYY-MM-DD 형식)
        
        Returns:
            Dict: 해당 날짜의 금 시세 정보
        """
        try:
            # 날짜 형식 검증
            datetime.strptime(target_date, '%Y-%m-%d')
            
            # 전체 데이터를 가져온 후 해당 날짜 필터링
            all_data = GoldPriceService._get_all_daily_prices()
            
            # 날짜 형식 변환 (YYYY-MM-DD -> YYYY.MM.DD)
            target_date_formatted = target_date.replace('-', '.')
            
            # 해당 날짜 데이터 찾기
            for price_data in all_data['daily_prices']:
                if price_data['date'] == target_date_formatted:
                    return {
                        'date': price_data['date'],
                        'closing_price': price_data['closing_price'],
                        'change': price_data['change'],
                        'change_rate': price_data['change_rate'],
                        'last_updated': datetime.now().isoformat()
                    }
            
            # 해당 날짜 데이터가 없는 경우
            raise CoreException("DATE_NOT_FOUND", f"해당 날짜({target_date})의 데이터를 찾을 수 없습니다.")
            
        except ValueError:
            raise CoreException("INVALID_DATE_FORMAT", "날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식으로 입력해주세요.")
        except CoreException:
            raise
        except Exception as e:
            logger.error(f"특정 날짜 금 시세 조회 중 오류: {str(e)}")
            raise CoreException("DATE_QUERY_ERROR", f"날짜별 조회 중 오류가 발생했습니다: {str(e)}")
    
    @staticmethod
    def get_date_range_prices(start_date: str, end_date: str) -> Dict:
        """
        날짜 범위의 금 시세를 조회합니다.
        
        Args:
            start_date: 시작 날짜 (YYYY-MM-DD 형식)
            end_date: 종료 날짜 (YYYY-MM-DD 형식)
        
        Returns:
            Dict: 날짜 범위의 금 시세 정보
        """
        try:
            # 날짜 형식 검증
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            if start_dt > end_dt:
                raise CoreException("INVALID_DATE_RANGE", "시작 날짜가 종료 날짜보다 늦을 수 없습니다.")
            
            # 전체 데이터 가져오기
            all_data = GoldPriceService._get_all_daily_prices()
            
            # 날짜 범위 필터링
            filtered_prices = []
            for price_data in all_data['daily_prices']:
                try:
                    price_date = datetime.strptime(price_data['date'], '%Y.%m.%d')
                    if start_dt <= price_date <= end_dt:
                        filtered_prices.append(price_data)
                except ValueError:
                    continue
            
            return {
                'start_date': start_date,
                'end_date': end_date,
                'daily_prices': filtered_prices,
                'total_count': len(filtered_prices),
                'last_updated': datetime.now().isoformat()
            }
            
        except ValueError:
            raise CoreException("INVALID_DATE_FORMAT", "날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식으로 입력해주세요.")
        except CoreException:
            raise
        except Exception as e:
            logger.error(f"날짜 범위 금 시세 조회 중 오류: {str(e)}")
            raise CoreException("DATE_RANGE_QUERY_ERROR", f"날짜 범위 조회 중 오류가 발생했습니다: {str(e)}")
        