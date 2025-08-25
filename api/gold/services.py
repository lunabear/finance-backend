import urllib.request
import urllib.parse
import re
from typing import Dict, Optional
from bs4 import BeautifulSoup
from datetime import datetime, date

from util.logging_util import logger
from exceptions import CoreException


class GoldPriceService:
    @staticmethod
    def get_gold_price_info(date: Optional[str] = None) -> Dict:
        """
        네이버 금융에서 금 가격 정보를 조회합니다.
        
        Args:
            date: 조회할 날짜 (YYYY-MM-DD 형식, 선택사항)
                미입력시 실시간 데이터를 조회합니다.
        """
        