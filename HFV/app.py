from flask import Flask, render_template, request, redirect, session, url_for
from db_config import get_connection
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from flask import make_response
from flask_mail import Mail, Message
import requests
import random
import string
from flask import jsonify
import datetime
import os
import json
import yaml
import time
from db_config import get_stock_codes_from_db
from kis_auth import auth, getTREnv, _getBaseHeader
import pandas as pd
from db_config import get_connection
import pymysql
from kis_auth import getTREnv, _getBaseHeader
from dotenv import load_dotenv
from openai import OpenAI


def save_ai_query(user_id, query, response):
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO ai_queries (user_id, query, response)
            VALUES (%s, %s, %s)
        """, (user_id, query, response))
        conn.commit()
    conn.close()

load_dotenv()
print("🔍 불러온 API KEY:", os.getenv("OPENAI_API_KEY")) 

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Flask app 설정
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'kdy63010917@gmail.com'
app.config['MAIL_PASSWORD'] = 'dbrf hztz ctfx iynh'
app.config['MAIL_DEFAULT_SENDER'] = 'kdy63010917@gmail.com'

mail = Mail(app)

@app.route('/')
def index():
    if 'user' in session:
        return render_template('main.html', user=session['user'])
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = request.form.get('remember_id')

        # DB 조회
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
            user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user'] = user['username']

            resp = make_response(redirect(url_for('index')))
            if remember:
                # 쿠키에 7일간 저장
                resp.set_cookie('saved_id', username, max_age=60*60*24*7)
            else:
                # 체크 안 했으면 쿠키 삭제
                resp.set_cookie('saved_id', '', expires=0)
            return resp
        else:
            return render_template('login.html', error="로그인 실패. 사용자 정보를 확인하세요.")

    # GET 요청 – 쿠키에서 저장된 ID 꺼내서 넘김
    saved_id = request.cookies.get('saved_id', '')
    return render_template('login.html', saved_id=saved_id)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm']

        if password != confirm:
            return render_template('signup.html', error="비밀번호가 일치하지 않습니다.")

        conn = get_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        try:
            # 중복 사용자 확인
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()

            if user:
                return render_template('signup.html', error="이미 존재하는 아이디입니다.")

            hashed_pw = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                (username, email, hashed_pw)
            )
            conn.commit()
            return redirect(url_for('login'))

        except Exception as e:
            conn.rollback()
            return render_template('signup.html', error="서버 오류가 발생했습니다. 다시 시도해주세요.")

        finally:
            conn.close()

    return render_template('signup.html')

@app.route('/check-username', methods=['POST'])
def check_username():
    username = request.form['username']

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return 'duplicate'
    else:
        return 'available'

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/find-id', methods=['GET', 'POST'])
def find_id():
    if request.method == 'POST':
        email = request.form['email']

        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT username FROM users WHERE email=%s", (email,))
            result = cursor.fetchone()
        conn.close()

        if result:
            return render_template('find_id.html', username=result['username'])
        else:
            return render_template('find_id.html', error="해당 이메일로 등록된 계정이 없습니다.")

    return render_template('find_id.html')

@app.route('/find-pw', methods=['GET', 'POST'])
def find_pw():
    if request.method == 'POST':
        email = request.form['email']

        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()

            if not user:
                conn.close()
                return render_template('find_pw.html', error="해당 이메일로 등록된 계정이 없습니다.")

            # 1. 임시 비밀번호 생성
            temp_pw = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            hashed_pw = generate_password_hash(temp_pw)

            # 2. DB에 비밀번호 업데이트
            cursor.execute("UPDATE users SET password=%s WHERE email=%s", (hashed_pw, email))
            conn.commit()
        conn.close()

        # 3. 이메일로 전송
        msg = Message('임시 비밀번호 안내', recipients=[email])
        msg.body = f"[HFV 모의투자 사이트] 임시 비밀번호는: {temp_pw} 입니다. 로그인 후 꼭 비밀번호를 변경해주세요."
        mail.send(msg)
        if user:
            # 비밀번호 재설정 이메일 전송 로직이 여기 들어감
            return render_template('find_pw.html', message="비밀번호 재설정 링크를 이메일로 보냈습니다.")
        else:
            return render_template('find_pw.html', error="등록되지 않은 이메일입니다.")

    return render_template('find_pw.html')

@app.route('/mypage')
def mypage():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('mypage.html', user=session['user'])

@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        current_pw = request.form['current_password']
        new_pw = request.form['new_password']
        confirm_pw = request.form['confirm_password']

        if new_pw != confirm_pw:
            return render_template('change_password.html', error="새 비밀번호가 일치하지 않습니다.")

        conn = get_connection()
        cursor = conn.cursor()

        # 현재 비밀번호 검증
        cursor.execute("SELECT password FROM users WHERE username = %s", (session['user'],))
        user = cursor.fetchone()

        if not user or not check_password_hash(user['password'], current_pw):
            conn.close()
            return render_template('change_password.html', error="현재 비밀번호가 틀렸습니다.")

        # 비밀번호 변경
        hashed_pw = generate_password_hash(new_pw)
        cursor.execute("UPDATE users SET password = %s WHERE username = %s", (hashed_pw, session['user']))
        conn.commit()
        conn.close()

        return redirect(url_for('mypage'))

    return render_template('change_password.html')


## 카카오 ##
KAKAO_CLIENT_ID = '1a08b5fe979a9b13776063096985acbd'
KAKAO_REDIRECT_URI = 'http://localhost:5000/login/kakao/callback'

@app.route('/login/kakao')
def login_kakao():
    kakao_auth_url = (
        f"https://kauth.kakao.com/oauth/authorize?"
        f"response_type=code&client_id={KAKAO_CLIENT_ID}&redirect_uri={KAKAO_REDIRECT_URI}"
    )
    return redirect(kakao_auth_url)

@app.route('/login/kakao/callback')
def kakao_callback():
    code = request.args.get('code')

    # 1. 인가코드로 토큰 요청
    token_url = "https://kauth.kakao.com/oauth/token"
    token_data = {
        "grant_type": "authorization_code",
        "client_id": KAKAO_CLIENT_ID,
        "redirect_uri": KAKAO_REDIRECT_URI,
        "code": code
    }
    token_res = requests.post(token_url, data=token_data)
    access_token = token_res.json().get("access_token")

    # 2. 사용자 정보 요청
    user_url = "https://kapi.kakao.com/v2/user/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    user_res = requests.get(user_url, headers=headers)
    kakao_account = user_res.json().get("kakao_account")
    email = kakao_account.get("email")
    nickname = kakao_account.get("profile").get("nickname")

    # 3. DB에 사용자 존재하는지 확인 (없으면 등록)
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        if not user:
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                (nickname, email, "")  # 소셜로그인은 비번 없음
            )
            conn.commit()
    conn.close()

    # 4. 세션 로그인 처리
    session['user'] = nickname
    return redirect(url_for('index'))

def get_market_code(stock_code):
    """종목코드 앞자리로 시장 구분"""
    if stock_code.startswith(("0", "1", "3")):
        return "J"  # KOSPI
    elif stock_code.startswith(("2", "9")):
        return "Q"  # KOSDAQ
    else:
        return "J"  # 기본값 fallback
    
## 주식 ##

# Flask 앱 구동 시 최초 1회 인증
auth(svr='vps')  # 실전투자는 'prod'

## 주식 테이블 (TOP 10)
@app.route('/get_stock_data_list')

def get_stock_data_list():

    sort_by = request.args.get('sort_by', 'volume')
    page = int(request.args.get('page', 1))  # 페이지 번호 (기본 1)
    per_page = 10  # 페이지당 항목 수
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    stock_codes = get_stock_codes_from_db()
    url = f"{getTREnv().my_url}/uapi/domestic-stock/v1/quotations/inquire-price"
    headers = _getBaseHeader()
    headers["authorization"] = getTREnv().my_token
    headers["appkey"] = getTREnv().my_app
    headers["appsecret"] = getTREnv().my_sec
    headers["tr_id"] = "FHKST01010100"

    result = []

    for stock in stock_codes:
        params = {
            "fid_cond_mrkt_div_code": get_market_code(stock['code']),
            "fid_input_iscd": stock['code']
        }

        try:
            res = requests.get(url, headers=headers, params=params)
            time.sleep(0.5)
            if res.status_code == 200:
                output = res.json().get("output", {})
                price = int(output.get("stck_prpr", "0"))
                if price == 0:
                    continue

                result.append({
                    "code": stock['code'],
                    "name": stock['name'],
                    "price": price,
                    "change": float(output.get("prdy_ctrt", "0")),
                    "volume": int(output.get("acml_tr_pbmn", "0")),
})
        except:
            continue

    sort_by = request.args.get('sort_by', 'volume')
    
    if sort_by == 'change':
        result.sort(key=lambda x: x["change"], reverse=True)
    elif sort_by == 'quantity':
        result.sort(key=lambda x: x["quantity"], reverse=True)
    else:
        result.sort(key=lambda x: x["volume"], reverse=True)

    for idx, stock in enumerate(result, start=1):
        stock["rank"] = idx

    paged_result = result[start_idx:end_idx]
    return jsonify(paged_result)

#종목 코드 불러오기 *값
@app.route('/get_candle_volume')
def get_candle_volume():
    

    code = request.args.get('code')  # 종목 코드
    period_days = int(request.args.get('days', 7))

    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=period_days)

    params = {
        "FID_COND_MRKT_DIV_CODE": "J",  # 코스피/코스닥
        "FID_INPUT_ISCD": code,
        "FID_PERIOD_DIV_CODE": "D",
        "FID_ORG_ADJ_PRC": "0",
        "FID_INPUT_DATE_1": start_date.strftime("%Y%m%d"),
        "FID_INPUT_DATE_2": end_date.strftime("%Y%m%d"),
    }

    headers = _getBaseHeader()
    headers["authorization"] = getTREnv().my_token
    headers["appkey"] = getTREnv().my_app
    headers["appsecret"] = getTREnv().my_sec
    headers["tr_id"] = "FHKST03010100"

    res = requests.get(f"{getTREnv().my_url}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice", headers=headers, params=params)

    return res.json()

#주식 검색
@app.route('/search_stock')
def search_stock():
    keyword = request.args.get('keyword', '').strip()

    # 종목 코드 또는 이름으로 검색
    stock_codes = get_stock_codes_from_db()
    target = None
    for stock in stock_codes:
        if keyword == stock['code'] or keyword in stock['name']:
            target = stock
            break

    if not target:
        return jsonify({'status': 'not_found'})

    # 가격 데이터 조회

    url = f"{getTREnv().my_url}/uapi/domestic-stock/v1/quotations/inquire-price"
    headers = _getBaseHeader()
    headers["authorization"] = getTREnv().my_token
    headers["appkey"] = getTREnv().my_app
    headers["appsecret"] = getTREnv().my_sec
    headers["tr_id"] = "FHKST01010100"

    market_code = get_market_code(target['code'])
    params = {
        "fid_cond_mrkt_div_code": market_code,
        "fid_input_iscd": target['code']
    }

    try:
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 200:
            output = res.json().get("output", {})
            return jsonify({
                'status': 'found',
                'data': {
                    'code': target['code'],
                    'name': target['name'],
                    'price': int(output.get("stck_prpr", "0")),
                    'change': float(output.get("prdy_ctrt", "0")),
                    'volume': int(output.get("acml_tr_pbmn", "0"))
                }
            })
        else:
            return jsonify({'status': 'error', 'message': res.text})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
    



@app.route('/ai_chat')
def ai_chat():
    return render_template('ai_chat.html')


@app.route('/ai/query', methods=['POST'])
def ai_query():
    question = request.json.get('question')
    user_id = session.get('user_id', 1)

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "당신은 똑똑한 투자 분석가입니다."},
                {"role": "user", "content": question}
            ]
        )
        answer = response.choices[0].message.content
        save_ai_query(user_id, question, answer)
        return jsonify({"response": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# ✅ 반드시 마지막에 있어야 함
if __name__ == '__main__':
    app.run(debug=True)

