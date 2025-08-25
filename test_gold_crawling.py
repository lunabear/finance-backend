#!/usr/bin/env python3
"""
네이버 금융 금 가격 크롤링 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.company.services import CompanyService


def test_gold_crawling():
    """금 가격 크롤링 테스트"""
    print("🔍 네이버 금융 금 가격 크롤링 테스트를 시작합니다...")
    print("=" * 60)
    
    try:
        # 금 가격 정보 조회
        result = CompanyService.get_gold_price_info()
        
        print(f"📊 크롤링 결과:")
        print(f"   상태: {result['status']}")
        print(f"   메시지: {result['message']}")
        
        if result['status'] == 'success' and result['data']:
            data = result['data']
            print(f"\n💰 금 가격 정보:")
            print(f"   현재 가격: {data['price']} {data['currency']}/{data['unit']}")
            print(f"   변동액: {data['change']:+.2f} {data['currency']}")
            print(f"   변동률: {data['change_rate']:+.2f}%")
            print(f"   거래소: {data['market']}")
            print(f"   업데이트 시간: {data['updated_at']}")
            
            # 간단한 분석
            if data['change'] > 0:
                trend = "📈 상승"
            elif data['change'] < 0:
                trend = "📉 하락"
            else:
                trend = "➡️ 보합"
                
            print(f"\n📈 추세 분석: {trend}")
            
        else:
            print(f"❌ 크롤링 실패:")
            if 'error_code' in result:
                print(f"   오류 코드: {result['error_code']}")
            print(f"   메시지: {result['message']}")
            
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {str(e)}")
    
    print("=" * 60)
    print("✅ 테스트 완료")


if __name__ == "__main__":
    test_gold_crawling()

