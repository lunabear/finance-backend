#!/usr/bin/env python3
"""
네이버 금융 HTML 구조 분석용 디버그 스크립트
"""

import urllib.request
import urllib.parse
import re
from datetime import datetime


def debug_naver_html():
    """
    네이버 금융 HTML을 저장하고 분석
    """
    try:
        # 네이버 금융 금 시세 URL
        url = "https://finance.naver.com/marketindex/worldGoldDetail.naver?marketindexCd=CMDT_GC&fdtc=2"
        
        # User-Agent 헤더 설정
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # HTTP 요청 생성
        req = urllib.request.Request(url, headers=headers)
        
        print("🔍 네이버 금융 사이트에 접속 중...")
        
        # 웹페이지 요청 및 응답 받기
        with urllib.request.urlopen(req, timeout=10) as response:
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
                html = raw_html.decode('utf-8', errors='ignore')
                print("⚠️ 에러 무시하고 디코딩 완료")
        
        # HTML을 파일로 저장
        with open('naver_gold_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("✅ HTML 파일 저장 완료: naver_gold_page.html")
        
        # 3000대 숫자 패턴 모두 찾기
        print("\n🔍 3000대 숫자 패턴 검색:")
        patterns_3000 = re.findall(r'3[0-9]{3}\.[0-9]{2}', html)
        if patterns_3000:
            for i, pattern in enumerate(set(patterns_3000)):
                print(f"   {i+1}. {pattern}")
        else:
            print("   3000대 패턴을 찾을 수 없습니다.")
        
        # 모든 숫자.소수점 패턴 찾기 (4자리 이상)
        print("\n🔍 4자리 이상 숫자.소수점 패턴:")
        all_numbers = re.findall(r'[0-9]{4,}\.[0-9]{2}', html)
        if all_numbers:
            unique_numbers = list(set(all_numbers))[:10]  # 상위 10개만
            for i, num in enumerate(unique_numbers):
                print(f"   {i+1}. {num}")
        
        # 특정 키워드 주변 텍스트 찾기
        print("\n🔍 '금' 키워드 주변 텍스트:")
        gold_context = re.findall(r'.{0,50}금.{0,50}', html)[:5]
        for i, context in enumerate(gold_context):
            clean_context = re.sub(r'<[^>]+>', '', context).strip()
            if clean_context:
                print(f"   {i+1}. ...{clean_context}...")
        
        # 달러 키워드 주변 텍스트 찾기
        print("\n🔍 '달러' 키워드 주변 텍스트:")
        dollar_context = re.findall(r'.{0,30}[0-9,]+\.[0-9]+.{0,30}달러.{0,30}', html)[:5]
        for i, context in enumerate(dollar_context):
            clean_context = re.sub(r'<[^>]+>', '', context).strip()
            if clean_context:
                print(f"   {i+1}. ...{clean_context}...")
        
        print("\n✅ 디버그 분석 완료")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")


if __name__ == "__main__":
    debug_naver_html()

