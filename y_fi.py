#!/usr/bin/env python3
import yfinance as yf

def main():


# Apple 주식 데이터 다운로드
    gold_futures = yf.Ticker("GC=F")
    # 2020년 한 해 동안의 주가 데이터 가져오기
    hist = gold_futures.history(period="1y")

    # 최근 5일간의 주가 데이터 출력
    print(hist.tail())


if __name__ == "__main__":
    main()
