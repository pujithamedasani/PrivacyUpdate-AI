/* PrivacyUpdate AI - Client Application Logic */

// Global HTML sanitization helper
function escapeHtml(text) {
  if (text === null || text === undefined) return '';
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// Modal utilities
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('show');
    document.body.style.overflow = '';
  }
}

// Close modal when clicking backdrop
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-backdrop')) {
    e.target.classList.remove('show');
    document.body.style.overflow = '';
  }
});

// Toast notification helper
function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  let iconSvg = '';
  if (type === 'success') {
    iconSvg = '<svg viewBox="0 0 24 24" width="16" height="16" stroke="#3A7D44" stroke-width="2" fill="none"><polyline points="20 6 9 17 4 12"></polyline></svg>';
  } else if (type === 'error') {
    iconSvg = '<svg viewBox="0 0 24 24" width="16" height="16" stroke="#C17C5A" stroke-width="2" fill="none"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>';
  } else {
    iconSvg = '<svg viewBox="0 0 24 24" width="16" height="16" stroke="#D97706" stroke-width="2" fill="none"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>';
  }

  toast.innerHTML = `
    <div style="flex-shrink: 0; padding-top: 2px;">${iconSvg}</div>
    <div class="toast-message">${message}</div>
    <button onclick="this.parentElement.remove()" style="background:none;border:none;cursor:pointer;color:var(--text-muted);font-size:1.1rem;line-height:1;">&times;</button>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.25s ease';
    setTimeout(() => toast.remove(), 250);
  }, 4500);
}

// Sidebar mobile toggle
document.addEventListener('DOMContentLoaded', () => {
  const toggleBtn = document.getElementById('sidebar-toggle');
  const sidebar = document.getElementById('sidebar');

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('show');
    });
  }

  // Open settings modal button
  const settingsBtn = document.getElementById('btn-open-settings');
  if (settingsBtn) {
    settingsBtn.addEventListener('click', () => {
      openModal('settings-modal');
      loadSettingsStatus();
    });
  }
});

// Load integrations health
async function loadSettingsStatus() {
  try {
    const res = await fetch('/api/settings/status');
    const data = await res.json();
    if (!data.success) return;

    // Firecrawl
    const fcBadge = document.getElementById('firecrawl-status-badge');
    const fcDesc = document.getElementById('firecrawl-desc');
    if (fcBadge && fcDesc) {
      if (data.firecrawl.configured) {
        fcBadge.className = 'badge badge-success';
        fcBadge.textContent = 'Configured (Active)';
        fcDesc.textContent = 'API key loaded. Clean DOM scraping active.';
      } else {
        fcBadge.className = 'badge badge-warning';
        fcBadge.textContent = 'Fallback Mode';
        fcDesc.textContent = 'FIRECRAWL_API_KEY not set. Using direct clean HTTP extractor.';
      }
    }

    // OpenAI / Groq AI Engine
    const aiBadge = document.getElementById('openai-status-badge');
    const aiDesc = document.getElementById('openai-desc');
    if (aiBadge && aiDesc) {
      if (data.openai.configured) {
        aiBadge.className = 'badge badge-success';
        aiBadge.textContent = data.openai.provider ? `Configured (${data.openai.provider})` : `Configured (${data.openai.model})`;
        aiDesc.textContent = 'Generative privacy policy diff explanations and impact scoring enabled.';
      } else {
        aiBadge.className = 'badge badge-warning';
        aiBadge.textContent = 'Rule-based Mode';
        aiDesc.textContent = 'AI Key not set. Using keyword heuristic privacy rubric.';
      }
    }
  } catch (err) {
    console.error('Failed to load status:', err);
  }
}

// Ping specific service
async function testService(target) {
  showToast(`Testing ${target} connection...`, 'info');
  try {
    const res = await fetch('/api/settings/test-connection', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target })
    });
    const data = await res.json();
    if (data.success) {
      showToast(data.message, 'success');
    } else {
      showToast(data.error, 'error');
    }
  } catch (err) {
    showToast(`Test failed: ${err.message}`, 'error');
  }
}
