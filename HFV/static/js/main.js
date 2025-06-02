function toggleAIBox() {
  const aiBox = document.getElementById('ai-box');
  aiBox.style.display = (aiBox.style.display === 'none') ? 'block' : 'none';
}

async function sendToAI() {
  const q = document.getElementById("question").value;
  const res = await fetch("/ai/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question: q })
  });

  const data = await res.json();
  const answer = data.response || data.error;

  const card = document.getElementById("ai-response-card");
  card.style.display = "block";
  card.innerHTML = `
    <div class="ai-answer-box">
      <h4>📌 HFV 분석기 </h4>
      <p>${answer.replace(/\n/g, "<br>")}</p>
    </div>
  `;
}

//검색 주식 값 전송
async function searchStock() {
  const keyword = document.getElementById('search-input').value.trim();
  if (!keyword) return;

  const res = await fetch(`/search_stock?keyword=${encodeURIComponent(keyword)}`);
  const result = await res.json();

  const container = document.getElementById('search-result');
  if (result.data) {
    container.innerHTML = `
      <div><strong>${result.data.name} (${result.data.code})</strong></div>
      <div>현재가: ${result.data.price.toLocaleString()}원</div>
      <div>등락률: ${result.data.change > 0 ? '+' : ''}${result.data.change.toFixed(2)}%</div>
      <div>거래대금: ${(result.data.volume / 1e8).toFixed(1)}억</div>
    `;
  } else {
    container.innerHTML = `<div>검색된 종목이 없습니다.</div>`;
  }
}

  let currentPage = 1;
  let currentSort = 'volume'; // 초기 정렬 기준
  
  // 정렬
  function changeSort(sortBy) {
    currentSort = sortBy;
    currentPage = 1; // 정렬 바뀌면 첫 페이지부터 시작
    fetchStockList();
  }
  
  // 테이블 주식 값 전송
  async function fetchStockList() {
    const res = await fetch(`/get_stock_data_list?page=${currentPage}&sort_by=${currentSort}`);
    const data = await res.json();
  
    const tbody = document.getElementById('stock-body');
    tbody.innerHTML = '';
  
    data.forEach(stock => {
      const changeClass = stock.change > 0 ? 'up' : stock.change < 0 ? 'down' : 'neutral';
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${stock.rank}</td>
        <td>${stock.name} (${stock.code})</td>
        <td>${stock.price.toLocaleString()}원</td>
        <td class="${changeClass}">${stock.change > 0 ? '+' : ''}${stock.change.toFixed(2)}%</td>
        <td>${(stock.volume / 1e8).toFixed(1)}억</td>
      `;
      tbody.appendChild(tr);
    });
  }


  // 환율 정보 가져오기
  async function fetchExchangeRates() {
    const res = await fetch('/exchange_rates');
    const data = await res.json();
  
    const el = document.getElementById('exchange-container');
    el.innerHTML = '';
  
    const flags = {
      USD: "🇺🇸",
      JPY: "🇯🇵",
      CNY: "🇨🇳",
      HKD: "🇭🇰"
    };
  
    Object.entries(data).forEach(([code, info]) => {
      if (info.rate) {
        const sign = info.updn === "1" ? "+" : info.updn === "2" ? "-" : "";
        const color = info.updn === "1" ? "red" : info.updn === "2" ? "blue" : "gray";
        el.innerHTML += `
          <div class="exchange-item">
            ${flags[code]} ${code}/KRW: ${info.rate.toLocaleString()}원
            <span style="color: ${color};">(${sign}${info.change})</span>
          </div>
        `;
      } else {
        el.innerHTML += `<div class="exchange-item">${flags[code]} ${code}/KRW: 조회 실패</div>`;
      }
    });
  }
  
  document.getElementById('next-btn')?.addEventListener('click', nextPage);
  document.getElementById('prev-btn')?.addEventListener('click', prevPage);
  
  fetchStockList();
  fetchExchangeRates();
  setInterval(fetchStockList, 10000); // 주식 리스트 10초마다 갱신
  setInterval(fetchExchangeRates, 60000); // 환율은 1분마다 갱신