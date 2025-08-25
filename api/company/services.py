import uuid
import urllib.request
import urllib.parse
import re
from typing import List, Optional, Dict
from pynamodb.exceptions import DoesNotExist, PutError
from botocore.exceptions import ClientError
from bs4 import BeautifulSoup
from datetime import datetime

from api.company.models import CompanyModel
from util.logging_util import logger
from exceptions import CoreException, BadRequestException, EntityNotFoundException


class CompanyService:
    """
    회사 정보 관리 서비스
    """

    @staticmethod
    def create_table_if_not_exists():
        """
        테이블이 존재하지 않으면 생성
        """
        try:
            if not CompanyModel.exists():
                logger.info("Creating CompanyModel table...")
                CompanyModel.create_table(wait=True)
                logger.info("CompanyModel table created successfully")
            else:
                logger.info("CompanyModel table already exists")
        except Exception as e:
            logger.error(f"Error creating table: {str(e)}")
            raise CoreException("테이블 생성에 실패했습니다", "TABLE_CREATION_FAILED")

    @staticmethod
    def create_company(company_data: dict) -> CompanyModel:
        """
        새로운 회사 생성
        
        Args:
            company_data: 회사 정보 딕셔너리
            
        Returns:
            CompanyModel: 생성된 회사 모델
        """
        try:
            # 고유 ID 생성
            company_id = str(uuid.uuid4())
            
            company = CompanyModel(
                company_id=company_id,
                company_name=company_data['company_name'],
                company_type=company_data['company_type']
            )
            
            company.save()
            logger.info(f"Company created with ID: {company_id}")
            return company
            
        except PutError as e:
            logger.error(f"Error creating company: {str(e)}")
            raise BadRequestException("회사 생성에 실패했습니다", "COMPANY_CREATION_FAILED")
        except Exception as e:
            logger.error(f"Unexpected error creating company: {str(e)}")
            raise CoreException("회사 생성 중 오류가 발생했습니다", "COMPANY_CREATION_ERROR")

    @staticmethod
    def get_company_by_name(company_name: str) -> CompanyModel:
        """
        회사명으로 회사 조회
        
        Args:
            company_name: 회사명
            
        Returns:
            CompanyModel: 조회된 회사 모델
            
        Raises:
            EntityNotFoundException: 회사를 찾을 수 없는 경우
        """
        try:
            for company in CompanyModel.scan():
                if company.company_name == company_name:
                    logger.info(f"Company found with name: {company_name}")
                    return company
            
            logger.warning(f"Company not found with name: {company_name}")
            raise EntityNotFoundException("회사를 찾을 수 없습니다", "COMPANY_NOT_FOUND")
        except EntityNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error getting company by name: {str(e)}")
            raise CoreException("회사 조회에 실패했습니다", "COMPANY_GET_BY_NAME_ERROR")

    @staticmethod
    def get_all_companies() -> List[CompanyModel]:
        """
        모든 회사 목록 조회
        
        Returns:
            List[CompanyModel]: 회사 목록
        """
        try:
            companies = list(CompanyModel.scan())
            logger.info(f"Retrieved {len(companies)} companies")
            return companies
        except Exception as e:
            logger.error(f"Error getting all companies: {str(e)}")
            raise CoreException("회사 목록 조회에 실패했습니다", "COMPANY_LIST_ERROR")

    @staticmethod
    def update_company(company_id: str, update_data: dict) -> CompanyModel:
        """
        회사 정보 업데이트
        
        Args:
            company_id: 회사 ID
            update_data: 업데이트할 데이터
            
        Returns:
            CompanyModel: 업데이트된 회사 모델
        """
        try:
            company = CompanyModel.get(company_id)
            
            # 업데이트할 필드들
            update_fields = [
                'company_name', 'company_type'
            ]
            
            for field in update_fields:
                if field in update_data:
                    setattr(company, field, update_data[field])
            
            company.save()
            logger.info(f"Company updated with ID: {company_id}")
            return company
            
        except DoesNotExist:
            logger.warning(f"Company not found for update with ID: {company_id}")
            raise EntityNotFoundException("수정할 회사를 찾을 수 없습니다", "COMPANY_NOT_FOUND")
        except Exception as e:
            logger.error(f"Error updating company: {str(e)}")
            raise BadRequestException("회사 정보 수정에 실패했습니다", "COMPANY_UPDATE_FAILED")

    @staticmethod
    def delete_company(company_id: str) -> bool:
        """
        회사 삭제
        
        Args:
            company_id: 회사 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            company = CompanyModel.get(company_id)
            company.delete()
            logger.info(f"Company deleted with ID: {company_id}")
            return True
            
        except DoesNotExist:
            logger.warning(f"Company not found for deletion with ID: {company_id}")
            raise EntityNotFoundException("삭제할 회사를 찾을 수 없습니다", "COMPANY_NOT_FOUND")
        except Exception as e:
            logger.error(f"Error deleting company: {str(e)}")
            raise BadRequestException("회사 삭제에 실패했습니다", "COMPANY_DELETE_FAILED")

    @staticmethod
    def crawl_gold_price() -> Dict:
        """
        네이버 금융에서 금 가격 정보를 크롤링
        
        Returns:
            Dict: 금 가격 정보 딕셔너리
                - current_price: 현재 금 가격 (달러/트로이온스)
                - change_amount: 변동액
                - change_rate: 변동률 (%)
                - currency: 통화 단위
                - last_updated: 마지막 업데이트 시간
                - market: 거래소 정보
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
        금 가격 정보를 조회하는 메인 함수
        
        Returns:
            Dict: 포맷된 금 가격 정보
        """
        try:
            raw_data = CompanyService.crawl_gold_price()
            
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

