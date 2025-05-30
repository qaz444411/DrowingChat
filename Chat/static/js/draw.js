const canvas = document.getElementById("drawingCanvas");
const ctx = canvas.getContext("2d");

const socket = io("http://730f-203-234-62-90.ngrok-free.app");

let drawing = false;
let colorPicker = document.getElementById("color");
let lineWidthRange = document.getElementById("lineWidth");

// ✅ 방 입장
socket.emit("join_room", { room_id: ROOM_ID, username: USERNAME });

// --- 그리기 시작 ---
canvas.addEventListener("mousedown", (e) => {
  drawing = true;
  ctx.beginPath();
  ctx.moveTo(e.offsetX, e.offsetY);
  socket.emit("start_draw", { x: e.offsetX, y: e.offsetY, color: colorPicker.value, width: lineWidthRange.value, room_id: ROOM_ID });
});

canvas.addEventListener("mousemove", (e) => {
  if (!drawing) return;
  ctx.lineTo(e.offsetX, e.offsetY);
  ctx.strokeStyle = colorPicker.value;
  ctx.lineWidth = lineWidthRange.value;
  ctx.lineCap = "round";
  ctx.stroke();
  socket.emit("draw", { x: e.offsetX, y: e.offsetY, color: colorPicker.value, width: lineWidthRange.value, room_id: ROOM_ID });
});

canvas.addEventListener("mouseup", () => {
  drawing = false;
  socket.emit("end_draw", { room_id: ROOM_ID });
});

canvas.addEventListener("mouseleave", () => {
  drawing = false;
  socket.emit("end_draw", { room_id: ROOM_ID });
});

document.getElementById("clearBtn").addEventListener("click", () => {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
});

// --- 동기화 이벤트 수신 ---
socket.on("start_draw", (data) => {
  ctx.beginPath();
  ctx.moveTo(data.x, data.y);
  ctx.strokeStyle = data.color;
  ctx.lineWidth = data.width;
  ctx.lineCap = "round";
});

socket.on("draw", (data) => {
  ctx.lineTo(data.x, data.y);
  ctx.strokeStyle = data.color;
  ctx.lineWidth = data.width;
  ctx.lineCap = "round";
  ctx.stroke();
});

socket.on("end_draw", () => {
  ctx.closePath();
});

socket.on("user_list", function (usernames) {
  for (let i = 1; i <= 4; i++) {
    const slot = document.getElementById(`player${i}`);
    if (usernames[i - 1]) {
      slot.textContent = usernames[i - 1];
    } else {
      slot.textContent = "비어있음";
    }
  }
});

let currentDrawer = null;

socket.on("set_drawer", (data) => {
  currentDrawer = data.drawer;
  console.log("👤 내 이름:", USERNAME);
  console.log("🎨 출제자:", currentDrawer);

  if (USERNAME === currentDrawer) {
    alert("당신이 이번 라운드의 출제자입니다!");
    allowDrawing();  // ✅ 여기
  } else {
    alert(`${currentDrawer}님이 그림을 그리고 있습니다.`);
    blockDrawing();  // ✅ 여기
  }
});

function blockDrawing() {
  canvas.onmousedown = null;
  canvas.onmousemove = null;
  canvas.onmouseup = null;
}

function allowDrawing() {
  canvas.onmousedown = drawStart;
  canvas.onmousemove = drawMove;
  canvas.onmouseup = drawEnd;
}
