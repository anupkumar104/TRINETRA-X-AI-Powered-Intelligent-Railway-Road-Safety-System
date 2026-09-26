
let cameras = [];
let selectedCamera = null;
let currentMode = 'railway';

let previousAlertIds = new Set();
let firstAlertLoad = true;
let refreshBusy = false;
let latestAlert = null;

const $ = id => document.getElementById(id);

function safeText(v) {
  return String(v ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  }[c]));
}

function cameraLabel(v) {
  return String(v || '')
    .replaceAll('_', ' ')
    .replace(/\b\w/g, x => x.toUpperCase());
}

function updateClock() {
  if ($('clock')) {
    $('clock').textContent =
      new Date().toLocaleTimeString('en-IN', { hour12: false });
  }
}

function showToast(title, msg, type = 'normal') {
  const c = $('toastContainer');
  if (!c) return;

  const e = document.createElement('div');
  e.className = `toast ${type}`;
  e.innerHTML = `<b>${safeText(title)}</b><span>${safeText(msg)}</span>`;

  c.appendChild(e);
  setTimeout(() => e.remove(), 5000);
}

// ==========================================
// MODE
// ==========================================

function setMode(mode) {
  if (!['railway', 'road'].includes(mode)) return;

  currentMode = mode;
  updateModeUI();

  if (
    selectedCamera &&
    String(selectedCamera.mode).toLowerCase() !== mode
  ) {
    stopCamera(false);
  }

  loadCameras(true);
  refreshTargets();
  refreshStatus();
}

function updateModeUI() {
  const rail = currentMode === 'railway';

  $('railwayModeBtn')?.classList.toggle('active', rail);
  $('roadModeBtn')?.classList.toggle('active', !rail);

  $('modeBadge').textContent = rail ? 'RAILWAY MODE' : 'ROAD MODE';
  $('modeBadge').className = `badge ${currentMode}`;

  $('zoneBadge').textContent = rail ? 'ZONE Z001' : 'ZONE Z002';

  $('heroTitle').textContent = rail
    ? 'Intelligent Railway Protection'
    : 'Intelligent Road Protection';

  $('heroSubtitle').textContent = rail
    ? 'Real-time animal detection, zone-aware risk analysis and safety alert routing for railway operations.'
    : 'Real-time animal detection, zone-aware risk analysis and safety alert routing for road operations.';

  $('cameraHeading').textContent = rail
    ? 'Railway Cameras'
    : 'Road Cameras';

  $('modeSummaryTitle').textContent = rail
    ? 'RAILWAY MODE'
    : 'ROAD MODE';

  $('modeSummaryText').textContent = rail
    ? 'Z001 • train safety monitoring'
    : 'Z002 • vehicle safety monitoring';

  $('operationsTitle').textContent = rail
    ? 'Railway Zone Operations'
    : 'Road Zone Operations';
}

// ==========================================
// CAMERA LIST
// ==========================================

async function loadCameras(showMessage = false) {
  try {
    const r = await fetch(
      `/api/cameras?mode=${currentMode}`,
      { cache: 'no-store' }
    );

    if (!r.ok) throw Error('Camera API failed');

    cameras = await r.json();

    $('cameraCount').textContent = cameras.length;

    const list = $('cameraList');
    list.innerHTML = '';

    cameras.forEach(c => {
      const b = document.createElement('button');

      b.className = 'camera-btn';
      b.id = `camera-${c.id}`;

      b.innerHTML = `
        <div>
          <strong>${safeText(c.id)}</strong>
          <span class="online-dot"></span>
        </div>
        <p>${safeText(cameraLabel(c.type))}</p>
        <small>${safeText(c.zone)} · ${safeText(c.mode)}</small>
        <em>${safeText(c.source)}</em>
      `;

      b.onclick = () => selectCamera(c.id);
      list.appendChild(b);
    });

    if (selectedCamera) {
      $(`camera-${selectedCamera.id}`)?.classList.add('active');
    }

    if (showMessage) {
      showToast(
        `${currentMode === 'railway' ? 'Railway' : 'Road'} mode active`,
        `${cameras.length} camera source(s) available.`
      );
    }

  } catch (e) {
    console.error(e);

    $('cameraList').innerHTML =
      '<div class="camera-error">Unable to load camera configuration.</div>';
  }
}

// ==========================================
// CAMERA SELECTION
// ==========================================

async function selectCamera(id) {
  const camera = cameras.find(x => x.id === id);
  if (!camera) return;

  try {
    const r = await fetch('/api/camera/select', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ camera_id: id })
    });

    const d = await r.json();

    if (!r.ok || !d.ok) {
      showToast(
        'Camera unavailable',
        d.message || 'Could not open camera.',
        'error'
      );
      return;
    }

    selectedCamera = camera;

    document.querySelectorAll('.camera-btn')
      .forEach(x => x.classList.remove('active'));

    $(`camera-${id}`)?.classList.add('active');

    $('videoTitle').textContent =
      `${id} · ${cameraLabel(camera.type)}`;

    $('videoZone').textContent = `Zone ${camera.zone}`;
    $('videoMode').textContent = `Mode ${camera.mode}`;
    $('sourceNote').textContent = camera.source;

    $('livePill').classList.add('live');
    $('livePill').innerHTML = '<i></i> LIVE';

    $('videoWrap').innerHTML = `
      <img
        id="liveVideo"
        src="/video_feed/${encodeURIComponent(id)}?t=${Date.now()}"
        alt="Live camera stream">
    `;

    $('liveVideo').onerror = () => {
      showToast(
        'Live feed error',
        `${id} stopped or could not provide frames.`,
        'error'
      );
    };

    await refreshStatus();

    showToast(
      'Camera connected',
      `${id} is streaming from ${camera.source}.`
    );

  } catch (e) {
    console.error(e);
    showToast('Connection error', 'Unable to select camera.', 'error');
  }
}

// ==========================================
// STOP CAMERA
// ==========================================

async function stopCamera(msg = true) {
  try {
    await fetch('/api/camera/stop', { method: 'POST' });
  } catch (_) {}

  selectedCamera = null;

  document.querySelectorAll('.camera-btn')
    .forEach(x => x.classList.remove('active'));

  $('videoTitle').textContent = 'Select a camera';
  $('videoZone').textContent = 'Zone —';
  $('videoMode').textContent = 'Mode —';
  $('videoTargets').textContent = 'Active targets —';

  $('livePill').classList.remove('live');
  $('livePill').innerHTML = '<i></i> NOT STREAMING';

  $('videoWrap').innerHTML = `
    <div class="empty-video">
      <img src="/static/images/trinetrax-ai-logo-compact.png" alt="">
      <div>◉</div>
      <h3>No camera selected</h3>
      <p>Select a camera to start real-time YOLO monitoring.</p>
    </div>
  `;

  if (msg) {
    showToast('Camera stopped', 'Live monitoring has been stopped.');
  }
}

// ==========================================
// VIDEO SOURCE SELECTOR
// ==========================================

function updateVideoSourceControls() {
  const mode = $('videoSourceMode')?.value || 'webcam';
  const controls = $('videoFileControls');

  if (!controls) return;

  controls.classList.toggle('hidden', mode !== 'file');

  if (mode === 'file') {
    $('videoUploadStatus').textContent =
      selectedCamera
        ? `Selected camera: ${selectedCamera.id}. Choose a video file.`
        : 'Select a camera first, then choose a video file.';
  }
}

async function uploadAndStartVideo() {
  const fileInput = $('videoFileInput');
  const status = $('videoUploadStatus');
  const button = $('uploadVideoBtn');

  if (!selectedCamera) {
    showToast(
      'Select a camera first',
      'Choose a camera before uploading a video.',
      'error'
    );
    return;
  }

  const file = fileInput?.files?.[0];

  if (!file) {
    showToast(
      'No video selected',
      'Please choose a video file from your laptop.',
      'error'
    );
    return;
  }

  if (!file.type.startsWith('video/')) {
    showToast(
      'Invalid file',
      'Please select a valid video file.',
      'error'
    );
    return;
  }

  const formData = new FormData();
  formData.append('camera_id', selectedCamera.id);
  formData.append('video', file);

  button.disabled = true;
  status.textContent = 'Uploading video...';

  try {
    const response = await fetch('/api/camera/upload', {
      method: 'POST',
      body: formData
    });

    const result = await response.json();

    if (!response.ok || !result.ok) {
      throw new Error(result.message || 'Video upload failed.');
    }

    status.textContent = 'Video uploaded. Starting AI monitoring...';

    // Re-select the camera to restart its video feed
    await selectCamera(selectedCamera.id);

    status.textContent = `Video started: ${file.name}`;

    showToast(
      'Video source updated',
      `${file.name} is selected for ${selectedCamera.id}.`
    );

  } catch (e) {
    console.error(e);

    status.textContent = e.message || 'Unable to upload video.';

    showToast(
      'Video upload failed',
      status.textContent,
      'error'
    );

  } finally {
    button.disabled = false;
  }
}

// ==========================================
// TARGETS
// ==========================================

function renderTargets(id, targets, empty) {
  const c = $(id);
  if (!c) return;

  if (!targets?.length) {
    c.innerHTML = `<span class="target-empty">${safeText(empty)}</span>`;
    return;
  }

  c.innerHTML = targets.map(t => `
    <div class="target-card">
      <div>
        <strong>${safeText(t.client_id)}</strong>
        <span>${safeText(t.name)}</span>
      </div>
      <b class="${String(t.status).toLowerCase() === 'online' ? 'ok' : 'bad'}">
        ● ${safeText(t.status)}
      </b>
      <small>
        ${safeText(t.client_type)} · ${safeText(t.zone_id)}
      </small>
    </div>
  `).join('');
}

async function refreshTargets() {
  try {
    const r = await fetch(
      `/api/targets?mode=${currentMode}`,
      { cache: 'no-store' }
    );

    const d = await r.json();

    renderTargets(
      'railwayTargetList',
      d.railway,
      'No active trains in Z001.'
    );

    renderTargets(
      'roadTargetList',
      d.road,
      'No active vehicles in Z002.'
    );

  } catch (e) {
    console.error(e);
  }
}

// ==========================================
// SYSTEM STATUS
// ==========================================

async function refreshStatus() {
  try {
    const r = await fetch('/api/status', { cache: 'no-store' });
    const d = await r.json();

    $('systemStatus').textContent =
      d.system === 'ONLINE' ? 'SYSTEM ONLINE' : 'SYSTEM OFFLINE';

    $('statusDot').classList.toggle(
      'offline',
      d.system !== 'ONLINE'
    );

    $('railwayTargets').textContent = d.railway_targets ?? 0;
    $('roadTargets').textContent = d.road_targets ?? 0;
    $('alertCount').textContent = d.alerts ?? 0;
    $('totalCameras').textContent = d.total_cameras ?? 4;

    $('alertStat').classList.toggle(
      'has-alert',
      Number(d.alerts) > 0
    );

    if (selectedCamera) {
      const n = currentMode === 'railway'
        ? d.railway_targets
        : d.road_targets;

      $('videoTargets').textContent =
        `${currentMode === 'railway' ? 'Active trains' : 'Active vehicles'} — ${n}`;
    }

  } catch (e) {
    $('systemStatus').textContent = 'SYSTEM CONNECTION ERROR';
    $('statusDot').classList.add('offline');
  }
}

// ==========================================
// DELIVERY STATUS
// ==========================================

function statusClass(s) {
  const v = String(s || '').toUpperCase();

  return (
    v === 'SENT' ||
    v === 'DELIVERED' ||
    v === 'ONLINE'
  )
    ? 'ok'
    : (
      v === 'FAILED' ||
      v === 'OFFLINE'
    )
      ? 'bad'
      : 'warn';
}

// ==========================================
// EVENT CARDS
// ==========================================

function renderEventCards(alerts) {
  const container = $('eventCards');
  if (!container) return;

  if (!alerts?.length) {
    container.innerHTML = `
      <div class="empty-cell">
        No critical events captured yet.
      </div>
    `;
    return;
  }

  container.innerHTML = alerts.map(a => {
    const recipients = a.recipients || [];

    const duration = a.duration ?? a.duration_seconds;

    const durationText =
      duration !== undefined && duration !== null
        ? `${Number(duration).toFixed(2)} seconds`
        : 'Not provided by backend';

    const recipientHTML = recipients.length
      ? recipients.map(r => `
          <div class="event-recipient">
            <div class="event-recipient-info">
              <strong>${safeText(r.recipient_id || 'Unknown')}</strong>
              <span>${safeText(r.name || 'Unknown recipient')}</span>
              <small>
                ${safeText(r.recipient_type_label || r.recipient_type || 'Recipient')}
              </small>
            </div>

            <span class="delivery ${statusClass(r.delivery_status || r.status)}">
              ${safeText(r.delivery_status || r.status || 'UNKNOWN')}
            </span>
          </div>
        `).join('')
      : `
          <div class="no-recipient">
            No recipients were returned for this event.
          </div>
        `;

    return `
      <article class="event-card">

        <div class="event-card-header">
          <div>
            <small>EVENT ID</small>
            <h3>${safeText(a.event_id || 'Unknown Event')}</h3>
          </div>

          <span class="risk-badge ${safeText(String(a.risk || 'critical').toLowerCase())}">
            ${safeText(a.risk || 'CRITICAL')}
          </span>
        </div>

        <div class="event-card-details">
          <div>
            <small>Animal</small>
            <strong>${safeText(a.animal || 'Unknown')}</strong>
          </div>

          <div>
            <small>Camera</small>
            <strong>${safeText(a.camera_id || '—')}</strong>
          </div>

          <div>
            <small>Zone</small>
            <strong>${safeText(a.zone_id || '—')}</strong>
          </div>

          <div>
            <small>Risk Score</small>
            <strong>${safeText(a.risk_score ?? '—')}</strong>
          </div>

          <div>
            <small>Detection Duration</small>
            <strong>${safeText(durationText)}</strong>
          </div>

          <div>
            <small>Routing</small>
            <strong>${safeText(a.routing || '—')}</strong>
          </div>
        </div>

        <div class="event-card-recipients">
          <h4>
            Alert Recipients
            <span>${recipients.length}</span>
          </h4>

          ${recipientHTML}
        </div>

        <div class="event-card-footer">
          <span>${safeText(a.time || 'Time unavailable')}</span>

          <button
            class="detail-btn"
            onclick="openAlert('${safeText(a.event_id)}')">
            View Details
          </button>
        </div>

      </article>
    `;
  }).join('');
}

// ==========================================
// ROUTING PANEL
// ==========================================

function renderRouting(a) {
  if (!a) {
    $('routingEmpty').classList.remove('hidden');
    $('routingContent').classList.add('hidden');
    return;
  }

  $('routingEmpty').classList.add('hidden');
  $('routingContent').classList.remove('hidden');

  const rec = a.recipients || [];

  $('routingContent').innerHTML = `
    <div class="alert-summary">
      <div>
        <span class="risk-icon">🚨</span>
        <div>
          <b>${safeText(a.animal)} — ${safeText(a.confidence)}%</b>
          <small>
            ${safeText(a.camera_id)} ·
            ${safeText(a.zone_id)} ·
            ${safeText(a.event_type)}
          </small>
        </div>
      </div>
      <strong>${safeText(a.risk || 'CRITICAL')}</strong>
    </div>

    <div class="routing-type">
      ROUTING: <b>${safeText(a.routing || 'UNKNOWN')}</b>
    </div>

    <div class="recipients">
      ${
        rec.length
          ? rec.map(r => `
              <div class="recipient">
                <span class="person">
                  ${
                    String(r.recipient_type).toLowerCase().includes('manager')
                      ? '👤'
                      : '📡'
                  }
                </span>

                <div>
                  <b>${safeText(r.recipient_id)}</b>
                  <strong>${safeText(r.name || 'Unknown recipient')}</strong>
                  <small>
                    ${safeText(r.recipient_type_label || r.recipient_type)}
                  </small>
                </div>

                <span class="delivery ${statusClass(r.delivery_status || r.status)}">
                  ${safeText(r.delivery_status || r.status)}
                </span>
              </div>
            `).join('')
          : '<div class="no-recipient">Backend returned no recipients for this event.</div>'
      }
    </div>

    <div class="message-box">
      <label>ACTUAL SAFETY MESSAGE</label>
      <p>
        ${safeText(a.message || 'Backend did not expose a message in this event result.')}
      </p>
    </div>

    <button
      class="detail-btn"
      onclick="openAlert('${safeText(a.event_id)}')">
      View Event Details
    </button>
  `;

  renderEvidence(a);
  renderFlow(a);
}

// ==========================================
// EVIDENCE
// ==========================================

function renderEvidence(a) {
  $('evidenceStatus').textContent = a?.event_id || 'No event';

  if (!a) {
    $('evidenceContent').innerHTML = `
      <div class="evidence-empty">
        <img src="/static/images/trinetrax-ai-logo-compact.png" alt="">
        <span>
          Snapshot will appear here after the backend creates a critical event.
        </span>
      </div>
    `;
    return;
  }

  const src = a.snapshot_url || '';

  $('evidenceContent').innerHTML = `
    <div class="evidence">
      <div class="snapshot">
        ${
          src
            ? `<img src="${safeText(src)}" alt="Detection snapshot">`
            : '<div class="snapshot-missing">Snapshot path not returned by backend.</div>'
        }
      </div>

      <div class="evidence-meta">
        <b>
          ${safeText(a.animal)}
          <span>${safeText(a.confidence)}%</span>
        </b>

        <small>Camera: ${safeText(a.camera_id)}</small>
        <small>Zone: ${safeText(a.zone_id)}</small>
        <small>Event: ${safeText(a.event_id)}</small>

        <button
          ${src ? '' : 'disabled'}
          onclick="window.open('${safeText(src)}','_blank')">
          View Full Image ↗
        </button>
      </div>
    </div>
  `;
}

// ==========================================
// ALERT FLOW
// ==========================================

function renderFlow(a) {
  $('flowCamera').textContent = a?.camera_id || 'CAMERA';

  $('flowDetection').textContent = a
    ? `${String(a.animal).toUpperCase()} DETECTED`
    : 'ANIMAL DETECTED';

  $('flowRisk').textContent = a
    ? `Score ${a.risk_score}`
    : 'Waiting';

  $('flowCritical').textContent = a?.risk || 'CRITICAL';
  $('flowRouting').textContent = a?.routing || 'RECIPIENTS';

  $('flowRecipientCount').textContent = a
    ? `${a.recipient_count || a.recipients?.length || 0} recipient(s)`
    : 'Actual delivery';
}

// ==========================================
// NOTIFICATION HISTORY TABLE
// ==========================================

function renderHistory(alerts) {
  const rows = [];

  alerts.forEach(a => {
    (a.recipients || []).forEach(r => {
      rows.push({
        time: a.time,
        event_id: a.event_id,
        recipient: r.recipient_id,
        name: r.name,
        type: r.recipient_type_label || r.recipient_type,
        risk: a.risk,
        status: r.delivery_status || r.status
      });
    });
  });

  $('historyBody').innerHTML = rows.length
    ? rows.map(x => `
        <tr>
          <td>${safeText(x.time)}</td>

          <td>
            <button
              class="event-link"
              onclick="openAlert('${safeText(x.event_id)}')">
              ${safeText(x.event_id)}
            </button>
          </td>

          <td>
            <b>${safeText(x.recipient)}</b>
            <small>${safeText(x.name)}</small>
          </td>

          <td>${safeText(x.type)}</td>

          <td>
            <span class="risk-text">${safeText(x.risk)}</span>
          </td>

          <td>
            <span class="table-status ${statusClass(x.status)}">
              ${statusClass(x.status) === 'ok' ? '✓' : '⚠'}
              ${safeText(x.status)}
            </span>
          </td>
        </tr>
      `).join('')
    : `
        <tr>
          <td colspan="6" class="empty-cell">
            No backend notifications captured in this UI session.
          </td>
        </tr>
      `;
}

// ==========================================
// REFRESH ALERTS
// ==========================================

async function refreshAlerts() {
  try {
    const r = await fetch('/api/alerts', { cache: 'no-store' });

    if (!r.ok) throw Error('Alert API failed');

    const alerts = await r.json();

    renderEventCards(alerts);
    renderHistory(alerts);

    if (alerts.length) {
      const a = alerts[0];

      latestAlert = a;
      renderRouting(a);

      if (!firstAlertLoad) {
        alerts
          .filter(x => !previousAlertIds.has(x.event_id))
          .forEach(x => {
            showToast(
              `🚨 ${x.animal} — ${x.risk || 'CRITICAL'}`,
              `${x.camera_id} · ${x.zone_id} · ${x.routing || 'ROUTING'}`,
              'critical'
            );
          });
      }

      previousAlertIds = new Set(alerts.map(x => x.event_id));
      firstAlertLoad = false;

    } else {
      latestAlert = null;
      renderRouting(null);
      previousAlertIds.clear();
      firstAlertLoad = true;
    }

  } catch (e) {
    console.error(e);
  }
}

// ==========================================
// EVENT DETAILS MODAL
// ==========================================

async function openAlert(id) {
  try {
    const r = await fetch(
      `/api/alerts/${encodeURIComponent(id)}`,
      { cache: 'no-store' }
    );

    if (!r.ok) throw Error();

    const a = await r.json();

    const duration = a.duration ?? a.duration_seconds;

    const durationText =
      duration !== undefined && duration !== null
        ? `${Number(duration).toFixed(2)} seconds`
        : 'Not provided by backend';

    $('modalBody').innerHTML = `
      <div class="modal-eyebrow">EVENT DETAILS</div>

      <h2>🚨 ${safeText(a.animal)} detected</h2>

      <div class="modal-grid">

        <div>
          <label>EVENT ID</label>
          <b>${safeText(a.event_id)}</b>
        </div>

        <div>
          <label>RISK</label>
          <b>${safeText(a.risk)} · ${safeText(a.risk_score)}</b>
        </div>

        <div>
          <label>CAMERA</label>
          <b>${safeText(a.camera_id)}</b>
        </div>

        <div>
          <label>ZONE</label>
          <b>${safeText(a.zone_id)}</b>
        </div>

        <div>
          <label>DETECTION DURATION</label>
          <b>${safeText(durationText)}</b>
        </div>

        <div>
          <label>CONFIDENCE</label>
          <b>${safeText(a.confidence)}%</b>
        </div>

      </div>

      <div class="modal-route">
        <h3>Alert Routing · ${safeText(a.routing)}</h3>

        ${
          (a.recipients || []).map(r => `
            <p>
              <b>${safeText(r.recipient_id)}</b>
              — ${safeText(r.name)}
              · ${safeText(r.recipient_type_label || r.recipient_type)}

              <span class="delivery ${statusClass(r.delivery_status || r.status)}">
                ${safeText(r.delivery_status || r.status)}
              </span>
            </p>
          `).join('')
        }
      </div>

      <div class="modal-message">
        <label>ACTUAL BACKEND MESSAGE</label>
        <p>${safeText(a.message || 'Not exposed')}</p>
      </div>

      ${
        a.snapshot_url
          ? `<a class="detail-btn" href="${safeText(a.snapshot_url)}" target="_blank">View Full Snapshot ↗</a>`
          : ''
      }
    `;

    $('detailModal').classList.remove('hidden');

  } catch (e) {
    showToast(
      'Event unavailable',
      'This event is no longer in the UI session.',
      'error'
    );
  }
}

function closeModal() {
  $('detailModal').classList.add('hidden');
}

// ==========================================
// CLEAR ALERTS
// ==========================================

async function clearAlerts() {
  try {
    await fetch('/api/alerts/clear', { method: 'POST' });

    latestAlert = null;
    previousAlertIds.clear();
    firstAlertLoad = true;

    await refreshAlerts();
    await refreshStatus();

    showToast(
      'Session alerts cleared',
      'Backend system is not modified.'
    );

  } catch (e) {
    showToast(
      'Action failed',
      'Could not clear UI session.',
      'error'
    );
  }
}

// ==========================================
// REFRESH DASHBOARD
// ==========================================

async function refreshAll() {
  if (refreshBusy) return;

  refreshBusy = true;

  document.querySelector('.refresh-btn')
    ?.classList.add('spinning');

  try {
    await Promise.all([
      loadCameras(),
      refreshStatus(),
      refreshTargets(),
      refreshAlerts()
    ]);

    showToast(
      'Dashboard refreshed',
      'TRINETRA X AI is up to date.'
    );

  } finally {
    setTimeout(
      () => document.querySelector('.refresh-btn')
        ?.classList.remove('spinning'),
      350
    );

    refreshBusy = false;
  }
}

// ==========================================
// EVENT LISTENERS
// ==========================================

$('detailModal')?.addEventListener('click', e => {
  if (e.target.id === 'detailModal') {
    closeModal();
  }
});

$('videoSourceMode')?.addEventListener(
  'change',
  updateVideoSourceControls
);

$('uploadVideoBtn')?.addEventListener(
  'click',
  uploadAndStartVideo
);

// ==========================================
// INITIALIZE DASHBOARD
// ==========================================

updateModeUI();
updateClock();
updateVideoSourceControls();

setInterval(updateClock, 1000);
setInterval(refreshStatus, 2000);
setInterval(refreshTargets, 3000);
setInterval(refreshAlerts, 1200);

loadCameras();
refreshStatus();
refreshTargets();
refreshAlerts();

setTimeout(
  () => $('pageLoader')?.classList.add('hide'),
  700
);