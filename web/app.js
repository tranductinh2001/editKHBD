// KHBD Pro - Frontend Application Logic

let currentConfig = {};
let scannedFiles = [];
let selectedFileIndices = new Set();
let ppctFilesList = [];
let currentDiffFile = null;

// DOM Elements
const inputFolderPath = document.getElementById("input-folder-path");
const selectPpctFile = document.getElementById("select-ppct-file");
const selectNamingScheme = document.getElementById("select-naming-scheme");
const selectOutputMode = document.getElementById("select-output-mode");
const btnScan = document.getElementById("btn-scan");
const btnOpenExplorer = document.getElementById("btn-open-explorer");
const btnBatchProcess = document.getElementById("btn-batch-process");
const btnClearLog = document.getElementById("btn-clear-log");
const btnThemeToggle = document.getElementById("btn-theme-toggle");
const btnHelpModal = document.getElementById("btn-help-modal");
const btnCloseHelp = document.getElementById("btn-close-help");
const btnHelpOk = document.getElementById("btn-help-ok");

// Stats & Progress
const statTotalFiles = document.getElementById("stat-total-files");
const statMatchedFiles = document.getElementById("stat-matched-files");
const statSelectedFiles = document.getElementById("stat-selected-files");
const statDoneFiles = document.getElementById("stat-done-files");
const progressContainer = document.getElementById("progress-container");
const progressLabel = document.getElementById("progress-label");
const progressPercentage = document.getElementById("progress-percentage");
const progressBarFill = document.getElementById("progress-bar-fill");
const terminalBody = document.getElementById("terminal-body");

// Tabs
const tabBtns = document.querySelectorAll(".tab-btn");
const tabPanels = document.querySelectorAll(".tab-panel");
const tabCountFiles = document.getElementById("tab-count-files");

// Files Table
const tableFilesBody = document.getElementById("table-files-body");
const checkSelectAll = document.getElementById("check-select-all");
const selectedSummaryText = document.getElementById("selected-summary-text");
const inputSearchFile = document.getElementById("input-search-file");

// Config Form - Visual Studio Controls
const cfgTeacherName = document.getElementById("cfg-teacher-name");
const cfgSchoolName = document.getElementById("cfg-school-name");
const cfgDepartment = document.getElementById("cfg-department");
const cfgSchoolYear = document.getElementById("cfg-school-year");
const cfgSubject = document.getElementById("cfg-subject");
const cfgSubjectType = document.getElementById("cfg-subject-type");
const cfgClasses = document.getElementById("cfg-classes");
const cfgTeachingDate = document.getElementById("cfg-teaching-date");
const cfgDuration = document.getElementById("cfg-duration");
const cfgTitlePrefix = document.getElementById("cfg-title-prefix");
const cfgOptHeader = document.getElementById("cfg-opt-header");
const cfgOptFooter = document.getElementById("cfg-opt-footer");
const cfgOptApproval = document.getElementById("cfg-opt-approval");
const cfgOptBorder = document.getElementById("cfg-opt-border");
const selectTemplateStyle = document.getElementById("select-template-style");
const cfgMarginTop = document.getElementById("cfg-margin-top");
const cfgMarginBottom = document.getElementById("cfg-margin-bottom");
const cfgMarginLeft = document.getElementById("cfg-margin-left");
const cfgMarginRight = document.getElementById("cfg-margin-right");
const cfgNamingNote = document.getElementById("cfg-naming-note");
const btnSaveConfig = document.getElementById("btn-save-config");
const saveConfigStatus = document.getElementById("save-config-status");

const cfgStartDate = document.getElementById("cfg-start-date");
const cfgDateFormat = document.getElementById("cfg-date-format");
const cfgAutoDate = document.getElementById("cfg-auto-date");
const cfgSignerSchool = document.getElementById("cfg-signer-school");
const cfgSignerDept = document.getElementById("cfg-signer-dept");
const signersBadgesPool = document.getElementById("signers-badges-pool");
const btnAddSigner = document.getElementById("btn-add-signer");
const dropzoneSchool = document.getElementById("dropzone-school");
const dropzoneDept = document.getElementById("dropzone-dept");
let signersList = [
  "Lê Thị Phương Thảo",
  "Nguyễn Văn Cường",
  "Lê Thị Hương",
  "Phạm Văn Tuấn",
  "Trần Thị Mai"
];

// Live Simulated A4 Sheet Elements
const pvHeader = document.getElementById("pv-header");
const pvTable = document.getElementById("pv-table");
const pvTuan = document.getElementById("pv-tuan");
const pvTiet = document.getElementById("pv-tiet");
const pvDate = document.getElementById("pv-date");
const pvTeacher = document.getElementById("pv-teacher");
const pvDept = document.getElementById("pv-dept");
const pvTitle = document.getElementById("pv-title");
const pvSubjectClass = document.getElementById("pv-subject-class");
const pvDuration = document.getElementById("pv-duration");
const pvApproval = document.getElementById("pv-approval");
const pvSignerSchool = document.getElementById("pv-signer-school");
const pvSignerDept = document.getElementById("pv-signer-dept");
const pvNoteSchool = document.getElementById("pv-note-school");
const pvNoteDept = document.getElementById("pv-note-dept");
const pvFooter = document.getElementById("pv-footer");

// PPCT Table
const ppctTitleDisplay = document.getElementById("ppct-title-display");
const tablePpctBody = document.getElementById("table-ppct-body");
const inputSearchPpct = document.getElementById("input-search-ppct");

// Modals
const modalDiff = document.getElementById("modal-diff");
const btnCloseModal = document.getElementById("btn-close-modal");
const btnModalCancel = document.getElementById("btn-modal-cancel");
const btnModalProcessSingle = document.getElementById("btn-modal-process-single");
const modalFileTitle = document.getElementById("modal-file-title");
const diffBeforeContent = document.getElementById("diff-before-content");
const diffAfterContent = document.getElementById("diff-after-content");
const modalHelp = document.getElementById("modal-help");

// Quick Edit Modal
const modalEditFile = document.getElementById("modal-edit-file");
const btnCloseEditModal = document.getElementById("btn-close-edit-modal");
const btnCancelEdit = document.getElementById("btn-cancel-edit");
const btnSaveEdit = document.getElementById("btn-save-edit");
const editOrigFilename = document.getElementById("edit-orig-filename");
const editWeek = document.getElementById("edit-week");
const editPeriods = document.getElementById("edit-periods");
const editLessonName = document.getElementById("edit-lesson-name");
const editTeachingDate = document.getElementById("edit-teaching-date");
const editTargetFilename = document.getElementById("edit-target-filename");
const btnSyncPpctDates = document.getElementById("btn-sync-ppct-dates");
const btnQuickAiFix = document.getElementById("btn-quick-ai-fix");
const quickAiStatus = document.getElementById("quick-ai-status");
let currentEditingIndex = -1;

// Beekone AI Elements
const btnBatchAiFix = document.getElementById("btn-batch-ai-fix");
const cfgAiEndpoint = document.getElementById("cfg-ai-endpoint");
const cfgAiKey = document.getElementById("cfg-ai-key");
const cfgAiModel = document.getElementById("cfg-ai-model");
const btnToggleKeyVis = document.getElementById("btn-toggle-key-vis");
const btnTestAi = document.getElementById("btn-test-ai");
const aiTestResult = document.getElementById("ai-test-result");
const aiOptAutoTitle = document.getElementById("ai-opt-auto-title");
const btnSaveAi = document.getElementById("btn-save-ai");
const aiStatusMsg = document.getElementById("ai-status-msg");

// Logger Helper
function log(msg, type = "info") {
  const line = document.createElement("div");
  line.className = `log-line log-${type}`;
  const now = new Date().toLocaleTimeString();
  line.textContent = `[${now}] ${msg}`;
  terminalBody.appendChild(line);
  terminalBody.scrollTop = terminalBody.scrollHeight;
}

// 1. Initialization
async function init() {
  setupEventListeners();
  setupDropZones();
  loadTheme();
  await fetchConfig();
  await fetchPpctFiles();
  // Auto scan default directory
  if (inputFolderPath.value.trim()) {
    scanFolder();
  }
}

// 2. Fetch Config
async function fetchConfig() {
  try {
    const res = await fetch("/api/config");
    const json = await res.json();
    if (json.success) {
      currentConfig = json.config;
      populateConfigForm(currentConfig);
    }
  } catch (err) {
    log(`Lỗi tải cấu hình: ${err.message}`, "error");
  }
}

function populateConfigForm(cfg) {
  if (cfg.default_scan_path) inputFolderPath.value = cfg.default_scan_path;
  if (cfg.teacher_name && cfgTeacherName) cfgTeacherName.value = cfg.teacher_name;
  if (cfg.school_name && cfgSchoolName) cfgSchoolName.value = cfg.school_name;
  if (cfg.department && cfgDepartment) cfgDepartment.value = cfg.department;
  if (cfg.school_year && cfgSchoolYear) cfgSchoolYear.value = cfg.school_year;
  if (cfg.subject && cfgSubject) cfgSubject.value = cfg.subject;
  if (cfg.subject_type && cfgSubjectType) cfgSubjectType.value = cfg.subject_type;
  if (cfg.classes && cfgClasses) cfgClasses.value = cfg.classes;
  if (cfg.teaching_date && cfgTeachingDate) cfgTeachingDate.value = cfg.teaching_date;
  if (cfg.duration && cfgDuration) cfgDuration.value = cfg.duration;
  if (cfg.title_prefix !== undefined && cfgTitlePrefix) cfgTitlePrefix.value = cfg.title_prefix;
  if (cfg.enable_header !== undefined && cfgOptHeader) cfgOptHeader.checked = cfg.enable_header;
  if (cfg.enable_footer !== undefined && cfgOptFooter) cfgOptFooter.checked = cfg.enable_footer;
  if (cfg.enable_approval_block !== undefined && cfgOptApproval) cfgOptApproval.checked = cfg.enable_approval_block;
  if (cfg.table_border !== undefined && cfgOptBorder) cfgOptBorder.checked = cfg.table_border;
  if (cfg.template_style && selectTemplateStyle) selectTemplateStyle.value = cfg.template_style;

  if (cfg.school_year_start_date && cfgStartDate) cfgStartDate.value = cfg.school_year_start_date;
  if (cfg.teaching_date_format && cfgDateFormat) cfgDateFormat.value = cfg.teaching_date_format;
  if (cfg.auto_calc_teaching_date !== undefined && cfgAutoDate) cfgAutoDate.checked = cfg.auto_calc_teaching_date;
  if (cfg.signer_school !== undefined && cfgSignerSchool) cfgSignerSchool.value = cfg.signer_school;
  if (cfg.signer_dept !== undefined && cfgSignerDept) cfgSignerDept.value = cfg.signer_dept;
  if (cfg.signers_list && Array.isArray(cfg.signers_list)) signersList = cfg.signers_list;

  if (cfg.margin_top_cm && cfgMarginTop) cfgMarginTop.value = cfg.margin_top_cm;
  if (cfg.margin_bottom_cm && cfgMarginBottom) cfgMarginBottom.value = cfg.margin_bottom_cm;
  if (cfg.margin_left_cm && cfgMarginLeft) cfgMarginLeft.value = cfg.margin_left_cm;
  if (cfg.margin_right_cm && cfgMarginRight) cfgMarginRight.value = cfg.margin_right_cm;
  if (cfg.include_file_naming_note !== undefined && cfgNamingNote) cfgNamingNote.checked = cfg.include_file_naming_note;
  if (cfg.naming_scheme && selectNamingScheme) selectNamingScheme.value = cfg.naming_scheme;
  if (cfg.output_mode && selectOutputMode) selectOutputMode.value = cfg.output_mode;
  if (cfg.ai_config) {
    if (cfg.ai_config.base_url && cfgAiEndpoint) cfgAiEndpoint.value = cfg.ai_config.base_url;
    if (cfg.ai_config.api_key && cfgAiKey) cfgAiKey.value = cfg.ai_config.api_key;
    if (cfg.ai_config.model && cfgAiModel) cfgAiModel.value = cfg.ai_config.model;
    if (cfg.ai_config.auto_format_title !== undefined && aiOptAutoTitle) aiOptAutoTitle.checked = cfg.ai_config.auto_format_title;
    if (cfg.ai_config.add_nls !== undefined && document.getElementById("ai-opt-nls")) document.getElementById("ai-opt-nls").checked = cfg.ai_config.add_nls;
    if (cfg.ai_config.format_5512 !== undefined && document.getElementById("ai-opt-5512")) document.getElementById("ai-opt-5512").checked = cfg.ai_config.format_5512;
  }

  renderSignersBadges();
  updateLivePreview();
}

// Calculate Monday-to-Friday week dates
function calculateWeekDates(weekNum, startDateStr = "2026-09-07", dateFormat = "d2_to_d6") {
  if (!weekNum || isNaN(weekNum) || parseInt(weekNum, 10) < 1) return "";
  try {
    const parts = (startDateStr || "2026-09-07").split("-");
    if (parts.length !== 3) return "";
    const year = parseInt(parts[0], 10);
    const month = parseInt(parts[1], 10) - 1;
    const day = parseInt(parts[2], 10);
    const d = new Date(year, month, day);

    // Monday of week 1
    const dayOfWeek = d.getDay(); // 0 is Sun, 1 is Mon
    const offsetToMon = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
    d.setDate(d.getDate() + offsetToMon);

    const weekOffsetDays = (parseInt(weekNum, 10) - 1) * 7;
    const monDate = new Date(d);
    monDate.setDate(monDate.getDate() + weekOffsetDays);

    const friDate = new Date(monDate);
    friDate.setDate(friDate.getDate() + 4);

    const pad = n => String(n).padStart(2, "0");
    const monStr = `${pad(monDate.getDate())}/${pad(monDate.getMonth() + 1)}/${monDate.getFullYear()}`;
    const friStr = `${pad(friDate.getDate())}/${pad(friDate.getMonth() + 1)}/${friDate.getFullYear()}`;

    if (dateFormat === "d2_only") {
      return monStr;
    } else if (dateFormat === "tu_den") {
      return `Từ ${monStr} đến ${friStr}`;
    } else {
      return `${monStr} - ${friStr}`;
    }
  } catch (e) {
    return "";
  }
}

// Render Draggable Signer Chips Pool
function renderSignersBadges() {
  if (!signersBadgesPool) return;
  signersBadgesPool.innerHTML = "";
  signersList.forEach((name, idx) => {
    const chip = document.createElement("div");
    chip.className = "signer-chip";
    chip.draggable = true;
    chip.dataset.name = name;
    chip.title = "Kéo thả vào ô bên dưới hoặc click để gán nhanh";
    chip.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="cursor: grab; flex-shrink: 0;">
        <circle cx="9" cy="12" r="1"></circle>
        <circle cx="9" cy="5" r="1"></circle>
        <circle cx="9" cy="19" r="1"></circle>
        <circle cx="15" cy="12" r="1"></circle>
        <circle cx="15" cy="5" r="1"></circle>
        <circle cx="15" cy="19" r="1"></circle>
      </svg>
      <span>${escapeHtml(name)}</span>
      <button type="button" class="btn-remove-signer" title="Xóa người này khỏi danh sách">&times;</button>
    `;

    chip.addEventListener("dragstart", (e) => {
      e.dataTransfer.setData("text/plain", name);
      chip.classList.add("dragging");
    });
    chip.addEventListener("dragend", () => {
      chip.classList.remove("dragging");
    });

    const btnRemove = chip.querySelector(".btn-remove-signer");
    btnRemove.addEventListener("click", (e) => {
      e.stopPropagation();
      signersList.splice(idx, 1);
      renderSignersBadges();
    });

    // Quick click assignment
    chip.addEventListener("click", () => {
      if (!cfgSignerSchool.value.trim()) {
        cfgSignerSchool.value = name;
        log(`Đã gán "${name}" cho Duyệt Chuyên môn`, "info");
      } else {
        cfgSignerDept.value = name;
        log(`Đã gán "${name}" cho Duyệt Tổ chuyên môn`, "info");
      }
      updateLivePreview();
    });

    signersBadgesPool.appendChild(chip);
  });
}

// Setup Drag & Drop Zones for Signers
function setupDropZones() {
  const zones = [
    { el: dropzoneSchool, targetInput: cfgSignerSchool },
    { el: dropzoneDept, targetInput: cfgSignerDept }
  ];

  zones.forEach(({ el, targetInput }) => {
    if (!el) return;
    el.addEventListener("dragover", (e) => {
      e.preventDefault();
      el.classList.add("dragover");
    });
    el.addEventListener("dragleave", () => {
      el.classList.remove("dragover");
    });
    el.addEventListener("drop", (e) => {
      e.preventDefault();
      el.classList.remove("dragover");
      const droppedName = e.dataTransfer.getData("text/plain");
      if (droppedName && targetInput) {
        targetInput.value = droppedName;
        updateLivePreview();
        log(`Đã kéo thả gán người ký: "${droppedName}"`, "success");
      }
    });
  });
}

// Determine label: "Môn học" vs "Hoạt động giáo dục"
function getSubjectLabel(subject) {
  if (cfgSubjectType && cfgSubjectType.value !== "auto") {
    return cfgSubjectType.value === "hoat_dong_giao_duc" ? "Hoạt động giáo dục" : "Môn học";
  }
  const s = (subject || "").toLowerCase().trim();
  const hdtnKeywords = [
    "hdtn", "hđtn", "tnhn", "trải nghiệm", "trai nghiem",
    "hướng nghiệp", "huong nghiep", "hoạt động trải nghiệm", "hoạt động giáo dục"
  ];
  if (hdtnKeywords.some(k => s.includes(k))) {
    return "Hoạt động giáo dục";
  }
  return "Môn học";
}

// Live Synchronized Visual A4 Sheet Preview
function updateLivePreview() {
  const teacher = cfgTeacherName ? cfgTeacherName.value.trim() : "Lê Thị Phương Thảo";
  const dept = cfgDepartment ? cfgDepartment.value.trim() : "Tổ Tự Nhiên";
  const school = cfgSchoolName ? cfgSchoolName.value.trim() : "Trường TH&THCS Đăk Trôi";
  const year = cfgSchoolYear ? cfgSchoolYear.value.trim() : "2025-2026";
  const subject = cfgSubject ? cfgSubject.value.trim() : "Tin học";
  const classes = cfgClasses ? cfgClasses.value.trim() : "9";
  const duration = cfgDuration ? cfgDuration.value.trim() : "2";
  const prefix = cfgTitlePrefix ? cfgTitlePrefix.value : "TÊN BÀI DẠY: ";

  // Teaching Date Auto / Manual
  let date = cfgTeachingDate ? cfgTeachingDate.value.trim() : "../../2026";
  if (cfgAutoDate && cfgAutoDate.checked) {
    const sDate = cfgStartDate ? cfgStartDate.value : "2026-09-07";
    const dFmt = cfgDateFormat ? cfgDateFormat.value : "d2_to_d6";
    const calc = calculateWeekDates(1, sDate, dFmt);
    if (calc) date = calc;
  }

  // Header
  if (pvHeader) {
    if (cfgOptHeader && !cfgOptHeader.checked) {
      pvHeader.style.display = "none";
    } else {
      pvHeader.style.display = "block";
      pvHeader.textContent = `Kế hoạch bài dạy ${subject} ${classes}, năm học ${year}`;
    }
  }

  // Top Table (Mau KHBD THCS.docx 1x2 at very top)
  if (pvDate) pvDate.textContent = `Ngày dạy: ${date}`;
  if (pvTeacher) pvTeacher.textContent = `Họ và tên giáo viên: ${teacher}`;
  if (pvDept) pvDept.textContent = `Tổ chuyên môn: ${dept}`;
  if (pvTable) {
    if (cfgOptBorder && cfgOptBorder.checked) {
      pvTable.classList.add("bordered");
    } else {
      pvTable.classList.remove("bordered");
    }
  }

  // Title Block
  if (pvTitle) {
    pvTitle.textContent = `${prefix}BÀI 1. THẾ GIỚI KĨ THUẬT SỐ`;
  }
  if (pvSubjectClass) {
    const subLabel = getSubjectLabel(subject);
    pvSubjectClass.textContent = `${subLabel}: ${subject}; lớp: ${classes}`;
  }
  if (pvDuration) {
    pvDuration.textContent = `Thời gian thực hiện: ${duration} tiết`;
  }

  // Approval Block
  if (pvApproval) {
    if (cfgOptApproval && !cfgOptApproval.checked) {
      pvApproval.style.display = "none";
    } else {
      pvApproval.style.display = "flex";
      const sSchool = cfgSignerSchool ? cfgSignerSchool.value.trim() : "";
      const sDept = cfgSignerDept ? cfgSignerDept.value.trim() : "";
      if (pvSignerSchool) pvSignerSchool.textContent = sSchool || "(Chưa chọn)";
      if (pvSignerDept) pvSignerDept.textContent = sDept || "(Chưa chọn)";
    }
  }

  // Footer
  if (pvFooter) {
    if (cfgOptFooter && !cfgOptFooter.checked) {
      pvFooter.style.display = "none";
    } else {
      pvFooter.style.display = "block";
      pvFooter.textContent = `${teacher} - ${school}`;
    }
  }
}

// 3. Fetch PPCT Files List
async function fetchPpctFiles() {
  try {
    const res = await fetch("/api/ppct/files");
    const json = await res.json();
    if (json.success && json.files) {
      ppctFilesList = json.files;
      selectPpctFile.innerHTML = "";
      
      // Prefer _Lop_9.xlsx as default or from config
      const activeFile = currentConfig.ppct_file || "_Lop_9.xlsx";
      
      json.files.forEach(f => {
        const opt = document.createElement("option");
        opt.value = f.filename;
        const countText = f.item_count ? ` (${f.item_count} bài/tiết)` : "";
        opt.textContent = `${f.filename}${countText}`;
        if (f.filename === activeFile) {
          opt.selected = true;
        }
        selectPpctFile.appendChild(opt);
      });

      // Load active PPCT data to tab
      loadPpctTableData(selectPpctFile.value);
    }
  } catch (err) {
    log(`Lỗi tải danh sách PPCT: ${err.message}`, "error");
  }
}

// 4. Load PPCT Table Data into Tab 3
async function loadPpctTableData(filename) {
  try {
    tablePpctBody.innerHTML = `<tr><td colspan="6" class="text-center py-6 text-muted">Đang tải dữ liệu ${filename}...</td></tr>`;
    const res = await fetch(`/api/ppct/data?file=${encodeURIComponent(filename)}`);
    const json = await res.json();
    if (json.success && json.data) {
      const data = json.data;
      ppctTitleDisplay.textContent = `Bảng PPCT: ${filename} - ${data.title || ''}`;
      renderPpctRows(data.items || []);
    } else {
      tablePpctBody.innerHTML = `<tr><td colspan="6" class="text-center py-6 text-muted">Không có dữ liệu bài học dạng bảng</td></tr>`;
    }
  } catch (err) {
    tablePpctBody.innerHTML = `<tr><td colspan="6" class="text-center py-6 text-danger">Lỗi: ${err.message}</td></tr>`;
  }
}

function renderPpctRows(items) {
  if (!items || items.length === 0) {
    tablePpctBody.innerHTML = `<tr><td colspan="6" class="text-center py-6 text-muted">Không có mục nào trong bảng PPCT này.</td></tr>`;
    return;
  }
  tablePpctBody.innerHTML = "";

  const startDate = cfgStartDate ? cfgStartDate.value : "2026-09-07";
  const dateFormat = cfgDateFormat ? cfgDateFormat.value : "d2_to_d6";

  items.forEach(it => {
    let ngayDayText = it.ngay_day || "";
    if (!ngayDayText && it.tuan) {
      ngayDayText = calculateWeekDates(it.tuan, startDate, dateFormat);
    }

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="font-bold">${it.stt !== null && it.stt !== undefined ? it.stt : ''}</td>
      <td>Tuần ${it.tuan !== null && it.tuan !== undefined ? it.tuan : ''}</td>
      <td>Tiết ${it.tiet !== null && it.tiet !== undefined ? it.tiet : ''}</td>
      <td class="font-bold">${escapeHtml(it.ten_bai || '')}</td>
      <td class="font-mono text-sm" style="color: #0284c7; font-weight: 500;">${escapeHtml(ngayDayText || 'Chưa xác định')}</td>
      <td class="text-muted text-sm font-mono">${escapeHtml(it.ghi_chu || '')}</td>
    `;
    tablePpctBody.appendChild(tr);
  });
}

// 5. Scan Folder
async function scanFolder() {
  const folder = inputFolderPath.value.trim();
  const ppct_file = selectPpctFile.value;
  const naming_scheme = selectNamingScheme.value;

  if (!folder) {
    alert("Vui lòng nhập đường dẫn thư mục chứa giáo án!");
    return;
  }

  btnScan.disabled = true;
  btnScan.innerHTML = `<span class="spinner"></span> Đang quét...`;
  log(`Bắt đầu quét thư mục: "${folder}" với PPCT: "${ppct_file}"...`);

  try {
    const res = await fetch("/api/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        folder: folder,
        ppct_file: ppct_file,
        naming_scheme: naming_scheme
      })
    });

    const json = await res.json();
    if (json.success) {
      scannedFiles = json.files || [];
      selectedFileIndices = new Set(scannedFiles.map((_, idx) => idx));
      
      log(`Quét hoàn tất: Tìm thấy ${scannedFiles.length} file giáo án docx.`, "success");
      updateStats();
      renderFilesTable();
    } else {
      log(`Lỗi khi quét: ${json.error}`, "error");
      alert(json.error);
    }
  } catch (err) {
    log(`Lỗi kết nối khi quét thư mục: ${err.message}`, "error");
  } finally {
    btnScan.disabled = false;
    btnScan.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="23 4 23 10 17 10"></polyline>
        <polyline points="1 20 1 14 7 14"></polyline>
        <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
      </svg>
      Quét Thư Mục
    `;
  }
}

// 6. Render Files Table
function renderFilesTable() {
  const query = inputSearchFile.value.trim().toLowerCase();
  tableFilesBody.innerHTML = "";

  const filtered = scannedFiles.filter(f => {
    if (!query) return true;
    return f.filename.toLowerCase().includes(query) ||
           (f.lesson_info && f.lesson_info.bai_title && f.lesson_info.bai_title.toLowerCase().includes(query)) ||
           (f.target_filename && f.target_filename.toLowerCase().includes(query));
  });

  if (filtered.length === 0) {
    tableFilesBody.innerHTML = `
      <tr>
        <td colspan="7" class="text-center py-8 text-muted">
          ${scannedFiles.length === 0 ? 'Không tìm thấy file .docx nào trong thư mục này.' : 'Không có file nào khớp với tìm kiếm.'}
        </td>
      </tr>
    `;
    return;
  }

  filtered.forEach(file => {
    const origIdx = scannedFiles.indexOf(file);
    const isChecked = selectedFileIndices.has(origIdx);
    const info = file.lesson_info || {};
    const ppct = file.matched_ppct || {};

    const tr = document.createElement("tr");

    // Detected lesson text
    let lessonDetectedHtml = "";
    if (info.bai_num || info.bai_title) {
      lessonDetectedHtml = `
        <div class="font-bold">Bài ${info.bai_num || '?'}: ${escapeHtml(info.bai_title || '')}</div>
        <div class="text-muted text-sm">${escapeHtml(info.chude || '')} • Tiết: ${escapeHtml(info.tiet_str || 'Chưa rõ')}</div>
      `;
    } else {
      lessonDetectedHtml = `<span class="text-muted">Chưa nhận diện được</span>`;
    }

    // Matched PPCT text
    let ppctMatchHtml = "";
    const effectiveDate = file.teaching_date || ppct.ngay_day || "";
    const dateHtml = effectiveDate ? `<div class="text-xs font-mono" style="color: #0284c7; margin-top: 3px;">📅 Ngày dạy: <strong>${escapeHtml(effectiveDate)}</strong></div>` : "";
    let aiBadge = file.ai_fixed ? `<div style="margin-top: 4px;"><span class="badge-ai" title="${escapeHtml(file.ai_explanation || 'Đã chuẩn hoá bởi Beekone AI')}"><span class="ai-pulse-dot"></span> 🤖 AI Chuẩn Hoá</span></div>` : "";

    if (ppct.ten_bai) {
      ppctMatchHtml = `
        <div class="text-success font-bold">✓ Tuần ${ppct.tuan || '?'}, Tiết ${ppct.tiet || '?'}</div>
        <div class="text-muted text-sm">${escapeHtml(ppct.ten_bai)}</div>
        ${dateHtml}
        ${aiBadge}
      `;
    } else {
      ppctMatchHtml = `<span class="badge badge-warning">Tự sinh theo nội dung</span>${dateHtml}${aiBadge}`;
    }

    // Status badge
    let statusBadge = "";
    if (file.status === "done") {
      statusBadge = `<span class="badge badge-success">✓ Đã Hoàn Thành</span>`;
    } else if (file.status === "ready") {
      statusBadge = `<span class="badge badge-ready">Sẵn Sàng</span>`;
    } else {
      statusBadge = `<span class="badge badge-error">Lỗi</span>`;
    }

    tr.innerHTML = `
      <td>
        <label class="checkbox-container">
          <input type="checkbox" class="file-checkbox" data-idx="${origIdx}" ${isChecked ? 'checked' : ''}>
          <span class="checkmark"></span>
        </label>
      </td>
      <td>
        <div class="font-bold font-mono text-sm">${escapeHtml(file.filename)}</div>
      </td>
      <td>${lessonDetectedHtml}</td>
      <td>${ppctMatchHtml}</td>
      <td>
        <div class="text-primary font-mono text-sm font-bold">${escapeHtml(file.target_filename || '')}</div>
      </td>
      <td>${statusBadge}</td>
      <td class="text-right">
        <div style="display: inline-flex; gap: 5px;">
          <button class="btn btn-secondary btn-sm btn-ai-single" data-idx="${origIdx}" title="Dùng Beekone AI phân tích & sửa lại tên bài này">
            🤖 AI
          </button>
          <button class="btn btn-secondary btn-sm btn-preview" data-idx="${origIdx}" title="Xem trước so sánh">
            👁️ Xem
          </button>
          <button class="btn btn-secondary btn-sm btn-edit-item" data-idx="${origIdx}" title="Chỉnh sửa thông số cho file này">
            ✏️ Sửa
          </button>
          <button class="btn btn-primary btn-sm btn-process-one" data-idx="${origIdx}" title="Render file này">
            ⚡ Xuất
          </button>
        </div>
      </td>
    `;
    tableFilesBody.appendChild(tr);
  });

  // Attach row event listeners
  document.querySelectorAll(".file-checkbox").forEach(cb => {
    cb.addEventListener("change", (e) => {
      const idx = parseInt(e.target.dataset.idx, 10);
      if (e.target.checked) selectedFileIndices.add(idx);
      else selectedFileIndices.delete(idx);
      updateStats();
    });
  });

  document.querySelectorAll(".btn-ai-single").forEach(btn => {
    btn.addEventListener("click", () => {
      const idx = parseInt(btn.dataset.idx, 10);
      runBeekoneAiSingleFile(idx, btn);
    });
  });

  document.querySelectorAll(".btn-preview").forEach(btn => {
    btn.addEventListener("click", () => {
      const idx = parseInt(btn.dataset.idx, 10);
      openDiffModal(scannedFiles[idx]);
    });
  });

  document.querySelectorAll(".btn-edit-item").forEach(btn => {
    btn.addEventListener("click", () => {
      const idx = parseInt(btn.dataset.idx, 10);
      openEditModal(idx);
    });
  });

  document.querySelectorAll(".btn-process-one").forEach(btn => {
    btn.addEventListener("click", () => {
      const idx = parseInt(btn.dataset.idx, 10);
      processBatch([scannedFiles[idx]]);
    });
  });
}

// Quick Edit Modal Handlers
function openEditModal(idx) {
  currentEditingIndex = idx;
  const file = scannedFiles[idx];
  if (!file) return;

  const info = file.lesson_info || {};
  const ppct = file.matched_ppct || {};

  editOrigFilename.value = file.filename;
  editWeek.value = file.week || ppct.tuan || info.tuan || "1";
  editPeriods.value = file.periods || ppct.tiet || info.tiet_str || "1, 2";
  editLessonName.value = file.bai_name || ppct.ten_bai || info.bai_title || "";
  if (editTeachingDate) {
    editTeachingDate.value = file.teaching_date || ppct.ngay_day || "";
  }
  editTargetFilename.value = file.target_filename || "";

  modalEditFile.classList.remove("hidden");
}

function closeEditModal() {
  modalEditFile.classList.add("hidden");
  currentEditingIndex = -1;
}

function saveEditModal() {
  if (currentEditingIndex < 0 || currentEditingIndex >= scannedFiles.length) return;
  const file = scannedFiles[currentEditingIndex];

  file.week = editWeek.value.trim();
  file.periods = editPeriods.value.trim();
  file.bai_name = editLessonName.value.trim();
  if (editTeachingDate) {
    file.teaching_date = editTeachingDate.value.trim();
    if (file.matched_ppct) file.matched_ppct.ngay_day = file.teaching_date;
  }
  if (editTargetFilename.value.trim()) {
    file.target_filename = editTargetFilename.value.trim();
  }

  // Update matched_ppct display text
  if (!file.matched_ppct) file.matched_ppct = {};
  file.matched_ppct.tuan = file.week;
  file.matched_ppct.tiet = file.periods;
  file.matched_ppct.ten_bai = file.bai_name;

  closeEditModal();
  renderFilesTable();
  log(`Đã cập nhật thông số cho file: ${file.filename} (Tuần ${file.week}, Tiết ${file.periods})`, "info");
}

// 7. Update Stats Counters
function updateStats() {
  const total = scannedFiles.length;
  const matched = scannedFiles.filter(f => f.matched_ppct && f.matched_ppct.ten_bai).length;
  const selected = selectedFileIndices.size;
  const done = scannedFiles.filter(f => f.status === "done").length;

  statTotalFiles.textContent = total;
  statMatchedFiles.textContent = matched;
  statSelectedFiles.textContent = selected;
  statDoneFiles.textContent = done;

  tabCountFiles.textContent = total;
  selectedSummaryText.textContent = `Đang chọn: ${selected}/${total} file`;
  checkSelectAll.checked = selected === total && total > 0;
}

// 8. Batch Processing Execution
async function processBatch(filesToRun = null) {
  const items = filesToRun || Array.from(selectedFileIndices).map(idx => scannedFiles[idx]);
  if (!items || items.length === 0) {
    alert("Vui lòng chọn ít nhất một file để xử lý!");
    return;
  }

  btnBatchProcess.disabled = true;
  progressContainer.classList.remove("hidden");
  progressBarFill.style.width = "0%";
  progressLabel.textContent = `Đang chuẩn bị xử lý ${items.length} file...`;
  progressPercentage.textContent = "0%";

  log(`🚀 BẮT ĐẦU XỬ LÝ HÀNG LOẠT: ${items.length} file...`);

  const outputMode = selectOutputMode.value;
  const payload = {
    files: items,
    output_mode: outputMode,
    config: {
      ppct_file: selectPpctFile.value,
      naming_scheme: selectNamingScheme.value,
      template_style: selectTemplateStyle ? selectTemplateStyle.value : "mau_thcs",
      teacher_name: cfgTeacherName.value,
      school_name: cfgSchoolName.value,
      department: cfgDepartment.value,
      school_year: cfgSchoolYear.value,
      subject: cfgSubject.value,
      subject_type: cfgSubjectType ? cfgSubjectType.value : "auto",
      classes: cfgClasses.value,
      school_year_start_date: cfgStartDate ? cfgStartDate.value : "2026-09-07",
      teaching_date_format: cfgDateFormat ? cfgDateFormat.value : "d2_to_d6",
      auto_calc_teaching_date: cfgAutoDate ? cfgAutoDate.checked : true,
      teaching_date: cfgTeachingDate.value,
      duration: cfgDuration.value,
      title_prefix: cfgTitlePrefix ? cfgTitlePrefix.value : "TÊN BÀI DẠY: ",
      enable_header: cfgOptHeader ? cfgOptHeader.checked : true,
      enable_footer: cfgOptFooter ? cfgOptFooter.checked : true,
      enable_approval_block: cfgOptApproval ? cfgOptApproval.checked : true,
      signer_school: cfgSignerSchool ? cfgSignerSchool.value.trim() : "",
      signer_dept: cfgSignerDept ? cfgSignerDept.value.trim() : "",
      table_border: cfgOptBorder ? cfgOptBorder.checked : false,
      margin_top_cm: parseFloat(cfgMarginTop ? cfgMarginTop.value : 2.0) || 2.0,
      margin_bottom_cm: parseFloat(cfgMarginBottom ? cfgMarginBottom.value : 2.0) || 2.0,
      margin_left_cm: parseFloat(cfgMarginLeft ? cfgMarginLeft.value : 2.0) || 2.0,
      margin_right_cm: parseFloat(cfgMarginRight ? cfgMarginRight.value : 1.5) || 1.5,
      include_file_naming_note: cfgNamingNote ? cfgNamingNote.checked : true
    }
  };

  try {
    progressBarFill.style.width = "40%";
    progressLabel.textContent = `Đang chuẩn hoá văn bản theo Mau KHBD THCS.docx, căn lề, cập nhật bảng và đổi tên...`;
    progressPercentage.textContent = "40%";

    const res = await fetch("/api/process_batch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const json = await res.json();
    if (json.success) {
      progressBarFill.style.width = "100%";
      progressPercentage.textContent = "100%";
      progressLabel.textContent = `Hoàn tất! Thành công: ${json.success_count}/${json.total}`;

      log(`✅ Xử lý hoàn tất! Thành công: ${json.success_count} file, Thất bại: ${json.fail_count} file.`, "success");
      if (json.output_directory && json.output_directory !== "inplace") {
        log(`📁 Thư mục lưu kết quả: ${json.output_directory}`, "info");
      }

      // Mark status in scannedFiles
      json.results.forEach(r => {
        const found = scannedFiles.find(f => f.filename === r.original_file);
        if (found) {
          found.status = r.status === "success" ? "done" : "error";
          if (r.new_file) found.target_filename = r.new_file;
        }
      });

      updateStats();
      renderFilesTable();

      alert(`Đã hoàn tất xử lý hàng loạt ${json.success_count} file KHBD chuẩn theo mẫu Mau KHBD THCS.docx!`);
    } else {
      log(`Lỗi khi xử lý hàng loạt: ${json.error}`, "error");
      alert(json.error);
    }
  } catch (err) {
    log(`Lỗi kết nối khi xử lý: ${err.message}`, "error");
    alert(`Lỗi: ${err.message}`);
  } finally {
    btnBatchProcess.disabled = false;
  }
}

// 9. Diff Preview Modal
async function openDiffModal(file) {
  currentDiffFile = file;
  modalFileTitle.textContent = `${file.filename} ➔ ${file.target_filename}`;
  modalDiff.classList.remove("hidden");

  diffBeforeContent.innerHTML = `<div class="text-center py-8 text-muted">Đang phân tích và so sánh...</div>`;
  diffAfterContent.innerHTML = `<div class="text-center py-8 text-muted">Đang tạo bản xem trước...</div>`;

  try {
    const res = await fetch("/api/preview_diff", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        file_path: file.file_path,
        ppct_file: selectPpctFile.value,
        week: file.week,
        periods: file.periods,
        bai_name: file.bai_name,
        teaching_date: file.teaching_date || (file.matched_ppct ? file.matched_ppct.ngay_day : ""),
        config: {
          teacher_name: cfgTeacherName.value,
          school_name: cfgSchoolName.value,
          department: cfgDepartment.value,
          school_year: cfgSchoolYear.value,
          subject: cfgSubject.value,
          subject_type: cfgSubjectType ? cfgSubjectType.value : "auto",
          classes: cfgClasses.value,
          school_year_start_date: cfgStartDate ? cfgStartDate.value : "2026-09-07",
          teaching_date_format: cfgDateFormat ? cfgDateFormat.value : "d2_to_d6",
          auto_calc_teaching_date: cfgAutoDate ? cfgAutoDate.checked : true,
          teaching_date: cfgTeachingDate.value,
          duration: cfgDuration.value,
          title_prefix: cfgTitlePrefix ? cfgTitlePrefix.value : "TÊN BÀI DẠY: ",
          enable_header: cfgOptHeader ? cfgOptHeader.checked : true,
          enable_footer: cfgOptFooter ? cfgOptFooter.checked : true,
          enable_approval_block: cfgOptApproval ? cfgOptApproval.checked : true,
          signer_school: cfgSignerSchool ? cfgSignerSchool.value.trim() : "",
          signer_dept: cfgSignerDept ? cfgSignerDept.value.trim() : "",
          table_border: cfgOptBorder ? cfgOptBorder.checked : false
        }
      })
    });

    const json = await res.json();
    if (json.success) {
      renderDiff(json.before, json.after);
    } else {
      diffBeforeContent.innerHTML = `<div class="text-danger">Lỗi: ${json.error}</div>`;
      diffAfterContent.innerHTML = `<div class="text-danger">Lỗi: ${json.error}</div>`;
    }
  } catch (err) {
    diffBeforeContent.innerHTML = `<div class="text-danger">Lỗi kết nối: ${err.message}</div>`;
  }
}

function renderDiff(before, after) {
  // Before Content
  let beforeHtml = `<div class="font-bold text-sm text-muted mb-2">[Tên file: ${escapeHtml(before.filename)}]</div>`;
  
  if (before.has_old_table && before.old_table_rows.length > 0) {
    beforeHtml += `<div class="text-sm font-bold text-danger mb-1">[Bảng cũ cần thay thế]:</div>`;
    beforeHtml += `<table class="doc-table">`;
    before.old_table_rows.forEach(r => {
      beforeHtml += `<tr>${r.map(c => `<td>${escapeHtml(c)}</td>`).join('')}</tr>`;
    });
    beforeHtml += `</table>`;
  }

  beforeHtml += `<div class="text-sm font-bold text-muted mt-2">[Tiêu đề cũ]:</div>`;
  before.header_texts.forEach(t => {
    beforeHtml += `<div class="doc-p text-sm">${escapeHtml(t)}</div>`;
  });
  beforeHtml += `<div class="doc-footer-preview" style="font-size: 11px; font-style: italic; color: #64748b; margin-top: 8px;">[Chân trang]: ${escapeHtml(before.footer)}</div>`;
  diffBeforeContent.innerHTML = beforeHtml;

  // After Content (Mau KHBD THCS.docx Standard)
  let afterHtml = `<div class="font-bold text-sm text-success mb-2">[Tên file mới: ${escapeHtml(after.filename)}]</div>`;
  
  // Header line
  if (after.header_top) {
    afterHtml += `<div class="doc-header-preview" style="font-size: 11px; font-style: italic; color: #475569; margin-bottom: 12px; border-bottom: 1px dotted #cbd5e1; padding-bottom: 3px;">[Header]: ${escapeHtml(after.header_top)}</div>`;
  }

  // Table 1x2 at Top (Tuần, Tiết, Ngày dạy | Họ tên GV, Tổ CM)
  const tbl = after.table_top || after.table_block;
  if (tbl) {
    afterHtml += `
      <table class="doc-table" style="margin-bottom: 14px; width: 100%;">
        <tr>
          <td style="width: 55%; vertical-align: top;">
            ${(tbl.col_left || []).map(line => `<div class="doc-italic">${escapeHtml(line)}</div>`).join('')}
          </td>
          <td style="width: 45%; vertical-align: top;">
            ${(tbl.col_right || []).map(line => `<div class="doc-italic">${escapeHtml(line)}</div>`).join('')}
          </td>
        </tr>
      </table>
    `;
  }

  // Title Block (TÊN BÀI DẠY, môn học/lớp, thời gian thực hiện)
  if (after.title_block) {
    after.title_block.forEach(p => {
      let classes = ["doc-p"];
      if (p.bold) classes.push("doc-bold");
      if (p.italic) classes.push("doc-italic");
      if (p.align === "center") classes.push("doc-center");
      afterHtml += `<div class="${classes.join(' ')}" style="text-align: center; margin-bottom: 3px;">${escapeHtml(p.text)}</div>`;
    });
  }

  // Body indicator
  afterHtml += `<div class="doc-p text-muted text-sm" style="margin-top: 10px; padding-top: 8px; border-top: 1px dashed #cbd5e1;">[... Tiếp tục giữ nguyên toàn bộ các mục: I. Mục tiêu, II. Thiết bị, III. Tiến trình dạy học ...]</div>`;

  // Approval Block
  if (after.approval_block) {
    let sSchool = cfgSignerSchool ? cfgSignerSchool.value.trim() : "";
    let sDept = cfgSignerDept ? cfgSignerDept.value.trim() : "";
    if (typeof after.approval_block === "object" && after.approval_block.col_left) {
      sSchool = after.approval_block.col_left.signer_name || sSchool;
      sDept = after.approval_block.col_right.signer_name || sDept;
    }
    afterHtml += `
      <div style="display: flex; justify-content: space-between; font-size: 13px; margin: 18px 0 10px 0; padding: 0 12px;">
        <div style="text-align: center; width: 45%;">
          <div style="font-weight: bold;">Duyệt của Chuyên môn</div>
          <div style="font-style: italic; font-size: 11px; color: #64748b;">(Ký và ghi rõ họ tên)</div>
          <div style="height: 38px;"></div>
          <div style="font-weight: bold; color: #1e293b;">${escapeHtml(sSchool)}</div>
        </div>
        <div style="text-align: center; width: 45%;">
          <div style="font-weight: bold;">Duyệt của tổ chuyên môn</div>
          <div style="font-style: italic; font-size: 11px; color: #64748b;">(Ký và ghi rõ họ tên)</div>
          <div style="height: 38px;"></div>
          <div style="font-weight: bold; color: #1e293b;">${escapeHtml(sDept)}</div>
        </div>
      </div>
    `;
  }

  // Footer
  if (after.footer) {
    afterHtml += `<div class="doc-footer-preview" style="font-size: 11px; font-style: italic; color: #475569; text-align: right; border-top: 1px dotted #cbd5e1; padding-top: 4px; margin-top: 12px;">[Footer]: ${escapeHtml(after.footer)}</div>`;
  }
  
  if (after.margins) {
    afterHtml += `<div class="text-xs text-muted mt-2" style="font-size: 11px; color: #94a3b8;">${escapeHtml(after.margins)}</div>`;
  }

  diffAfterContent.innerHTML = afterHtml;
}

// 10. Open in Windows Explorer
async function openFolderInExplorer() {
  const folder = inputFolderPath.value.trim();
  try {
    const res = await fetch("/api/open_folder", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: folder })
    });
    const json = await res.json();
    if (json.success) {
      log(`Đã mở thư mục trong Windows Explorer: ${json.path}`, "info");
    }
  } catch (err) {
    log(`Lỗi khi mở Explorer: ${err.message}`, "error");
  }
}

// 11. Save Config
async function saveConfigForm() {
  const payload = {
    default_scan_path: inputFolderPath.value.trim(),
    teacher_name: cfgTeacherName.value.trim(),
    school_name: cfgSchoolName.value.trim(),
    department: cfgDepartment.value.trim(),
    school_year: cfgSchoolYear.value.trim(),
    subject: cfgSubject.value.trim(),
    subject_type: cfgSubjectType ? cfgSubjectType.value : "auto",
    classes: cfgClasses.value.trim(),
    school_year_start_date: cfgStartDate ? cfgStartDate.value : "2026-09-07",
    teaching_date_format: cfgDateFormat ? cfgDateFormat.value : "d2_to_d6",
    auto_calc_teaching_date: cfgAutoDate ? cfgAutoDate.checked : true,
    teaching_date: cfgTeachingDate.value.trim(),
    duration: cfgDuration.value.trim(),
    title_prefix: cfgTitlePrefix ? cfgTitlePrefix.value : "TÊN BÀI DẠY: ",
    enable_header: cfgOptHeader ? cfgOptHeader.checked : true,
    enable_footer: cfgOptFooter ? cfgOptFooter.checked : true,
    enable_approval_block: cfgOptApproval ? cfgOptApproval.checked : true,
    signer_school: cfgSignerSchool ? cfgSignerSchool.value.trim() : "",
    signer_dept: cfgSignerDept ? cfgSignerDept.value.trim() : "",
    signers_list: signersList,
    table_border: cfgOptBorder ? cfgOptBorder.checked : false,
    template_style: selectTemplateStyle ? selectTemplateStyle.value : "mau_thcs",
    margin_top_cm: parseFloat(cfgMarginTop.value) || 2.0,
    margin_bottom_cm: parseFloat(cfgMarginBottom.value) || 2.0,
    margin_left_cm: parseFloat(cfgMarginLeft.value) || 2.0,
    margin_right_cm: parseFloat(cfgMarginRight.value) || 1.5,
    include_file_naming_note: cfgNamingNote.checked,
    ppct_file: selectPpctFile.value,
    naming_scheme: selectNamingScheme.value,
    output_mode: selectOutputMode.value
  };

  try {
    const res = await fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const json = await res.json();
    if (json.success) {
      currentConfig = json.config;
      saveConfigStatus.classList.remove("hidden");
      setTimeout(() => saveConfigStatus.classList.add("hidden"), 3000);
      log("Đã lưu cấu hình mẫu Mau KHBD THCS.docx thành công!", "success");
    }
  } catch (err) {
    alert(`Lỗi lưu cấu hình: ${err.message}`);
  }
}

// 12. Save AI Config (Beekone AI)
async function saveAiConfig() {
  const payload = {
    ai_config: {
      enabled: Boolean(cfgAiKey.value.trim()),
      base_url: cfgAiEndpoint ? cfgAiEndpoint.value.trim() : "https://platform.beeknoee.com/api/v1",
      api_key: cfgAiKey.value.trim(),
      model: cfgAiModel.value,
      auto_format_title: aiOptAutoTitle ? aiOptAutoTitle.checked : true,
      add_nls: document.getElementById("ai-opt-nls").checked,
      format_5512: document.getElementById("ai-opt-5512").checked
    }
  };

  try {
    const res = await fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const json = await res.json();
    if (json.success) {
      aiStatusMsg.classList.remove("hidden");
      setTimeout(() => aiStatusMsg.classList.add("hidden"), 3000);
      log("Đã cập nhật thiết lập Beekone AI thành công!", "success");
    }
  } catch (err) {
    alert(`Lỗi lưu Beekone AI: ${err.message}`);
  }
}

// 13. Test Beekone AI Connection
async function testBeekoneAiConnection() {
  const apiKey = cfgAiKey ? cfgAiKey.value.trim() : "";
  const model = cfgAiModel ? cfgAiModel.value : "gemini-2.5-flash-lite";
  const baseUrl = cfgAiEndpoint ? cfgAiEndpoint.value.trim() : "https://platform.beeknoee.com/api/v1";

  if (!apiKey) {
    alert("Vui lòng nhập Beekone API Key trước khi kiểm tra!");
    return;
  }

  btnTestAi.disabled = true;
  btnTestAi.innerHTML = `<span class="spinner"></span> Đang kiểm tra kết nối...`;
  if (aiTestResult) aiTestResult.classList.add("hidden");

  log(`[BEEKONE AI] Đang kiểm tra kết nối tới ${baseUrl} (${model})...`);

  try {
    const res = await fetch("/api/ai/test_connection", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        api_key: apiKey,
        model: model,
        base_url: baseUrl
      })
    });
    const json = await res.json();
    if (json.success) {
      log(`✅ [BEEKONE AI] Kết nối thành công! Độ trễ: ${json.latency_ms}ms, Mô hình: ${json.model}`, "success");
      if (aiTestResult) {
        aiTestResult.className = "status-box status-success";
        aiTestResult.style.background = "rgba(16, 185, 129, 0.15)";
        aiTestResult.style.border = "1px solid #10b981";
        aiTestResult.style.color = "#10b981";
        aiTestResult.innerHTML = `<strong>🟢 Kết Nối Tốt!</strong> Phản hồi từ Beekone AI sau <strong>${json.latency_ms}ms</strong> (Model: ${json.model})`;
        aiTestResult.classList.remove("hidden");
      }
    } else {
      log(`❌ [BEEKONE AI] Lỗi kết nối: ${json.error}`, "error");
      if (aiTestResult) {
        aiTestResult.className = "status-box status-danger";
        aiTestResult.style.background = "rgba(239, 68, 68, 0.15)";
        aiTestResult.style.border = "1px solid #ef4444";
        aiTestResult.style.color = "#f87171";
        aiTestResult.innerHTML = `<strong>🔴 Lỗi Kết Nối:</strong> ${escapeHtml(json.error)}`;
        aiTestResult.classList.remove("hidden");
      }
    }
  } catch (err) {
    log(`❌ [BEEKONE AI] Lỗi mạng: ${err.message}`, "error");
    if (aiTestResult) {
      aiTestResult.className = "status-box status-danger";
      aiTestResult.style.background = "rgba(239, 68, 68, 0.15)";
      aiTestResult.style.border = "1px solid #ef4444";
      aiTestResult.style.color = "#f87171";
      aiTestResult.innerHTML = `<strong>🔴 Lỗi Mạng:</strong> ${escapeHtml(err.message)}`;
      aiTestResult.classList.remove("hidden");
    }
  } finally {
    btnTestAi.disabled = false;
    btnTestAi.innerHTML = `<span>⚡ Kiểm Tra Kết Nối Beekone API</span>`;
  }
}

// 14. Run Beekone AI for Single File (1-Click Fix)
async function runBeekoneAiSingleFile(idx, btnElement = null) {
  const file = scannedFiles[idx];
  if (!file) return;

  const origBtnText = btnElement ? btnElement.innerHTML : "";
  if (btnElement) {
    btnElement.disabled = true;
    btnElement.innerHTML = `<span class="spinner"></span> AI...`;
  }

  const model = cfgAiModel ? cfgAiModel.value : "gemini-2.5-flash-lite";
  log(`🤖 [BEEKONE AI] Đang gửi "${file.filename}" đến Beekone AI (${model}) để đọc và chuẩn hoá tên bài...`);

  try {
    const res = await fetch("/api/ai/analyze_title", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        file_path: file.file_path,
        ppct_file: selectPpctFile.value,
        api_key: cfgAiKey ? cfgAiKey.value.trim() : "",
        model: model
      })
    });

    const json = await res.json();
    if (json.success && json.result) {
      const r = json.result;
      if (!file.lesson_info) file.lesson_info = {};
      file.lesson_info.bai_num = r.bai_num;
      file.lesson_info.bai_title = r.bai_title;
      file.lesson_info.chude = r.chude;
      file.lesson_info.tiet_str = r.tiet;
      file.week = r.tuan;
      file.periods = r.tiet;
      file.bai_name = r.bai_title;
      file.teaching_date = r.teaching_date;
      file.matched_ppct = r.matched_ppct;
      file.target_filename = r.target_filename;
      file.ai_fixed = true;
      file.ai_explanation = r.explanation;

      renderFilesTable();
      updateStats();

      log(`✅ [BEEKONE AI] Thành công cho "${file.filename}": Bài ${r.bai_num}. "${r.bai_title}" (Tuần ${r.tuan}, Tiết ${r.tiet}) ➔ File mới: ${r.target_filename}`, "success");
    } else {
      log(`❌ [BEEKONE AI] Không thể phân tích "${file.filename}": ${json.error}`, "error");
      alert(`Lỗi AI: ${json.error}`);
    }
  } catch (err) {
    log(`❌ [BEEKONE AI Lỗi]: ${err.message}`, "error");
    alert(`Lỗi kết nối AI: ${err.message}`);
  } finally {
    if (btnElement) {
      btnElement.disabled = false;
      btnElement.innerHTML = origBtnText;
    }
  }
}

// 15. Run Beekone AI for Batch Files (Toolbar Button)
async function runBeekoneAiBatch() {
  const items = Array.from(selectedFileIndices).map(idx => scannedFiles[idx]);
  const targetFiles = items.length > 0 ? items : scannedFiles;

  if (!targetFiles || targetFiles.length === 0) {
    alert("Vui lòng quét thư mục trước khi chạy Beekone AI!");
    return;
  }

  const model = cfgAiModel ? cfgAiModel.value : "gemini-2.5-flash-lite";
  const confirmMsg = `Bạn có muốn sử dụng Beekone AI (${model}) để đọc và chuẩn hoá tự động tên bài, số bài, tuần, tiết theo PPCT cho ${targetFiles.length} file giáo án?`;
  if (!confirm(confirmMsg)) return;

  btnBatchAiFix.disabled = true;
  const origBtnText = btnBatchAiFix.innerHTML;
  btnBatchAiFix.innerHTML = `<span class="spinner"></span> Đang phân tích AI...`;

  progressContainer.classList.remove("hidden");
  progressBarFill.style.width = "0%";
  progressLabel.textContent = `Beekone AI đang khởi động phân tích ${targetFiles.length} file...`;
  progressPercentage.textContent = "0%";

  log(`🚀 [BEEKONE AI BATCH] Bắt đầu phân tích & chuẩn hoá tên bài cho ${targetFiles.length} file...`);

  let successCount = 0;
  let failCount = 0;

  for (let i = 0; i < targetFiles.length; i++) {
    const file = targetFiles[i];
    const pct = Math.round(((i + 1) / targetFiles.length) * 100);
    progressLabel.textContent = `[Beekone AI] Đang phân tích file (${i + 1}/${targetFiles.length}): ${file.filename}...`;
    progressBarFill.style.width = `${pct}%`;
    progressPercentage.textContent = `${pct}%`;

    try {
      const res = await fetch("/api/ai/analyze_title", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_path: file.file_path,
          ppct_file: selectPpctFile.value,
          api_key: cfgAiKey ? cfgAiKey.value.trim() : "",
          model: model
        })
      });

      const json = await res.json();
      if (json.success && json.result) {
        const r = json.result;
        if (!file.lesson_info) file.lesson_info = {};
        file.lesson_info.bai_num = r.bai_num;
        file.lesson_info.bai_title = r.bai_title;
        file.lesson_info.chude = r.chude;
        file.lesson_info.tiet_str = r.tiet;
        file.week = r.tuan;
        file.periods = r.tiet;
        file.bai_name = r.bai_title;
        file.teaching_date = r.teaching_date;
        file.matched_ppct = r.matched_ppct;
        file.target_filename = r.target_filename;
        file.ai_fixed = true;
        file.ai_explanation = r.explanation;
        successCount++;
        log(`✓ [${i + 1}/${targetFiles.length}] Bài ${r.bai_num}: "${r.bai_title}" (Tuần ${r.tuan}, Tiết ${r.tiet})`, "info");
      } else {
        failCount++;
        log(`⚠️ [${i + 1}/${targetFiles.length}] Bỏ qua "${file.filename}": ${json.error}`, "warning");
      }
    } catch (err) {
      failCount++;
      log(`❌ [${i + 1}/${targetFiles.length}] Lỗi file "${file.filename}": ${err.message}`, "error");
    }
  }

  progressBarFill.style.width = "100%";
  progressPercentage.textContent = "100%";
  progressLabel.textContent = `Hoàn tất phân tích AI! Thành công: ${successCount}/${targetFiles.length}`;

  renderFilesTable();
  updateStats();

  btnBatchAiFix.disabled = false;
  btnBatchAiFix.innerHTML = origBtnText;

  log(`🎉 [BEEKONE AI BATCH HOÀN TẤT] Đã chuẩn hoá thành công ${successCount} file giáo án!`, "success");
  alert(`Beekone AI đã chuẩn hoá thành công ${successCount} file giáo án!\nCác file đã được cập nhật Tên bài SGK chuẩn, Tuần, Tiết và Tên file mới tương ứng.`);
}

// 16. Run Beekone AI Quick Edit inside Edit Modal
async function runBeekoneAiQuickEdit() {
  if (currentEditingIndex < 0 || currentEditingIndex >= scannedFiles.length) return;
  const file = scannedFiles[currentEditingIndex];

  btnQuickAiFix.disabled = true;
  btnQuickAiFix.innerHTML = `<span class="spinner"></span> Đang phân tích...`;
  if (quickAiStatus) {
    quickAiStatus.textContent = "Beekone AI đang đọc nội dung giáo án...";
    quickAiStatus.classList.remove("hidden");
  }

  const model = cfgAiModel ? cfgAiModel.value : "gemini-2.5-flash-lite";

  try {
    const res = await fetch("/api/ai/analyze_title", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        file_path: file.file_path,
        ppct_file: selectPpctFile.value,
        api_key: cfgAiKey ? cfgAiKey.value.trim() : "",
        model: model
      })
    });

    const json = await res.json();
    if (json.success && json.result) {
      const r = json.result;
      editLessonName.value = r.bai_title;
      editWeek.value = r.tuan;
      editPeriods.value = r.tiet;
      if (r.teaching_date && editTeachingDate) {
        editTeachingDate.value = r.teaching_date;
      }
      editTargetFilename.value = r.target_filename;

      if (quickAiStatus) {
        quickAiStatus.style.color = "#10b981";
        quickAiStatus.textContent = `✨ AI nhận diện: Bài ${r.bai_num} (${r.explanation || 'Khớp chuẩn PPCT'})`;
      }
      log(`✨ [Beekone AI Quick Edit] Đã điền chuẩn bài: "${r.bai_title}" cho modal sửa.`, "success");
    } else {
      if (quickAiStatus) {
        quickAiStatus.style.color = "#ef4444";
        quickAiStatus.textContent = `Lỗi: ${json.error}`;
      }
    }
  } catch (err) {
    if (quickAiStatus) {
      quickAiStatus.style.color = "#ef4444";
      quickAiStatus.textContent = `Lỗi: ${err.message}`;
    }
  } finally {
    btnQuickAiFix.disabled = false;
    btnQuickAiFix.innerHTML = `<span>🤖 Beekone AI Tự Điền</span>`;
  }
}

// Event Listeners Setup
function setupEventListeners() {
  // Buttons
  btnScan.addEventListener("click", scanFolder);
  btnOpenExplorer.addEventListener("click", openFolderInExplorer);
  btnBatchProcess.addEventListener("click", () => processBatch());
  btnClearLog.addEventListener("click", () => { terminalBody.innerHTML = ""; });

  // Beekone AI Buttons
  if (btnBatchAiFix) btnBatchAiFix.addEventListener("click", runBeekoneAiBatch);
  if (btnQuickAiFix) btnQuickAiFix.addEventListener("click", runBeekoneAiQuickEdit);
  if (btnTestAi) btnTestAi.addEventListener("click", testBeekoneAiConnection);
  if (btnToggleKeyVis && cfgAiKey) {
    btnToggleKeyVis.addEventListener("click", () => {
      cfgAiKey.type = cfgAiKey.type === "password" ? "text" : "password";
    });
  }

  // Dropdown changes
  selectPpctFile.addEventListener("change", (e) => {
    loadPpctTableData(e.target.value);
    scanFolder();
  });

  selectNamingScheme.addEventListener("change", () => {
    scanFolder();
  });

  // Live Visual A4 Sheet Synchronization Listeners
  const visualInputs = [
    cfgTeacherName, cfgSchoolName, cfgDepartment, cfgSchoolYear,
    cfgSubject, cfgSubjectType, cfgClasses, cfgTeachingDate, cfgDuration, cfgTitlePrefix,
    cfgSignerSchool, cfgSignerDept
  ];
  visualInputs.forEach(inp => {
    if (inp) {
      inp.addEventListener("input", updateLivePreview);
      inp.addEventListener("change", updateLivePreview);
    }
  });

  const visualCheckboxes = [cfgOptHeader, cfgOptFooter, cfgOptApproval, cfgOptBorder, cfgAutoDate];
  visualCheckboxes.forEach(cb => {
    if (cb) cb.addEventListener("change", updateLivePreview);
  });

  if (cfgStartDate) {
    cfgStartDate.addEventListener("change", () => {
      updateLivePreview();
      if (selectPpctFile && selectPpctFile.value) {
        loadPpctTableData(selectPpctFile.value);
      }
    });
  }

  if (cfgDateFormat) {
    cfgDateFormat.addEventListener("change", () => {
      updateLivePreview();
      if (selectPpctFile && selectPpctFile.value) {
        loadPpctTableData(selectPpctFile.value);
      }
    });
  }

  if (btnAddSigner) {
    btnAddSigner.addEventListener("click", () => {
      const newName = prompt("Nhập họ và tên người ký mới cần thêm vào danh sách kéo thả:");
      if (newName && newName.trim()) {
        const trimmed = newName.trim();
        if (!signersList.includes(trimmed)) {
          signersList.push(trimmed);
          renderSignersBadges();
          log(`Đã thêm nhân sự vào danh sách: "${trimmed}"`, "info");
        }
      }
    });
  }

  if (selectTemplateStyle) {
    selectTemplateStyle.addEventListener("change", updateLivePreview);
  }

  // Quick Edit Modal buttons
  if (btnCloseEditModal) btnCloseEditModal.addEventListener("click", closeEditModal);
  if (btnCancelEdit) btnCancelEdit.addEventListener("click", closeEditModal);
  if (btnSaveEdit) btnSaveEdit.addEventListener("click", saveEditModal);

  // Sync PPCT Dates to Excel button
  if (btnSyncPpctDates) {
    btnSyncPpctDates.addEventListener("click", async () => {
      const startDate = cfgStartDate ? cfgStartDate.value : "2026-09-07";
      const dateFormat = cfgDateFormat ? cfgDateFormat.value : "d2_to_d6";
      const currentFile = selectPpctFile ? selectPpctFile.value : "";

      const formatLabel = dateFormat === "d2_to_d6" ? "Thứ 2 - Thứ 6 (07/09/2026 - 11/09/2026)" :
                         dateFormat === "tu_den" ? "Từ 07/09 đến 11/09/2026" : "Chỉ ngày Thứ 2";

      const confirmMsg = `Bạn có muốn tính toán và ghi đè cột "Ngày dạy theo tuần" vào tất cả các file Excel PPCT?\n\n• Ngày bắt đầu Tuần 1: ${startDate}\n• Định dạng: ${formatLabel}\n\nDữ liệu sẽ được ghi trực tiếp vào các file Excel trong thư mục PPCT và tự động áp dụng vào KHBD.`;
      if (!confirm(confirmMsg)) return;

      btnSyncPpctDates.disabled = true;
      btnSyncPpctDates.innerHTML = `<span class="spinner"></span> Đang ghi Excel...`;

      try {
        const res = await fetch("/api/ppct/update_dates", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            school_year_start_date: startDate,
            teaching_date_format: dateFormat
          })
        });
        const json = await res.json();
        if (json.success) {
          log(`✅ ${json.message}`, "success");
          alert(json.message);
          if (currentFile) {
            await loadPpctTableData(currentFile);
          }
        } else {
          log(`❌ Lỗi cập nhật ngày PPCT: ${json.error}`, "error");
          alert(`Lỗi: ${json.error}`);
        }
      } catch (err) {
        log(`❌ Lỗi kết nối: ${err.message}`, "error");
        alert(`Lỗi: ${err.message}`);
      } finally {
        btnSyncPpctDates.disabled = false;
        btnSyncPpctDates.innerHTML = `📅 Ghi Ngày Vào Excel PPCT`;
      }
    });
  }

  // Select all checkbox
  checkSelectAll.addEventListener("change", (e) => {
    if (e.target.checked) {
      selectedFileIndices = new Set(scannedFiles.map((_, idx) => idx));
    } else {
      selectedFileIndices.clear();
    }
    renderFilesTable();
    updateStats();
  });

  // Search input
  inputSearchFile.addEventListener("input", renderFilesTable);

  // PPCT Search
  inputSearchPpct.addEventListener("input", (e) => {
    const q = e.target.value.toLowerCase();
    document.querySelectorAll("#table-ppct-body tr").forEach(row => {
      const text = row.textContent.toLowerCase();
      row.style.display = text.includes(q) ? "" : "none";
    });
  });

  // Tab switching
  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.dataset.tab;
      tabBtns.forEach(b => b.classList.remove("active"));
      tabPanels.forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(targetId).classList.add("active");
    });
  });

  // Theme toggle
  btnThemeToggle.addEventListener("click", toggleTheme);

  // Modals
  btnCloseModal.addEventListener("click", () => modalDiff.classList.add("hidden"));
  btnModalCancel.addEventListener("click", () => modalDiff.classList.add("hidden"));
  btnModalProcessSingle.addEventListener("click", () => {
    if (currentDiffFile) {
      modalDiff.classList.add("hidden");
      processBatch([currentDiffFile]);
    }
  });

  btnHelpModal.addEventListener("click", () => modalHelp.classList.remove("hidden"));
  btnCloseHelp.addEventListener("click", () => modalHelp.classList.add("hidden"));
  btnHelpOk.addEventListener("click", () => modalHelp.classList.add("hidden"));

  // Forms
  btnSaveConfig.addEventListener("click", saveConfigForm);
  btnSaveAi.addEventListener("click", saveAiConfig);
}

// Theme Handlers
function toggleTheme() {
  const isLight = document.body.classList.toggle("light-theme");
  localStorage.setItem("khbd_theme", isLight ? "light" : "dark");
}

function loadTheme() {
  const saved = localStorage.getItem("khbd_theme");
  if (saved === "light") {
    document.body.classList.add("light-theme");
  } else {
    document.body.classList.remove("light-theme");
  }
}

// Utility
function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
}

// Start application
window.addEventListener("DOMContentLoaded", init);
