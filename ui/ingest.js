document.addEventListener('DOMContentLoaded', () => {
  const tabFile = document.getElementById('tab-file');
  const tabText = document.getElementById('tab-text');
  const contentFile = document.getElementById('content-file');
  const contentText = document.getElementById('content-text');

  // Tabs logic
  tabFile.addEventListener('click', () => {
    tabFile.classList.add('active');
    tabFile.style.borderColor = 'var(--color-forest-ink)';
    tabText.classList.remove('active');
    tabText.style.borderColor = 'transparent';
    contentFile.style.display = 'flex';
    contentText.style.display = 'none';
  });

  tabText.addEventListener('click', () => {
    tabText.classList.add('active');
    tabText.style.borderColor = 'var(--color-forest-ink)';
    tabFile.classList.remove('active');
    tabFile.style.borderColor = 'transparent';
    contentText.style.display = 'flex';
    contentFile.style.display = 'none';
  });

  // File Upload Logic
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');
  const fileNameDisplay = document.getElementById('file-name');
  const fileTitle = document.getElementById('file-title');
  const btnSubmitFile = document.getElementById('btn-submit-file');
  let selectedFile = null;

  dropZone.addEventListener('click', () => fileInput.click());
  
  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
  });
  
  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
  });
  
  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
      handleFile(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length) {
      handleFile(fileInput.files[0]);
    }
  });

  function handleFile(file) {
    selectedFile = file;
    fileNameDisplay.textContent = `Selected: ${file.name}`;
    fileNameDisplay.style.display = 'block';
    if (!fileTitle.value) {
      fileTitle.value = file.name.replace(/\.[^/.]+$/, "");
    }
    checkFileSubmit();
  }

  fileTitle.addEventListener('input', checkFileSubmit);

  function checkFileSubmit() {
    btnSubmitFile.disabled = !(selectedFile && fileTitle.value.trim());
  }

  // Text Paste Logic
  const textInput = document.getElementById('text-input');
  const textTitle = document.getElementById('text-title');
  const btnSubmitText = document.getElementById('btn-submit-text');

  function checkTextSubmit() {
    btnSubmitText.disabled = !(textInput.value.trim() && textTitle.value.trim());
  }

  textInput.addEventListener('input', checkTextSubmit);
  textTitle.addEventListener('input', checkTextSubmit);

  // Form Submission
  const loading = document.getElementById('ingest-loading');
  const errorMsg = document.getElementById('ingest-error');
  const successMsg = document.getElementById('ingest-success');
  const previewSection = document.getElementById('preview-section');
  const chunkList = document.getElementById('chunk-list');
  const savedUrl = localStorage.getItem('backendUrl') || 'http://localhost:8000';

  btnSubmitFile.addEventListener('click', async () => {
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('title', fileTitle.value.trim());
    await submitIngest(formData);
  });

  btnSubmitText.addEventListener('click', async () => {
    const formData = new FormData();
    formData.append('raw_text', textInput.value.trim());
    formData.append('title', textTitle.value.trim());
    await submitIngest(formData);
  });

  async function submitIngest(formData) {
    loading.style.display = 'flex';
    errorMsg.style.display = 'none';
    successMsg.style.display = 'none';
    previewSection.style.display = 'none';
    btnSubmitFile.disabled = true;
    btnSubmitText.disabled = true;

    try {
      const response = await fetch(`${savedUrl}/ingest`, {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || `HTTP error ${response.status}`);
      }

      successMsg.innerHTML = `✅ Document ingested! <strong>${data.chunk_count}</strong> chunks created.`;
      successMsg.style.display = 'block';

      // Render previews
      chunkList.innerHTML = '';
      data.sample_chunks.forEach(chunk => {
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
          <div style="font-size: var(--text-caption); color: var(--color-charcoal); margin-bottom: var(--spacing-7);">
            <strong style="color: var(--color-forest-ink);">📦 ${chunk.chunk_id}</strong> | ${chunk.token_count} tokens
            ${chunk.section_header ? `| 📑 ${chunk.section_header}` : ''}
          </div>
          <div class="body-sm">${chunk.text_preview}...</div>
        `;
        chunkList.appendChild(card);
      });
      previewSection.style.display = 'block';
      updateHealthStats(); // Refresh stats

    } catch (e) {
      errorMsg.textContent = `Error: ${e.message}`;
      errorMsg.style.display = 'block';
    } finally {
      loading.style.display = 'none';
      checkFileSubmit();
      checkTextSubmit();
    }
  }

  // Initial Health Stats
  async function updateHealthStats() {
    try {
      const response = await fetch(`${savedUrl}/health`);
      if (response.ok) {
        const data = await response.json();
        document.getElementById('docs-count').textContent = data.documents_count;
        document.getElementById('chunks-count').textContent = data.chunks_count;
        document.getElementById('evals-count').textContent = data.eval_runs_count;
      }
    } catch(e) {}
  }
  updateHealthStats();
});
