document.addEventListener('DOMContentLoaded', () => {
  const questionInput = document.getElementById('question-input');
  const modeSelect = document.getElementById('mode-select');
  const topkInput = document.getElementById('topk-input');
  const topkVal = document.getElementById('topk-val');
  const btnAsk = document.getElementById('btn-ask');

  const loading = document.getElementById('ask-loading');
  const errorMsg = document.getElementById('ask-error');
  const resultSection = document.getElementById('result-section');
  const answerBox = document.getElementById('answer-box');
  const citationsList = document.getElementById('citations-list');
  const citationsEmpty = document.getElementById('citations-empty');

  // Debug elements
  const debugHeader = document.getElementById('debug-accordion-header');
  const debugContent = document.getElementById('debug-accordion-content');
  const debugChevron = document.getElementById('debug-chevron');
  const debugTabButtons = document.querySelectorAll('#debug-accordion-content .nav-link');
  const debugTabContent = document.getElementById('debug-tab-content');

  let currentDebugData = null;
  let currentDebugTab = 'bm25';
  const savedUrl = localStorage.getItem('backendUrl') || 'http://localhost:8000';

  topkInput.addEventListener('input', (e) => {
    topkVal.textContent = e.target.value;
  });

  questionInput.addEventListener('input', () => {
    btnAsk.disabled = !questionInput.value.trim();
  });

  // Debug accordion
  debugHeader.addEventListener('click', () => {
    const isExpanded = debugContent.style.display === 'block';
    debugContent.style.display = isExpanded ? 'none' : 'block';
    debugChevron.textContent = isExpanded ? '▼' : '▲';
    if (!isExpanded && currentDebugData) {
      renderDebugTab();
    }
  });

  // Debug tabs
  debugTabButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      debugTabButtons.forEach(b => {
        b.classList.remove('active');
        b.style.borderColor = 'transparent';
      });
      const target = e.target;
      target.classList.add('active');
      target.style.borderColor = 'var(--color-forest-ink)';
      currentDebugTab = target.getAttribute('data-tab');
      renderDebugTab();
    });
  });

  function renderDebugTab() {
    if (!currentDebugData) return;
    debugTabContent.innerHTML = '';
    
    let hits = [];
    let scoreLabel = '';
    let prefix = '';

    if (currentDebugTab === 'bm25') {
      hits = currentDebugData.bm25_hits;
      scoreLabel = 'score';
    } else if (currentDebugTab === 'vector') {
      hits = currentDebugData.vector_hits;
      scoreLabel = 'similarity';
    } else if (currentDebugTab === 'fused') {
      hits = currentDebugData.fused_order;
      scoreLabel = 'RRF';
    } else if (currentDebugTab === 'reranked') {
      hits = currentDebugData.reranked_order;
      scoreLabel = 'cross-encoder';
      prefix = '#';
    }

    if (!hits || hits.length === 0) {
      debugTabContent.innerHTML = `<div class="body-sm" style="color: var(--color-charcoal);">No hits.</div>`;
      return;
    }

    hits.forEach((hit, i) => {
      const card = document.createElement('div');
      card.style.backgroundColor = 'var(--color-linen-white)';
      card.style.borderLeft = '3px solid var(--color-sage-wash)';
      card.style.padding = 'var(--spacing-14)';
      card.style.borderRadius = '0 var(--radius-nav) var(--radius-nav) 0';
      card.style.marginBottom = 'var(--spacing-4)';
      
      card.innerHTML = `
        <div style="font-size: var(--text-caption); margin-bottom: var(--spacing-7);">
          <strong style="color: var(--color-forest-ink);">${prefix ? prefix + (i+1) + ' ' : ''}${hit.chunk_id}</strong> 
          <span style="color: var(--color-charcoal);">(${scoreLabel}: ${Number(hit.score).toFixed(4)})</span>
        </div>
        <div class="body-sm" style="color: var(--color-true-black);">${hit.text_preview}...</div>
      `;
      debugTabContent.appendChild(card);
    });
  }

  btnAsk.addEventListener('click', async () => {
    const question = questionInput.value.trim();
    if (!question) return;

    loading.style.display = 'flex';
    errorMsg.style.display = 'none';
    resultSection.style.display = 'none';
    btnAsk.disabled = true;

    try {
      const response = await fetch(`${savedUrl}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: question,
          mode: modeSelect.value,
          top_k: parseInt(topkInput.value, 10)
        })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || `HTTP error ${response.status}`);
      }

      // Answer
      // Formatting markdown simply for now (bolding and line breaks)
      let formattedAnswer = data.answer.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
      answerBox.innerHTML = formattedAnswer;

      // Citations
      citationsList.innerHTML = '';
      if (data.citations && data.citations.length > 0) {
        citationsEmpty.style.display = 'none';
        data.citations.forEach((cit, i) => {
          const card = document.createElement('div');
          card.className = 'card';
          card.style.padding = 'var(--spacing-14)';
          card.innerHTML = `
            <div style="display: flex; gap: var(--spacing-7); align-items: baseline; margin-bottom: var(--spacing-7);">
              <span style="color: var(--color-forest-ink); font-size: var(--text-body-sm); font-weight: 700;">[${i+1}]</span>
              <span class="body-sm">${cit.doc_title || 'Unknown'}</span>
            </div>
            <div style="font-size: var(--text-caption); color: var(--color-charcoal); font-style: italic; margin-bottom: var(--spacing-7);">Chunk: ${cit.chunk_id}</div>
            <div class="body-sm" style="color: var(--color-charcoal); opacity: 0.7;">"${cit.snippet}..."</div>
          `;
          citationsList.appendChild(card);
        });
      } else {
        citationsEmpty.style.display = 'block';
      }

      // Debug
      currentDebugData = data.retrieval_debug;
      if (debugContent.style.display === 'block') {
        renderDebugTab();
      }

      resultSection.style.display = 'block';

    } catch (e) {
      errorMsg.textContent = `Error: ${e.message}`;
      errorMsg.style.display = 'block';
    } finally {
      loading.style.display = 'none';
      btnAsk.disabled = false;
    }
  });

});
