// AES M-App Mobile Frontend Logic
let currentTab = 'tools';
let currentPage = 1;
let currentSearchTimeout = null;
let currentSelectedChip = 'all';

let currentLoadedChecklists = { daily: [], monthly: [], tool_type: 'ทั่วไป' };
let currentChecklistFrequency = 'monthly';

const MONTH_NAMES = [
  "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
  "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
];

// Register PWA Service Worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(err => console.log('SW registration error:', err));
  });
}

document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) lucide.createIcons();

  const todayStr = new Date().toISOString().split('T')[0];
  const dateInput = document.getElementById('form-maintenance-date');
  if (dateInput) dateInput.value = todayStr;

  loadStats();
  loadCategories();
  loadTools(1);
  loadSchedule();

  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      clearTimeout(currentSearchTimeout);
      const clearBtn = document.getElementById('clear-search-btn');
      if (clearBtn) clearBtn.classList.toggle('hidden', !e.target.value);
      currentSearchTimeout = setTimeout(() => loadTools(1), 250);
    });
  }

  const scheduleMonth = document.getElementById('schedule-month-select');
  if (scheduleMonth) scheduleMonth.addEventListener('change', () => loadSchedule());

  const scheduleWeek = document.getElementById('schedule-week-select');
  if (scheduleWeek) scheduleWeek.addEventListener('change', () => loadSchedule());
});

function switchTab(tabId) {
  currentTab = tabId;
  document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('.bottom-nav-item').forEach(el => el.classList.remove('active'));

  const activeContent = document.getElementById(`tab-${tabId}`);
  if (activeContent) activeContent.classList.remove('hidden');

  const activeBtn = document.getElementById(`tab-btn-${tabId}`);
  if (activeBtn) activeBtn.classList.add('active');

  window.scrollTo({ top: 0, behavior: 'smooth' });

  if (tabId === 'tools') loadTools(currentPage);
  if (tabId === 'schedule') loadSchedule();
  if (tabId === 'logs') loadLogs(1);
  if (tabId === 'dashboard') loadDashboard();

  if (window.lucide) lucide.createIcons();
}

function filterByChip(keyword) {
  currentSelectedChip = keyword;
  document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
  const activeChip = document.getElementById(`chip-${keyword}`);
  if (activeChip) activeChip.classList.add('active');

  if (currentTab !== 'tools') {
    switchTab('tools');
  }

  const searchInput = document.getElementById('search-input');
  if (keyword === 'all') {
    searchInput.value = '';
  } else {
    searchInput.value = keyword;
  }
  loadTools(1);
}

async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    if (data.success) {
      const s = data.data;
      document.getElementById('stat-total-tools').innerText = s.total_tools.toLocaleString();
      document.getElementById('stat-pm-rate').innerText = `${s.pm_completion_rate}%`;

      const pmCard = document.getElementById('stat-total-pm-card');
      if (pmCard) pmCard.innerText = s.total_pm_plans.toLocaleString();

      const dashTools = document.getElementById('dash-total-tools');
      if (dashTools) {
        dashTools.innerText = s.total_tools.toLocaleString();
        document.getElementById('dash-total-pm').innerText = s.total_pm_plans.toLocaleString();
      }
    }
  } catch (err) {
    console.error(err);
  }
}

async function loadCategories() {
  try {
    const res = await fetch('/api/categories');
    const json = await res.json();
    if (json.success) {
      const container = document.getElementById('dash-categories-list');
      if (container) {
        container.innerHTML = '';
        json.data.slice(0, 15).forEach(c => {
          const item = document.createElement('div');
          item.className = 'flex items-center justify-between p-2 bg-slate-50 rounded-lg text-xs';
          item.innerHTML = `
            <div class="flex items-center space-x-1.5">
              <span class="w-1.5 h-1.5 rounded-full bg-blue-600"></span>
              <span class="font-bold text-slate-800 font-mono">${c.category}</span>
            </div>
            <span class="font-bold text-blue-700">${c.count} รายการ</span>
          `;
          container.appendChild(item);
        });
      }
    }
  } catch (err) {
    console.error(err);
  }
}

// Load Mobile Feed Cards
async function loadTools(page = 1) {
  currentPage = page;
  const container = document.getElementById('tools-cards-container');
  container.innerHTML = `<div class="text-center py-8 text-slate-400 text-xs">กำลังค้นหาและโหลดข้อมูล...</div>`;

  const q = document.getElementById('search-input').value.trim();
  const url = `/api/tools?page=${page}&limit=25&q=${encodeURIComponent(q)}`;

  try {
    const res = await fetch(url);
    const result = await res.json();

    if (!result.success || !result.data.length) {
      container.innerHTML = `
        <div class="text-center py-10 bg-white rounded-2xl border border-slate-200 p-6 space-y-2">
          <i data-lucide="inbox" class="w-8 h-8 mx-auto text-slate-300"></i>
          <p class="text-xs font-semibold text-slate-500">ไม่พบเครื่องมือที่ค้นหา</p>
        </div>`;
      document.getElementById('tools-count-badge').innerText = '0 รายการ';
      renderPagination(0, 1, 25);
      if (window.lucide) lucide.createIcons();
      return;
    }

    const { data: tools, pagination } = result;
    document.getElementById('tools-count-badge').innerText = `${pagination.total.toLocaleString()} เครื่อง`;

    container.innerHTML = '';
    tools.forEach((t) => {
      const card = document.createElement('div');
      card.className = 'bg-white rounded-2xl p-3.5 border border-slate-200/80 shadow-xs touch-card flex flex-col space-y-2.5';
      card.innerHTML = `
        <div class="flex items-start justify-between">
          <div>
            <div class="flex items-center space-x-1.5">
              <span class="font-mono font-bold text-blue-900 text-xs tracking-wide">${t.code}</span>
              <span class="bg-indigo-50 text-indigo-800 border border-indigo-200 text-[10px] px-1.5 py-0.2 rounded font-medium">${t.tool_type}</span>
            </div>
            <h4 class="text-xs font-semibold text-slate-800 mt-0.5 leading-snug">${t.name}</h4>
          </div>
          ${getStatusBadge(t.status)}
        </div>

        <div class="flex items-center justify-between pt-2 border-t border-slate-100 text-[11px]">
          <div class="flex items-center space-x-2 text-slate-500">
            <span class="flex items-center"><i data-lucide="target" class="w-3 h-3 mr-0.5 text-blue-600"></i> ${t.pm_count} รอบ/ปี</span>
            <span>•</span>
            <span>ตรวจล่าสุด: <strong>${t.last_maintenance_date || '-'}</strong></span>
          </div>

          <div class="flex items-center space-x-1.5">
            <button onclick="openRecordForTool(${t.id}, '${t.code}', '${escapeHtml(t.name)}', '${t.category}', '${t.tool_type}')"
                    class="bg-blue-600 hover:bg-blue-700 active:scale-95 text-white px-2.5 py-1 rounded-lg text-xs font-bold shadow-xs flex items-center transition">
              <i data-lucide="wrench" class="w-3 h-3 mr-1"></i> ตรวจเช็ค
            </button>
            <button onclick="openToolModal(${t.id})" class="p-1 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100">
              <i data-lucide="chevron-right" class="w-4 h-4"></i>
            </button>
          </div>
        </div>
      `;
      container.appendChild(card);
    });

    renderPagination(pagination.total, pagination.page, pagination.limit);
    if (window.lucide) lucide.createIcons();

  } catch (err) {
    console.error(err);
    container.innerHTML = `<div class="text-center py-6 text-red-500 text-xs">เกิดข้อผิดพลาดในการโหลดข้อมูล</div>`;
  }
}

function clearSearch() {
  document.getElementById('search-input').value = '';
  document.getElementById('clear-search-btn').classList.add('hidden');
  loadTools(1);
}

function getStatusBadge(status) {
  if (status === 'ใช้งานได้') {
    return `<span class="bg-emerald-100 text-emerald-800 text-[10px] px-2 py-0.5 rounded-full font-bold inline-flex items-center">
      <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1"></span>พร้อมใช้</span>`;
  } else if (status.includes('รอ')) {
    return `<span class="bg-amber-100 text-amber-800 text-[10px] px-2 py-0.5 rounded-full font-bold inline-flex items-center">
      <span class="w-1.5 h-1.5 rounded-full bg-amber-500 mr-1"></span>รอซ่อม</span>`;
  } else {
    return `<span class="bg-rose-100 text-rose-800 text-[10px] px-2 py-0.5 rounded-full font-bold inline-flex items-center">
      <span class="w-1.5 h-1.5 rounded-full bg-rose-500 mr-1"></span>ชำรุด</span>`;
  }
}

function renderPagination(total, page, limit) {
  const totalPages = Math.ceil(total / limit) || 1;
  document.getElementById('pagination-info').innerText = `หน้า ${page}/${totalPages} (${total.toLocaleString()} รายการ)`;

  const container = document.getElementById('pagination-buttons');
  container.innerHTML = '';

  if (page > 1) {
    const prev = document.createElement('button');
    prev.className = 'px-2 py-1 bg-white border border-slate-300 rounded-lg text-xs font-semibold';
    prev.innerText = '‹ หน้าก่อน';
    prev.onclick = () => loadTools(page - 1);
    container.appendChild(prev);
  }

  if (page < totalPages) {
    const next = document.createElement('button');
    next.className = 'px-2 py-1 bg-white border border-slate-300 rounded-lg text-xs font-semibold';
    next.innerText = 'ถัดไป ›';
    next.onclick = () => loadTools(page + 1);
    container.appendChild(next);
  }
}

// Weekly PM Schedule
async function loadSchedule() {
  const month = document.getElementById('schedule-month-select').value;
  const weekVal = document.getElementById('schedule-week-select').value;
  const statusFilter = document.getElementById('schedule-status-filter').value;

  const container = document.getElementById('schedule-cards-container');
  container.innerHTML = `<div class="text-center py-8 text-slate-400 text-xs">กำลังโหลดแผน PM...</div>`;

  let weekParam = '';
  if (weekVal !== 'all') {
    const yearlyWeek = (parseInt(month) - 1) * 4 + parseInt(weekVal);
    weekParam = `&week=${yearlyWeek}`;
  }

  const url = `/api/pm-schedule?month=${month}${weekParam}&status_filter=${statusFilter}`;

  try {
    const res = await fetch(url);
    const json = await res.json();
    if (!json.success || !json.data.length) {
      container.innerHTML = `<div class="text-center py-10 bg-white rounded-2xl border border-slate-200 p-6 text-xs text-slate-400">ไม่มีรายการตามแผนในช่วงนี้</div>`;
      document.getElementById('schedule-count-badge').innerText = '0 รายการ';
      return;
    }

    const items = json.data;
    document.getElementById('schedule-count-badge').innerText = `${items.length.toLocaleString()} รายการ`;
    const mName = MONTH_NAMES[parseInt(month) - 1];
    const wText = weekVal !== 'all' ? `สัปดาห์ที่ ${weekVal}` : 'ทุกสัปดาห์';
    document.getElementById('schedule-table-title').innerText = `แผนเดือน ${mName} (${wText})`;

    container.innerHTML = '';
    items.forEach((item) => {
      const isDone = item.actual_value && item.actual_value.trim() !== '';
      const card = document.createElement('div');
      card.className = `p-3.5 rounded-2xl border ${isDone ? 'bg-emerald-50/40 border-emerald-200' : 'bg-white border-slate-200'} shadow-xs flex flex-col space-y-2`;
      card.innerHTML = `
        <div class="flex items-start justify-between">
          <div>
            <div class="flex items-center space-x-1.5">
              <span class="font-mono font-bold text-blue-900 text-xs">${item.code}</span>
              <span class="bg-indigo-50 text-indigo-800 text-[10px] px-1.5 py-0.2 rounded font-medium">${item.tool_type}</span>
            </div>
            <h4 class="text-xs font-semibold text-slate-800 mt-0.5">${item.name}</h4>
          </div>
          <span class="text-[10px] font-bold ${isDone ? 'text-emerald-700 bg-emerald-100' : 'text-amber-700 bg-amber-100'} px-2 py-0.5 rounded-full">
            ${isDone ? `✓ ตรวจแล้ว` : `⚫ มีแผน PM`}
          </span>
        </div>

        <div class="flex items-center justify-between pt-2 border-t border-slate-100 text-xs">
          <span class="text-[11px] text-slate-500">${item.month_name} (สัปดาห์ที่ ${item.week_index})</span>
          <button onclick="openRecordForPM(${item.tool_id}, '${item.code}', '${escapeHtml(item.name)}', ${item.month_index}, ${item.week_index})"
                  class="bg-blue-600 active:scale-95 text-white px-3 py-1 rounded-lg text-xs font-bold shadow-xs flex items-center">
            <i data-lucide="clipboard-check" class="w-3.5 h-3.5 mr-1"></i> ${isDone ? 'ตรวจซ้ำ' : 'ตรวจตามแผน'}
          </button>
        </div>
      `;
      container.appendChild(card);
    });

    if (window.lucide) lucide.createIcons();

  } catch (err) {
    console.error(err);
    container.innerHTML = `<div class="text-center py-6 text-red-500 text-xs">เกิดข้อผิดพลาดในการโหลดแผน</div>`;
  }
}

function setScheduleStatusFilter(status) {
  document.getElementById('schedule-status-filter').value = status;
  document.querySelectorAll('#sched-tab-all, #sched-tab-pending, #sched-tab-done').forEach(b => {
    b.className = 'flex-1 py-1 text-center rounded font-medium text-blue-200';
  });
  const activeBtn = document.getElementById(`sched-tab-${status}`);
  if (activeBtn) activeBtn.className = 'flex-1 py-1 text-center rounded font-semibold bg-white/20 text-white';
  loadSchedule();
}

function setCurrentWeekAndMonth() {
  document.getElementById('schedule-month-select').value = '8';
  document.getElementById('schedule-week-select').value = '4';
  loadSchedule();
}

// Tool Autocomplete
let formSearchTimeout = null;
function searchToolForForm(query) {
  clearTimeout(formSearchTimeout);
  const dropdown = document.getElementById('form-tool-dropdown');

  if (!query || query.trim().length < 1) {
    dropdown.classList.add('hidden');
    return;
  }

  formSearchTimeout = setTimeout(async () => {
    try {
      const res = await fetch(`/api/tools?limit=10&q=${encodeURIComponent(query)}`);
      const json = await res.json();
      if (json.success && json.data.length > 0) {
        dropdown.innerHTML = '';
        json.data.forEach(t => {
          const item = document.createElement('div');
          item.className = 'px-3 py-2 hover:bg-blue-50 cursor-pointer flex items-center justify-between text-xs';
          item.innerHTML = `
            <div>
              <span class="font-bold text-blue-900 font-mono">${t.code}</span>
              <span class="ml-1.5 font-medium text-slate-700">${t.name}</span>
            </div>
            <span class="bg-indigo-50 text-indigo-700 px-1.5 py-0.2 rounded font-mono text-[10px]">${t.tool_type}</span>
          `;
          item.onclick = () => selectToolForForm(t);
          dropdown.appendChild(item);
        });
        dropdown.classList.remove('hidden');
      } else {
        dropdown.innerHTML = `<div class="p-2.5 text-center text-xs text-slate-400">ไม่พบเครื่องมือ</div>`;
        dropdown.classList.remove('hidden');
      }
    } catch (err) {
      console.error(err);
    }
  }, 200);
}

async function selectToolForForm(tool) {
  document.getElementById('form-tool-id').value = tool.id;
  document.getElementById('card-tool-code').innerText = tool.code;
  document.getElementById('card-tool-category').innerText = tool.category;
  document.getElementById('card-tool-name').innerText = tool.name;
  document.getElementById('card-tool-type').innerText = tool.tool_type || 'ทั่วไป';

  document.getElementById('form-selected-tool-card').classList.remove('hidden');
  document.getElementById('form-tool-dropdown').classList.add('hidden');
  document.getElementById('form-tool-search').value = '';
  document.getElementById('form-tool-search').classList.add('hidden');

  await loadChecklistForTool(tool.id);
}

async function loadChecklistForTool(toolId) {
  const section = document.getElementById('form-checklist-section');
  const container = document.getElementById('form-checklist-container');
  container.innerHTML = '<div class="text-center py-4 text-xs text-slate-400">กำลังโหลดหัวข้อตรวจเช็ค...</div>';
  section.classList.remove('hidden');

  try {
    const res = await fetch(`/api/checklists?tool_id=${toolId}`);
    const json = await res.json();
    if (json.success) {
      currentLoadedChecklists = {
        daily: json.daily_checklist || [],
        monthly: json.monthly_checklist || [],
        tool_type: json.tool_type || 'ทั่วไป'
      };

      document.getElementById('checklist-type-label').innerText = currentLoadedChecklists.tool_type;
      renderChecklistItems(currentChecklistFrequency);
    }
  } catch (err) {
    console.error(err);
  }
}

function switchChecklistFrequency(freq) {
  currentChecklistFrequency = freq;
  const btnMonthly = document.getElementById('chk-btn-monthly');
  const btnDaily = document.getElementById('chk-btn-daily');

  if (freq === 'monthly') {
    btnMonthly.className = 'flex-1 py-1 text-center rounded font-semibold bg-white shadow-xs text-blue-900';
    btnDaily.className = 'flex-1 py-1 text-center rounded font-medium text-slate-600';
    document.getElementById('form-maintenance-type').value = 'PM ตามแผนประจำปี';
  } else {
    btnDaily.className = 'flex-1 py-1 text-center rounded font-semibold bg-white shadow-xs text-amber-900';
    btnMonthly.className = 'flex-1 py-1 text-center rounded font-medium text-slate-600';
    document.getElementById('form-maintenance-type').value = 'ตรวจเช็คสภาพรายวัน';
  }
  renderChecklistItems(freq);
}

function renderChecklistItems(freq) {
  const container = document.getElementById('form-checklist-container');
  const items = freq === 'monthly' ? currentLoadedChecklists.monthly : currentLoadedChecklists.daily;

  if (!items.length) {
    container.innerHTML = '<div class="text-center py-3 text-xs text-slate-400">ไม่มีรายการตรวจเฉพาะ (ใช้การตรวจทั่วไป)</div>';
    return;
  }

  container.innerHTML = '';
  items.forEach((it) => {
    const row = document.createElement('div');
    row.className = 'p-2.5 bg-slate-50 border border-slate-200 rounded-xl space-y-1.5';
    row.innerHTML = `
      <div class="flex items-start justify-between gap-2">
        <div class="flex items-start space-x-1.5 flex-1">
          <span class="w-4 h-4 rounded-full bg-blue-600 text-white text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5">${it.item_no}</span>
          <span class="text-xs font-medium text-slate-800 leading-snug">${escapeHtml(it.item_text)}</span>
        </div>

        <div class="flex items-center space-x-1 shrink-0">
          <label class="cursor-pointer">
            <input type="radio" name="chk_status_${it.item_no}" value="ปกติ (P)" checked onchange="onChecklistStatusChange(${it.item_no}, 'pass')" class="peer sr-only">
            <span class="px-2 py-0.5 rounded text-[11px] font-bold bg-white text-slate-600 border border-slate-200 peer-checked:bg-emerald-600 peer-checked:text-white peer-checked:border-emerald-600 inline-block transition">P</span>
          </label>
          <label class="cursor-pointer">
            <input type="radio" name="chk_status_${it.item_no}" value="ผิดปกติ (O)" onchange="onChecklistStatusChange(${it.item_no}, 'fail')" class="peer sr-only">
            <span class="px-2 py-0.5 rounded text-[11px] font-bold bg-white text-slate-600 border border-slate-200 peer-checked:bg-rose-600 peer-checked:text-white peer-checked:border-rose-600 inline-block transition">O</span>
          </label>
        </div>
      </div>

      <div id="chk_notes_div_${it.item_no}" class="hidden pt-1">
        <input type="text" id="chk_notes_${it.item_no}" placeholder="ระบุสิ่งที่พบ..." class="w-full px-2.5 py-1 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-900">
      </div>
    `;
    container.appendChild(row);
  });
}

function onChecklistStatusChange(itemNo, status) {
  const notesDiv = document.getElementById(`chk_notes_div_${itemNo}`);
  if (notesDiv) {
    if (status === 'fail') {
      notesDiv.classList.remove('hidden');
      document.getElementById('form-result-status').value = 'มีข้อบกพร่อง/รอซ่อม';
    } else {
      notesDiv.classList.add('hidden');
    }
  }
}

function setAllChecklistPass() {
  const items = currentChecklistFrequency === 'monthly' ? currentLoadedChecklists.monthly : currentLoadedChecklists.daily;
  items.forEach(it => {
    const radio = document.querySelector(`input[name="chk_status_${it.item_no}"][value="ปกติ (P)"]`);
    if (radio) {
      radio.checked = true;
      onChecklistStatusChange(it.item_no, 'pass');
    }
  });
  document.getElementById('form-result-status').value = 'ปกติผ่านเกณฑ์';
  showToast("เลือกผลตรวจปกติ (P) ทั้งหมดแล้ว");
}

function previewPhoto(input) {
  if (input.files && input.files[0]) {
    const reader = new FileReader();
    reader.onload = function(e) {
      document.getElementById('photo-preview-img').src = e.target.result;
      document.getElementById('photo-preview-container').classList.remove('hidden');
      document.getElementById('photo-label-text').innerText = 'ถ่ายภาพเรียบร้อย';
    };
    reader.readAsDataURL(input.files[0]);
  }
}

function removePhoto() {
  document.getElementById('form-photo-input').value = '';
  document.getElementById('photo-preview-container').classList.add('hidden');
  document.getElementById('photo-label-text').innerText = 'แตะเพื่อถ่ายรูป / เลือกภาพ';
}

function clearSelectedTool() {
  document.getElementById('form-tool-id').value = '';
  document.getElementById('form-selected-tool-card').classList.add('hidden');
  document.getElementById('form-checklist-section').classList.add('hidden');
  const searchInput = document.getElementById('form-tool-search');
  searchInput.classList.remove('hidden');
  searchInput.value = '';
  searchInput.focus();
}

function openRecordForTool(id, code, name, category, toolType) {
  switchTab('new-maintenance');
  selectToolForForm({ id, code, name, category, tool_type: toolType });
}

function openRecordForPM(id, code, name, monthIndex, weekIndex) {
  switchTab('new-maintenance');
  selectToolForForm({ id, code, name, category: '', tool_type: '' });
  document.getElementById('form-maintenance-type').value = 'PM ตามแผนประจำปี';
  document.getElementById('form-result-status').value = 'ปกติผ่านเกณฑ์';
  document.getElementById('form-details').value = `ตรวจสอบ PM ประจำปี 2026 (เดือน ${MONTH_NAMES[monthIndex-1]} สัปดาห์ ${weekIndex})`;
  document.getElementById('form-update-pm').checked = true;
}

// Submit Maintenance Form
async function submitMaintenanceForm(e) {
  e.preventDefault();

  const toolId = document.getElementById('form-tool-id').value;
  if (!toolId) {
    showToast("กรุณาเลือกเครื่องมือก่อนบันทึก", "error");
    return;
  }

  const items = currentChecklistFrequency === 'monthly' ? currentLoadedChecklists.monthly : currentLoadedChecklists.daily;
  const checklistResults = [];
  items.forEach(it => {
    const checkedRadio = document.querySelector(`input[name="chk_status_${it.item_no}"]:checked`);
    const statusVal = checkedRadio ? checkedRadio.value : 'ปกติ (P)';
    const noteVal = document.getElementById(`chk_notes_${it.item_no}`)?.value.trim() || '';

    checklistResults.push({
      item_no: it.item_no,
      item_text: it.item_text,
      status_result: statusVal,
      notes: noteVal
    });
  });

  const payload = {
    tool_id: parseInt(toolId),
    maintenance_type: document.getElementById('form-maintenance-type').value,
    maintenance_date: document.getElementById('form-maintenance-date').value,
    inspector_name: document.getElementById('form-inspector-name').value,
    result_status: document.getElementById('form-result-status').value,
    details: document.getElementById('form-details').value,
    update_pm_actual: document.getElementById('form-update-pm').checked,
    checklist_items: checklistResults
  };

  const btn = document.getElementById('form-submit-btn');
  btn.disabled = true;
  btn.innerHTML = '<span>กำลังบันทึก...</span>';

  try {
    const res = await fetch('/api/maintenance', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await res.json();

    if (result.success) {
      showToast("บันทึกการตรวจเช็คสำเร็จแล้ว!", "success");
      resetMaintenanceForm();
      loadStats();
      setTimeout(() => switchTab('logs'), 600);
    } else {
      showToast(result.error || "เกิดข้อผิดพลาดในการบันทึก", "error");
    }
  } catch (err) {
    console.error(err);
    showToast("ไม่สามารถเชื่อมต่อได้", "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i data-lucide="save" class="w-4 h-4 mr-1"></i> <span>บันทึกผลการตรวจสอบ</span>`;
    if (window.lucide) lucide.createIcons();
  }
}

function resetMaintenanceForm() {
  clearSelectedTool();
  removePhoto();
  document.getElementById('form-details').value = '';
  document.getElementById('form-result-status').value = 'ปกติผ่านเกณฑ์';
}

// Load Logs
async function loadLogs(page = 1) {
  const container = document.getElementById('logs-cards-container');
  container.innerHTML = `<div class="text-center py-8 text-slate-400 text-xs">กำลังโหลดประวัติ...</div>`;

  try {
    const res = await fetch(`/api/logs?page=${page}&limit=25`);
    const json = await res.json();

    if (!json.success || !json.data.length) {
      container.innerHTML = `<div class="text-center py-10 bg-white rounded-2xl border border-slate-200 p-6 text-xs text-slate-400">ยังไม่มีบันทึกประวัติ</div>`;
      return;
    }

    const { data: logs, pagination } = json;
    container.innerHTML = '';

    logs.forEach((log) => {
      let chkHtml = '';
      if (log.inspection_details && log.inspection_details.length > 0) {
        const passCount = log.inspection_details.filter(d => d.status_result.includes('ปกติ (P)')).length;
        const failItems = log.inspection_details.filter(d => d.status_result.includes('ผิดปกติ'));
        if (failItems.length > 0) {
          chkHtml = `<div class="text-[10px] text-rose-700 bg-rose-50 p-1.5 rounded border border-rose-200 mt-1">⚠️ พบจุดผิดปกติ: ${failItems.map(f => `ข้อ ${f.item_no}`).join(', ')}</div>`;
        } else {
          chkHtml = `<div class="text-[10px] text-emerald-700 mt-0.5">✓ ตรวจผ่านครบ ${passCount} ข้อ</div>`;
        }
      }

      const card = document.createElement('div');
      card.className = 'p-3 bg-white rounded-2xl border border-slate-200 shadow-xs space-y-1.5 text-xs';
      card.innerHTML = `
        <div class="flex items-center justify-between">
          <span class="font-bold text-blue-900 font-mono">${log.code}</span>
          <span class="text-[10px] text-slate-400 font-mono">${log.maintenance_date}</span>
        </div>
        <p class="font-semibold text-slate-800">${log.tool_name}</p>
        <p class="text-slate-600 text-[11px]">${escapeHtml(log.details || 'ตรวจสภาพตามรอบ')}</p>
        ${chkHtml}
        <div class="flex items-center justify-between pt-1 text-[10px] text-slate-500 border-t border-slate-100">
          <span>ผู้ตรวจ: <strong>${log.inspector_name}</strong></span>
          <span class="font-bold text-emerald-700">${log.result_status}</span>
        </div>
      `;
      container.appendChild(card);
    });

  } catch (err) {
    console.error(err);
  }
}

// Tool Detail Modal
async function openToolModal(toolId) {
  const modal = document.getElementById('tool-detail-modal');
  modal.classList.remove('hidden');

  try {
    const res = await fetch(`/api/tools/${toolId}`);
    const json = await res.json();
    if (!json.success) return;

    const { tool, pm_plans, logs, daily_checklist, monthly_checklist } = json.data;

    document.getElementById('modal-tool-code').innerText = tool.code;
    document.getElementById('modal-tool-name').innerText = tool.name;
    document.getElementById('modal-tool-status').innerHTML = getStatusBadge(tool.status);

    document.getElementById('modal-quick-record-btn').onclick = () => {
      closeToolModal();
      openRecordForTool(tool.id, tool.code, tool.name, tool.category, tool.tool_type);
    };

    document.getElementById('modal-pm-grid').innerHTML = buildPMGridHTML(pm_plans);

    document.getElementById('modal-monthly-chk-list').innerHTML = monthly_checklist.map(c => `<div>• ${escapeHtml(c.item_text)}</div>`).join('');
    document.getElementById('modal-daily-chk-list').innerHTML = daily_checklist.map(c => `<div>• ${escapeHtml(c.item_text)}</div>`).join('');

    const logsContainer = document.getElementById('modal-logs-list');
    if (!logs.length) {
      logsContainer.innerHTML = `<div class="p-3 text-center text-xs text-slate-400 bg-slate-50 rounded-xl">ยังไม่มีประวัติการซ่อม</div>`;
    } else {
      logsContainer.innerHTML = '';
      logs.forEach(log => {
        const item = document.createElement('div');
        item.className = 'p-2 bg-slate-50 rounded-xl text-xs space-y-0.5';
        item.innerHTML = `
          <div class="flex justify-between font-semibold text-blue-900">
            <span>${log.maintenance_type}</span>
            <span class="font-mono text-slate-400">${log.maintenance_date}</span>
          </div>
          <p class="text-slate-600 text-[11px]">${escapeHtml(log.details || '-')}</p>
        `;
        logsContainer.appendChild(item);
      });
    }

    if (window.lucide) lucide.createIcons();

  } catch (err) {
    console.error(err);
  }
}

function buildPMGridHTML(pm_plans) {
  const planMap = {};
  pm_plans.forEach(p => {
    planMap[p.week_num_yearly] = p;
  });

  let html = `<table class="w-full text-center border-collapse text-[10px]"><thead><tr class="bg-slate-100 font-bold"><th class="p-1">Target</th>`;
  MONTH_NAMES.forEach(m => {
    html += `<th colspan="4" class="p-1 border-l border-slate-200 text-blue-900">${m.substring(0, 3)}</th>`;
  });
  html += `</tr></thead><tbody><tr class="border-t border-slate-200"><td class="p-1 font-bold text-blue-900">Plan</td>`;
  for (let i = 1; i <= 48; i++) {
    const hasDot = planMap[i] && planMap[i].plan_value === '⚫';
    html += `<td class="p-0.5 border-l border-slate-100">${hasDot ? '<span class="inline-block w-2.5 h-2.5 rounded-full bg-slate-800"></span>' : ''}</td>`;
  }
  html += `</tr><tr class="border-t border-slate-200"><td class="p-1 font-bold text-emerald-700">Actual</td>`;
  for (let i = 1; i <= 48; i++) {
    const isDone = planMap[i] && planMap[i].actual_value;
    html += `<td class="p-0.5 border-l border-slate-100">${isDone ? '<span class="text-emerald-600 font-bold">✓</span>' : ''}</td>`;
  }
  html += `</tr></tbody></table>`;
  return html;
}

function closeToolModal() {
  document.getElementById('tool-detail-modal').classList.add('hidden');
}

function showToast(message, type = 'success') {
  const toast = document.getElementById('toast');
  const icon = document.getElementById('toast-icon');
  const msg = document.getElementById('toast-message');

  msg.innerText = message;
  icon.innerHTML = type === 'success' ? '✅' : '⚠️';
  toast.classList.remove('hidden');
  setTimeout(() => toast.classList.add('hidden'), 2500);
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
