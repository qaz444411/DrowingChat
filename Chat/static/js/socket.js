if (typeof window.socket === 'undefined') {
  window.socket = io();  // 전역으로 선언

  window.setupSocketEvents = function(roomId, nickname) {
    // ✅ 방 입장 요청
    socket.emit("join_room", {
      room_id: roomId,
      nickname: nickname
    });

    // ✅ 중복 퇴장 방지 플래그
    let hasLeft = false;

    // ✅ 퇴장 이벤트 정의
    function emitLeaveEvent() {
      if (!hasLeft && socket.connected) {
        socket.emit("leave_room", {
          room_id: roomId,
          nickname: nickname
        });
        hasLeft = true;
      }
    }

    // 전역에서도 퇴장 가능하도록 expose
    window.emitLeaveEvent = emitLeaveEvent;

    // 브라우저 종료, 새로고침, 뒤로가기 시 퇴장
    window.addEventListener("beforeunload", emitLeaveEvent);

    // 탭 전환/숨김 시 퇴장
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "hidden") {
        emitLeaveEvent();
      }
    });
  };
}
