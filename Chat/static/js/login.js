document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("login-form");
  
    // 등장 애니메이션
    form.classList.add("fade-in");
  
    // shake animation on fake validation fail
    form.addEventListener("submit", function (e) {
      e.preventDefault();
  
      const username = form.username.value.trim();
      const password = form.password.value.trim();
  
      if (username !== "admin" || password !== "admin") {
        form.classList.add("shake");
        setTimeout(() => form.classList.remove("shake"), 500);
      } else {
        form.submit(); // 실제 제출
      }
    });
  });
  