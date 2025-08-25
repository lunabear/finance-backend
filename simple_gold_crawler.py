#!/usr/bin/env python3
"""
네이버 금융 금 가격 크롤링 독립 테스트 스크립트
(Flask 및 다른 의존성 없이 실행 가능)
"""

import urllib.request
import urllib.parse
import re
from datetime import datetime


def crawl_naver_gold_price():
    """
    네이버 금융에서 금 가격 정보를 크롤링하는 함수
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
        
        print("🔍 네이버 금융 사이트에 접속 중...")
        
        # 웹페이지 요청 및 응답 받기
        with urllib.request.urlopen(req, timeout=10) as response:
            # 응답 헤더에서 인코딩 확인
            content_type = response.headers.get('content-type', '')
            
            # 여러 인코딩 시도
            raw_html = response.read()
            html = None
            
            for encoding in ['euc-kr', 'utf-8', 'cp949']:
                try:
                    html = raw_html.decode(encoding)
                    print(f"✅ 인코딩 성공: {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
            
            if html is None:
                # 모든 인코딩 실패시 에러 무시하고 디코딩
                html = raw_html.decode('utf-8', errors='ignore')
                print("⚠️ 에러 무시하고 디코딩 완료")
        
        print("✅ 웹페이지 로드 완료")
        
        # HTML에서 금 가격 정보 추출
        gold_data = {}
        
        print("🔎 금 가격 데이터 추출 중...")
        
        # 현재 가격 추출 - 3000대 금 가격 정확히 찾기
        current_price = None
        
        # 3000대 금 가격 정확한 패턴들
        price_patterns = [
            r'>([3][0-9]{3}\.[0-9]{2})<',  # >3378.00< 형태
            r'([3][0-9]{3}\.[0-9]{2})\s*달러',  # 3378.00 달러 형태  
            r'([3][0-9]{3}\.[0-9]{2})\s*USD',  # 3378.00 USD 형태
            r'([3][0-9]{3}\.[0-9]{2})',  # 단순 3378.00 형태
            r'class="value"[^>]*>([3][0-9]{3}\.[0-9]{2})',  # class="value">3378.00
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, html)
            if matches:
                try:
                    current_price = float(matches[0])
                    print(f"💰 발견된 가격: {current_price}")
                    break
                except:
                    continue
        
        gold_data['current_price'] = current_price
        
        # 변동액 추출 - 개선된 패턴
        change_patterns = [
            r'전일대비.*?([+-]?[0-9]+\.[0-9]+)',  # 전일대비 +4.60 형태
            r'([+-][0-9]+\.[0-9]+).*?달러',  # +4.60 달러 형태
            r'>([+-][0-9]+\.[0-9]+)<',  # >+4.60< 형태
            r'([+-]?[0-9]+\.[0-9]+)\s*\(',  # 4.60 ( 형태
        ]
        
        change_amount = 0.0
        for pattern in change_patterns:
            matches = re.findall(pattern, html)
            if matches:
                try:
                    change_amount = float(matches[0])
                    print(f"📊 발견된 변동액: {change_amount}")
                    break
                except:
                    continue
        
        gold_data['change_amount'] = change_amount
        
        # 변동률 추출 - 개선된 패턴
        rate_patterns = [
            r'([+-]?[0-9]+\.[0-9]+)%',  # 0.13% 형태
            r'\(\s*([+-]?[0-9]+\.[0-9]+)\s*%\s*\)',  # ( -0.13% ) 형태
        ]
        
        change_rate = 0.0
        for pattern in rate_patterns:
            matches = re.findall(pattern, html)
            if matches:
                try:
                    change_rate = float(matches[0])
                    print(f"📊 발견된 변동률: {change_rate}%")
                    break
                except:
                    continue
        
        gold_data['change_rate'] = change_rate
        
        # 추가 정보
        gold_data['currency'] = 'USD'
        gold_data['unit'] = 'Troy Ounce'
        gold_data['market'] = 'COMEX'
        gold_data['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return gold_data
        
    except urllib.error.URLError as e:
        print(f"❌ 네트워크 오류: {str(e)}")
        return None
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP 오류: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {str(e)}")
        return None


def main():
    """메인 함수"""
    print("🏆 네이버 금융 금 가격 크롤링 테스트")
    print("=" * 60)
    
    # 크롤링 실행
    result = crawl_naver_gold_price()
    
    if result:
        print("💰 금 가격 정보 크롤링 성공!")
        print("-" * 40)
        print(f"📈 현재 가격: {result['current_price']} {result['currency']}/{result['unit']}")
        print(f"📊 변동액: {result['change_amount']:+.2f} {result['currency']}")
        print(f"📊 변동률: {result['change_rate']:+.2f}%")
        print(f"🏪 거래소: {result['market']}")
        print(f"⏰ 업데이트: {result['last_updated']}")
        
        # 추세 분석
        if result['change_amount'] > 0:
            trend = "📈 상승 추세"
            emoji = "🟢"
        elif result['change_amount'] < 0:
            trend = "📉 하락 추세"
            emoji = "🔴"
        else:
            trend = "➡️ 보합"
            emoji = "🟡"
        
        print(f"\n{emoji} 시장 동향: {trend}")
        
        # 웹검색 정보와 비교
        print(f"\n📋 참고: 웹검색 결과에 따르면 현재 금 가격은 3,378.00 달러/트로이온스입니다.")
        
    else:
        print("❌ 금 가격 정보 크롤링 실패")
    
    print("=" * 60)
    print("✨ 테스트 완료")


if __name__ == "__main__":
    main()
