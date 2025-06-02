from flask import Flask, jsonify, render_template
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import json

app = Flask(__name__)

# 네이버 API 키 설정
CLIENT_ID = "qYVyhXKXdSlt9GL7MnHF"  # 발급받은 Client ID로 교체
CLIENT_SECRET = "oFKVljNMsV"  # 발급받은 Client Secret으로 교체

def get_naver_news():
    """
    네이버 뉴스 API를 사용하여 주식 관련 뉴스를 가져오는 함수
    """
    url = "https://openapi.naver.com/v1/search/news.json"
    
    # 검색어를 주식 관련으로 설정
    query = "주식 코스피 금융"
    
    # API 요청 헤더
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET
    }
    
    # API 요청 파라미터
    params = {
        "query": query,
        "display": 5,  # 가져올 뉴스 수
        "sort": "date"  # 최신순 정렬
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # HTTP 에러 체크
        
        news_data = response.json()
        
        # 응답 데이터 정제
        news_list = []
        for item in news_data.get('items', []):
            # HTML 태그 제거 및 제목 정제
            title = item['title'].replace('<b>', '').replace('</b>', '')
            
            # 날짜 형식 변환
            # pubDate 형식: "Wed, 08 May 2025 09:34:00 +0900"
            # datetime 객체로 변환 후 원하는 형식으로 포맷팅
            try:
                pub_date = datetime.strptime(item['pubDate'], '%a, %d %b %Y %H:%M:%S %z')
                formatted_date = pub_date.strftime('%Y.%m.%d')
            except:
                formatted_date = item['pubDate']  # 파싱 실패 시 원본 데이터 사용
            
            news_list.append({
                'title': title,
                'url': item['link'],
                'date': formatted_date
            })
        
        return news_list
    
    except Exception as e:
        print(f"API 호출 오류: {e}")
        # 오류 발생 시 크롤링으로 대체
        return crawl_stock_news()

def crawl_stock_news():
    """
    주식 뉴스를 크롤링하는 함수 (API 호출 실패 시 대체)
    """
    # 네이버 금융 뉴스 페이지에서 뉴스를 크롤링
    url = "https://finance.naver.com/news/mainnews.naver"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    news_list = []
    
    # 뉴스 목록 요소 찾기
    news_items = soup.select('ul.mainNewsList li dl')
    
    for item in news_items[:5]:  # 상위 5개 뉴스만
        try:
            title_tag = item.select_one('dd.articleSubject a')
            title = title_tag.text.strip()
            
            # 뉴스 URL 생성
            link = "https://finance.naver.com" + title_tag['href']
            
            # 날짜 추출
            date_tag = item.select_one('dd.articleSummary span.wdate')
            date = date_tag.text.strip() if date_tag else "날짜 없음"
            
            # 날짜 형식 간소화 (예: "2023.05.05 15:30" -> "2023.05.05")
            date_match = re.search(r'\d{4}\.\d{2}\.\d{2}', date)
            if date_match:
                date = date_match.group()
            
            news_list.append({
                'title': title,
                'url': link,
                'date': date
            })
        except Exception as e:
            print(f"뉴스 파싱 오류: {e}")
    
    return news_list

@app.route('/')
def index():
    return render_template('test.html')

@app.route('/api/stock-news')
def stock_news():
    # API로 뉴스를 가져오기 시도, 실패 시 크롤링 결과 반환
    news = get_naver_news()
    return jsonify(news)

if __name__ == '__main__':
    app.run(debug=True)