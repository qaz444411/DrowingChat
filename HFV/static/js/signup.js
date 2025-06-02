
function checkUsername() {
    const username = document.getElementById('username').value;
    const result = document.getElementById('username-result');
  
    if (!username) {
      result.innerText = "아이디를 입력해주세요.";
      result.style.color = 'red';
      return;
    }
  
    fetch("/check-username", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: "username=" + encodeURIComponent(username)
    })
    .then(res => res.text())
    .then(data => {
      if (data === "duplicate") {
        result.innerText = "이미 존재하는 아이디입니다.";
        result.style.color = 'red';
      } else {
        result.innerText = "사용 가능한 아이디입니다.";
        result.style.color = 'green';
      }
    });
  }
  