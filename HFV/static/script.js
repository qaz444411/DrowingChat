document.addEventListener('DOMContentLoaded', () => {
  const menuToggle = document.getElementById('menu-toggle');
  const menuClose = document.getElementById('menu-close');
  const sidebar = document.getElementById('sidebar');
  const mainContent = document.getElementById('main-content');
  const userSection = document.getElementById('user-section');
  const searchInput = document.getElementById('search');

  const homeSection = document.getElementById('home-section');
  const signupSection = document.getElementById('signup-section');
  const loginSection = document.getElementById('login-section');
  const findIdSection = document.getElementById('find_id-section');
  const findPasswordSection = document.getElementById('find_password-section');

  const signupForm = document.getElementById('signup-form');
  const loginForm = document.getElementById('login-form');
  const findIdForm = document.getElementById('find-id-form');
  const findPwForm = document.getElementById('find-password-form');

  let isLoggedIn = false;

  function updateUserInfo() {
    userSection.innerHTML = '';
    if (isLoggedIn) {
      ['투자내역 조회', '투자금액 조회', '보유종목 확인', '입출금 내역'].forEach(label => {
        const btn = document.createElement('button');
        btn.textContent = label;
        Object.assign(btn.style, {
          display: 'block', marginBottom: '0.5rem', padding: '0.5rem',
          width: '100%', background: '#555', color: '#fff',
          border: 'none', borderRadius: '6px'
        });
        userSection.appendChild(btn);
      });
    } else {
      const msg = document.createElement('div');
      msg.textContent = '정보 없음 (로그인 필요)';
      msg.style.padding = '1rem';
      userSection.appendChild(msg);
    }
  }

  function showSection(section) {
    [homeSection, signupSection, loginSection, findIdSection, findPasswordSection]
      .forEach(s => s?.classList.add('hidden'));
    section.classList.remove('hidden');
  }

  // 메뉴 토글
  menuToggle.addEventListener('click', () => {
    sidebar.classList.add('open');
    mainContent.classList.add('shifted');
  });

  menuClose.addEventListener('click', () => {
    sidebar.classList.remove('open');
    mainContent.classList.remove('shifted');
  });

  // 검색 기능
  searchInput.addEventListener('input', () => {
    const term = searchInput.value.toLowerCase();
    document.querySelectorAll('.stock').forEach(stock => {
      const name = stock.getAttribute('data-name').toLowerCase();
      stock.style.display = name.includes(term) ? 'block' : 'none';
    });
  });

  // 네비게이션 버튼
  document.getElementById('signup-nav-btn').addEventListener('click', () => showSection(signupSection));
  document.getElementById('login-nav-btn').addEventListener('click', () => showSection(loginSection));
  document.getElementById('signup-link').addEventListener('click', (e) => {
    e.preventDefault();
    showSection(signupSection);
  });
  document.getElementById('login-link').addEventListener('click', (e) => {
    e.preventDefault();
    showSection(loginSection);
  });

  // 아이디/비번 찾기
  document.getElementById('find-id-btn').addEventListener('click', (e) => {
    e.preventDefault();
    showSection(findIdSection);
  });

  document.getElementById('find-password-btn').addEventListener('click', (e) => {
    e.preventDefault();
    showSection(findPasswordSection);
  });

  document.getElementById('back-to-login-from-id').addEventListener('click', (e) => {
    e.preventDefault();
    showSection(loginSection);
  });

  document.getElementById('back-to-login-from-password').addEventListener('click', (e) => {
    e.preventDefault();
    showSection(loginSection);
  });

  // 폼 처리
  signupForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(signupForm);
    const res = await fetch('/signup', { method: 'POST', body: formData });
    const result = await res.json();
    alert(result.message);
    if (result.success) showSection(loginSection);
  });

  loginForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(loginForm);
    const res = await fetch('/login', { method: 'POST', body: formData });
    const result = await res.json();
    alert(result.message);
    if (result.success) {
      isLoggedIn = true;
      updateUserInfo();
      showSection(homeSection);
    }
  });

  findIdForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(findIdForm);
    const res = await fetch('/find_id', { method: 'POST', body: formData });
    const text = await res.text();
    alert(text);
    showSection(loginSection);
  });

  findPwForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(findPwForm);
    const res = await fetch('/find_password', { method: 'POST', body: formData });
    const text = await res.text();
    alert(text);
    showSection(loginSection);
  });

  updateUserInfo();
});
