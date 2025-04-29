from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO, emit
import mysql.connector
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key'
socketio = SocketIO(app)

# MySQL 연결
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="chat"
)
cursor = db.cursor(dictionary=True)

KAKAO_CLIENT_ID = '1a08b5fe979a9b13776063096985acbd'
KAKAO_REDIRECT_URI = 'http://localhost:5000/kakao/callback'

@app.route("/")
def index():
    username = session.get("user")
    return render_template("introduce.html", username=username)

@app.route("/register", methods=["GET", "POST"])
def register():
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
    else:
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

    # 액세스 토큰 요청
    token_url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": KAKAO_CLIENT_ID,
        "redirect_uri": KAKAO_REDIRECT_URI,
        "code": code,
    }
    token_response = requests.post(token_url, data=data)
    access_token = token_response.json().get("access_token")

    # 사용자 정보 요청
    user_info_url = "https://kapi.kakao.com/v2/user/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    user_info_response = requests.get(user_info_url, headers=headers)
    user_info = user_info_response.json()

    kakao_id = user_info.get("id")
    kakao_account = user_info.get("kakao_account", {})
    email = kakao_account.get("email", "")
    nickname = kakao_account.get("profile", {}).get("nickname", "")

    # 로그인 처리
    session["user"] = nickname
    return redirect("/mainpage")

# WebSocket 이벤트 처리
@socketio.on("chat")
def handle_chat(data):
    username = session.get("user", "익명")
    msg = data.get("message", "")
    image_data = data.get("image", None)

    # 문자열만 MySQL에 넣음 (딕셔너리 아님)
    cursor.execute(
        "INSERT INTO chat_logs (username, message) VALUES (%s, %s)",
        (username, msg)
    )
    db.commit()

    emit("chat", {"username": username, "message": msg, "image": image_data}, broadcast=True)



@socketio.on("draw")
def handle_draw(data):
    username = session.get("user", "익명")
    cursor.execute("INSERT INTO draw_logs (username, x, y) VALUES (%s, %s, %s)", (username, data["x"], data["y"]))
    db.commit()
    emit("draw", data, broadcast=True)


if __name__ == "__main__":
    socketio.run(app, debug=True)
