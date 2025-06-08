// static/js/socket.js

if (typeof window.socket === 'undefined') {
    window.socket = io();  // 전역으로 선언
  
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
  }
  