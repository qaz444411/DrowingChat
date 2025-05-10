from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO, emit , join_room, leave_room
import mysql.connector
import smtplib
import random
from email.mime.text import MIMEText
from werkzeug.utils import secure_filename
import os

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

#

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

        # ✅ 이메일 중복 확인
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            return "이미 가입된 이메일입니다. 다른 이메일을 사용해주세요."

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



UPLOAD_FOLDER = 'static/profile'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/register", methods=["GET", "POST"])
def register():
    if not session.get("email_verified"):
        return redirect("/email_verify")

    if request.method == "POST":
        name = request.form["username"]
        email = request.form["email"]
        username = request.form["username"]
        password = request.form["password"]
        nickname = request.form["nickname"]

        profile_image_file = request.files["profile_image"]
        if profile_image_file and profile_image_file.filename != "":
            filename = secure_filename(profile_image_file.filename)
            profile_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_image_file.save(profile_path)
            profile_image = f"/static/profile/{filename}"
        else:
            profile_image = "/static/profile/default.jpg"  # ✅ 기본 이미지 경로


        # DB에 저장
        cursor.execute("""
            INSERT INTO users (name, email, username, password, nickname, profile_image)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, email, username, password, nickname, profile_image))
        db.commit()

        # 세션 초기화
        session.pop("email_verified", None)
        session.pop("email_to_verify", None)
        session.pop("email_code", None)

        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login(): #
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        if user:
            session["user"] = user["username"]
            session["nickname"] = user["nickname"]
            session["profile_image"] = user["profile_image"] or "/static/profile/default.jpg"
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


@app.route("/channels")
def channels():
    cursor.execute("SELECT * FROM channels")
    channel_list = cursor.fetchall()
    return render_template("channels.html", channels=channel_list)  # ✅ 변수명은 channels

@app.route("/channel/<int:channel_id>")
def room_list(channel_id):
    cursor.execute("SELECT * FROM chat_rooms WHERE channel_id = %s AND current_users > 0", (channel_id,))
    rooms = cursor.fetchall()
    return render_template("room_list.html", rooms=rooms, channel_id=channel_id)




@app.route("/canvas/<int:room_id>")
def canvas_with_room(room_id):
    cursor.execute("SELECT * FROM chat_rooms WHERE id = %s", (room_id,))
    room = cursor.fetchone()
    if not room:
        return "존재하지 않는 방입니다."

    return render_template("canvas.html", room=room, username=session.get("user", "익명"))


# 채널별 방 목록
@app.route("/channel/<int:channel_id>/create_room", methods=["GET", "POST"])
def create_room(channel_id):
    if request.method == "POST":
        title = request.form["title"]
        host = session.get("user", "익명")
        max_users = int(request.form.get("max_users", 16))
        is_private = request.form.get("is_private") == "on"

        # ✅ INSERT
        cursor.execute("""
            INSERT INTO chat_rooms (channel_id, title, host, max_users, is_private)
            VALUES (%s, %s, %s, %s, %s)
        """, (channel_id, title, host, max_users, is_private))
        db.commit()

        # ✅ 마지막으로 삽입된 room_id 가져오기
        room_id = cursor.lastrowid

        # ✅ 바로 canvas로 리디렉션
        return redirect(f"/canvas/{room_id}")

    return render_template("create_room.html", channel_id=channel_id)







# WebSocket 이벤트 ()


@socketio.on("join_room")
def handle_join_room(data):
    room_id = int(data["room_id"])
    username = data.get("username", "익명")
    join_room(str(room_id))

    # ✅ DB에서 current_users +1
    cursor.execute("UPDATE chat_rooms SET current_users = current_users + 1 WHERE id = %s", (room_id,))
    db.commit()

    emit("system", {"message": f"{username}님이 입장했습니다."}, to=str(room_id))


@socketio.on("leave_room")
def handle_leave_room(data):
    room_id = int(data["room_id"])
    username = data.get("username", "익명")
    leave_room(str(room_id))

    # ✅ DB에서 current_users -1
    cursor.execute("UPDATE chat_rooms SET current_users = current_users - 1 WHERE id = %s AND current_users > 0", (room_id,))
    db.commit()

    emit("system", {"message": f"{username}님이 퇴장했습니다."}, to=str(room_id))

@socketio.on("chat_room")
def handle_chat_room(data):
    room_id = str(data["room_id"])
    emit("chat", {
        "username": data["username"],
        "nickname": data["nickname"],
        "profile_image": data["profile_image"],
        "message": data["message"]
    }, to=room_id)


@socketio.on("join") 
def handle_join(data):
    username = data.get("username", "익명")
    join_message = f"{username}님이 입장하셨습니다."
    emit("system", {"message": join_message}, broadcast=True)

@socketio.on("leave") 
def handle_leave(data):
    username = data.get("username", "익명")
    leave_message = f"{username}님이 퇴장하셨습니다."
    emit("system", {"message": leave_message}, broadcast=True)

@socketio.on("chat") #
def handle_chat(data):
    username = session.get("user", "익명")
    nickname = session.get("nickname", "익명")
    profile_image = session.get("profile_image", "/static/profile/default.png")
    msg = data.get("message", "")

    cursor.execute("INSERT INTO chat_logs (username, message) VALUES (%s, %s)", (username, msg))
    db.commit()

    emit("chat", {
        "username": username,
        "nickname": nickname,
        "profile_image": profile_image,
        "message": msg
    }, broadcast=True)


@app.route("/drowing")
def catchmind():
    if "user" in session:
        return render_template("drowing.html", username=session["user"])
    return redirect("/login")

# 서버 실행
if __name__ == "__main__":
    socketio.run(app, debug=True)
