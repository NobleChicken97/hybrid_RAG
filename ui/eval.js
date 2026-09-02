document.addEventListener('DOMContentLoaded', () => {
  const qaSetInput = document.getElementById('qa-set-input');
  const modeSelect = document.getElementById('mode-select');
  const btnRun = document.getElementById('btn-run');

  const loading = document.getElementById('eval-loading');
  const errorMsg = document.getElementById('eval-error');
  const successMsg = document.getElementById('eval-success');
  const resultSection = document.getElementById('result-section');

  const savedUrl = localStorage.getItem('backendUrl') || 'http://localhost:8000';

  qaSetInput.addEventListener('input', () => {
    btnRun.disabled = !qaSetInput.value.trim();
  });

  btnRun.addEventListener('click', async () => {
    const qaSet = qaSetInput.value.trim();
    if (!qaSet) return;

    loading.style.display = 'flex';
    errorMsg.style.display = 'none';
    successMsg.style.display = 'none';
    resultSection.style.display = 'none';
    btnRun.disabled = true;

    try {
      const response = await fetch(`${savedUrl}/eval/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          qa_set_name: qaSet,
          mode: modeSelect.value
        })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || `HTTP error ${response.status}`);
      }

      successMsg.innerHTML = `✅ Evaluation complete! Run ID: <strong>${data.run_id}</strong>`;
      successMsg.style.display = 'block';

      // Scores
      document.getElementById('score-faithfulness').textContent = Number(data.scores.faithfulness || 0).toFixed(4);
      document.getElementById('score-answer-relevancy').textContent = Number(data.scores.answer_relevancy || 0).toFixed(4);
      document.getElementById('score-context-precision').textContent = Number(data.scores.context_precision || 0).toFixed(4);
      document.getElementById('score-context-recall').textContent = Number(data.scores.context_recall || 0).toFixed(4);

      // Breakdown
      const tbody = document.getElementById('breakdown-body');
      tbody.innerHTML = '';
      if (data.per_question_breakdown) {
        data.per_question_breakdown.forEach(item => {
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${item.question}">${item.question}</td>
            <td>${Number(item.faithfulness || 0).toFixed(4)}</td>
            <td>${Number(item.answer_relevancy || 0).toFixed(4)}</td>
            <td>${Number(item.context_precision || 0).toFixed(4)}</td>
            <td>${Number(item.context_recall || 0).toFixed(4)}</td>
          `;
          tbody.appendChild(tr);
        });
      }

      resultSection.style.display = 'block';
      loadPastRuns(); // Refresh table

    } catch (e) {
      errorMsg.textContent = `Error: ${e.message}`;
      errorMsg.style.display = 'block';
    } finally {
      loading.style.display = 'none';
      btnRun.disabled = false;
    }
  });

  // Past Runs
  async function loadPastRuns() {
    try {
      const response = await fetch(`${savedUrl}/eval/runs`);
      if (!response.ok) return;
      const data = await response.json();
      
      const noRunsMsg = document.getElementById('no-runs-msg');
      const tableContainer = document.getElementById('runs-table-container');
      const tbody = document.getElementById('runs-body');
      
      const run1Select = document.getElementById('run1-select');
      const run2Select = document.getElementById('run2-select');

      if (data && data.length > 0) {
        noRunsMsg.style.display = 'none';
        tableContainer.style.display = 'block';
        tbody.innerHTML = '';
        
        // Selectors for compare
        run1Select.innerHTML = '';
        run2Select.innerHTML = '';

        data.forEach((run, index) => {
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td style="font-family: monospace;">${run.run_id}</td>
            <td>${run.retrieval_mode}</td>
            <td>${new Date(run.timestamp).toLocaleString()}</td>
            <td>${Number(run.scores.faithfulness || 0).toFixed(4)}</td>
            <td>${Number(run.scores.answer_relevancy || 0).toFixed(4)}</td>
            <td>${Number(run.scores.context_precision || 0).toFixed(4)}</td>
            <td>${Number(run.scores.context_recall || 0).toFixed(4)}</td>
          `;
          tbody.appendChild(tr);

          const opt1 = new Option(run.run_id, run.run_id);
          const opt2 = new Option(run.run_id, run.run_id);
          run1Select.add(opt1);
          run2Select.add(opt2);
        });

        if (data.length >= 2) {
          document.getElementById('compare-divider').style.display = 'block';
          document.getElementById('compare-section').style.display = 'block';
          run2Select.selectedIndex = 1; // Default select second item for comparison
        } else {
          document.getElementById('compare-divider').style.display = 'none';
          document.getElementById('compare-section').style.display = 'none';
        }

      } else {
        noRunsMsg.style.display = 'block';
        tableContainer.style.display = 'none';
        document.getElementById('compare-divider').style.display = 'none';
        document.getElementById('compare-section').style.display = 'none';
      }
    } catch(e) {}
  }

  loadPastRuns();

  // Compare Logic
  const btnCompare = document.getElementById('btn-compare');
  const compResult = document.getElementById('compare-result');
  const compBody = document.getElementById('comp-body');

  btnCompare.addEventListener('click', async () => {
    const id1 = document.getElementById('run1-select').value;
    const id2 = document.getElementById('run2-select').value;
    if (id1 === id2) {
      alert('Please select two different runs to compare.');
      return;
    }
    
    try {
      const response = await fetch(`${savedUrl}/eval/compare?run_id_1=${id1}&run_id_2=${id2}`, { method: 'POST' });
      if (!response.ok) throw new Error('Failed to compare');
      const data = await response.json();

      document.getElementById('comp-mode-1').textContent = `Run 1 (${data.run_1.retrieval_mode})`;
      document.getElementById('comp-mode-2').textContent = `Run 2 (${data.run_2.retrieval_mode})`;

      compBody.innerHTML = '';
      const metrics = ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall'];
      
      metrics.forEach(m => {
        const v1 = data.run_1.scores[m] || 0;
        const v2 = data.run_2.scores[m] || 0;
        const diff = v2 - v1;
        let diffColor = diff > 0 ? 'var(--color-forest-ink)' : (diff < 0 ? '#dc2626' : 'var(--color-true-black)');
        let diffSign = diff > 0 ? '+' : '';

        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${m}</strong></td>
          <td>${v1.toFixed(4)}</td>
          <td>${v2.toFixed(4)}</td>
          <td style="color: ${diffColor};">${diffSign}${diff.toFixed(4)}</td>
        `;
        compBody.appendChild(tr);
      });

      document.getElementById('comp-summary').textContent = data.summary;
      compResult.style.display = 'block';

    } catch(e) {
      alert(e.message);
    }
  });
});
