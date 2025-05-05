document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("register-form");
  
    form.addEventListener("submit", function (e) {
      const pw = form.password.value.trim();
      const confirm = form.confirm.value.trim();
  
      if (pw !== confirm) {
        e.preventDefault();
        alert("비밀번호가 일치하지 않습니다.");
      }
    });
  });
  