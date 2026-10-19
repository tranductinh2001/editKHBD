// KHBD Pro - Frontend Application Logic

let currentConfig = {};
let scannedFiles = [];
let selectedFileIndices = new Set();
let ppctFilesList = [];
let activePpctItems = [];
let currentDiffFile = null;

// Helpers: Vietnamese Accent Removal & Slug
function removeVietnameseAccents(str) {
  if (!str) return "";
  return str.normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .replace(/đ/g, "d")
            .replace(/Đ/g, "D");
}

function toSlug(text) {
  if (!text) return "";
  let s = removeVietnameseAccents(text);
  if (s === s.toUpperCase()) {
    s = s.toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
  }
  return s.replace(/[^a-zA-Z0-9\s_-]/g, '').trim().replace(/[\s_]+/g, '-').replace(/^-+|-+$/g, '');
}

// DOM Elements
const inputFolderPath = document.getElementById("input-folder-path");
const selectPpctFile = document.getElementById("select-ppct-file");
const selectNamingScheme = document.getElementById("select-naming-scheme");
const selectOutputMode = document.getElementById("select-output-mode");
const btnScan = document.getElementById("btn-scan");
const btnOpenExplorer = document.getElementById("btn-open-explorer");
const btnBatchProcess = document.getElementById("btn-batch-process");
const btnFastRename = document.getElementById("btn-fast-rename");
const btnClearLog = document.getElementById("btn-clear-log");
const btnThemeToggle = document.getElementById("btn-theme-toggle");
const btnHelpModal = document.getElementById("btn-help-modal");
const btnCloseHelp = document.getElementById("btn-close-help");
const btnHelpOk = document.getElementById("btn-help-ok");

// Step 1: Grade & Subject & SMAS Quick Sync
const selectMainGrade = document.getElementById("select-main-grade");
const selectMainSubject = document.getElementById("select-main-subject");
const btnQuickSyncSmas = document.getElementById("btn-quick-sync-smas");
const smasQuickStatus = document.getElementById("smas-quick-status");
const linkViewPpctQuick = document.getElementById("link-view-ppct-quick");
const linkMoreConfig = document.getElementById("link-more-config");

// Step 2: Naming rule & Pattern & Chips & Preview
const inputCustomPattern = document.getElementById("input-custom-pattern");
const wrapCustomPattern = document.getElementById("wrap-custom-pattern");
const namingPreviewSample = document.getElementById("naming-preview-sample");
const namingChips = document.querySelectorAll(".naming-chip");
const activePpctBadgeText = document.getElementById("active-ppct-badge-text");

// Step 3: Quick Toggles & Signers
const cfgOptFormat5512Quick = document.getElementById("cfg-opt-format-5512-quick");
const cfgOptSmasDateQuick = document.getElementById("cfg-opt-smas-date-quick");
const cfgQuickSignerDept = document.getElementById("cfg-quick-signer-dept");
const cfgQuickTeacher = document.getElementById("cfg-quick-teacher");

// Modal Quick Edit PPCT Select
const editPpctSelect = document.getElementById("edit-ppct-select");

// NLS Elements
const btnBatchNlsMaster = document.getElementById("btn-batch-nls-master");
const btnToolbarNls = document.getElementById("btn-toolbar-nls");
const btnOpenNlsFolder = document.getElementById("btn-open-nls-folder");
const optAutoNls = document.getElementById("opt-auto-nls");
const optNlsRed = document.getElementById("opt-nls-red");
const optNlsOnlyAudit = document.getElementById("opt-nls-only-audit");

// NLS Modal Elements
const modalNlsDetail = document.getElementById("modal-nls-detail");
const btnCloseNlsModal = document.getElementById("btn-close-nls-modal");
const btnCloseNlsOk = document.getElementById("btn-close-nls-ok");
const btnNlsApplySingle = document.getElementById("btn-nls-apply-single");
const nlsModalBadge = document.getElementById("nls-modal-badge");
const nlsModalFilename = document.getElementById("nls-modal-filename");
const nlsModalLoading = document.getElementById("nls-modal-loading");
const nlsModalContent = document.getElementById("nls-modal-content");
let currentNlsFileIndex = -1;

// KHGD Elements
const optSyncKhgd = document.getElementById("opt-sync-khgd");
const khgdSourceBadge = document.getElementById("khgd-source-badge");
const selectKhgdGrade = document.getElementById("select-khgd-grade");
const inputKhgdFile = document.getElementById("input-khgd-file");
const btnUploadKhgd = document.getElementById("btn-upload-khgd");
const btnParseKhgd = document.getElementById("btn-parse-khgd");
const tableKhgdBody = document.getElementById("table-khgd-body");
let currentKhgdData = null;

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
const cfgOptAutofitTable = document.getElementById("cfg-opt-autofit-table");
const cfgOptAutofitTableQuick = document.getElementById("cfg-opt-autofit-table-quick");
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
const cfgTitleSignerSchool = document.getElementById("cfg-title-signer-school");
const cfgSignerSchool = document.getElementById("cfg-signer-school");
const cfgTitleSignerDept = document.getElementById("cfg-title-signer-dept");
const cfgSignerDept = document.getElementById("cfg-signer-dept");
const cfgOptFormat5512 = document.getElementById("cfg-opt-format-5512");
const signersBadgesPool = document.getElementById("signers-badges-pool");
const btnAddSigner = document.getElementById("btn-add-signer");
const dropzoneSchool = document.getElementById("dropzone-school");
const dropzoneDept = document.getElementById("dropzone-dept");
let signersList = [
  "Trần Đức Tình"
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
const pvTitleSignerSchool = document.getElementById("pv-title-signer-school");
const pvSignerSchool = document.getElementById("pv-signer-school");
const pvTitleSignerDept = document.getElementById("pv-title-signer-dept");
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
  loadKhgdStatus();
  initSmasTab();
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
  if (cfg.autofit_tables !== undefined) {
    if (cfgOptAutofitTable) cfgOptAutofitTable.checked = cfg.autofit_tables;
    if (cfgOptAutofitTableQuick) cfgOptAutofitTableQuick.checked = cfg.autofit_tables;
  }
  if (cfg.template_style && selectTemplateStyle) selectTemplateStyle.value = cfg.template_style;

  if (cfg.school_year_start_date && cfgStartDate) cfgStartDate.value = cfg.school_year_start_date;
  if (cfg.teaching_date_format && cfgDateFormat) cfgDateFormat.value = cfg.teaching_date_format;
  if (cfg.auto_calc_teaching_date !== undefined && cfgAutoDate) cfgAutoDate.checked = cfg.auto_calc_teaching_date;
  if (cfg.title_signer_school !== undefined && cfgTitleSignerSchool) cfgTitleSignerSchool.value = cfg.title_signer_school;
  if (cfg.signer_school !== undefined && cfgSignerSchool) cfgSignerSchool.value = cfg.signer_school;
  if (cfg.title_signer_dept !== undefined && cfgTitleSignerDept) cfgTitleSignerDept.value = cfg.title_signer_dept;
  if (cfg.signer_dept !== undefined && cfgSignerDept) cfgSignerDept.value = cfg.signer_dept;
  if (cfg.format_5512 !== undefined && cfgOptFormat5512) cfgOptFormat5512.checked = cfg.format_5512;
  if (cfg.signers_list && Array.isArray(cfg.signers_list)) signersList = cfg.signers_list;

  if (cfg.margin_top_cm && cfgMarginTop) cfgMarginTop.value = cfg.margin_top_cm;
  if (cfg.margin_bottom_cm && cfgMarginBottom) cfgMarginBottom.value = cfg.margin_bottom_cm;
  if (cfg.margin_left_cm && cfgMarginLeft) cfgMarginLeft.value = cfg.margin_left_cm;
  if (cfg.margin_right_cm && cfgMarginRight) cfgMarginRight.value = cfg.margin_right_cm;
  if (cfg.include_file_naming_note !== undefined && cfgNamingNote) cfgNamingNote.checked = cfg.include_file_naming_note;
  if (cfg.naming_scheme && selectNamingScheme) selectNamingScheme.value = cfg.naming_scheme;
  if (cfg.custom_pattern && inputCustomPattern) {
    inputCustomPattern.value = cfg.custom_pattern;
  } else if (selectNamingScheme && selectNamingScheme.value === "vietnamese_standard") {
    inputCustomPattern.value = "Tuần {tuan} - Tiết {tiet} - Bài {bai_num} - {ten_bai}.docx";
  }
  if (wrapCustomPattern && selectNamingScheme) {
    wrapCustomPattern.classList.toggle("hidden", selectNamingScheme.value !== "custom");
  }
  if (cfg.classes && selectMainGrade) selectMainGrade.value = cfg.classes;
  if (cfg.subject && selectMainSubject) selectMainSubject.value = cfg.subject;
  if (cfg.signer_dept && cfgQuickSignerDept) cfgQuickSignerDept.value = cfg.signer_dept;
  if (cfg.teacher_name && cfgQuickTeacher) cfgQuickTeacher.value = cfg.teacher_name;
  if (cfg.format_5512 !== undefined && cfgOptFormat5512Quick) cfgOptFormat5512Quick.checked = cfg.format_5512;
  if (cfg.output_mode && selectOutputMode) selectOutputMode.value = cfg.output_mode;
  if (cfg.ai_config) {
    if (cfg.ai_config.base_url && cfgAiEndpoint) cfgAiEndpoint.value = cfg.ai_config.base_url;
    if (cfg.ai_config.api_key && cfgAiKey) cfgAiKey.value = cfg.ai_config.api_key;
    if (cfg.ai_config.model && cfgAiModel) {
      let m = cfg.ai_config.model;
      if (m === "gemini-2.5-flash-lite" || m === "google/gemini-2.5-flash-lite" || m === "google/gemini-3.1-flash-lite") {
        m = "gemini-3.1-flash-lite";
      }
      cfgAiModel.value = m;
    }
    if (cfg.ai_config.auto_format_title !== undefined && aiOptAutoTitle) aiOptAutoTitle.checked = cfg.ai_config.auto_format_title;
    if (cfg.ai_config.add_nls !== undefined && document.getElementById("ai-opt-nls")) document.getElementById("ai-opt-nls").checked = cfg.ai_config.add_nls;
    if (cfg.ai_config.format_5512 !== undefined && document.getElementById("ai-opt-5512")) document.getElementById("ai-opt-5512").checked = cfg.ai_config.format_5512;
  }

  renderSignersBadges();
  updateLivePreview();
  updateLiveNamingPreview();
}

// Compute Target Filename Matching Engine Logic
function computeTargetFilename(file, scheme, pattern) {
  scheme = scheme || (selectNamingScheme ? selectNamingScheme.value : "vietnamese_standard");
  pattern = pattern || (inputCustomPattern ? inputCustomPattern.value : "Tuần {tuan} - Tiết {tiet} - Bài {bai_num} - {ten_bai}.docx");

  const grade = (selectMainGrade ? selectMainGrade.value : (cfgClasses ? cfgClasses.value : "9")) || "9";
  const subject = (selectMainSubject ? selectMainSubject.value : (cfgSubject ? cfgSubject.value : "Tin học")) || "Tin học";
  const teacher = (cfgQuickTeacher ? cfgQuickTeacher.value.trim() : (cfgTeacherName ? cfgTeacherName.value.trim() : "Lê Thị Phương Thảo")) || "Lê Thị Phương Thảo";
  const teacherAscii = removeVietnameseAccents(teacher);

  const info = file.lesson_info || {};
  const ppct = file.matched_ppct || {};

  // Lesson number
  const baiRaw = file.bai_num || info.bai_num || ppct.stt || "1";
  const bMatch = String(baiRaw).match(/\d+/);
  const baiInt = bMatch ? parseInt(bMatch[0], 10) : 1;
  const baiStr = String(baiInt).padStart(2, "0");
  const baiNum = String(baiInt);

  // Week
  const weekVal = file.week || ppct.tuan || info.week || info.tuan || "1";
  const wMatch = String(weekVal).match(/\d+/);
  const wInt = wMatch ? parseInt(wMatch[0], 10) : 1;
  const tuan = String(wInt).padStart(2, "0");
  const tuan1 = String(wInt);

  // Period
  const periodVal = file.periods || ppct.tiet || info.tiet_str || "1";
  const pMatch = String(periodVal).match(/\d+/);
  const pInt = pMatch ? parseInt(pMatch[0], 10) : 1;
  const tiet = String(pInt).padStart(2, "0");
  const tiet1 = String(pInt);
  const tietDisplay = (String(periodVal).includes("+") || String(periodVal).includes(",") || String(periodVal).includes("-"))
    ? String(periodVal).replace(/\s+/g, "") : tiet;

  // Title
  let rawTitle = file.bai_name || ppct.ten_bai || info.bai_title || `Bài ${baiNum}`;
  let cleanTitle = rawTitle.replace(/^(?:TUẦN|TUAN)\s*\d+(?:\s*[\-–—\+và\s]+\s*\d+)?[\s\:\.\-–—_]*/gi, '')
                          .replace(/^(?:CĐ|CD|CHỦ\s*ĐỀ|CHU\s*DE)\s*[0-9A-Za-z]+[\s\:\.\-–—]*/gi, '')
                          .replace(/^(?:BÀI|BAI)\s*\d+[a-zA-Z]?[\s\:\.\-–—]*/gi, '')
                          .replace(/^(?:TIẾT|TIET)\s*\d+[\d\+\,\-\s]*[\:\.\-–—\s]*/gi, '')
                          .replace(/^[\:\.\-–—\s\+\,]+/, '')
                          .replace(/[\:\.\-–—\s]+$/, '').trim();
  if (!cleanTitle) cleanTitle = `Bài ${baiNum}`;
  const slugName = toSlug(cleanTitle) || `Bai-${baiNum}`;
  const tenKhongDau = removeVietnameseAccents(cleanTitle);

  // Subject codes
  const subLower = removeVietnameseAccents(subject).toLowerCase().replace(/\s+/g, "");
  let subCode = subLower;
  let subShort = subject;
  if (subLower.includes("tin")) { subCode = "tinhoc"; subShort = "Tin"; }
  else if (subLower.includes("toan")) { subCode = "toan"; subShort = "Toan"; }
  else if (subLower.includes("congnghe")) { subCode = "congnghe"; subShort = "Cong Nghe"; }
  else if (subLower.includes("hdtn") || subLower.includes("trainghiem")) { subCode = "hdtnhn"; subShort = "HDTN"; }

  if (scheme === "ppct_exact" && ppct && ppct.ghi_chu) {
    let fn = ppct.ghi_chu.trim();
    if (!fn.toLowerCase().endsWith(".docx")) fn += ".docx";
    return fn;
  }

  const tokens = {
    tuan: tuan,
    week: tuan,
    tuan_1: tuan1,
    week_1: tuan1,
    tiet: tietDisplay,
    period: tietDisplay,
    tiet_1: tiet1,
    bai: baiStr,
    bai_str: baiStr,
    bai_num: baiNum,
    ten_bai: cleanTitle,
    lesson_name: cleanTitle,
    ten_khong_dau: tenKhongDau,
    slug_name: slugName,
    mon: subject,
    mon_code: subCode,
    sub_code: subCode,
    mon_short: subShort,
    sub_short: subShort,
    lop: grade,
    grade: grade,
    gv: teacher,
    teacher: teacherAscii
  };

  let pat = "Tuần {tuan} - Tiết {tiet} - Bài {bai_num} - {ten_bai}.docx";
  if (scheme === "vietnamese_standard") {
    pat = "Tuần {tuan} - Tiết {tiet} - Bài {bai_num} - {ten_bai}.docx";
  } else if (scheme === "vietnamese_simple") {
    pat = "{mon_short} {lop} - Tuần {tuan} - Tiết {tiet} - {ten_bai}.docx";
  } else if (scheme === "period_lesson") {
    pat = "Tiết {tiet} - {ten_bai}.docx";
  } else if (scheme === "ppct_slug") {
    pat = "{mon_code}{grade}_tuan{week}_Bai{bai_str}_{slug_name}_Tiet{period}.docx";
  } else if (scheme === "teacher") {
    pat = "{teacher}_{mon_short} {grade}_Tuan {week}_Bai {bai_str}.docx";
  } else if (scheme === "custom") {
    pat = pattern || "Tuần {tuan} - Tiết {tiet} - Bài {bai_num} - {ten_bai}.docx";
  }

  let result = pat;
  for (const [k, v] of Object.entries(tokens)) {
    result = result.split(`{${k}}`).join(String(v));
  }

  result = result.replace(/[\\/*?:"<>|]/g, '-').replace(/\s+/g, ' ').trim();
  if (!result.toLowerCase().endsWith(".docx")) result += ".docx";
  return result;
}

// Live Preview Updater
function updateLiveNamingPreview() {
  if (!namingPreviewSample) return;
  const curSub = selectMainSubject ? selectMainSubject.value : (cfgSubject ? cfgSubject.value : "Tin học");
  const isHdtn = removeVietnameseAccents(curSub).toLowerCase().includes("hdtn") || removeVietnameseAccents(curSub).toLowerCase().includes("trai nghiem");
  
  let sampleTitle = "Thế giới kĩ thuật số";
  let sampleBaiNum = "1";
  let sampleTuan = "1";
  let sampleTiet = "1";

  if (activePpctItems && activePpctItems.length > 0) {
    const it0 = activePpctItems[0];
    sampleTitle = it0.ten_bai || sampleTitle;
    sampleBaiNum = String(it0.stt || "1");
    sampleTuan = String(it0.tuan || "1");
    sampleTiet = String(it0.tiet || "1");
  } else if (isHdtn) {
    sampleTitle = "Bầu cử ban chỉ huy chi đội";
  }

  const sampleFile = {
    bai_num: sampleBaiNum,
    week: sampleTuan,
    periods: sampleTiet,
    bai_name: sampleTitle,
    lesson_info: { bai_num: sampleBaiNum, bai_title: sampleTitle, week: sampleTuan, tiet_str: sampleTiet }
  };
  const scheme = selectNamingScheme ? selectNamingScheme.value : "vietnamese_standard";
  const pattern = inputCustomPattern ? inputCustomPattern.value : "";
  const sampleName = computeTargetFilename(sampleFile, scheme, pattern);
  namingPreviewSample.textContent = sampleName;
}

// Update all target filenames live in scanned files list
function updateAllTargetFilenames() {
  const scheme = selectNamingScheme ? selectNamingScheme.value : "vietnamese_standard";
  const pattern = inputCustomPattern ? inputCustomPattern.value : "";

  scannedFiles.forEach(f => {
    f.target_filename = computeTargetFilename(f, scheme, pattern);
  });

  renderFilesTable();
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
  const teacher = cfgTeacherName ? cfgTeacherName.value.trim() : "Trần Đức Tình";
  const dept = cfgDepartment ? cfgDepartment.value.trim() : "Tổ KHTN";
  const school = cfgSchoolName ? cfgSchoolName.value.trim() : "Trường THCS";
  const year = cfgSchoolYear ? cfgSchoolYear.value.trim() : "2026-2027";
  const subject = (cfgSubject && cfgSubject.value.trim()) || (selectMainSubject ? selectMainSubject.value : "Tin học");
  const classes = (cfgClasses && cfgClasses.value.trim()) || (selectMainGrade ? selectMainGrade.value : "9");
  const prefix = cfgTitlePrefix ? cfgTitlePrefix.value : "TÊN BÀI DẠY: ";

  // Lấy dữ liệu bài mẫu thực tế từ PPCT đang chọn để hiển thị chân thực
  const samplePpct = (activePpctItems && activePpctItems.length > 0) ? activePpctItems[0] : null;
  const sampleTitle = samplePpct ? samplePpct.ten_bai : "BÀI 1. THẾ GIỚI KĨ THUẬT SỐ";
  const sampleDuration = (samplePpct && (samplePpct.so_tiet || samplePpct.duration)) || "1";
  const samplePeriods = (samplePpct && (samplePpct.tiet_range || samplePpct.tiet)) || "1";
  const sampleWeek = (samplePpct && samplePpct.tuan) || "1";

  // Teaching Date Auto / Manual
  let date = cfgTeachingDate ? cfgTeachingDate.value.trim() : "../../2026";
  if (cfgAutoDate && cfgAutoDate.checked) {
    const sDate = cfgStartDate ? cfgStartDate.value : "2026-09-07";
    const dFmt = cfgDateFormat ? cfgDateFormat.value : "d2_to_d6";
    const calc = calculateWeekDates(sampleWeek, sDate, dFmt);
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
  if (pvTuan) pvTuan.textContent = `Tuần: ${sampleWeek}`;
  if (pvTiet) pvTiet.textContent = `Tiết: ${samplePeriods}`;
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
    let cleanT = sampleTitle.toUpperCase();
    if (!cleanT.startsWith("BÀI ") && !cleanT.startsWith("CHỦ ĐỀ ")) {
      cleanT = `BÀI 1. ${cleanT}`;
    }
    pvTitle.textContent = `${prefix}${cleanT}`;
  }
  if (pvSubjectClass) {
    const subLabel = getSubjectLabel(subject);
    pvSubjectClass.textContent = `${subLabel}: ${subject}; lớp: ${classes}`;
  }
  if (pvDuration) {
    pvDuration.textContent = `Thời gian thực hiện: ${sampleDuration} tiết`;
  }

  // Approval Block
  if (pvApproval) {
    if (cfgOptApproval && !cfgOptApproval.checked) {
      pvApproval.style.display = "none";
    } else {
      pvApproval.style.display = "flex";
      const sSchool = cfgSignerSchool ? cfgSignerSchool.value.trim() : "";
      const sDept = cfgSignerDept ? cfgSignerDept.value.trim() : "";
      const tSchool = cfgTitleSignerSchool ? cfgTitleSignerSchool.value.trim() : "Duyệt của tổ chuyên môn";
      const tDept = cfgTitleSignerDept ? cfgTitleSignerDept.value.trim() : "Người thực hiện";
      if (pvTitleSignerSchool) pvTitleSignerSchool.textContent = tSchool || "Duyệt của tổ chuyên môn";
      if (pvTitleSignerDept) pvTitleSignerDept.textContent = tDept || "Người thực hiện";
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
      
      const activeFile = currentConfig.ppct_file || "_Lop_9.xlsx";
      
      const smasGroup = document.createElement("optgroup");
      smasGroup.label = "⚡ SMAS (Thời Khóa Biểu & PPCT Đồng Bộ)";
      const schoolGroup = document.createElement("optgroup");
      schoolGroup.label = "📁 Kế Hoạch PPCT Nhà Trường (File Excel)";

      json.files.forEach(f => {
        const opt = document.createElement("option");
        opt.value = f.filename;
        opt.dataset.subject = f.subject || "";
        opt.dataset.grade = f.grade || "";
        opt.dataset.className = f.className || "";
        const countText = f.item_count ? ` (${f.item_count} tiết)` : "";
        if (f.is_smas) {
          opt.textContent = `⚡ ${f.title || f.filename}${countText}`;
          opt.style.fontWeight = "600";
          opt.style.color = "#059669";
          smasGroup.appendChild(opt);
        } else {
          opt.textContent = `${f.filename}${countText}`;
          schoolGroup.appendChild(opt);
        }
      });

      if (smasGroup.children.length > 0) selectPpctFile.appendChild(smasGroup);
      if (schoolGroup.children.length > 0) selectPpctFile.appendChild(schoolGroup);

      // Nếu activeFile tồn tại trong danh sách, giữ nguyên và đồng bộ Môn/Khối
      const hasActive = json.files.some(f => f.filename === activeFile);
      if (hasActive) {
        selectPpctFile.value = activeFile;
        syncSubjectAndGradeFromSelectedPpct();
      } else {
        const curSubject = selectMainSubject ? selectMainSubject.value : (cfgSubject ? cfgSubject.value : "Tin học");
        const curGrade = selectMainGrade ? selectMainGrade.value : (cfgClasses ? cfgClasses.value : "9");
        autoSelectPpctForSubjectGrade(curSubject, curGrade, false);
      }

      // Load active PPCT data to tab
      if (selectPpctFile.value) {
        loadPpctTableData(selectPpctFile.value);
      }
    }
  } catch (err) {
    log(`Lỗi tải danh sách PPCT: ${err.message}`, "error");
  }
}

// Hàm chọn tự động bộ PPCT thông minh nhất theo Môn học và Khối lớp
function autoSelectPpctForSubjectGrade(subject, grade, doReloadTable = true) {
  if (!selectPpctFile || !selectPpctFile.options || selectPpctFile.options.length === 0) return null;
  const s = removeVietnameseAccents(subject || "").toLowerCase().trim();
  const g = String(grade || "").replace(/\D/g, "");

  const isHdtn = s.includes("hdtn") || s.includes("trai nghiem") || s.includes("tnhn") || s.includes("huong nghiep");
  const isTin = s.includes("tin");
  const isGdtc = s.includes("the chat") || s.includes("gdtc") || s.includes("the duc");
  const isToan = s.includes("toan");
  const isCongNghe = s.includes("cong nghe");

  let bestIndex = -1;
  let bestScore = -999;

  for (let i = 0; i < selectPpctFile.options.length; i++) {
    const opt = selectPpctFile.options[i];
    const val = opt.value.toLowerCase();
    const txt = opt.text.toLowerCase();
    const optSubject = removeVietnameseAccents(opt.dataset.subject || "").toLowerCase();
    const optGrade = String(opt.dataset.grade || "").replace(/\D/g, "");
    const optClass = (opt.dataset.className || "").toLowerCase();

    let score = 0;
    const allText = `${optSubject} ${val} ${txt} ${optClass}`;

    // 1. Chấm điểm Môn Học (Ưu tiên số 1, loại bỏ tuyệt đối môn sai lệch)
    if (isHdtn) {
      if (allText.includes("hdtn") || allText.includes("trai nghiem") || allText.includes("tnhn") || allText.includes("huong nghiep")) {
        score += 100;
      } else {
        score -= 500;
      }
    } else if (isTin) {
      if (allText.includes("tin") || val.includes("_lop_")) {
        score += 100;
      } else {
        score -= 500;
      }
    } else if (isGdtc) {
      if (allText.includes("gdtc") || allText.includes("the chat") || allText.includes("the duc")) {
        score += 100;
      } else {
        score -= 500;
      }
    } else if (isToan) {
      if (allText.includes("toan")) {
        score += 100;
      } else {
        score -= 500;
      }
    } else if (isCongNghe) {
      if (allText.includes("cong nghe")) {
        score += 100;
      } else {
        score -= 500;
      }
    } else {
      if (allText.includes(s)) {
        score += 50;
      }
    }

    // 2. Chấm điểm Khối Lớp
    if (g) {
      if (optGrade === g) {
        score += 40;
      } else if (allText.includes(`lop_${g}`) || allText.includes(`lop ${g}`) || allText.includes(`_${g}`) || allText.includes(` ${g}`) || allText.includes(`${g}a`) || allText.includes(`${g}b`)) {
        score += 35;
      }
    }

    // 3. Ưu tiên SMAS chính thức
    if (opt.value.startsWith("[SMAS]")) {
      score += 5;
    }

    if (score > bestScore) {
      bestScore = score;
      bestIndex = i;
    }
  }

  if (bestIndex >= 0 && bestScore > 0) {
    selectPpctFile.selectedIndex = bestIndex;
    const selectedFile = selectPpctFile.options[bestIndex].value;
    syncSubjectAndGradeFromSelectedPpct();
    if (doReloadTable) {
      loadPpctTableData(selectedFile);
    }
    return selectedFile;
  }
  return null;
}

// Hàm đồng bộ hai chiều: Khi chọn tệp PPCT, tự động cập nhật Môn học, Khối lớp và Badge hiển thị
function syncSubjectAndGradeFromSelectedPpct() {
  if (!selectPpctFile || selectPpctFile.selectedIndex < 0) return;
  const opt = selectPpctFile.options[selectPpctFile.selectedIndex];
  if (!opt) return;

  const fn = opt.value.toLowerCase();
  const dsSub = (opt.dataset.subject || "").toLowerCase();
  const dsGrd = String(opt.dataset.grade || "").replace(/\D/g, "");

  // Tự động nhận diện Môn học từ tệp PPCT đã chọn
  let targetSubject = "";
  if (dsSub.includes("hdtn") || dsSub.includes("trai nghiem") || dsSub.includes("tnhn") || dsSub.includes("huong nghiep") ||
      fn.includes("hdtn") || fn.includes("tnhn") || fn.includes("trai nghiem") || fn.includes("hđ tn") || fn.includes("hướng nghiệp")) {
    targetSubject = "Hoạt động trải nghiệm, hướng nghiệp";
  } else if (dsSub.includes("toan") || fn.includes("toan")) {
    targetSubject = "Toán";
  } else if (dsSub.includes("cong nghe") || fn.includes("congnghe")) {
    targetSubject = "Công nghệ";
  } else if (dsSub.includes("van") || fn.includes("van") || fn.includes("ngữ văn")) {
    targetSubject = "Ngữ Văn";
  } else if (dsSub.includes("the chat") || dsSub.includes("gdtc") || fn.includes("gdtc")) {
    targetSubject = "Giáo dục thể chất";
  } else if (dsSub.includes("tin") || fn.includes("tin") || fn.includes("_lop_")) {
    targetSubject = "Tin học";
  } else {
    targetSubject = opt.dataset.subject || "Tin học";
  }

  if (targetSubject && selectMainSubject) {
    let matched = false;
    for (let i = 0; i < selectMainSubject.options.length; i++) {
      const optV = selectMainSubject.options[i].value;
      const optT = selectMainSubject.options[i].text;
      if (optV === targetSubject || optV.toLowerCase() === targetSubject.toLowerCase() || optT.includes(targetSubject)) {
        selectMainSubject.selectedIndex = i;
        if (cfgSubject) cfgSubject.value = selectMainSubject.value;
        matched = true;
        break;
      }
    }
    if (!matched) {
      const newOpt = document.createElement("option");
      newOpt.value = targetSubject;
      newOpt.textContent = targetSubject;
      newOpt.selected = true;
      selectMainSubject.appendChild(newOpt);
      if (cfgSubject) cfgSubject.value = targetSubject;
    }
  }

  // Tự động nhận diện Khối lớp từ tệp PPCT đã chọn
  let targetGrade = dsGrd;
  if (!targetGrade) {
    const m = fn.match(/(?:lop[_\s]*|khối[_\s]*|thcs[_\s]*|_|\b)([6-9])\b/);
    if (m) targetGrade = m[1];
  }

  if (targetGrade && selectMainGrade) {
    for (let i = 0; i < selectMainGrade.options.length; i++) {
      if (selectMainGrade.options[i].value === targetGrade) {
        selectMainGrade.selectedIndex = i;
        if (cfgClasses) cfgClasses.value = selectMainGrade.value;
        break;
      }
    }
  }

  // Cập nhật Live Status Badge để người dùng nhìn thấy rõ ràng
  if (activePpctBadgeText) {
    const sName = selectMainSubject ? selectMainSubject.value : targetSubject;
    const gName = selectMainGrade ? selectMainGrade.value : (targetGrade || "9");
    const shortSub = sName.includes("trải nghiệm") ? "HĐTN" : sName;
    activePpctBadgeText.textContent = `${shortSub} - Khối ${gName} • ${opt.text || opt.value}`;
  }
}

async function loadPpctTableData(filename) {
  try {
    tablePpctBody.innerHTML = `<tr><td colspan="6" class="text-center py-6 text-muted">Đang tải dữ liệu ${filename}...</td></tr>`;
    const res = await fetch(`/api/ppct/data?file=${encodeURIComponent(filename)}`);
    const json = await res.json();
    if (json.success && json.data) {
      const data = json.data;
      activePpctItems = data.items || [];
      ppctTitleDisplay.textContent = `Bảng PPCT: ${filename} - ${data.title || ''}`;
      renderPpctRows(data.items || []);
    } else {
      activePpctItems = [];
      tablePpctBody.innerHTML = `<tr><td colspan="6" class="text-center py-6 text-muted">Không có dữ liệu bài học dạng bảng</td></tr>`;
    }
  } catch (err) {
    activePpctItems = [];
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
  const naming_scheme = selectNamingScheme ? selectNamingScheme.value : "vietnamese_standard";
  const custom_pattern = inputCustomPattern ? inputCustomPattern.value : "";
  const selectedPpctOpt = (selectPpctFile && selectPpctFile.selectedIndex >= 0) ? selectPpctFile.options[selectPpctFile.selectedIndex] : null;
  const userSubject = (cfgSubject && cfgSubject.value.trim()) || (selectMainSubject ? selectMainSubject.value : "");
  const userGrade = (cfgClasses && cfgClasses.value.trim()) || (selectMainGrade ? selectMainGrade.value : "");
  const ppctSubject = (selectedPpctOpt && selectedPpctOpt.dataset.subject) || "";
  const ppctGrade = (selectedPpctOpt && selectedPpctOpt.dataset.grade) || "";

  const subject = userSubject || ppctSubject || "Tin học";
  const grade = userGrade || ppctGrade || "9";
  const teacher_name = cfgQuickTeacher ? cfgQuickTeacher.value.trim() : (cfgTeacherName ? cfgTeacherName.value.trim() : "Trần Đức Tình");

  if (!folder) {
    alert("Vui lòng nhập đường dẫn thư mục chứa giáo án!");
    return;
  }

  btnScan.disabled = true;
  btnScan.innerHTML = `<span class="spinner"></span> Đang quét...`;
  log(`Bắt đầu quét thư mục: "${folder}" với PPCT: "${ppct_file}" (Khối ${grade}, Môn: ${subject})...`);

  try {
    const res = await fetch("/api/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        folder: folder,
        ppct_file: ppct_file,
        naming_scheme: naming_scheme,
        custom_pattern: custom_pattern,
        grade: grade,
        classes: grade,
        subject: subject,
        teacher_name: teacher_name
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

    // NLS Status Badge
    let nlsBadgeHtml = `<span class="badge-nls-none">Chưa kiểm tra</span>`;
    if (file.nls_status === "already_integrated") {
      const codes = (file.nls_codes || []).map(c => `<span class="nls-code-tag">${escapeHtml(c)}</span>`).join("");
      nlsBadgeHtml = `
        <div><span class="badge-nls-already">🟢 Đã có NLS</span></div>
        <div style="margin-top: 3px;">${codes}</div>
      `;
    } else if (file.nls_status === "integrated") {
      const codes = (file.added_codes || file.nls_codes || []).map(c => `<span class="nls-code-tag">${escapeHtml(c)}</span>`).join("");
      nlsBadgeHtml = `
        <div><span class="badge-nls-integrated">🟣 Đã tích hợp</span></div>
        <div style="margin-top: 3px;">${codes}</div>
      `;
    } else if (file.nls_status === "need_review") {
      nlsBadgeHtml = `<span class="badge-nls-review" title="${escapeHtml(file.nls_message || '')}">🟡 Cần kiểm tra</span>`;
    } else if (file.nls_status === "error") {
      nlsBadgeHtml = `<span class="badge badge-error" title="${escapeHtml(file.nls_message || '')}">Lỗi NLS</span>`;
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
      <td>${nlsBadgeHtml}</td>
      <td>${statusBadge}</td>
      <td class="text-right">
        <div style="display: inline-flex; gap: 4px;">
          <button class="btn btn-secondary btn-sm btn-nls-single" data-idx="${origIdx}" title="Kiểm tra & Tích hợp Năng lực số chuẩn TT 02/2025">
            🎯 NLS
          </button>
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

  document.querySelectorAll(".btn-nls-single").forEach(btn => {
    btn.addEventListener("click", () => {
      const idx = parseInt(btn.dataset.idx, 10);
      openNlsModal(idx);
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

  // Populate quick PPCT selector
  if (editPpctSelect) {
    editPpctSelect.innerHTML = `<option value="">-- Chọn bài học từ PPCT để tự điền 100% --</option>`;
    if (activePpctItems && activePpctItems.length > 0) {
      activePpctItems.forEach((it, i) => {
        const opt = document.createElement("option");
        opt.value = i;
        const weekTxt = it.tuan !== null && it.tuan !== undefined ? `Tuần ${it.tuan}` : '';
        const tietTxt = it.tiet !== null && it.tiet !== undefined ? `Tiết ${it.tiet}` : '';
        opt.textContent = `${weekTxt} - ${tietTxt}: ${it.ten_bai || ''}`;
        if (ppct.ten_bai && it.ten_bai && ppct.ten_bai.trim().toLowerCase() === it.ten_bai.trim().toLowerCase()) {
          opt.selected = true;
        }
        editPpctSelect.appendChild(opt);
      });
    }
  }

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
  log(`Đã cập nhật thông số cho file: ${file.filename} (Tuần ${file.week}, Tiết ${file.periods}) ➔ ${file.target_filename}`, "success");
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

// 8. Batch Processing Execution (Per-File Sequential Loop with Live Real-time Progress %)
async function processBatch(filesToRun = null) {
  const items = filesToRun || Array.from(selectedFileIndices).map(idx => scannedFiles[idx]);
  if (!items || items.length === 0) {
    alert("Vui lòng chọn ít nhất một file để xử lý!");
    return;
  }

  btnBatchProcess.disabled = true;
  if (btnFastRename) btnFastRename.disabled = true;
  if (btnBatchNlsMaster) btnBatchNlsMaster.disabled = true;

  progressContainer.classList.remove("hidden");
  progressBarFill.style.width = "0%";
  progressPercentage.textContent = "0%";
  progressLabel.textContent = `Bắt đầu chuẩn hoá & đổi tên ${items.length} file...`;

  log(`🚀 BẮT ĐẦU RENDER & ĐỔI TÊN HÀNG LOẠT: ${items.length} file...`, "info");

  const outputMode = selectOutputMode ? selectOutputMode.value : "new_folder";
  const autoNls = optAutoNls ? optAutoNls.checked : false;
  const nlsRed = optNlsRed ? optNlsRed.checked : true;
  const syncKhgd = optSyncKhgd ? optSyncKhgd.checked : true;
  const selectedPpctOpt = (selectPpctFile && selectPpctFile.selectedIndex >= 0) ? selectPpctFile.options[selectPpctFile.selectedIndex] : null;
  const userSubject = (cfgSubject && cfgSubject.value.trim()) || (selectMainSubject ? selectMainSubject.value : "");
  const userGrade = (cfgClasses && cfgClasses.value.trim()) || (selectMainGrade ? selectMainGrade.value : "");
  const ppctSubject = (selectedPpctOpt && selectedPpctOpt.dataset.subject) || "";
  const ppctGrade = (selectedPpctOpt && selectedPpctOpt.dataset.grade) || "";

  const finalSubject = userSubject || ppctSubject || "Tin học";
  const finalGrade = userGrade || ppctGrade || "9";

  const configObj = {
    ppct_file: selectPpctFile ? selectPpctFile.value : "_Lop_9.xlsx",
    naming_scheme: selectNamingScheme ? selectNamingScheme.value : "vietnamese_standard",
    custom_pattern: inputCustomPattern ? inputCustomPattern.value : "",
    template_style: selectTemplateStyle ? selectTemplateStyle.value : "mau_thcs",
    teacher_name: cfgTeacherName ? cfgTeacherName.value : "Trần Đức Tình",
    school_name: cfgSchoolName ? cfgSchoolName.value : "THCS",
    department: cfgDepartment ? cfgDepartment.value : "Tổ KHTN",
    school_year: cfgSchoolYear ? cfgSchoolYear.value : "2026-2027",
    subject: finalSubject,
    subject_type: cfgSubjectType ? cfgSubjectType.value : "auto",
    classes: finalGrade,
    grade: finalGrade,
    school_year_start_date: cfgStartDate ? cfgStartDate.value : "2026-09-07",
    teaching_date_format: cfgDateFormat ? cfgDateFormat.value : "smas_exact",
    auto_calc_teaching_date: cfgAutoDate ? cfgAutoDate.checked : true,
    teaching_date: cfgTeachingDate ? cfgTeachingDate.value : "",
    title_prefix: cfgTitlePrefix ? cfgTitlePrefix.value : "TÊN BÀI DẠY: ",
    enable_header: cfgOptHeader ? cfgOptHeader.checked : true,
    enable_footer: cfgOptFooter ? cfgOptFooter.checked : true,
    enable_approval_block: cfgOptApproval ? cfgOptApproval.checked : true,
    title_signer_school: cfgTitleSignerSchool ? cfgTitleSignerSchool.value.trim() : "Duyệt của tổ chuyên môn",
    signer_school: cfgSignerSchool ? cfgSignerSchool.value.trim() : "",
    title_signer_dept: cfgTitleSignerDept ? cfgTitleSignerDept.value.trim() : "Người thực hiện",
    signer_dept: cfgSignerDept ? cfgSignerDept.value.trim() : "",
    format_5512: cfgOptFormat5512 ? cfgOptFormat5512.checked : true,
    table_border: cfgOptBorder ? cfgOptBorder.checked : false,
    autofit_tables: cfgOptAutofitTable ? cfgOptAutofitTable.checked : true,
    margin_top_cm: parseFloat(cfgMarginTop ? cfgMarginTop.value : 2.0) || 2.0,
    margin_bottom_cm: parseFloat(cfgMarginBottom ? cfgMarginBottom.value : 2.0) || 2.0,
    margin_left_cm: parseFloat(cfgMarginLeft ? cfgMarginLeft.value : 2.0) || 2.0,
    margin_right_cm: parseFloat(cfgMarginRight ? cfgMarginRight.value : 1.5) || 1.5,
    include_file_naming_note: cfgNamingNote ? cfgNamingNote.checked : true
  };

  let successCount = 0;
  let failCount = 0;
  let lastOutDir = "";

  try {
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      const pct = Math.round((i / items.length) * 100);
      progressBarFill.style.width = `${pct}%`;
      progressPercentage.textContent = `${pct}%`;
      progressLabel.textContent = `[${i + 1}/${items.length}] Đang xử lý: ${item.filename}` + (autoNls ? " & NLS..." : "...");

      const targetFileObj = scannedFiles.find(f => f.filename === item.filename || f.file_path === item.file_path);
      if (targetFileObj) {
        targetFileObj.status = "processing";
        renderFilesTable();
      }

      try {
        const res = await fetch("/api/process_batch", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            files: [item],
            output_mode: outputMode,
            sync_khgd_yccd: syncKhgd,
            auto_integrate_nls: autoNls,
            highlight_red: nlsRed,
            config: configObj
          })
        });

        const json = await res.json();
        if (json.success && json.results && json.results.length > 0) {
          const r = json.results[0];
          lastOutDir = json.output_directory || lastOutDir;
          if (r.status === "success") {
            successCount++;
            if (targetFileObj) {
              targetFileObj.status = "done";
              if (r.new_file) targetFileObj.target_filename = r.new_file;
              if (r.nls_info) {
                targetFileObj.nls_status = r.nls_info.status;
                targetFileObj.nls_codes = r.nls_info.detected_codes || [];
                targetFileObj.added_codes = r.nls_info.added_codes || [];
                targetFileObj.nls_message = r.nls_info.message;
              }
            }
            log(`[${i + 1}/${items.length}] ✅ ${r.original_file} ➔ ${r.new_file}`, "success");
          } else {
            failCount++;
            if (targetFileObj) targetFileObj.status = "error";
            log(`[${i + 1}/${items.length}] ❌ ${r.original_file}: ${r.message}`, "error");
          }
        } else {
          failCount++;
          if (targetFileObj) targetFileObj.status = "error";
          log(`[${i + 1}/${items.length}] ❌ Lỗi xử lý ${item.filename}: ${json.error || "Không có phản hồi"}`, "error");
        }
      } catch (err) {
        failCount++;
        if (targetFileObj) targetFileObj.status = "error";
        log(`[${i + 1}/${items.length}] ⚠️ Lỗi kết nối với file ${item.filename}: ${err.message}`, "error");
      }

      const currentPct = Math.round(((i + 1) / items.length) * 100);
      progressBarFill.style.width = `${currentPct}%`;
      progressPercentage.textContent = `${currentPct}%`;
      updateStats();
      renderFilesTable();
    }

    progressBarFill.style.width = "100%";
    progressPercentage.textContent = "100%";
    progressLabel.textContent = `Hoàn tất! Thành công: ${successCount}/${items.length}` + (failCount > 0 ? ` (Lỗi: ${failCount})` : "");

    log(`🏁 Hoàn tất: ${successCount} file thành công, ${failCount} lỗi.`, successCount > 0 ? "success" : "error");
    if (lastOutDir && lastOutDir !== "inplace") {
      log(`📁 Thư mục kết quả: ${lastOutDir}`, "info");
    }

    alert(`Đã hoàn tất xử lý ${successCount}/${items.length} file KHBD theo mẫu chuẩn!`);
  } catch (globalErr) {
    log(`❌ Lỗi nghiêm trọng khi chạy hàng loạt: ${globalErr.message}`, "error");
    alert(`Lỗi xử lý: ${globalErr.message}`);
  } finally {
    btnBatchProcess.disabled = false;
    if (btnFastRename) btnFastRename.disabled = false;
    if (btnBatchNlsMaster) btnBatchNlsMaster.disabled = false;
  }
}

// 8b. Fast Rename Only (0.1s per file, no docx modification)
async function runFastRename(filesToRun = null) {
  const items = filesToRun || Array.from(selectedFileIndices).map(idx => scannedFiles[idx]);
  if (!items || items.length === 0) {
    alert("Vui lòng chọn ít nhất một file để đổi tên!");
    return;
  }

  if (btnFastRename) btnFastRename.disabled = true;
  btnBatchProcess.disabled = true;
  if (btnBatchNlsMaster) btnBatchNlsMaster.disabled = true;

  progressContainer.classList.remove("hidden");
  progressBarFill.style.width = "0%";
  progressPercentage.textContent = "0%";
  progressLabel.textContent = `Bắt đầu đổi tên nhanh ${items.length} file...`;

  log(`🏷️ [ĐỔI TÊN NHANH] Bắt đầu đổi tên ${items.length} file theo PPCT...`, "info");

  const outputMode = selectOutputMode ? selectOutputMode.value : "new_folder";
  const selectedPpctOpt = (selectPpctFile && selectPpctFile.selectedIndex >= 0) ? selectPpctFile.options[selectPpctFile.selectedIndex] : null;
  const userSubject = (cfgSubject && cfgSubject.value.trim()) || (selectMainSubject ? selectMainSubject.value : "");
  const userGrade = (cfgClasses && cfgClasses.value.trim()) || (selectMainGrade ? selectMainGrade.value : "");
  const ppctSubject = (selectedPpctOpt && selectedPpctOpt.dataset.subject) || "";
  const ppctGrade = (selectedPpctOpt && selectedPpctOpt.dataset.grade) || "";

  const finalSubject = userSubject || ppctSubject || "Tin học";
  const finalGrade = userGrade || ppctGrade || "9";

  const configObj = {
    ppct_file: selectPpctFile ? selectPpctFile.value : "_Lop_9.xlsx",
    naming_scheme: selectNamingScheme ? selectNamingScheme.value : "vietnamese_standard",
    custom_pattern: inputCustomPattern ? inputCustomPattern.value : "",
    subject: finalSubject,
    classes: finalGrade,
    grade: finalGrade,
    teacher_name: cfgQuickTeacher ? cfgQuickTeacher.value.trim() : (cfgTeacherName ? cfgTeacherName.value.trim() : "Trần Đức Tình"),
    signer_dept: cfgQuickSignerDept ? cfgQuickSignerDept.value.trim() : (cfgSignerDept ? cfgSignerDept.value.trim() : "Trần Đức Tình")
  };

  let successCount = 0;
  let failCount = 0;
  let lastOutDir = "";

  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    const pct = Math.round((i / items.length) * 100);
    progressBarFill.style.width = `${pct}%`;
    progressPercentage.textContent = `${pct}%`;
    progressLabel.textContent = `[${i + 1}/${items.length}] Đang đổi tên: ${item.filename}...`;

    const targetFileObj = scannedFiles.find(f => f.filename === item.filename || f.file_path === item.file_path);
    if (targetFileObj) {
      targetFileObj.status = "processing";
      renderFilesTable();
    }

    try {
      const res = await fetch("/api/fast_rename", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          files: [item],
          output_mode: outputMode,
          config: configObj
        })
      });

      const json = await res.json();
      if (json.success && json.results && json.results.length > 0) {
        const r = json.results[0];
        lastOutDir = json.output_directory || lastOutDir;
        if (r.status === "success") {
          successCount++;
          if (targetFileObj) {
            targetFileObj.status = "done";
            if (r.new_file) targetFileObj.target_filename = r.new_file;
          }
          log(`[${i + 1}/${items.length}] 🏷️ Đã đổi tên: ${r.original_file} ➔ ${r.new_file}`, "success");
        } else {
          failCount++;
          if (targetFileObj) targetFileObj.status = "error";
          log(`[${i + 1}/${items.length}] ❌ Lỗi đổi tên ${r.original_file}: ${r.message}`, "error");
        }
      } else {
        failCount++;
        if (targetFileObj) targetFileObj.status = "error";
        log(`[${i + 1}/${items.length}] ❌ Lỗi đổi tên ${item.filename}: ${json.error || "Không có phản hồi"}`, "error");
      }
    } catch (err) {
      failCount++;
      if (targetFileObj) targetFileObj.status = "error";
      log(`[${i + 1}/${items.length}] ⚠️ Lỗi kết nối: ${err.message}`, "error");
    }

    const currentPct = Math.round(((i + 1) / items.length) * 100);
    progressBarFill.style.width = `${currentPct}%`;
    progressPercentage.textContent = `${currentPct}%`;
    updateStats();
    renderFilesTable();
  }

  progressBarFill.style.width = "100%";
  progressPercentage.textContent = "100%";
  progressLabel.textContent = `Hoàn tất đổi tên! Thành công: ${successCount}/${items.length}`;

  log(`🏁 Hoàn tất đổi tên: ${successCount} file thành công, ${failCount} lỗi.`, successCount > 0 ? "success" : "error");
  if (lastOutDir && lastOutDir !== "inplace") {
    log(`📁 Thư mục lưu file đổi tên: ${lastOutDir}`, "info");
  }

  if (btnFastRename) btnFastRename.disabled = false;
  btnBatchProcess.disabled = false;
  if (btnBatchNlsMaster) btnBatchNlsMaster.disabled = false;

  alert(`Đã hoàn tất đổi tên ${successCount}/${items.length} file theo PPCT!`);
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
          teacher_name: cfgTeacherName ? cfgTeacherName.value : "Trần Đức Tình",
          school_name: cfgSchoolName ? cfgSchoolName.value : "THCS",
          department: cfgDepartment ? cfgDepartment.value : "Tổ KHTN",
          school_year: cfgSchoolYear ? cfgSchoolYear.value : "2026-2027",
          subject: selectMainSubject ? selectMainSubject.value : (cfgSubject ? cfgSubject.value : "Tin học"),
          subject_type: cfgSubjectType ? cfgSubjectType.value : "auto",
          classes: selectMainGrade ? selectMainGrade.value : (cfgClasses ? cfgClasses.value : "9"),
          grade: selectMainGrade ? selectMainGrade.value : (cfgClasses ? cfgClasses.value : "9"),
          school_year_start_date: cfgStartDate ? cfgStartDate.value : "2026-09-07",
          teaching_date_format: cfgDateFormat ? cfgDateFormat.value : "smas_exact",
          auto_calc_teaching_date: cfgAutoDate ? cfgAutoDate.checked : true,
          teaching_date: cfgTeachingDate ? cfgTeachingDate.value : "",
          duration: cfgDuration ? cfgDuration.value : "1",
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
    teaching_date_format: cfgDateFormat ? cfgDateFormat.value : "smas_exact",
    auto_calc_teaching_date: cfgAutoDate ? cfgAutoDate.checked : true,
    teaching_date: cfgTeachingDate.value.trim(),
    duration: cfgDuration.value.trim(),
    title_prefix: cfgTitlePrefix ? cfgTitlePrefix.value : "TÊN BÀI DẠY: ",
    enable_header: cfgOptHeader ? cfgOptHeader.checked : true,
    enable_footer: cfgOptFooter ? cfgOptFooter.checked : true,
    enable_approval_block: cfgOptApproval ? cfgOptApproval.checked : true,
    title_signer_school: cfgTitleSignerSchool ? cfgTitleSignerSchool.value.trim() : "Duyệt của tổ chuyên môn",
    signer_school: cfgSignerSchool ? cfgSignerSchool.value.trim() : "",
    title_signer_dept: cfgTitleSignerDept ? cfgTitleSignerDept.value.trim() : "Người thực hiện",
    signer_dept: cfgSignerDept ? cfgSignerDept.value.trim() : "",
    format_5512: cfgOptFormat5512 ? cfgOptFormat5512.checked : true,
    signers_list: signersList,
    table_border: cfgOptBorder ? cfgOptBorder.checked : false,
    template_style: selectTemplateStyle ? selectTemplateStyle.value : "mau_thcs",
    margin_top_cm: parseFloat(cfgMarginTop ? cfgMarginTop.value : 2.0) || 2.0,
    margin_bottom_cm: parseFloat(cfgMarginBottom ? cfgMarginBottom.value : 2.0) || 2.0,
    margin_left_cm: parseFloat(cfgMarginLeft ? cfgMarginLeft.value : 2.0) || 2.0,
    margin_right_cm: parseFloat(cfgMarginRight ? cfgMarginRight.value : 1.5) || 1.5,
    include_file_naming_note: cfgNamingNote ? cfgNamingNote.checked : true,
    ppct_file: selectPpctFile ? selectPpctFile.value : "_Lop_9.xlsx",
    naming_scheme: selectNamingScheme ? selectNamingScheme.value : "vietnamese_standard",
    output_mode: selectOutputMode ? selectOutputMode.value : "new_folder"
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

// Debounced auto-save for naming rules & workflow controls
let saveNamingTimeout = null;
function saveNamingConfigToServer() {
  clearTimeout(saveNamingTimeout);
  saveNamingTimeout = setTimeout(async () => {
    try {
      await fetch("/api/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ppct_file: selectPpctFile ? selectPpctFile.value : "_Lop_9.xlsx",
          naming_scheme: selectNamingScheme ? selectNamingScheme.value : "vietnamese_standard",
          custom_pattern: inputCustomPattern ? inputCustomPattern.value : "",
          classes: selectMainGrade ? selectMainGrade.value : "9",
          grade: selectMainGrade ? selectMainGrade.value : "9",
          subject: selectMainSubject ? selectMainSubject.value : "Tin học",
          teacher_name: cfgQuickTeacher ? cfgQuickTeacher.value.trim() : (cfgTeacherName ? cfgTeacherName.value.trim() : "Hoàng Thị Kim Tuyết"),
          signer_dept: cfgQuickSignerDept ? cfgQuickSignerDept.value.trim() : (cfgSignerDept ? cfgSignerDept.value.trim() : "Trần Đức Tình")
        })
      });
    } catch (e) {}
  }, 400);
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
  let apiKey = cfgAiKey ? cfgAiKey.value.trim() : "";
  if (!apiKey || apiKey.startsWith("YOUR_")) {
    apiKey = "sk-bee-73e9d744f8ef96f61278f28f4acfc8e44b69ee94c9cf6714720044f8c91c8502";
    if (cfgAiKey) cfgAiKey.value = apiKey;
  }
  const model = cfgAiModel ? cfgAiModel.value : "gemini-3.1-flash-lite";
  const baseUrl = cfgAiEndpoint ? cfgAiEndpoint.value.trim() : "https://platform.beeknoee.com/api/v1";

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

  const model = cfgAiModel ? cfgAiModel.value : "gemini-3.1-flash-lite";
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

  const model = cfgAiModel ? cfgAiModel.value : "gemini-3.1-flash-lite";
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

  const model = cfgAiModel ? cfgAiModel.value : "gemini-3.1-flash-lite";

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

// 17. NLS (Năng Lực Số) Execution Functions (Sequential Loop with Live Real-time Progress %)
async function runBatchNls(filesToRun = null) {
  const items = filesToRun || Array.from(selectedFileIndices).map(idx => scannedFiles[idx]);
  if (!items || items.length === 0) {
    alert("Vui lòng chọn ít nhất một file để tích hợp Năng lực số (NLS)!");
    return;
  }

  const onlyAudit = optNlsOnlyAudit ? optNlsOnlyAudit.checked : false;
  const highlightRed = optNlsRed ? optNlsRed.checked : true;
  const actionName = onlyAudit ? "KIỂM TRA NĂNG LỰC SỐ (AUDIT)" : "TỰ ĐỘNG TÍCH HỢP NĂNG LỰC SỐ (NLS)";

  if (btnBatchNlsMaster) btnBatchNlsMaster.disabled = true;
  if (btnToolbarNls) btnToolbarNls.disabled = true;
  if (btnBatchProcess) btnBatchProcess.disabled = true;

  progressContainer.classList.remove("hidden");
  progressBarFill.style.width = "0%";
  progressPercentage.textContent = "0%";
  progressLabel.textContent = `Bắt đầu ${actionName} cho ${items.length} file...`;

  log(`🎯 [NLS] BẮT ĐẦU ${actionName} TRÊN ${items.length} FILE...`, "info");

  const overallStats = {
    total: items.length,
    already_integrated: 0,
    integrated: 0,
    need_review: 0,
    error: 0
  };
  let lastOutDir = "";

  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    const pct = Math.round((i / items.length) * 100);
    progressBarFill.style.width = `${pct}%`;
    progressPercentage.textContent = `${pct}%`;
    progressLabel.textContent = `[${i + 1}/${items.length}] Đang xử lý NLS: ${item.filename}...`;

    const targetFileObj = scannedFiles.find(f => f.filename === item.filename || f.file_path === item.file_path);
    if (targetFileObj) {
      targetFileObj.status = "processing";
      renderFilesTable();
    }

    try {
      const payload = {
        files: [{
          file_path: item.file_path,
          filename: item.filename,
          subject: cfgSubject ? cfgSubject.value : "Tin học",
          grade: cfgClasses ? cfgClasses.value : "9",
          lesson_title: item.bai_name || (item.lesson_info ? item.lesson_info.bai_title : "")
        }],
        output_mode: "new_folder",
        highlight_red: highlightRed,
        only_audit: onlyAudit
      };

      const res = await fetch("/api/nls/batch_integrate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const json = await res.json();
      if (json.success && json.results && json.results.length > 0) {
        lastOutDir = json.output_directory || lastOutDir;
        const r = json.results[0];
        const st = r.status || "error";
        if (overallStats[st] !== undefined) overallStats[st]++;
        else overallStats.error++;

        if (targetFileObj) {
          targetFileObj.status = st === "error" ? "error" : "done";
          targetFileObj.nls_status = r.status;
          targetFileObj.nls_codes = r.detected_codes || [];
          targetFileObj.added_codes = r.added_codes || [];
          targetFileObj.nls_message = r.message;
        }

        const icon = r.status === "already_integrated" ? "🟢" :
                     r.status === "integrated" ? "🟣" :
                     r.status === "need_review" ? "🟡" : "🔴";
        log(`[${i + 1}/${items.length}] ${icon} [NLS] ${r.filename || item.filename}: ${r.message}`, r.status === "error" ? "error" : "success");
      } else {
        overallStats.error++;
        if (targetFileObj) targetFileObj.status = "error";
        log(`[${i + 1}/${items.length}] ❌ Lỗi xử lý NLS ${item.filename}: ${json.error || "Không có phản hồi"}`, "error");
      }
    } catch (err) {
      overallStats.error++;
      if (targetFileObj) targetFileObj.status = "error";
      log(`[${i + 1}/${items.length}] ⚠️ Lỗi kết nối NLS ${item.filename}: ${err.message}`, "error");
    }

    const currentPct = Math.round(((i + 1) / items.length) * 100);
    progressBarFill.style.width = `${currentPct}%`;
    progressPercentage.textContent = `${currentPct}%`;
    updateStats();
    renderFilesTable();
  }

  progressBarFill.style.width = "100%";
  progressPercentage.textContent = "100%";
  progressLabel.textContent = `Hoàn tất xử lý NLS!`;

  const summaryMsg = `XỬ LÝ NĂNG LỰC SỐ HOÀN TẤT!\n\n` +
    `• Tổng số file: ${overallStats.total}\n` +
    `• 🟢 Đã có NLS đầy đủ (giữ nguyên): ${overallStats.already_integrated} file\n` +
    `• 🟣 Đã tích hợp NLS mới (tô đỏ): ${overallStats.integrated} file\n` +
    `• 🟡 Cần giáo viên kiểm tra: ${overallStats.need_review} file\n` +
    `• 🔴 Lỗi: ${overallStats.error} file\n\n` +
    (lastOutDir && lastOutDir !== "inplace" ? `Thư mục kết quả: ${lastOutDir}` : "");

  alert(summaryMsg);
  if (lastOutDir && lastOutDir !== "inplace") {
    log(`📁 Kết quả lưu tại: ${lastOutDir}`, "info");
  }

  if (btnBatchNlsMaster) btnBatchNlsMaster.disabled = false;
  if (btnToolbarNls) btnToolbarNls.disabled = false;
  if (btnBatchProcess) btnBatchProcess.disabled = false;
}

async function openNlsModal(idx) {
  currentNlsFileIndex = idx;
  const file = scannedFiles[idx];
  if (!file) return;

  modalNlsDetail.classList.remove("hidden");
  nlsModalFilename.textContent = file.filename;
  nlsModalLoading.classList.remove("hidden");
  nlsModalContent.innerHTML = "";

  try {
    const res = await fetch("/api/nls/audit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        file_path: file.file_path,
        subject: cfgSubject ? cfgSubject.value : "Tin học",
        grade: cfgClasses ? cfgClasses.value : "9",
        lesson_title: file.bai_name || (file.lesson_info ? file.lesson_info.bai_title : "")
      })
    });

    const json = await res.json();
    nlsModalLoading.classList.add("hidden");

    if (json.success) {
      const r = json.result || {};
      const status = r.status || "not_integrated";

      // Cập nhật badge
      if (status === "already_integrated") {
        nlsModalBadge.className = "badge badge-success";
        nlsModalBadge.textContent = "🟢 Đã có NLS đầy đủ";
      } else if (status === "integrated" || status === "not_integrated") {
        nlsModalBadge.className = "badge badge-accent";
        nlsModalBadge.textContent = "🟣 Sẵn sàng tích hợp";
      } else if (status === "need_review") {
        nlsModalBadge.className = "badge badge-warning";
        nlsModalBadge.textContent = "🟡 Cần kiểm tra";
      } else {
        nlsModalBadge.className = "badge badge-error";
        nlsModalBadge.textContent = "🔴 Lỗi";
      }

      // Lưu vào file hiện tại
      file.nls_status = status;
      file.nls_codes = r.detected_codes || [];
      file.nls_message = r.message;
      renderFilesTable();

      const plan = r.plan || {};
      const objs = plan.nls_objectives || [];
      const rows = plan.nls_table_rows || [];

      let objsHtml = "";
      if (objs.length > 0) {
        objsHtml = objs.map(o => `
          <div style="margin-bottom: 6px; padding: 8px 12px; background: rgba(239, 68, 68, 0.08); border-left: 3px solid #ef4444; border-radius: 4px;">
            <strong style="color: #ef4444;">${escapeHtml(o.code || '')}</strong>: ${escapeHtml(o.text || '')}
          </div>
        `).join("");
      } else {
        objsHtml = `<div class="text-muted">Không có mục tiêu NLS mới cần bổ sung (đã đầy đủ hoặc không phù hợp).</div>`;
      }

      let rowsHtml = "";
      if (rows.length > 0) {
        rowsHtml = `
          <div style="margin-top: 14px;">
            <h4 style="font-size: 14px; font-weight: 700; margin-bottom: 8px; color: #ef4444;">📋 Bảng Phân Tích Phát Triển NLS Cho Học Sinh (Sẽ được bổ sung chữ đỏ):</h4>
            <table class="data-table" style="font-size: 12.5px;">
              <thead>
                <tr>
                  <th width="40">TT</th>
                  <th width="180">Tên Hoạt Động</th>
                  <th>Tổ Chức Dạy Học</th>
                  <th width="160">Mã NLS</th>
                </tr>
              </thead>
              <tbody>
                ${rows.map(rw => `
                  <tr>
                    <td class="text-center font-bold" style="color: #ef4444;">${escapeHtml(rw.tt)}</td>
                    <td style="color: #ef4444;">${escapeHtml(rw.ten_hoat_dong)}</td>
                    <td style="color: #ef4444;">${escapeHtml(rw.to_chuc_day_hoc)}</td>
                    <td class="font-mono font-bold" style="color: #ef4444;">${escapeHtml(rw.nang_luc_so)}</td>
                  </tr>
                `).join("")}
              </tbody>
            </table>
          </div>
        `;
      }

      nlsModalContent.innerHTML = `
        <div style="background: rgba(30, 41, 59, 0.5); padding: 14px; border-radius: 8px; margin-bottom: 16px;">
          <div style="font-size: 14px; font-weight: 600; margin-bottom: 6px;">💡 Nhận định sư phạm của AI:</div>
          <p style="color: #cbd5e1; margin: 0; line-height: 1.5;">${escapeHtml(r.message || r.reason || '')}</p>
          ${r.detected_codes && r.detected_codes.length > 0 ? `<div style="margin-top: 8px; font-size: 12px; color: #34d399;">✓ Mã NLS phát hiện trong tài liệu: <strong>${r.detected_codes.join(', ')}</strong></div>` : ''}
        </div>

        <div style="margin-bottom: 12px;">
          <h4 style="font-size: 14px; font-weight: 700; margin-bottom: 6px; color: #ef4444;">🎯 Mục tiêu 2.3. Các NLS được phát triển:</h4>
          ${objsHtml}
        </div>

        ${plan.device_addition ? `
          <div style="margin-bottom: 14px; padding: 8px 12px; background: rgba(59, 130, 246, 0.1); border-radius: 6px;">
            <strong>🖥️ Thiết bị dạy học bổ sung:</strong> <span style="color: #ef4444;">${escapeHtml(plan.device_addition)}</span>
          </div>
        ` : ''}

        ${rowsHtml}
      `;
    } else {
      nlsModalContent.innerHTML = `<div class="text-error">Lỗi phân tích: ${escapeHtml(json.error)}</div>`;
    }
  } catch (err) {
    nlsModalLoading.classList.add("hidden");
    nlsModalContent.innerHTML = `<div class="text-error">Lỗi kết nối: ${escapeHtml(err.message)}</div>`;
  }
}

async function applySingleNls(idx) {
  const file = scannedFiles[idx];
  if (!file) return;

  log(`🎯 Đang tích hợp NLS cho file: "${file.filename}"...`, "info");
  try {
    const res = await fetch("/api/nls/integrate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        file_path: file.file_path,
        subject: cfgSubject ? cfgSubject.value : "Tin học",
        grade: cfgClasses ? cfgClasses.value : "9",
        lesson_title: file.bai_name || (file.lesson_info ? file.lesson_info.bai_title : ""),
        highlight_red: optNlsRed ? optNlsRed.checked : true
      })
    });

    const json = await res.json();
    if (json.success && json.result) {
      const r = json.result;
      file.nls_status = r.status;
      file.nls_codes = r.detected_codes || [];
      file.added_codes = r.added_codes || [];
      file.nls_message = r.message;
      renderFilesTable();
      updateStats();

      log(`✅ ${r.filename}: ${r.message}`, "success");
      alert(r.message);
    } else {
      alert(`Lỗi: ${json.error}`);
    }
  } catch (err) {
    alert(`Lỗi kết nối: ${err.message}`);
  }
}

// 18. KHGD (Kế Hoạch Giáo Dục Trường) Functions
async function loadKhgdStatus() {
  try {
    const res = await fetch("/api/khgd/status");
    const json = await res.json();
    if (json.success) {
      if (json.has_cache && json.cache) {
        currentKhgdData = json.cache;
        if (khgdSourceBadge) {
          khgdSourceBadge.className = "badge badge-success";
          khgdSourceBadge.textContent = `✓ ${json.cache.source_file || 'Đã nạp'}`;
        }
        const currentGrade = selectKhgdGrade ? selectKhgdGrade.value : "9";
        renderKhgdTable(currentGrade);
      } else {
        // Nếu chưa có cache nhưng có file có sẵn trong thư mục, tự động phân tích
        if (json.available_files && json.available_files.length > 0) {
          const defaultFile = json.available_files[0].path;
          parseKhgd(defaultFile);
        } else {
          if (khgdSourceBadge) {
            khgdSourceBadge.className = "badge badge-warning";
            khgdSourceBadge.textContent = "Chưa có file KHGD";
          }
        }
      }
    }
  } catch (e) {
    console.error("Lỗi tải trạng thái KHGD:", e);
  }
}

function renderKhgdTable(grade = "9") {
  if (!tableKhgdBody) return;
  if (!currentKhgdData || !currentKhgdData.grades) {
    tableKhgdBody.innerHTML = `<tr><td colspan="5" class="text-center py-6 text-muted">Chưa có dữ liệu Kế hoạch giáo dục. Vui lòng bấm "Phân Tích Lại KHGD" hoặc tải lên file mới.</td></tr>`;
    return;
  }

  const gradeKey = String(grade).trim();
  let gradeInfo = currentKhgdData.grades[gradeKey];
  if (!gradeInfo) {
    for (const [k, v] of Object.entries(currentKhgdData.grades)) {
      if (k.includes(gradeKey)) {
        gradeInfo = v;
        break;
      }
    }
  }

  if (!gradeInfo || !gradeInfo.lessons || gradeInfo.lessons.length === 0) {
    tableKhgdBody.innerHTML = `<tr><td colspan="5" class="text-center py-6 text-muted">Không tìm thấy dữ liệu bài học cho Lớp ${grade}.</td></tr>`;
    return;
  }

  const lessons = gradeInfo.lessons;
  tableKhgdBody.innerHTML = "";

  lessons.forEach((item, idx) => {
    const tr = document.createElement("tr");
    
    // Format YCCĐ bullets
    let yccdHtml = "";
    if (item.yccd_bullets && item.yccd_bullets.length > 0) {
      yccdHtml = item.yccd_bullets.map(b => `<div style="margin-bottom: 3px; line-height: 1.4;">${escapeHtml(b)}</div>`).join("");
    } else {
      yccdHtml = `<span class="text-muted">${escapeHtml(item.yccd_raw || 'Chưa có')}</span>`;
    }

    tr.innerHTML = `
      <td class="text-center font-bold">${escapeHtml(item.stt || idx + 1)}</td>
      <td class="text-center font-mono font-bold" style="color: #6366f1;">Bài ${escapeHtml(item.bai_num || '?')}</td>
      <td>
        <div class="font-bold">${escapeHtml(item.ten_bai || '')}</div>
        ${item.chu_de ? `<div class="text-xs text-muted" style="margin-top: 2px;">${escapeHtml(item.chu_de)}</div>` : ''}
      </td>
      <td class="text-center font-mono text-sm">${escapeHtml(item.so_tiet || '')}</td>
      <td style="font-size: 13px;">${yccdHtml}</td>
    `;
    tableKhgdBody.appendChild(tr);
  });
}

async function parseKhgd(filePath = "") {
  if (btnParseKhgd) {
    btnParseKhgd.disabled = true;
    btnParseKhgd.innerHTML = `<span class="spinner"></span> Đang phân tích...`;
  }
  log(`🏫 Đang phân tích Kế hoạch giáo dục trường (Tin học 6, 7, 8, 9)...`, "info");

  try {
    const res = await fetch("/api/khgd/parse", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file_path: filePath })
    });

    const json = await res.json();
    if (json.success && json.data) {
      currentKhgdData = json.data;
      if (khgdSourceBadge) {
        khgdSourceBadge.className = "badge badge-success";
        khgdSourceBadge.textContent = `✓ ${json.data.source_file || 'Đã phân tích'}`;
      }
      const currentGrade = selectKhgdGrade ? selectKhgdGrade.value : "9";
      renderKhgdTable(currentGrade);
      log(`✅ ${json.message}`, "success");
      alert(json.message);
    } else {
      log(`❌ Lỗi phân tích KHGD: ${json.error}`, "error");
      alert(`Lỗi: ${json.error}`);
    }
  } catch (err) {
    log(`❌ Lỗi kết nối khi phân tích KHGD: ${err.message}`, "error");
    alert(`Lỗi: ${err.message}`);
  } finally {
    if (btnParseKhgd) {
      btnParseKhgd.disabled = false;
      btnParseKhgd.innerHTML = `⚡ Phân Tích Lại KHGD`;
    }
  }
}

async function uploadKhgdFile(fileObj) {
  if (!fileObj) return;
  const formData = new FormData();
  formData.append("file", fileObj);

  if (btnUploadKhgd) {
    btnUploadKhgd.disabled = true;
    btnUploadKhgd.innerHTML = `<span class="spinner"></span> Đang tải lên...`;
  }
  log(`📤 Đang tải lên và phân tích file KHGD: ${fileObj.name}...`, "info");

  try {
    const res = await fetch("/api/khgd/upload", {
      method: "POST",
      body: formData
    });

    const json = await res.json();
    if (json.success && json.data) {
      currentKhgdData = json.data;
      if (khgdSourceBadge) {
        khgdSourceBadge.className = "badge badge-success";
        khgdSourceBadge.textContent = `✓ ${json.data.source_file}`;
      }
      const currentGrade = selectKhgdGrade ? selectKhgdGrade.value : "9";
      renderKhgdTable(currentGrade);
      log(`✅ ${json.message}`, "success");
      alert(json.message);
    } else {
      log(`❌ Lỗi tải file KHGD: ${json.error}`, "error");
      alert(`Lỗi: ${json.error}`);
    }
  } catch (err) {
    log(`❌ Lỗi kết nối tải file: ${err.message}`, "error");
    alert(`Lỗi: ${err.message}`);
  } finally {
    if (btnUploadKhgd) {
      btnUploadKhgd.disabled = false;
      btnUploadKhgd.innerHTML = `📤 Tải Lên KHGD Mới (.doc, .docx)`;
    }
  }
}

// Open NLS output folder
async function openNlsFolder() {
  const currentPath = (inputFolderPath && inputFolderPath.value.trim()) ? inputFolderPath.value.trim() : "";
  const targetFolder = currentPath ? (currentPath + "_NLS") : "output_khbd_nls";
  try {
    const res = await fetch("/api/open_folder", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: targetFolder })
    });
    const json = await res.json();
    if (json.success) {
      log(`Đã mở thư mục NLS: ${json.path}`, "info");
    } else {
      log(`Không thể mở thư mục NLS: ${json.error}`, "warning");
    }
  } catch (err) {
    log(`Lỗi khi mở thư mục NLS: ${err.message}`, "error");
  }
}

// Event Listeners Setup
function setupEventListeners() {
  // Tab switching (Always initialize first so navigation is 100% responsive)
  if (tabBtns && tabBtns.length > 0) {
    tabBtns.forEach(btn => {
      btn.addEventListener("click", () => {
        const targetId = btn.dataset.tab;
        tabBtns.forEach(b => b.classList.remove("active"));
        tabPanels.forEach(p => p.classList.remove("active"));
        btn.classList.add("active");
        const targetPanel = document.getElementById(targetId);
        if (targetPanel) {
          targetPanel.classList.add("active");
        }
      });
    });
  }

  // Buttons
  if (btnScan) btnScan.addEventListener("click", scanFolder);
  if (btnOpenExplorer) btnOpenExplorer.addEventListener("click", openFolderInExplorer);
  if (btnBatchProcess) btnBatchProcess.addEventListener("click", () => processBatch());
  if (btnFastRename) btnFastRename.addEventListener("click", () => runFastRename());
  if (btnClearLog) btnClearLog.addEventListener("click", () => { if (terminalBody) terminalBody.innerHTML = ""; });

  // Beekone AI Buttons
  if (btnBatchAiFix) btnBatchAiFix.addEventListener("click", runBeekoneAiBatch);
  if (btnQuickAiFix) btnQuickAiFix.addEventListener("click", runBeekoneAiQuickEdit);
  if (btnTestAi) btnTestAi.addEventListener("click", testBeekoneAiConnection);
  if (btnToggleKeyVis && cfgAiKey) {
    btnToggleKeyVis.addEventListener("click", () => {
      cfgAiKey.type = cfgAiKey.type === "password" ? "text" : "password";
    });
  }

  // NLS Buttons
  if (btnBatchNlsMaster) btnBatchNlsMaster.addEventListener("click", () => runBatchNls());
  if (btnToolbarNls) btnToolbarNls.addEventListener("click", () => runBatchNls());
  if (btnOpenNlsFolder) btnOpenNlsFolder.addEventListener("click", openNlsFolder);
  if (btnCloseNlsModal) btnCloseNlsModal.addEventListener("click", () => modalNlsDetail && modalNlsDetail.classList.add("hidden"));
  if (btnCloseNlsOk) btnCloseNlsOk.addEventListener("click", () => modalNlsDetail && modalNlsDetail.classList.add("hidden"));
  if (btnNlsApplySingle) {
    btnNlsApplySingle.addEventListener("click", () => {
      if (currentNlsFileIndex >= 0) {
        if (modalNlsDetail) modalNlsDetail.classList.add("hidden");
        applySingleNls(currentNlsFileIndex);
      }
    });
  }

  // Dropdown changes
  if (selectPpctFile) {
    selectPpctFile.addEventListener("change", (e) => {
      syncSubjectAndGradeFromSelectedPpct();
      loadPpctTableData(e.target.value);
      updateLivePreview();
      updateLiveNamingPreview();
      updateAllTargetFilenames();
      saveNamingConfigToServer();
      if (inputFolderPath.value.trim()) {
        scanFolder();
      }
    });
  }

  // Step 1: Grade & Subject & SMAS Sync & PPCT
  if (selectMainGrade && cfgClasses) {
    selectMainGrade.addEventListener("change", () => {
      cfgClasses.value = selectMainGrade.value;
      const curSubject = selectMainSubject ? selectMainSubject.value : (cfgSubject ? cfgSubject.value : "Tin học");
      const picked = autoSelectPpctForSubjectGrade(curSubject, selectMainGrade.value, true);
      if (picked) {
        log(`Đã chọn Khối ${selectMainGrade.value} ➔ Khớp PPCT: "${picked}"`, "info");
      }
      updateLivePreview();
      updateLiveNamingPreview();
      updateAllTargetFilenames();
      saveNamingConfigToServer();
      if (inputFolderPath.value.trim()) {
        scanFolder();
      }
    });
  }

  if (selectMainSubject && cfgSubject) {
    selectMainSubject.addEventListener("change", () => {
      cfgSubject.value = selectMainSubject.value;
      const curGrade = selectMainGrade ? selectMainGrade.value : (cfgClasses ? cfgClasses.value : "9");
      const picked = autoSelectPpctForSubjectGrade(selectMainSubject.value, curGrade, true);
      if (picked) {
        log(`Đã chuyển môn sang "${selectMainSubject.value}" ➔ Tự động gán PPCT: "${picked}"`, "success");
      }
      updateLivePreview();
      updateLiveNamingPreview();
      updateAllTargetFilenames();
      saveNamingConfigToServer();
      if (inputFolderPath.value.trim()) {
        scanFolder();
      }
    });
  }

  // Đồng bộ hai chiều từ Tab 2 (Giao diện trực quan) sang Step 1 và bộ PPCT
  if (cfgSubject) {
    cfgSubject.addEventListener("input", () => {
      const val = cfgSubject.value.trim();
      if (selectMainSubject) {
        let matched = false;
        for (let i = 0; i < selectMainSubject.options.length; i++) {
          const optV = selectMainSubject.options[i].value;
          const optT = selectMainSubject.options[i].text;
          if (optV === val || optV.toLowerCase() === val.toLowerCase() || optT.includes(val)) {
            selectMainSubject.selectedIndex = i;
            matched = true;
            break;
          }
        }
        if (!matched && val) {
          const newOpt = document.createElement("option");
          newOpt.value = val;
          newOpt.textContent = val;
          newOpt.selected = true;
          selectMainSubject.appendChild(newOpt);
        }
      }
      const curGrd = selectMainGrade ? selectMainGrade.value : (cfgClasses ? cfgClasses.value : "9");
      autoSelectPpctForSubjectGrade(val, curGrd, true);
      updateLivePreview();
      updateLiveNamingPreview();
      updateAllTargetFilenames();
      saveNamingConfigToServer();
    });
  }

  if (cfgClasses) {
    cfgClasses.addEventListener("input", () => {
      const val = cfgClasses.value.trim();
      const numOnly = val.replace(/\D/g, "");
      if (selectMainGrade && numOnly) {
        for (let i = 0; i < selectMainGrade.options.length; i++) {
          if (selectMainGrade.options[i].value === numOnly) {
            selectMainGrade.selectedIndex = i;
            break;
          }
        }
      }
      const curSub = selectMainSubject ? selectMainSubject.value : (cfgSubject ? cfgSubject.value : "Tin học");
      autoSelectPpctForSubjectGrade(curSub, numOnly || val, true);
      updateLivePreview();
      updateLiveNamingPreview();
      updateAllTargetFilenames();
      saveNamingConfigToServer();
    });
  }

  if (btnQuickSyncSmas) {
    btnQuickSyncSmas.addEventListener("click", async () => {
      btnQuickSyncSmas.disabled = true;
      btnQuickSyncSmas.innerHTML = `<span class="spinner"></span> Đang đồng bộ...`;
      const curSub = selectMainSubject ? selectMainSubject.value : (cfgSubject ? cfgSubject.value : "Tin học");
      const curGrd = selectMainGrade ? selectMainGrade.value : (cfgClasses ? cfgClasses.value : "9");
      log(`⚡ Đang đồng bộ TKB & PPCT từ SMAS cho môn "${curSub}" Khối ${curGrd}...`, "info");
      try {
        // Tải PPCT động cho môn/khối được chọn nếu có
        try {
          await fetch("/api/smas/fetch-subject-ppct", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ subject: curSub, grade: curGrd, className: curGrd })
          });
        } catch (e) {}

        const res = await fetch("/api/smas/refresh-ppct", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({})
        });
        const json = await res.json();
        if (json.success) {
          if (smasQuickStatus) {
            smasQuickStatus.textContent = "🟢 Đã đồng bộ SMAS";
            smasQuickStatus.style.color = "#10b981";
          }
          log(`✅ ${json.message || "Đã đồng bộ thành công từ SMAS!"}`, "success");
          await fetchPpctFiles();
          autoSelectPpctForSubjectGrade(curSub, curGrd, true);
          if (scannedFiles.length > 0 || inputFolderPath.value.trim()) {
            scanFolder();
          }
        } else {
          log(`⚠️ SMAS: ${json.error}`, "warning");
        }
      } catch (err) {
        log(`Lỗi kết nối SMAS: ${err.message}`, "error");
      } finally {
        btnQuickSyncSmas.disabled = false;
        btnQuickSyncSmas.innerHTML = `<span class="pulse-dot"></span> <span>⚡ Đồng Bộ Ngay Từ SMAS</span>`;
      }
    });
  }

  if (linkViewPpctQuick) {
    linkViewPpctQuick.addEventListener("click", () => {
      const ppctTabBtn = document.querySelector(`.tab-btn[data-tab="tab-ppct"]`);
      if (ppctTabBtn) ppctTabBtn.click();
    });
  }

  if (linkMoreConfig) {
    linkMoreConfig.addEventListener("click", () => {
      const configTabBtn = document.querySelector(`.tab-btn[data-tab="tab-config"]`);
      if (configTabBtn) configTabBtn.click();
    });
  }

  // Step 2: Naming Scheme & Live Synchronized Table Update
  if (selectNamingScheme) {
    selectNamingScheme.addEventListener("change", (e) => {
      const val = e.target.value;
      if (val === "vietnamese_standard") {
        if (inputCustomPattern) inputCustomPattern.value = "Tuần {tuan} - Tiết {tiet} - Bài {bai_num} - {ten_bai}.docx";
      } else if (val === "vietnamese_simple") {
        if (inputCustomPattern) inputCustomPattern.value = "{mon_short} {lop} - Tuần {tuan} - Tiết {tiet} - {ten_bai}.docx";
      } else if (val === "period_lesson") {
        if (inputCustomPattern) inputCustomPattern.value = "Tiết {tiet} - {ten_bai}.docx";
      } else if (val === "ppct_slug") {
        if (inputCustomPattern) inputCustomPattern.value = "{mon_code}{grade}_tuan{week}_Bai{bai_str}_{slug_name}_Tiet{period}.docx";
      } else if (val === "teacher") {
        if (inputCustomPattern) inputCustomPattern.value = "{teacher}_{mon_short} {grade}_Tuan {week}_Bai {bai_str}.docx";
      }
      if (wrapCustomPattern) {
        wrapCustomPattern.classList.toggle("hidden", val !== "custom");
      }
      updateLiveNamingPreview();
      updateAllTargetFilenames();
      saveNamingConfigToServer();
    });
  }

  if (inputCustomPattern) {
    inputCustomPattern.addEventListener("input", () => {
      if (selectNamingScheme) selectNamingScheme.value = "custom";
      updateLiveNamingPreview();
      updateAllTargetFilenames();
      saveNamingConfigToServer();
    });
  }

  if (namingChips) {
    namingChips.forEach(chip => {
      chip.addEventListener("click", () => {
        const tag = chip.dataset.tag;
        if (!tag || !inputCustomPattern) return;
        const start = inputCustomPattern.selectionStart || inputCustomPattern.value.length;
        const end = inputCustomPattern.selectionEnd || inputCustomPattern.value.length;
        const text = inputCustomPattern.value;
        inputCustomPattern.value = text.slice(0, start) + tag + text.slice(end);
        inputCustomPattern.focus();
        inputCustomPattern.setSelectionRange(start + tag.length, start + tag.length);
        if (selectNamingScheme) selectNamingScheme.value = "custom";
        updateLiveNamingPreview();
        updateAllTargetFilenames();
        saveNamingConfigToServer();
      });
    });
  }

  // Step 3: Quick Toggles & Signers Synchronization
  if (cfgQuickSignerDept && cfgSignerDept) {
    cfgQuickSignerDept.addEventListener("input", () => {
      cfgSignerDept.value = cfgQuickSignerDept.value;
      updateLivePreview();
      saveNamingConfigToServer();
    });
    cfgSignerDept.addEventListener("input", () => {
      cfgQuickSignerDept.value = cfgSignerDept.value;
    });
  }

  if (cfgQuickTeacher && cfgTeacherName) {
    cfgQuickTeacher.addEventListener("input", () => {
      cfgTeacherName.value = cfgQuickTeacher.value;
      updateLivePreview();
      updateLiveNamingPreview();
      updateAllTargetFilenames();
      saveNamingConfigToServer();
    });
    cfgTeacherName.addEventListener("input", () => {
      cfgQuickTeacher.value = cfgTeacherName.value;
      updateLiveNamingPreview();
    });
  }

  if (cfgOptFormat5512Quick && cfgOptFormat5512) {
    cfgOptFormat5512Quick.addEventListener("change", () => {
      cfgOptFormat5512.checked = cfgOptFormat5512Quick.checked;
      updateLivePreview();
      saveConfigForm();
    });
    cfgOptFormat5512.addEventListener("change", () => {
      cfgOptFormat5512Quick.checked = cfgOptFormat5512.checked;
    });
  }

  // Live Visual A4 Sheet Synchronization Listeners
  const visualInputs = [
    cfgTeacherName, cfgSchoolName, cfgDepartment, cfgSchoolYear,
    cfgSubject, cfgSubjectType, cfgClasses, cfgTeachingDate, cfgDuration, cfgTitlePrefix,
    cfgTitleSignerSchool, cfgSignerSchool, cfgTitleSignerDept, cfgSignerDept
  ];
  visualInputs.forEach(inp => {
    if (inp) {
      inp.addEventListener("input", updateLivePreview);
      inp.addEventListener("change", updateLivePreview);
    }
  });

  const visualCheckboxes = [cfgOptHeader, cfgOptFooter, cfgOptApproval, cfgOptBorder, cfgAutoDate, cfgOptFormat5512, cfgOptAutofitTable];
  if (cfgOptAutofitTable && cfgOptAutofitTableQuick) {
    cfgOptAutofitTable.addEventListener("change", () => {
      cfgOptAutofitTableQuick.checked = cfgOptAutofitTable.checked;
    });
    cfgOptAutofitTableQuick.addEventListener("change", () => {
      cfgOptAutofitTable.checked = cfgOptAutofitTableQuick.checked;
    });
  }
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

  if (editPpctSelect) {
    editPpctSelect.addEventListener("change", (e) => {
      const itemIndex = parseInt(e.target.value, 10);
      if (!isNaN(itemIndex) && activePpctItems && activePpctItems[itemIndex]) {
        const it = activePpctItems[itemIndex];
        if (it.tuan !== null && it.tuan !== undefined) editWeek.value = it.tuan;
        if (it.tiet !== null && it.tiet !== undefined) editPeriods.value = it.tiet;
        if (it.ten_bai) editLessonName.value = it.ten_bai;
        if (it.ngay_day) editTeachingDate.value = it.ngay_day;
        else if (it.tuan) {
          const sDate = cfgStartDate ? cfgStartDate.value : "2026-09-07";
          const dFmt = cfgDateFormat ? cfgDateFormat.value : "smas_exact";
          const calc = calculateWeekDates(it.tuan, sDate, dFmt);
          if (calc) editTeachingDate.value = calc;
        }

        if (currentEditingIndex >= 0 && scannedFiles[currentEditingIndex]) {
          const tempFile = {
            ...scannedFiles[currentEditingIndex],
            week: editWeek.value,
            periods: editPeriods.value,
            bai_name: editLessonName.value,
            teaching_date: editTeachingDate.value,
            matched_ppct: it
          };
          editTargetFilename.value = computeTargetFilename(tempFile);
        }
      }
    });
  }

  // Live Auto-recalc filename when editing week/period/name in modal
  [editWeek, editPeriods, editLessonName].forEach(inp => {
    if (inp) {
      inp.addEventListener("input", () => {
        if (currentEditingIndex >= 0 && scannedFiles[currentEditingIndex]) {
          const tempFile = {
            ...scannedFiles[currentEditingIndex],
            week: editWeek.value,
            periods: editPeriods.value,
            bai_name: editLessonName.value,
            teaching_date: editTeachingDate ? editTeachingDate.value : ""
          };
          editTargetFilename.value = computeTargetFilename(tempFile);
        }
      });
    }
  });

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
  if (checkSelectAll) {
    checkSelectAll.addEventListener("change", (e) => {
      if (e.target.checked) {
        selectedFileIndices = new Set(scannedFiles.map((_, idx) => idx));
      } else {
        selectedFileIndices.clear();
      }
      renderFilesTable();
      updateStats();
    });
  }

  // Search input
  if (inputSearchFile) inputSearchFile.addEventListener("input", renderFilesTable);

  // PPCT Search
  if (inputSearchPpct) {
    inputSearchPpct.addEventListener("input", (e) => {
      const q = e.target.value.toLowerCase();
      document.querySelectorAll("#table-ppct-body tr").forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(q) ? "" : "none";
      });
    });
  }

  // Theme toggle
  if (btnThemeToggle) btnThemeToggle.addEventListener("click", toggleTheme);

  // Modals
  if (btnCloseModal) btnCloseModal.addEventListener("click", () => modalDiff && modalDiff.classList.add("hidden"));
  if (btnModalCancel) btnModalCancel.addEventListener("click", () => modalDiff && modalDiff.classList.add("hidden"));
  if (btnModalProcessSingle) {
    btnModalProcessSingle.addEventListener("click", () => {
      if (currentDiffFile) {
        if (modalDiff) modalDiff.classList.add("hidden");
        processBatch([currentDiffFile]);
      }
    });
  }

  if (btnHelpModal) btnHelpModal.addEventListener("click", () => modalHelp && modalHelp.classList.remove("hidden"));
  if (btnCloseHelp) btnCloseHelp.addEventListener("click", () => modalHelp && modalHelp.classList.add("hidden"));
  if (btnHelpOk) btnHelpOk.addEventListener("click", () => modalHelp && modalHelp.classList.add("hidden"));

  // Forms
  if (btnSaveConfig) btnSaveConfig.addEventListener("click", saveConfigForm);
  if (btnSaveAi) btnSaveAi.addEventListener("click", saveAiConfig);

  // KHGD Listeners
  if (selectKhgdGrade) {
    selectKhgdGrade.addEventListener("change", (e) => {
      renderKhgdTable(e.target.value);
    });
  }
  if (btnUploadKhgd && inputKhgdFile) {
    btnUploadKhgd.addEventListener("click", () => inputKhgdFile.click());
    inputKhgdFile.addEventListener("change", (e) => {
      if (e.target.files && e.target.files[0]) {
        uploadKhgdFile(e.target.files[0]);
      }
    });
  }
  if (btnParseKhgd) {
    btnParseKhgd.addEventListener("click", () => parseKhgd());
  }
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

// Notification Toast Utility
function showToast(msg, type = "info") {
  log(msg, type);
  const toastContainer = document.getElementById("toast-container") || (() => {
    const el = document.createElement("div");
    el.id = "toast-container";
    el.style.cssText = "position: fixed; bottom: 20px; right: 20px; z-index: 9999; display: flex; flex-direction: column; gap: 8px;";
    document.body.appendChild(el);
    return el;
  })();
  const toast = document.createElement("div");
  const bg = type === "success" ? "#10b981" : type === "error" ? "#ef4444" : "#3b82f6";
  toast.style.cssText = `background: ${bg}; color: #fff; padding: 10px 18px; border-radius: 8px; box-shadow: 0 4px 14px rgba(0,0,0,0.3); font-size: 13.5px; font-weight: 500; transition: all 0.3s ease; opacity: 0; transform: translateY(10px);`;
  toast.textContent = msg;
  toastContainer.appendChild(toast);
  requestAnimationFrame(() => {
    toast.style.opacity = "1";
    toast.style.transform = "translateY(0)";
  });
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
window.showToast = showToast;

// ----------------- SMAS & TKB Tab Controller -----------------
let currentSmasPpctDb = {};
let currentSmasPayloadWeeks = [];

async function initSmasTab() {
  // Subtab switching
  const subtabBtns = document.querySelectorAll(".subtab-btn");
  const subtabPanels = document.querySelectorAll(".subtab-panel");
  subtabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.dataset.subtab;
      subtabBtns.forEach(b => b.classList.remove("active"));
      subtabPanels.forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      const targetPanel = document.getElementById(targetId);
      if (targetPanel) targetPanel.classList.add("active");
    });
  });

  const tokenInput = document.getElementById("smas-input-token");
  const tokenBadge = document.getElementById("smas-token-badge");
  const tokenMsg = document.getElementById("smas-token-msg");
  const btnCheckToken = document.getElementById("btn-smas-check-token");
  const btnLoadPpct = document.getElementById("btn-smas-load-ppct");
  const btnSyncPpctSmas = document.getElementById("btn-sync-ppct-from-smas");

  // Populate Token từ Cấu Hình Dùng Chung
  async function loadTokenAndCheck() {
    try {
      const res = await fetch("/api/smas/config");
      const json = await res.json();
      if (json.success && json.config) {
        const tok = json.config.bearerToken || currentConfig.token || currentConfig.bearerToken || "";
        if (tokenInput && tok) {
          tokenInput.value = tok;
        }
        // Cập nhật chip giáo viên & trường
        const teacherEl = document.getElementById("smas-stat-teacher");
        const schoolEl = document.getElementById("smas-stat-school");
        if (teacherEl && json.config.employeeName) teacherEl.textContent = json.config.employeeName;
        if (schoolEl && json.config.schoolYearCode) schoolEl.textContent = `TH&THCS Đăk Trôi (${json.config.schoolYearCode})`;

        if (tok && tokenBadge) {
          const checkRes = await fetch("/api/smas/check-token", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token: tok })
          });
          const checkJson = await checkRes.json();
          if (checkJson.valid) {
            tokenBadge.textContent = "🟢 Token Hoạt Động";
            tokenBadge.className = "badge badge-success";
            if (tokenMsg) tokenMsg.textContent = checkJson.message;
          } else {
            tokenBadge.textContent = "🔴 Token Hết Hạn";
            tokenBadge.className = "badge badge-danger";
            if (tokenMsg) tokenMsg.textContent = checkJson.message;
          }
        }
      }
    } catch (e) {
      console.warn("Lỗi nạp cấu hình SMAS:", e);
    }
  }

  // Nút Kiểm Tra & Đồng Bộ Token Toàn Hệ Thống
  if (btnCheckToken) {
    btnCheckToken.addEventListener("click", async () => {
      const tok = tokenInput ? tokenInput.value.trim() : "";
      if (!tok) {
        alert("Vui lòng dán Bearer Token vào ô văn bản!");
        return;
      }
      btnCheckToken.disabled = true;
      btnCheckToken.innerHTML = "⏳ Đang kiểm tra & đồng bộ...";
      try {
        const res = await fetch("/api/smas/token-sync", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token: tok })
        });
        const json = await res.json();
        if (json.success) {
          if (tokenBadge) {
            tokenBadge.textContent = "🟢 Token Hoạt Động";
            tokenBadge.className = "badge badge-success";
          }
          if (tokenMsg) tokenMsg.textContent = `✅ ${json.message}`;
          showToast(`Đã đồng bộ Token cho ${json.fullname} (${json.schoolYear}) dùng chung toàn hệ thống!`, "success");
          await fetchConfig();
          await fetchPpctFiles();
          await loadSmasPpctView();
        } else {
          if (tokenBadge) {
            tokenBadge.textContent = "🔴 Lỗi Token";
            tokenBadge.className = "badge badge-danger";
          }
          showToast(json.error || "Token không hợp lệ", "error");
        }
      } catch (err) {
        showToast(`Lỗi kết nối: ${err.message}`, "error");
      } finally {
        btnCheckToken.disabled = false;
        btnCheckToken.innerHTML = "⚡ Kiểm Tra & Đồng Bộ Hồ Sơ Giáo Viên";
      }
    });
  }

  // Tải mới toàn bộ PPCT từ SMAS
  const handleRefreshPpct = async (btn) => {
    if (btn) btn.disabled = true;
    showToast("Đang kết nối SMAS tải mới toàn bộ PPCT...", "info");
    try {
      const res = await fetch("/api/smas/refresh-ppct", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({})
      });
      const data = await res.json();
      if (data.success) {
        showToast(data.message || "Đã đồng bộ PPCT từ SMAS thành công!", "success");
        await fetchPpctFiles();
        await loadSmasPpctView();
      } else {
        showToast(data.error || "Không thể đồng bộ PPCT từ SMAS", "error");
      }
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      if (btn) btn.disabled = false;
    }
  };

  if (btnLoadPpct) btnLoadPpct.addEventListener("click", () => handleRefreshPpct(btnLoadPpct));
  if (btnSyncPpctSmas) btnSyncPpctSmas.addEventListener("click", () => handleRefreshPpct(btnSyncPpctSmas));

  // Tải và hiển thị Thời Khóa Biểu
  async function loadTkbSchedule() {
    const tbody = document.getElementById("smas-tkb-tbody");
    if (!tbody) return;
    try {
      const res = await fetch("/api/smas/schedule");
      const json = await res.json();
      const slots = json.slots || [];

      tbody.innerHTML = "";
      // Buổi Sáng: Tiết 1 - 5; Buổi Chiều: Tiết 1 - 4
      const periodsDef = [
        { section: 0, period: 1, label: "Sáng" },
        { section: 0, period: 2, label: "Sáng" },
        { section: 0, period: 3, label: "Sáng" },
        { section: 0, period: 4, label: "Sáng" },
        { section: 0, period: 5, label: "Sáng" },
        { section: 1, period: 1, label: "Chiều" },
        { section: 1, period: 2, label: "Chiều" },
        { section: 1, period: 3, label: "Chiều" },
        { section: 1, period: 4, label: "Chiều" }
      ];

      periodsDef.forEach(pd => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td class="text-center font-bold" style="background: rgba(255,255,255,0.02);">${pd.label}</td>
          <td class="text-center font-bold">${pd.period}</td>
        `;
        // Thứ 2 (1) -> Thứ 7 (6)
        for (let d = 1; d <= 6; d++) {
          const match = slots.find(s => Number(s.section) === pd.section && Number(s.period) === pd.period && Number(s.dayOfWeek) === d);
          const td = document.createElement("td");
          td.style.padding = "4px";
          if (match) {
            const isTin = (match.subjectName || "").includes("Tin");
            const bgClass = isTin ? "background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3);" : "background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.3);";
            td.innerHTML = `
              <div style="padding: 6px; border-radius: 6px; ${bgClass}">
                <div class="font-bold text-sm text-primary">${match.className}</div>
                <div class="text-xs text-muted">${match.subjectName}</div>
              </div>
            `;
          } else {
            td.innerHTML = `<div style="text-align: center; color: rgba(255,255,255,0.15); font-size: 11px;">-</div>`;
          }
          tr.appendChild(td);
        }
        tbody.appendChild(tr);
      });
    } catch (err) {
      console.warn("Lỗi nạp TKB:", err);
    }
  }

  // Tải và hiển thị PPCT DB Viewer
  async function loadSmasPpctView() {
    const selClass = document.getElementById("smas-select-ppct-class");
    const tbody = document.getElementById("smas-ppct-tbody");
    if (!selClass || !tbody) return;

    try {
      const res = await fetch("/api/smas/ppct-db");
      const json = await res.json();
      currentSmasPpctDb = json.ppct || {};
      const keys = Object.keys(currentSmasPpctDb);

      selClass.innerHTML = "";
      if (keys.length === 0) {
        selClass.innerHTML = `<option value="">(Chưa có PPCT, vui lòng bấm Tải PPCT)</option>`;
        tbody.innerHTML = `<tr><td colspan="4" class="text-center py-4 text-muted">Chưa có dữ liệu PPCT SMAS. Bấm "Tải PPCT Thật Từ SMAS" để cập nhật.</td></tr>`;
        return;
      }

      keys.forEach(k => {
        const item = currentSmasPpctDb[k];
        const opt = document.createElement("option");
        opt.value = k;
        opt.textContent = `Lớp ${item.className} - ${item.subjectName} (${item.totalCount} tiết)`;
        selClass.appendChild(opt);
      });

      function renderActivePpctTable(key) {
        const data = currentSmasPpctDb[key];
        tbody.innerHTML = "";
        if (!data || !data.lessons || data.lessons.length === 0) {
          tbody.innerHTML = `<tr><td colspan="4" class="text-center py-4 text-muted">Không có bài học nào.</td></tr>`;
          return;
        }
        data.lessons.forEach(l => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td class="text-center font-bold text-accent">${l.period}</td>
            <td class="text-center">Tuần ${l.weekNumber || 1}</td>
            <td class="font-semibold">${escapeHtml(l.name)}</td>
            <td class="font-mono text-xs text-muted">${l.id || ""}</td>
          `;
          tbody.appendChild(tr);
        });
      }

      selClass.onchange = (e) => renderActivePpctTable(e.target.value);
      if (keys.length > 0) renderActivePpctTable(keys[0]);

      const btnReload = document.getElementById("btn-smas-reload-ppct-view");
      if (btnReload) btnReload.onclick = () => loadSmasPpctView();
    } catch (err) {
      console.warn("Lỗi nạp PPCT viewer:", err);
    }
  }

  // Sinh và xem trước Lịch Báo Giảng
  const btnPreviewPayloads = document.getElementById("btn-smas-preview-payloads");
  const btnExecuteSync = document.getElementById("btn-smas-execute-sync");
  const previewSelect = document.getElementById("smas-preview-week-select");
  const previewTbody = document.getElementById("smas-preview-tbody");
  const previewCount = document.getElementById("smas-preview-weeks-count");

  if (btnPreviewPayloads) {
    btnPreviewPayloads.addEventListener("click", async () => {
      const startW = parseInt(document.getElementById("smas-sync-start-week")?.value || "1");
      const endW = parseInt(document.getElementById("smas-sync-end-week")?.value || "35");
      const startD = document.getElementById("smas-sync-start-date")?.value || "2026-09-07";

      btnPreviewPayloads.disabled = true;
      btnPreviewPayloads.innerHTML = "⏳ Đang sinh dữ liệu...";
      try {
        const res = await fetch("/api/smas/generate-payloads", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ startWeek: startW, endWeek: endW, startDate: startD })
        });
        const json = await res.json();
        if (json.success) {
          currentSmasPayloadWeeks = json.weeks || [];
          if (previewCount) previewCount.textContent = currentSmasPayloadWeeks.length;
          showToast(`Đã sinh xong dữ liệu cho ${currentSmasPayloadWeeks.length} tuần!`, "success");

          if (previewSelect) {
            previewSelect.innerHTML = "";
            currentSmasPayloadWeeks.forEach(w => {
              const opt = document.createElement("option");
              opt.value = w.weekNumber;
              opt.textContent = `Tuần ${w.weekNumber}: ${w.dateFrom} ➔ ${w.dateTo}`;
              previewSelect.appendChild(opt);
            });
            previewSelect.onchange = () => renderPreviewTable(parseInt(previewSelect.value));
          }
          if (currentSmasPayloadWeeks.length > 0) {
            renderPreviewTable(currentSmasPayloadWeeks[0].weekNumber);
          }
        }
      } catch (err) {
        showToast(err.message, "error");
      } finally {
        btnPreviewPayloads.disabled = false;
        btnPreviewPayloads.innerHTML = "👁️ Sinh Lịch & Xem Trước Chi Tiết";
      }
    });
  }

  function renderPreviewTable(weekNum) {
    if (!previewTbody) return;
    previewTbody.innerHTML = "";
    const wData = currentSmasPayloadWeeks.find(w => w.weekNumber === weekNum);
    if (!wData) return;

    const allDetails = [
      ...(wData.level02?.teachingScheduleDetails || []),
      ...(wData.level03?.teachingScheduleDetails || [])
    ];
    allDetails.sort((a, b) => (a.dayOfWeek - b.dayOfWeek) || (a.section - b.section) || (a.period - b.period));

    allDetails.forEach(d => {
      const dayNames = ["", "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"];
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="font-bold text-center">${dayNames[d.dayOfWeek] || d.dayOfWeek}</td>
        <td class="text-center font-mono text-accent">${d.dateStudy || ""}</td>
        <td class="text-center font-bold">${d.section === 0 ? "Sáng" : "Chiều"} - T${d.period}</td>
        <td class="font-bold text-primary">${d.className}</td>
        <td>${d.subjectName}</td>
        <td class="text-center font-bold text-accent">${d.distributeProgramPeriod}</td>
        <td class="font-semibold">${escapeHtml(d.distributeProgramName)}</td>
        <td class="text-muted text-xs">${escapeHtml(d.toolName || "")} (${d.totalTool || 1})</td>
      `;
      previewTbody.appendChild(tr);
    });
  }

  if (btnExecuteSync) {
    btnExecuteSync.addEventListener("click", async () => {
      if (currentSmasPayloadWeeks.length === 0) {
        alert("Vui lòng bấm 'Sinh Lịch & Xem Trước Chi Tiết' trước khi đồng bộ!");
        return;
      }
      const syncLevel = document.getElementById("smas-sync-level")?.value || "all";
      if (!confirm(`Bạn có chắc muốn ĐỒNG BỘ ${currentSmasPayloadWeeks.length} tuần Lịch Báo Giảng trực tiếp lên hệ thống SMAS?`)) return;

      btnExecuteSync.disabled = true;
      btnExecuteSync.innerHTML = "🚀 Đang gửi dữ liệu lên SMAS...";
      const logBox = document.getElementById("smas-sync-log-card");
      const logContent = document.getElementById("smas-sync-log-content");
      if (logBox) logBox.classList.remove("hidden");
      if (logContent) logContent.innerHTML = "Đang bắt đầu đồng bộ lên SMAS...<br>";

      try {
        const res = await fetch("/api/smas/sync", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ weeks: currentSmasPayloadWeeks, level: syncLevel })
        });
        const json = await res.json();
        if (json.success) {
          showToast("Đồng bộ Lịch Báo Giảng lên SMAS hoàn tất!", "success");
          if (logContent) {
            logContent.innerHTML += `<span style="color:#10b981;">✅ Đồng bộ thành công ${json.results?.length || 0} yêu cầu lên SMAS!</span><br>`;
          }
        } else {
          showToast(json.error || "Lỗi khi đồng bộ lên SMAS", "error");
        }
      } catch (err) {
        showToast(err.message, "error");
      } finally {
        btnExecuteSync.disabled = false;
        btnExecuteSync.innerHTML = "🚀 ĐỒNG BỘ TRỰC TIẾP LÊN SMAS";
      }
    });
  }

  // Khởi động nạp dữ liệu SMAS
  loadTokenAndCheck();
  loadTkbSchedule();
  loadSmasPpctView();
}

window.addEventListener("DOMContentLoaded", init);

