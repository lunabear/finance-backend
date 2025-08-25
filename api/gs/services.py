import urllib.request
import urllib.parse
import re
import requests
from typing import Dict, Optional, List
from bs4 import BeautifulSoup
from datetime import datetime, date

from util.logging_util import logger
from exceptions import CoreException


class GsStockService:
    STOCK_CODE = "078930"
    STOCK_NAME = "GS"
    BASE_URL = f"https://finance.naver.com/item/sise_day.naver?code={STOCK_CODE}"
    REALTIME_URL = f"https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:{STOCK_CODE}"
    
    @staticmethod
    def get_gs_stock_info(date: Optional[str] = None) -> Dict:
        """
        네이버 금융에서 GS 종목 정보를 조회합니다.
        
        Args:
            date: 조회할 날짜 (YYYY-MM-DD 형식, 선택사항)
                미입력시 전체 일별 시세를 조회합니다.
        
        Returns:
            Dict: GS 종목 정보
        """
        try:
            if date:
                # 특정 날짜 조회
                return GsStockService._get_gs_stock_by_date(date)
            else:
                # 전체 일별 시세 조회
                return GsStockService._get_all_daily_prices()
        except Exception as e:
            logger.error(f"GS 종목 정보 조회 중 오류 발생: {str(e)}")
            raise CoreException("GS_STOCK_FETCH_ERROR", f"GS 종목 정보를 가져올 수 없습니다: {str(e)}")
    
    @staticmethod
    def _get_all_daily_prices() -> Dict:
        """
        네이버 금융에서 GS 종목의 전체 일별 시세를 크롤링합니다.
        
        Returns:
            Dict: 전체 일별 시세 데이터
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # 일별 시세 데이터 크롤링
            response = requests.get(GsStockService.BASE_URL, headers=headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'euc-kr'  # 네이버 금융은 euc-kr 인코딩 사용
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 일별 시세 테이블 찾기
            daily_prices = []
            
            # 테이블에서 데이터 행들을 찾기
            table = soup.find('table')
            if table:
                # 헤더 행을 제외한 데이터 행들
                rows = table.find_all('tr')
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 7:  # 날짜, 종가, 전일비, 시가, 고가, 저가, 거래량
                        try:
                            date_text = cells[0].get_text(strip=True)
                            closing_price = cells[1].get_text(strip=True).replace(',', '')
                            change_text = cells[2].get_text(strip=True)
                            open_price = cells[3].get_text(strip=True).replace(',', '')
                            high_price = cells[4].get_text(strip=True).replace(',', '')
                            low_price = cells[5].get_text(strip=True).replace(',', '')
                            volume = cells[6].get_text(strip=True).replace(',', '')
                            
                            # 날짜 형식 확인 (YYYY.MM.DD 형식)
                            if re.match(r'\d{4}\.\d{2}\.\d{2}', date_text):
                                # 전일비에서 숫자만 추출
                                change_match = re.search(r'[\d,.]+', change_text)
                                change_value = change_match.group() if change_match else "0"
                                
                                # 등락 방향 판단
                                direction = "상승" if "상승" in change_text or "up" in str(row) else "하락" if "하락" in change_text or "down" in str(row) else "보합"
                                
                                daily_prices.append({
                                    'date': date_text,
                                    'closing_price': closing_price,
                                    'change_value': change_value.replace(',', ''),
                                    'direction': direction,
                                    'open_price': open_price,
                                    'high_price': high_price,
                                    'low_price': low_price,
                                    'volume': volume
                                })
                        except (IndexError, ValueError, AttributeError) as e:
                            logger.warning(f"테이블 행 파싱 중 오류: {str(e)}")
                            continue
            
            # 현재가 정보는 실시간 API에서 가져오기
            current_price_info = GsStockService._get_current_price()
            
            return {
                'stock_code': GsStockService.STOCK_CODE,
                'stock_name': GsStockService.STOCK_NAME,
                'current_price_info': current_price_info,
                'daily_prices': daily_prices,
                'last_updated': datetime.now().isoformat(),
                'total_count': len(daily_prices)
            }
            
        except requests.RequestException as e:
            logger.error(f"네이버 금융 페이지 요청 중 오류: {str(e)}")
            raise CoreException("NETWORK_ERROR", f"네트워크 오류가 발생했습니다: {str(e)}")
        except Exception as e:
            logger.error(f"GS 종목 시세 크롤링 중 오류: {str(e)}")
            raise CoreException("CRAWLING_ERROR", f"데이터 파싱 중 오류가 발생했습니다: {str(e)}")
    
    @staticmethod
    def _get_current_price() -> Dict:
        """
        실시간 API에서 GS 종목 현재가 정보를 가져옵니다.
        
        Returns:
            Dict: 현재가 정보
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(GsStockService.REALTIME_URL, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('resultCode') == 'success' and data.get('result'):
                areas = data['result'].get('areas', [])
                if areas and len(areas) > 0:
                    datas = areas[0].get('datas', [])
                    if datas and len(datas) > 0:
                        gs_data = datas[0]
                        
                        # 값들을 적절히 포맷팅
                        current_price = gs_data.get('nv', 0)
                        change_value = gs_data.get('cv', 0)
                        change_rate = gs_data.get('cr', 0)
                        
                        # 등락 방향 판단 (rf: 1=상승, 2=상승, 3=보합, 4=하락, 5=하락)
                        direction_map = {"1": "상승", "2": "상승", "3": "보합", "4": "하락", "5": "하락"}
                        direction = direction_map.get(str(gs_data.get('rf', 3)), "보합")
                        
                        return {
                            'current_price': str(current_price),
                            'change_value': str(change_value),
                            'change_rate': f"{change_rate:.2f}%",
                            'direction': direction,
                            'open_price': str(gs_data.get('ov', 0)),
                            'high_price': str(gs_data.get('hv', 0)),
                            'low_price': str(gs_data.get('lv', 0)),
                            'volume': str(gs_data.get('aq', 0)),
                            'trading_value': str(gs_data.get('aa', 0)),
                            'market_status': gs_data.get('ms', 'UNKNOWN')
                        }
            
            return {
                'current_price': "N/A",
                'change_value': "N/A",
                'change_rate': "N/A",
                'direction': "N/A"
            }
                
        except Exception as e:
            logger.warning(f"현재가 조회 중 오류: {str(e)}")
            return {
                'current_price': "N/A",
                'change_value': "N/A", 
                'change_rate': "N/A",
                'direction': "N/A"
            }
    
    @staticmethod
    def _get_gs_stock_by_date(target_date: str) -> Dict:
        """
        특정 날짜의 GS 종목 시세를 조회합니다.
        
        Args:
            target_date: 조회할 날짜 (YYYY-MM-DD 형식)
        
        Returns:
            Dict: 해당 날짜의 GS 종목 시세 정보
        """
        try:
            # 날짜 형식 검증
            datetime.strptime(target_date, '%Y-%m-%d')
            
            # 전체 데이터를 가져온 후 해당 날짜 필터링
            all_data = GsStockService._get_all_daily_prices()
            
            # 날짜 형식 변환 (YYYY-MM-DD -> YYYY.MM.DD)
            target_date_formatted = target_date.replace('-', '.')
            
            # 해당 날짜 데이터 찾기
            for price_data in all_data['daily_prices']:
                if price_data['date'] == target_date_formatted:
                    return {
                        'stock_code': GsStockService.STOCK_CODE,
                        'stock_name': GsStockService.STOCK_NAME,
                        'date': price_data['date'],
                        'closing_price': price_data['closing_price'],
                        'change_value': price_data['change_value'],
                        'direction': price_data['direction'],
                        'open_price': price_data['open_price'],
                        'high_price': price_data['high_price'],
                        'low_price': price_data['low_price'],
                        'volume': price_data['volume'],
                        'last_updated': datetime.now().isoformat()
                    }
            
            # 해당 날짜 데이터가 없는 경우
            raise CoreException("DATE_NOT_FOUND", f"해당 날짜({target_date})의 데이터를 찾을 수 없습니다.")
            
        except ValueError:
            raise CoreException("INVALID_DATE_FORMAT", "날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식으로 입력해주세요.")
        except CoreException:
            raise
        except Exception as e:
            logger.error(f"특정 날짜 GS 종목 시세 조회 중 오류: {str(e)}")
            raise CoreException("DATE_QUERY_ERROR", f"날짜별 조회 중 오류가 발생했습니다: {str(e)}")
    
    @staticmethod
    def get_date_range_prices(start_date: str, end_date: str) -> Dict:
        """
        날짜 범위의 GS 종목 시세를 조회합니다.
        
        Args:
            start_date: 시작 날짜 (YYYY-MM-DD 형식)
            end_date: 종료 날짜 (YYYY-MM-DD 형식)
        
        Returns:
            Dict: 날짜 범위의 GS 종목 시세 정보
        """
        try:
            # 날짜 형식 검증
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            if start_dt > end_dt:
                raise CoreException("INVALID_DATE_RANGE", "시작 날짜가 종료 날짜보다 늦을 수 없습니다.")
            
            # 전체 데이터 가져오기
            all_data = GsStockService._get_all_daily_prices()
            
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
                'stock_code': GsStockService.STOCK_CODE,
                'stock_name': GsStockService.STOCK_NAME,
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
            logger.error(f"날짜 범위 GS 종목 시세 조회 중 오류: {str(e)}")
            raise CoreException("DATE_RANGE_QUERY_ERROR", f"날짜 범위 조회 중 오류가 발생했습니다: {str(e)}")
    
    @staticmethod
    def get_realtime_price() -> Dict:
        """
        실시간 GS 종목 가격 정보만 조회합니다.
        
        Returns:
            Dict: 실시간 GS 종목 가격 정보
        """
        try:
            current_price_info = GsStockService._get_current_price()
            return {
                'stock_code': GsStockService.STOCK_CODE,
                'stock_name': GsStockService.STOCK_NAME,
                'realtime_data': current_price_info,
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"실시간 GS 종목 가격 조회 중 오류: {str(e)}")
            raise CoreException("REALTIME_FETCH_ERROR", f"실시간 가격 정보를 가져올 수 없습니다: {str(e)}")
    
    @staticmethod
    def get_paginated_prices(page: int = 1) -> Dict:
        """
        페이지별 GS 종목 시세를 조회합니다.
        
        Args:
            page: 페이지 번호 (기본값: 1)
        
        Returns:
            Dict: 해당 페이지의 GS 종목 시세 정보
        """
        try:
            url = f"{GsStockService.BASE_URL}&page={page}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'euc-kr'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 페이지별 시세 데이터 파싱
            daily_prices = []
            table = soup.find('table')
            
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 7:
                        try:
                            date_text = cells[0].get_text(strip=True)
                            
                            if re.match(r'\d{4}\.\d{2}\.\d{2}', date_text):
                                closing_price = cells[1].get_text(strip=True).replace(',', '')
                                change_text = cells[2].get_text(strip=True)
                                open_price = cells[3].get_text(strip=True).replace(',', '')
                                high_price = cells[4].get_text(strip=True).replace(',', '')
                                low_price = cells[5].get_text(strip=True).replace(',', '')
                                volume = cells[6].get_text(strip=True).replace(',', '')
                                
                                # 전일비에서 숫자만 추출
                                change_match = re.search(r'[\d,.]+', change_text)
                                change_value = change_match.group() if change_match else "0"
                                
                                # 등락 방향 판단
                                direction = "상승" if "상승" in change_text else "하락" if "하락" in change_text else "보합"
                                
                                daily_prices.append({
                                    'date': date_text,
                                    'closing_price': closing_price,
                                    'change_value': change_value.replace(',', ''),
                                    'direction': direction,
                                    'open_price': open_price,
                                    'high_price': high_price,
                                    'low_price': low_price,
                                    'volume': volume
                                })
                        except Exception as e:
                            logger.warning(f"행 파싱 중 오류: {str(e)}")
                            continue
            
            return {
                'stock_code': GsStockService.STOCK_CODE,
                'stock_name': GsStockService.STOCK_NAME,
                'page': page,
                'daily_prices': daily_prices,
                'total_count': len(daily_prices),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"페이지별 GS 종목 시세 조회 중 오류: {str(e)}")
            raise CoreException("PAGINATED_FETCH_ERROR", f"페이지별 조회 중 오류가 발생했습니다: {str(e)}")
