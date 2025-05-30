// static/js/socket.js

// ngrok 주소로 전역 socket 객체 정의
const socket = io("http://730f-203-234-62-90.ngrok-free.app");
window.socket = socket;  // 전역에서도 접근 가능하게

// 이벤트 바인딩 함수 정의
window.setupSocketEvents = function(roomId, username) {
  socket.emit("join_room", {
    room_id: roomId,
    username: username
  });

  window.addEventListener("beforeunload", () => {
    socket.emit("leave_room", {
      room_id: roomId,
      username: username
    });
  });
};
