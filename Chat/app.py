from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO, emit
import mysql.connector
import requests
import smtplib
import random
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = 'your_secret_key'
socketio = SocketIO(app)

# MySQL 연결
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="drowingchat"
)
cursor = db.cursor(dictionary=True)

# 카카오 로그인 설정
KAKAO_CLIENT_ID = '1a08b5fe979a9b13776063096985acbd'
KAKAO_REDIRECT_URI = 'http://localhost:5000/kakao/callback'

# 이메일 서버 설정
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "kdy63010917@gmail.com"       # 너의 Gmail
SENDER_PASSWORD = "nkyn qtid bnjb vjov"        # 앱 비밀번호

# 이메일 전송 함수
def send_verification_email(receiver_email, code):
    html_content = f"""
    <html>
      <body>
        <h2 style="color: #333;">학교 이메일 인증코드</h2>
        <p>아래 인증 코드를 입력해주세요:</p>
        <h1 style="color: #4CAF50;">{code}</h1>
        <p>본 이메일은 인증 용도로만 사용됩니다.</p>
      </body>
    </html>
    """
    msg = MIMEText(html_content, "html")
    msg["Subject"] = "학교 이메일 인증코드"
    msg["From"] = SENDER_EMAIL
    msg["To"] = receiver_email

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
        server.quit()
        print("이메일 전송 성공!")
    except Exception as e:
        print("이메일 전송 실패:", e)

# ----------------------- Flask 라우트 ----------------------------

@app.route("/")
def index():
    username = session.get("user")
    return render_template("introduce.html", username=username)

@app.route("/email_verify", methods=["GET", "POST"])
def email_verify():
    if request.method == "POST":
        email = request.form["email"]
        if not email.endswith("@kunsan.ac.kr"):
            return "학교 이메일(@kunsan.ac.kr)만 사용 가능합니다."

        code = str(random.randint(100000, 999999))
        session["email_code"] = code
        session["email_to_verify"] = email

        send_verification_email(email, code)
        return redirect("/verify_code")

    return render_template("email_verify.html")

@app.route("/verify_code", methods=["GET", "POST"])
def verify_code():
    if request.method == "POST":
        email = request.form["email"]
        code = request.form["code"]

        if email == session.get("email_to_verify") and code == session.get("email_code"):
            session["email_verified"] = True
            return redirect("/register")
        else:
            return "인증 실패. 이메일 또는 코드가 일치하지 않습니다."

    return render_template("verify_code.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if not session.get("email_verified"):
        return redirect("/email_verify")

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        username = request.form["username"]
        password = request.form["password"]

        cursor.execute("""
            INSERT INTO users (name, email, username, password)
            VALUES (%s, %s, %s, %s)
        """, (name, email, username, password))
        db.commit()

        # 인증 세션 초기화
        session.pop("email_verified", None)
        session.pop("email_to_verify", None)
        session.pop("email_code", None)

        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        if user:
            session["user"] = user["username"]
            return redirect("/mainpage")
        else:
            return "로그인 실패. <a href='/login'>다시 시도</a>"
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

@app.route("/find_id", methods=["GET", "POST"])
def find_id():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        cursor.execute("SELECT username FROM users WHERE name=%s AND email=%s", (name, email))
        result = cursor.fetchone()
        if result:
            return f"아이디는 다음과 같습니다: <strong>{result['username']}</strong>"
        else:
            return "일치하는 사용자가 없습니다."
    return render_template("find_id.html")

@app.route("/find_password", methods=["GET", "POST"])
def find_password():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        cursor.execute("SELECT password FROM users WHERE name=%s AND email=%s", (name, email))
        result = cursor.fetchone()
        if result:
            return f"비밀번호는 다음과 같습니다: <strong>{result['password']}</strong>"
        else:
            return "일치하는 사용자가 없습니다."
    return render_template("find_password.html")

@app.route("/mainpage")
def mainpage():
    if "user" in session:
        return render_template("mainpage.html", username=session["user"])
    return redirect("/login")

@app.route("/canvas")
def canvas():
    if "user" in session:
        return render_template("canvas.html", username=session["user"])
    return redirect("/login")

@app.route('/kakao/login')
def kakao_login():
    kakao_auth_url = (
        f"https://kauth.kakao.com/oauth/authorize?"
        f"response_type=code&client_id={KAKAO_CLIENT_ID}&redirect_uri={KAKAO_REDIRECT_URI}"
    )
    return redirect(kakao_auth_url)

@app.route('/kakao/callback')
def kakao_callback():
    code = request.args.get("code")

    token_url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": KAKAO_CLIENT_ID,
        "redirect_uri": KAKAO_REDIRECT_URI,
        "code": code,
    }
    token_response = requests.post(token_url, data=data)
    access_token = token_response.json().get("access_token")

    user_info_url = "https://kapi.kakao.com/v2/user/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    user_info_response = requests.get(user_info_url, headers=headers)
    user_info = user_info_response.json()

    nickname = user_info.get("kakao_account", {}).get("profile", {}).get("nickname", "카카오사용자")

    session["user"] = nickname
    return redirect("/mainpage")

# WebSocket 이벤트
@socketio.on("chat")
def handle_chat(data):
    username = session.get("user", "익명")
    msg = data.get("message", "")
    image_data = data.get("image", None)

    cursor.execute("INSERT INTO chat_logs (username, message) VALUES (%s, %s)", (username, msg))
    db.commit()

    emit("chat", {"username": username, "message": msg, "image": image_data}, broadcast=True)

@socketio.on("draw")
def handle_draw(data):
    username = session.get("user", "익명")
    cursor.execute("INSERT INTO draw_logs (username, x, y) VALUES (%s, %s, %s)", (username, data["x"], data["y"]))
    db.commit()

    emit("draw", data, broadcast=True)

# 서버 실행
if __name__ == "__main__":
    socketio.run(app, debug=True)
