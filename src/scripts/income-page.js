// src/scripts/income-page.js
// 소득 백분위 계산기 — 클라이언트 사이드 로직
// Vite가 이 파일을 번들링하여 _astro/*.js 로 출력함
import { calcTopPct } from '../lib/income-percentile.js';

document.addEventListener('DOMContentLoaded', () => {
  // ── DOM refs ──
  const modeBtns     = document.querySelectorAll('#mode-toggle .toggle-btn');
  const incomeInput  = document.getElementById('income-input');
  const calcBtn      = document.getElementById('calc-btn');
  const resultSec    = document.getElementById('result-section');
  const errEl        = document.getElementById('input-error');
  const warnEl       = document.getElementById('input-warn');
  const unitEl       = document.getElementById('amount-unit');

  const resultIncome = document.getElementById('result-income');
  const gaugeFill    = document.getElementById('gauge-fill');
  const gaugeMarker  = document.getElementById('gauge-marker');
  const resultPct    = document.getElementById('result-percentile');

  const shareUrlBtn  = document.getElementById('share-url-btn');
  const shareKakaoBtn= document.getElementById('share-kakao-btn');
  const toast        = document.getElementById('share-toast');

  let currentMode = 'annual'; // 'annual' | 'monthly'

  // ── 모드 전환 ──
  modeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      modeBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentMode = btn.dataset.mode;
      unitEl.textContent = '만원';
      incomeInput.placeholder = currentMode === 'annual' ? '5000' : '400';
      // 입력값 초기화 (모드 전환 시 혼동 방지)
      incomeInput.value = '';
      errEl.classList.remove('visible');
      warnEl.classList.remove('visible');
      resultSec.classList.remove('visible');
      calcBtn.disabled = true;
    });
  });

  // ── 입력 검증 ──
  function validateInput(val) {
    const num = parseFloat(val);
    if (!val || val.trim() === '') return { valid: false, error: '금액을 입력해주세요' };
    if (isNaN(num) || num <= 0) return { valid: false, error: '0보다 큰 금액을 입력해주세요' };

    // 연봉 100억 = 10,000,000만원 — 비정상 큰 값 경고
    if (currentMode === 'annual' && num > 1000000) {
      return { valid: true, value: num, warn: true };
    }
    if (currentMode === 'monthly' && num > 100000) {
      return { valid: true, value: num, warn: true };
    }
    return { valid: true, value: num, warn: false };
  }

  incomeInput.addEventListener('input', () => {
    const val = incomeInput.value;
    const result = validateInput(val);
    errEl.classList.remove('visible');
    warnEl.classList.remove('visible');
    incomeInput.classList.remove('error');

    if (!result.valid) {
      calcBtn.disabled = true;
      if (val && val.trim() !== '') {
        errEl.textContent = result.error;
        errEl.classList.add('visible');
        incomeInput.classList.add('error');
      }
    } else {
      calcBtn.disabled = false;
      if (result.warn) {
        warnEl.classList.add('visible');
      }
    }
  });

  // ── 계산 실행 ──
  function calculate() {
    const val = incomeInput.value;
    const result = validateInput(val);
    if (!result.valid) return;

    let monthlyIncome;
    if (currentMode === 'annual') {
      monthlyIncome = result.value / 12;  // 연봉 → 월소득
    } else {
      monthlyIncome = result.value;       // 이미 월소득
    }

    // 반올림 (소수 첫째 자리)
    monthlyIncome = Math.round(monthlyIncome * 10) / 10;
    if (monthlyIncome <= 0) return;

    const topPct = calcTopPct(monthlyIncome);
    if (topPct === null) return;

    // 결과 표시
    const fillWidth = Math.max(1, 100 - topPct);  // 최소 1% 너비 보장
    gaugeFill.style.width = fillWidth + '%';
    gaugeMarker.style.left = fillWidth + '%';
    resultPct.textContent = '상위 ' + topPct + '%';

    // 월소득 표시 (정수로 반올림)
    const displayIncome = Math.round(monthlyIncome);
    resultIncome.innerHTML = displayIncome.toLocaleString() + '<span class="income-unit">만원</span>';

    resultSec.classList.add('visible');

    // URL 갱신 (공유용)
    const params = new URLSearchParams();
    if (currentMode === 'annual') {
      params.set('salary', String(Math.round(result.value)));
    } else {
      params.set('monthly', String(Math.round(result.value)));
    }
    const newUrl = window.location.pathname + '?' + params.toString();
    window.history.replaceState({}, '', newUrl);
  }

  calcBtn.addEventListener('click', calculate);

  // ── Enter 키로 계산 ──
  incomeInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !calcBtn.disabled) {
      e.preventDefault();
      calculate();
    }
  });

  // ── URL 파라미터 자동 로드 (manual input과 동일한 validateInput 사용) ──
  (function loadFromUrl() {
    const params = new URLSearchParams(window.location.search);
    const salaryVal  = params.get('salary');
    const monthlyVal = params.get('monthly');

    if (salaryVal) {
      // 연봉 모드
      currentMode = 'annual';
      modeBtns.forEach(b => b.classList.toggle('active', b.dataset.mode === 'annual'));
      incomeInput.value = salaryVal;
      // 동일한 validateInput() 검증 적용
      const result = validateInput(salaryVal);
      if (!result.valid) {
        errEl.textContent = result.error;
        errEl.classList.add('visible');
        incomeInput.classList.add('error');
        calcBtn.disabled = true;
        return; // calcTopPct 호출 없이 초기 상태 유지
      }
      if (result.warn) {
        warnEl.classList.add('visible');
      }
      calcBtn.disabled = false;
      calculate();
    } else if (monthlyVal) {
      // 월소득 모드
      currentMode = 'monthly';
      modeBtns.forEach(b => b.classList.toggle('active', b.dataset.mode === 'monthly'));
      unitEl.textContent = '만원';
      incomeInput.value = monthlyVal;
      const result = validateInput(monthlyVal);
      if (!result.valid) {
        errEl.textContent = result.error;
        errEl.classList.add('visible');
        incomeInput.classList.add('error');
        calcBtn.disabled = true;
        return; // calcTopPct 호출 없이 초기 상태 유지
      }
      if (result.warn) {
        warnEl.classList.add('visible');
      }
      calcBtn.disabled = false;
      calculate();
    }
  })();

  // ── 링크 복사 ──
  shareUrlBtn.addEventListener('click', () => {
    const url = window.location.href;
    navigator.clipboard.writeText(url).then(() => {
      toast.classList.add('visible');
      setTimeout(() => toast.classList.remove('visible'), 2500);
    }).catch(() => {
      // 폴백
      const input = document.createElement('input');
      input.value = url;
      document.body.appendChild(input);
      input.select();
      document.execCommand('copy');
      document.body.removeChild(input);
      toast.classList.add('visible');
      setTimeout(() => toast.classList.remove('visible'), 2500);
    });
  });

  // ── 카카오톡 공유 ──
  shareKakaoBtn.addEventListener('click', () => {
    const url = window.location.href;
    if (window.Kakao && window.Kakao.isInitialized()) {
      window.Kakao.Share.sendDefault({
        objectType: 'feed',
        content: {
          title: '내 소득 백분위 확인하기',
          description: '내 연봉이 전체 취업자 중 상위 몇 %인지 확인해보세요.',
          imageUrl: 'https://persona.aikorea24.kr/og-default.png',
          link: { mobileWebUrl: url, webUrl: url },
        },
        buttons: [{
          title: '계산하기',
          link: { mobileWebUrl: url, webUrl: url },
        }],
      });
    } else {
      navigator.clipboard.writeText(url).then(() => {
        toast.textContent = '링크가 복사되었습니다. 카카오톡에 붙여넣어 공유하세요';
        toast.classList.add('visible');
        setTimeout(() => {
          toast.classList.remove('visible');
          toast.textContent = '링크가 복사되었습니다';
        }, 3000);
      });
    }
  });
});
