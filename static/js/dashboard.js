/* PrivacyUpdate AI - Dashboard Telemetry & Chart.js Integration */

let timelineChart = null;
let categoriesChart = null;
let reviewsChart = null;
let severityChart = null;

document.addEventListener('DOMContentLoaded', () => {
  fetchDashboardStats();
});

async function fetchDashboardStats() {
  try {
    const res = await fetch('/api/dashboard/stats');
    const data = await res.json();
    if (!data.success) return;

    // 1. Update KPI Values
    document.getElementById('kpi-sources').textContent = data.summary.total_sources;
    document.getElementById('kpi-active-sources').textContent = data.summary.active_sources;
    document.getElementById('kpi-snapshots').textContent = data.summary.total_snapshots;
    document.getElementById('kpi-changes').textContent = data.summary.total_changes;
    document.getElementById('kpi-pending-reviews').textContent = data.summary.pending_reviews;

    // 2. Render Chart 1: Activity Timeline
    renderTimelineChart(data.timeline);

    // 3. Render Chart 2: Categories Distribution
    renderCategoriesChart(data.categories_distribution);

    // 4. Render Chart 3: Reviews Distribution
    renderReviewsChart(data.reviews_distribution);

    // 5. Render Chart 4: Severity Risk Breakdown
    renderSeverityChart(data.severity_distribution);

    // 6. Populate Recent Changes Table
    populateRecentChanges(data.recent_changes);

    // 7. Populate Recent Logs Table
    populateRecentLogs(data.recent_logs);

  } catch (err) {
    console.error('Failed to load dashboard statistics:', err);
  }
}

function renderTimelineChart(timeline) {
  const ctx = document.getElementById('chart-timeline');
  if (!ctx) return;

  const labels = timeline.length > 0 ? timeline.map(t => t.date) : ['No activity'];
  const counts = timeline.length > 0 ? timeline.map(t => t.count) : [0];

  if (timelineChart) timelineChart.destroy();
  timelineChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Policy Scans & Captures',
        data: counts,
        borderColor: '#344E41',
        backgroundColor: 'rgba(52, 78, 65, 0.12)',
        fill: true,
        tension: 0.35,
        pointBackgroundColor: '#C17C5A',
        pointBorderColor: '#FFFFFF',
        pointBorderWidth: 2,
        pointRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { stepSize: 1, color: '#6C756F' },
          grid: { color: 'rgba(226, 221, 213, 0.6)' }
        },
        x: {
          ticks: { color: '#6C756F' },
          grid: { display: false }
        }
      }
    }
  });
}

function renderCategoriesChart(categories) {
  const ctx = document.getElementById('chart-categories');
  if (!ctx) return;

  const labels = Object.keys(categories);
  const counts = Object.values(categories);

  const earthyColors = [
    '#344E41', '#A3B18A', '#C17C5A', '#588157',
    '#3A5A40', '#DDA15E', '#BC6C25', '#6B705C'
  ];

  if (categoriesChart) categoriesChart.destroy();
  categoriesChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels.length > 0 ? labels : ['None'],
      datasets: [{
        data: counts.length > 0 ? counts : [0],
        backgroundColor: earthyColors.slice(0, labels.length || 1),
        borderWidth: 2,
        borderColor: '#FFFFFF'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: { boxWidth: 12, font: { size: 11 }, color: '#292D2A' }
        }
      },
      cutout: '65%'
    }
  });
}

function renderReviewsChart(reviewsDist) {
  const ctx = document.getElementById('chart-reviews');
  if (!ctx) return;

  const labels = Object.keys(reviewsDist);
  const counts = Object.values(reviewsDist);

  if (reviewsChart) reviewsChart.destroy();
  reviewsChart = new Chart(ctx, {
    type: 'pie',
    data: {
      labels: labels,
      datasets: [{
        data: counts,
        backgroundColor: ['#3A7D44', '#D97706', '#C17C5A'],
        borderWidth: 2,
        borderColor: '#FFFFFF'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: { boxWidth: 12, font: { size: 11 }, color: '#292D2A' }
        }
      }
    }
  });
}

function renderSeverityChart(severities) {
  const ctx = document.getElementById('chart-severity');
  if (!ctx) return;

  const labels = ['Critical', 'High', 'Medium', 'Low'];
  const counts = labels.map(l => (severities && severities[l]) || 0);

  const colors = [
    '#C17C5A', // Critical (terracotta / high risk)
    '#D97706', // High (amber)
    '#DDA15E', // Medium (warm gold)
    '#588157'  // Low (forest green)
  ];

  if (severityChart) severityChart.destroy();
  severityChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Detected Policy Changes',
        data: counts,
        backgroundColor: colors,
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          beginAtZero: true,
          ticks: { stepSize: 1, color: '#6C756F' },
          grid: { color: 'rgba(226, 221, 213, 0.6)' }
        },
        y: {
          ticks: { color: '#292D2A', font: { weight: '600' } },
          grid: { display: false }
        }
      }
    }
  });
}

function populateRecentChanges(changes) {
  const tbody = document.getElementById('recent-changes-tbody');
  if (!tbody) return;

  if (!changes || changes.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color: var(--text-muted); padding: 1.5rem;">No policy changes detected yet.</td></tr>';
    return;
  }

  tbody.innerHTML = changes.map(c => {
    let sevBadge = 'badge-neutral';
    if (c.severity === 'Critical') sevBadge = 'badge-danger';
    else if (c.severity === 'High') sevBadge = 'badge-danger';
    else if (c.severity === 'Medium') sevBadge = 'badge-warning';
    else if (c.severity === 'Low') sevBadge = 'badge-success';

    let revBadge = 'badge-neutral';
    if (c.review_status === 'Approved') revBadge = 'badge-success';
    else if (c.review_status === 'Pending') revBadge = 'badge-warning';
    else revBadge = 'badge-danger';

    return `
      <tr>
        <td><strong>${escapeHtml(c.source_name)}</strong></td>
        <td><span style="font-size: 0.8rem;">${escapeHtml(c.affected_section)}</span></td>
        <td><span class="badge badge-neutral" style="font-size: 0.72rem;">${escapeHtml(c.category)}</span></td>
        <td><span class="badge ${sevBadge}" style="font-size: 0.72rem;">${escapeHtml(c.severity)}</span></td>
        <td><span class="badge ${revBadge}" style="font-size: 0.72rem;">${escapeHtml(c.review_status)}</span></td>
      </tr>
    `;
  }).join('');
}

function populateRecentLogs(logs) {
  const tbody = document.getElementById('recent-logs-tbody');
  if (!tbody) return;

  if (!logs || logs.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color: var(--text-muted); padding: 1.5rem;">No monitoring logs recorded.</td></tr>';
    return;
  }

  tbody.innerHTML = logs.map(l => {
    let statBadge = 'badge-neutral';
    if (l.status === 'Success') statBadge = 'badge-success';
    else if (l.status === 'Failed') statBadge = 'badge-danger';
    else statBadge = 'badge-warning';

    const shortTime = l.created_at ? l.created_at.slice(11, 16) : '';

    return `
      <tr>
        <td style="font-size: 0.78rem; color: var(--text-muted); white-space: nowrap;">${shortTime}</td>
        <td><strong>${escapeHtml(l.source_name || 'System')}</strong></td>
        <td><span class="badge badge-neutral" style="font-size: 0.7rem;">${escapeHtml(l.extraction_tool)}</span></td>
        <td><span class="badge ${statBadge}" style="font-size: 0.7rem;">${escapeHtml(l.status)}</span></td>
        <td style="font-size: 0.78rem; color: var(--text-muted); max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(l.message)}">
          ${escapeHtml(l.message)}
        </td>
      </tr>
    `;
  }).join('');
}

function escapeHtml(text) {
  if (!text) return '';
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
