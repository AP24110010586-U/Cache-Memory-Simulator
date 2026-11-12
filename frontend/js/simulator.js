/**
 * simulator.js  –  Cache Memory Simulator Frontend Logic
 * Communicates exclusively with Flask backend – never calculates locally.
 */

const API_BASE = "http://127.0.0.1:5000";

// ================================================================
// State
// ================================================================
const state = {
  config: {
    main_memory_size: 256,
    cache_size: 64,
    block_size: 4,
    mapping: "direct",
    associativity: 1,
    replacement: "lru",
  },
  configDerived: null,
  simulationResult: null,
  events: [],
  currentStep: -1,
  backendOk: false,
};

// ================================================================
// Navigation
// ================================================================
function navigateTo(pageId) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".nav-links a").forEach(a => a.classList.remove("active"));
  const page = document.getElementById("page-" + pageId);
  if (page) page.classList.add("active");
  const link = document.querySelector(`.nav-links a[data-page="${pageId}"]`);
  if (link) link.classList.add("active");
  window.scrollTo(0, 0);
}

// ================================================================
// API helpers
// ================================================================
async function apiGet(path) {
  const res = await fetch(API_BASE + path);
  return res.json();
}

async function apiPost(path, body) {
  const res = await fetch(API_BASE + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return res.json();
}

// ================================================================
// Health check
// ================================================================
async function checkHealth() {
  try {
    const data = await apiGet("/api/health");
    state.backendOk = data.status === "ok";
    const el = document.getElementById("backend-status");
    if (el) {
      el.textContent = state.backendOk
        ? `✅ Backend connected (engine: ${data.engine})`
        : "⚠️ Backend not responding";
      el.className = state.backendOk ? "alert alert-success" : "alert alert-warning";
    }
  } catch (e) {
    state.backendOk = false;
    const el = document.getElementById("backend-status");
    if (el) {
      el.textContent = "❌ Cannot connect to backend. Please run start_server.bat";
      el.className = "alert alert-error";
    }
  }
}

// ================================================================
// Configuration Page
// ================================================================
function initConfigPage() {
  const mappingSelect = document.getElementById("cfg-mapping");
  const assocGroup    = document.getElementById("assoc-group");
  const repGroup      = document.getElementById("rep-group");

  if (mappingSelect) {
    mappingSelect.addEventListener("change", () => {
      const v = mappingSelect.value;
      assocGroup.style.display = (v === "set_associative") ? "block" : "none";
      repGroup.style.display   = (v === "direct") ? "none" : "block";
      if (v === "direct") {
        document.getElementById("cfg-associativity").value = 1;
      }
    });
    mappingSelect.dispatchEvent(new Event("change"));
  }

  document.getElementById("btn-validate-config")?.addEventListener("click", validateConfig);
  document.getElementById("btn-apply-config")?.addEventListener("click", applyConfig);
}

async function validateConfig() {
  const cfg = readConfig();
  showAlert("config-alert", "", "hidden");
  try {
    const data = await apiPost("/api/configure", cfg);
    if (data.error) {
      showAlert("config-alert", "❌ " + data.error, "alert-error");
    } else {
      showAlert("config-alert",
        `✅ Configuration valid!  Lines: ${data.config.num_cache_lines}  Sets: ${data.config.num_sets}  Bits: TAG(${data.config.tag_bits}) INDEX(${data.config.index_bits}) OFFSET(${data.config.offset_bits})`,
        "alert-success");
      state.configDerived = data.config;
      renderConfigSummary(data.config);
    }
  } catch (e) {
    showAlert("config-alert", "❌ Backend error: " + e.message, "alert-error");
  }
}

async function applyConfig() {
  const cfg = readConfig();
  try {
    const data = await apiPost("/api/configure", cfg);
    if (data.error) {
      showAlert("config-alert", "❌ " + data.error, "alert-error");
    } else {
      state.config = cfg;
      state.configDerived = data.config;
      showAlert("config-alert", "✅ Configuration applied. Ready to simulate!", "alert-success");
      renderConfigSummary(data.config);
      navigateTo("simulate");
    }
  } catch (e) {
    showAlert("config-alert", "❌ Backend error: " + e.message, "alert-error");
  }
}

function readConfig() {
  const toBytes = (val, unit) => {
    const n = parseFloat(val) || 0;
    if (unit === "KB") return Math.round(n * 1024);
    if (unit === "MB") return Math.round(n * 1024 * 1024);
    return Math.round(n);
  };
  return {
    main_memory_size: toBytes(
      document.getElementById("cfg-mm-size")?.value,
      document.getElementById("cfg-mm-unit")?.value
    ),
    cache_size: toBytes(
      document.getElementById("cfg-cache-size")?.value,
      document.getElementById("cfg-cache-unit")?.value
    ),
    block_size: toBytes(
      document.getElementById("cfg-block-size")?.value,
      document.getElementById("cfg-block-unit")?.value
    ),
    mapping:       document.getElementById("cfg-mapping")?.value,
    associativity: parseInt(document.getElementById("cfg-associativity")?.value) || 1,
    replacement:   document.getElementById("cfg-replacement")?.value,
  };
}

function renderConfigSummary(cfg) {
  const el = document.getElementById("config-summary");
  if (!el) return;
  el.innerHTML = `
    <div class="detail-row"><span class="detail-key">Main Memory</span><span class="detail-value">${formatBytes(cfg.main_memory_size)}</span></div>
    <div class="detail-row"><span class="detail-key">Cache Size</span><span class="detail-value">${formatBytes(cfg.cache_size)}</span></div>
    <div class="detail-row"><span class="detail-key">Block Size</span><span class="detail-value">${formatBytes(cfg.block_size)}</span></div>
    <div class="detail-row"><span class="detail-key">Mapping</span><span class="detail-value">${cfg.mapping.replace("_", " ").toUpperCase()}</span></div>
    <div class="detail-row"><span class="detail-key">Associativity</span><span class="detail-value">${cfg.associativity}-way</span></div>
    <div class="detail-row"><span class="detail-key">Replacement</span><span class="detail-value">${cfg.replacement.toUpperCase()}</span></div>
    <div class="detail-row"><span class="detail-key">Cache Lines</span><span class="detail-value">${cfg.num_cache_lines}</span></div>
    <div class="detail-row"><span class="detail-key">Sets</span><span class="detail-value">${cfg.num_sets}</span></div>
    <div class="detail-row"><span class="detail-key">Tag Bits</span><span class="detail-value">${cfg.tag_bits}</span></div>
    <div class="detail-row"><span class="detail-key">Index Bits</span><span class="detail-value">${cfg.index_bits}</span></div>
    <div class="detail-row"><span class="detail-key">Offset Bits</span><span class="detail-value">${cfg.offset_bits}</span></div>
    <div class="detail-row"><span class="detail-key">Address Format</span><span class="detail-value">[TAG:${cfg.tag_bits}][${cfg.mapping==="fully_associative"?"":`IDX:${cfg.index_bits}`}][OFF:${cfg.offset_bits}]</span></div>
  `;
}

// ================================================================
// Simulation Page
// ================================================================
function initSimulatePage() {
  document.getElementById("btn-run-sim")?.addEventListener("click", runSimulation);
  document.getElementById("btn-reset-sim")?.addEventListener("click", resetSimulation);
  document.getElementById("btn-next-step")?.addEventListener("click", nextStep);
  document.getElementById("btn-prev-step")?.addEventListener("click", prevStep);
  document.getElementById("btn-load-sample")?.addEventListener("click", loadSampleAddresses);
  loadSamples();
}

async function loadSamples() {
  try {
    const data = await apiGet("/api/sample");
    const sel = document.getElementById("sample-select");
    if (sel && data.samples) {
      data.samples.forEach(s => {
        const opt = document.createElement("option");
        opt.value = s.id;
        opt.textContent = s.name;
        sel.appendChild(opt);
      });
      sel._samples = data.samples;
    }
  } catch (e) { /* ignore */ }
}

async function loadSampleAddresses() {
  const sel = document.getElementById("sample-select");
  if (!sel || !sel._samples) return;
  const id = parseInt(sel.value);
  const sample = sel._samples.find(s => s.id === id);
  if (!sample) return;

  // Apply config
  const cfg = sample.config;
  state.config = cfg;
  applyConfigToForm(cfg);

  // Apply addresses
  const addrInput = document.getElementById("sim-addresses");
  if (addrInput) addrInput.value = sample.addresses.join(", ");

  // Validate config
  try {
    const data = await apiPost("/api/configure", cfg);
    if (!data.error) {
      state.configDerived = data.config;
    }
  } catch(e) {}

  showAlert("sim-alert", `ℹ️ Loaded: ${sample.name}. Click "Run Simulation".`, "alert-info");
}

function applyConfigToForm(cfg) {
  const setVal = (id, val) => { const el = document.getElementById(id); if(el) el.value = val; };
  setVal("cfg-mm-size", cfg.main_memory_size);
  setVal("cfg-mm-unit", "B");
  setVal("cfg-cache-size", cfg.cache_size);
  setVal("cfg-cache-unit", "B");
  setVal("cfg-block-size", cfg.block_size);
  setVal("cfg-block-unit", "B");
  setVal("cfg-mapping", cfg.mapping);
  setVal("cfg-associativity", cfg.associativity);
  setVal("cfg-replacement", cfg.replacement);

  const mappingSelect = document.getElementById("cfg-mapping");
  if (mappingSelect) mappingSelect.dispatchEvent(new Event("change"));
}

async function runSimulation() {
  showAlert("sim-alert", "", "hidden");
  const addrInput = document.getElementById("sim-addresses");
  if (!addrInput || !addrInput.value.trim()) {
    showAlert("sim-alert", "❌ Please enter at least one memory address.", "alert-error");
    return;
  }
  const rawAddresses = addrInput.value.split(/[\s,;]+/).filter(s => s !== "");
  const addresses = [];
  for (let i = 0; i < rawAddresses.length; i++) {
    const v = parseInt(rawAddresses[i], 10);
    if (isNaN(v) || v < 0) {
      showAlert("sim-alert", `❌ Invalid address at position ${i+1}: "${rawAddresses[i]}"`, "alert-error");
      return;
    }
    addresses.push(v);
  }

  const payload = { config: state.config, addresses };

  document.getElementById("btn-run-sim").disabled = true;
  document.getElementById("btn-run-sim").textContent = "Running…";

  try {
    const data = await apiPost("/api/simulate", payload);
    if (data.error) {
      showAlert("sim-alert", "❌ " + data.error, "alert-error");
    } else {
      state.simulationResult = data;
      state.events = data.events;
      state.currentStep = -1;
      renderSimulationLog(data.events);
      renderStatistics(data.statistics);
      renderCacheVisualization(null, null);
      showAlert("sim-alert",
        `✅ Simulation complete! ${addresses.length} accesses — Hits: ${data.statistics.hits}, Misses: ${data.statistics.misses}, Hit rate: ${data.statistics.hit_percentage}%`,
        "alert-success");
      document.getElementById("sim-controls")?.classList.remove("hidden");
      navigateTo("visualize");
    }
  } catch (e) {
    showAlert("sim-alert", "❌ Backend error: " + e.message, "alert-error");
  } finally {
    document.getElementById("btn-run-sim").disabled = false;
    document.getElementById("btn-run-sim").textContent = "▶ Run Simulation";
  }
}

function resetSimulation() {
  state.simulationResult = null;
  state.events = [];
  state.currentStep = -1;
  const tbl = document.getElementById("sim-log-body");
  if (tbl) tbl.innerHTML = "";
  renderStatistics(null);
  renderCacheVisualization(null, null);
  showAlert("sim-alert", "ℹ️ Simulation reset.", "alert-info");
  document.getElementById("sim-controls")?.classList.add("hidden");
}

function nextStep() {
  if (!state.events.length) return;
  state.currentStep = Math.min(state.currentStep + 1, state.events.length - 1);
  updateStepView();
}

function prevStep() {
  if (!state.events.length) return;
  state.currentStep = Math.max(state.currentStep - 1, 0);
  updateStepView();
}

function updateStepView() {
  const ev = state.events[state.currentStep];
  if (!ev) return;

  // Highlight row in table
  document.querySelectorAll("#sim-log-body tr").forEach((tr, i) => {
    tr.classList.toggle("current-step", i === state.currentStep);
  });

  // Update step counter
  const counter = document.getElementById("step-counter");
  if (counter) counter.textContent = `Step ${state.currentStep + 1} / ${state.events.length}`;

  renderStepDetail(ev);
  renderCacheVisualization(ev, state.currentStep);
  updateArchDiagram(ev);
  renderStatisticsFromEvent(ev);
}

// ================================================================
// Rendering helpers
// ================================================================
function renderSimulationLog(events) {
  const tbody = document.getElementById("sim-log-body");
  if (!tbody) return;
  tbody.innerHTML = events.map((ev, i) => `
    <tr class="fade-in" onclick="jumpToStep(${i})">
      <td>${i + 1}</td>
      <td class="text-mono">${ev.address}</td>
      <td class="text-mono">${ev.block_number}</td>
      <td class="text-mono">${ev.tag}</td>
      <td class="text-mono">${ev.index}</td>
      <td class="text-mono">${ev.offset}</td>
      <td class="${ev.hit ? "col-hit" : "col-miss"}">
        <span class="badge ${ev.hit ? "badge-hit" : ev.replacement ? "badge-replace" : "badge-miss"}">
          ${ev.event_type}
        </span>
      </td>
      <td>${ev.replacement ? `Block ${ev.evicted_block}` : "—"}</td>
    </tr>
  `).join("");
}

function jumpToStep(i) {
  state.currentStep = i;
  updateStepView();
  navigateTo("visualize");
}

function renderStatistics(stats) {
  const fields = ["total_accesses", "hits", "misses", "hit_percentage", "miss_percentage"];
  if (!stats) {
    fields.forEach(f => {
      const el = document.getElementById("stat-" + f);
      if (el) el.textContent = "—";
    });
    document.querySelectorAll(".progress-fill").forEach(el => el.style.width = "0%");
    return;
  }
  document.getElementById("stat-total_accesses") && (document.getElementById("stat-total_accesses").textContent = stats.total_accesses);
  document.getElementById("stat-hits")           && (document.getElementById("stat-hits").textContent           = stats.hits);
  document.getElementById("stat-misses")         && (document.getElementById("stat-misses").textContent         = stats.misses);
  document.getElementById("stat-hit_percentage") && (document.getElementById("stat-hit_percentage").textContent = stats.hit_percentage.toFixed(2) + "%");
  document.getElementById("stat-miss_percentage")&& (document.getElementById("stat-miss_percentage").textContent= stats.miss_percentage.toFixed(2) + "%");
  document.getElementById("stat-hit_ratio")      && (document.getElementById("stat-hit_ratio").textContent      = stats.hit_ratio.toFixed(4));
  document.getElementById("stat-miss_ratio")     && (document.getElementById("stat-miss_ratio").textContent     = stats.miss_ratio.toFixed(4));
  document.querySelectorAll(".progress-fill.hit") .forEach(el => el.style.width = stats.hit_percentage + "%");
  document.querySelectorAll(".progress-fill.miss").forEach(el => el.style.width = stats.miss_percentage + "%");
}

function renderStatisticsFromEvent(ev) {
  if (!ev) return;
  const stats = {
    total_accesses: ev.total_accesses,
    hits: ev.hits,
    misses: ev.misses,
    hit_percentage: ev.total_accesses ? (ev.hits / ev.total_accesses * 100) : 0,
    miss_percentage: ev.total_accesses ? (ev.misses / ev.total_accesses * 100) : 0,
    hit_ratio: ev.total_accesses ? ev.hits / ev.total_accesses : 0,
    miss_ratio: ev.total_accesses ? ev.misses / ev.total_accesses : 0,
  };
  renderStatistics(stats);
}

function renderStepDetail(ev) {
  const panel = document.getElementById("step-detail-panel");
  if (!panel) return;
  const mapping = state.config.mapping;
  const hasIndex = mapping !== "fully_associative";
  panel.innerHTML = `
    <h4>🔍 Step ${state.currentStep + 1} Details</h4>
    <div class="detail-row"><span class="detail-key">Address</span><span class="detail-value">${ev.address} (0x${ev.address.toString(16).padStart(4,"0").toUpperCase()})</span></div>
    <div class="detail-row"><span class="detail-key">Block Number</span><span class="detail-value">${ev.block_number}</span></div>
    <div class="detail-row"><span class="detail-key">Tag</span><span class="detail-value">${ev.tag}</span></div>
    ${hasIndex ? `<div class="detail-row"><span class="detail-key">${mapping==="direct"?"Cache Line":"Set Index"}</span><span class="detail-value">${ev.index}</span></div>` : ""}
    <div class="detail-row"><span class="detail-key">Block Offset</span><span class="detail-value">${ev.offset}</span></div>
    <div class="detail-row"><span class="detail-key">Result</span><span class="detail-value"><span class="badge ${ev.hit?"badge-hit":ev.replacement?"badge-replace":"badge-miss"}">${ev.event_type}</span></span></div>
    ${ev.replacement ? `
    <div class="detail-row"><span class="detail-key">Evicted Block</span><span class="detail-value">${ev.evicted_block}</span></div>
    <div class="detail-row"><span class="detail-key">Inserted Block</span><span class="detail-value">${ev.inserted_block}</span></div>
    ` : ""}
    <div class="detail-row"><span class="detail-key">Running Stats</span><span class="detail-value">${ev.hits} hits / ${ev.misses} misses / ${ev.total_accesses} total</span></div>
  `;

  // Address breakdown visual
  const bd = document.getElementById("addr-breakdown-display");
  if (bd) {
    const cfg = state.configDerived || state.config;
    const tagBits   = cfg.tag_bits   || "";
    const idxBits   = cfg.index_bits || "";
    const offBits   = cfg.offset_bits|| "";
    bd.innerHTML = `
      <div class="addr-breakdown">
        <div class="addr-part tag"><span class="part-label">TAG (${tagBits} bits)</span><span class="part-value">${ev.tag}</span></div>
        ${hasIndex ? `<div class="addr-part index"><span class="part-label">${mapping==="direct"?"LINE":"SET"} (${idxBits} bits)</span><span class="part-value">${ev.index}</span></div>` : ""}
        <div class="addr-part offset"><span class="part-label">OFFSET (${offBits} bits)</span><span class="part-value">${ev.offset}</span></div>
      </div>
    `;
  }
}

function renderCacheVisualization(ev, stepIdx) {
  const container = document.getElementById("cache-lines-container");
  if (!container) return;

  if (!ev) {
    container.innerHTML = `<p class="text-muted text-center mt-3">Run a simulation to see the cache state.</p>`;
    return;
  }

  const snapshot = ev.cache_snapshot;
  const mapping = state.config.mapping;
  const isFA = mapping === "fully_associative";
  const isDM = mapping === "direct";

  let html = "";
  snapshot.forEach((setLines, setIdx) => {
    const setTitle = isDM ? `Cache Lines` : isFA ? `Cache (Fully Associative)` : `Set ${setIdx}`;
    if (!isDM && !isFA) {
      html += `<div class="memory-block-title">SET ${setIdx}</div>`;
    }

    setLines.forEach((line, lineIdx) => {
      let globalLine = isDM ? lineIdx : (setIdx * setLines.length + lineIdx);
      let lineClass = "state-empty";
      if (line.valid) lineClass = "state-valid";

      // Highlight accessed line
      if (ev && line.valid) {
        if (isDM && lineIdx === ev.index) {
          lineClass = ev.hit ? "state-hit" : (ev.replacement ? "state-replace" : "state-miss");
        } else if (!isDM && setIdx === ev.index) {
          if (ev.hit && line.block === ev.block_number) lineClass = "state-hit";
          else if (ev.replacement && lineIdx === ev.victim_line) lineClass = "state-replace";
        }
      }

      const lineLabel = isDM ? lineIdx : lineIdx;
      html += `
        <div class="cache-line-row ${lineClass}">
          <span class="line-idx">[${lineLabel}]</span>
          <span class="line-valid" style="color:${line.valid?"#22c55e":"#475569"}">${line.valid ? "V=1" : "V=0"}</span>
          <span class="line-data">${line.valid ? `Tag:${line.tag} | Blk:${line.block}` : "— empty —"}</span>
        </div>
      `;
    });
    if (!isDM && snapshot.length > 1) html += `<hr style="border-color:var(--border);margin:0.6rem 0">`;
  });
  container.innerHTML = html;
}

function updateArchDiagram(ev) {
  const cpuBox   = document.getElementById("arch-cpu");
  const cacheBox = document.getElementById("arch-cache");
  const ramBox   = document.getElementById("arch-ram");
  const arrow1   = document.getElementById("arch-arrow1");
  const arrow2   = document.getElementById("arch-arrow2");
  const statusEl = document.getElementById("arch-status");

  [cpuBox, cacheBox, ramBox].forEach(el => el?.classList.remove("flash-hit","flash-miss","flash-access"));
  [arrow1, arrow2].forEach(el => el?.classList.remove("active-hit","active-miss"));

  if (!ev) return;

  cpuBox?.classList.add("flash-access");
  if (ev.hit) {
    cacheBox?.classList.add("flash-hit");
    arrow1?.classList.add("active-hit");
    if (statusEl) { statusEl.textContent = "CACHE HIT ✅"; statusEl.className = "badge badge-hit"; }
  } else {
    cacheBox?.classList.add("flash-miss");
    ramBox?.classList.add("flash-access");
    arrow1?.classList.add("active-miss");
    arrow2?.classList.add("active-miss");
    if (statusEl) {
      statusEl.textContent = ev.replacement ? "CACHE MISS + REPLACE 🔄" : "CACHE MISS ❌";
      statusEl.className = ev.replacement ? "badge badge-replace" : "badge badge-miss";
    }
  }

  // Update sizes in diagram
  const cfg = state.config;
  document.getElementById("arch-mm-size")    && (document.getElementById("arch-mm-size").textContent    = formatBytes(cfg.main_memory_size));
  document.getElementById("arch-cache-size") && (document.getElementById("arch-cache-size").textContent = formatBytes(cfg.cache_size));
}

// ================================================================
// Utility
// ================================================================
function formatBytes(n) {
  if (n >= 1048576) return (n / 1048576).toFixed(0) + " MB";
  if (n >= 1024)    return (n / 1024).toFixed(0) + " KB";
  return n + " B";
}

function showAlert(id, msg, cls) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg;
  el.className = "alert " + cls;
}

// ================================================================
// Learn page — scroll spy
// ================================================================
function initLearnPage() {
  const links = document.querySelectorAll(".learn-nav a");
  links.forEach(a => {
    a.addEventListener("click", e => {
      e.preventDefault();
      const target = document.getElementById(a.getAttribute("href").slice(1));
      if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
      links.forEach(x => x.classList.remove("active"));
      a.classList.add("active");
    });
  });
}

// ================================================================
// Bootstrap
// ================================================================
document.addEventListener("DOMContentLoaded", () => {
  // Wire navigation
  document.querySelectorAll(".nav-links a, [data-nav]").forEach(a => {
    a.addEventListener("click", e => {
      e.preventDefault();
      const page = a.dataset.page || a.getAttribute("href")?.replace("#","");
      if (page) navigateTo(page);
    });
  });

  document.querySelectorAll("[data-nav-to]").forEach(btn => {
    btn.addEventListener("click", () => navigateTo(btn.dataset.navTo));
  });

  navigateTo("home");
  initConfigPage();
  initSimulatePage();
  initLearnPage();
  checkHealth();

  // Re-check every 10 seconds
  setInterval(checkHealth, 10000);
});

// Expose for inline onclick
window.jumpToStep = jumpToStep;
window.navigateTo = navigateTo;
