/**
 * SMAS Timetable & Lesson Plan Sync Module for editKHBD
 * Quản lý Token SMAS, TKB 19 tiết, PPCT thật từ SMAS và Đồng bộ Lịch Báo Giảng.
 */

(function () {
  let smasConfig = {};
  let smasSchedule = [];
  let smasPpctDb = {};
  let generatedWeeks = [];

  // Helper show notification toast
  function showSmasToast(message, type = "info") {
    if (typeof window.showToast === "function") {
      window.showToast(message, type);
    } else {
      console.log(`[SMAS ${type.toUpperCase()}] ${message}`);
    }
  }

  // 1. Chuyển đổi Sub-tabs trong tab-smas
  function initSubtabs() {
    const subtabBtns = document.querySelectorAll(".subtab-btn");
    const subtabPanels = document.querySelectorAll(".subtab-panel");

    subtabBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        const targetId = btn.getAttribute("data-subtab");
        subtabBtns.forEach((b) => b.classList.remove("active"));
        subtabPanels.forEach((p) => p.classList.remove("active"));

        btn.classList.add("active");
        const targetPanel = document.getElementById(targetId);
        if (targetPanel) {
          targetPanel.classList.add("active");
          if (targetId === "subtab-sync-smas") {
            if (generatedWeeks.length === 0) {
              generateAndPreviewPayloads(true);
            }
            setTimeout(() => {
              const card = document.getElementById("smas-preview-card");
              if (card) card.scrollIntoView({ behavior: "smooth", block: "start" });
            }, 120);
          }
        }
      });
    });
  }

  // 2. Load dữ liệu khởi tạo
  async function loadInitialSmasData() {
    try {
      // 1. Cấu hình SMAS
      const resCfg = await fetch("/api/smas/config");
      const dataCfg = await resCfg.json();
      if (dataCfg.success) {
        smasConfig = dataCfg.config || {};
        const tokInput = document.getElementById("smas-input-token");
        if (tokInput && smasConfig.bearerToken) {
          tokInput.value = smasConfig.bearerToken;
        }
        if (smasConfig.employeeName) {
          const el = document.getElementById("smas-stat-teacher");
          if (el) el.textContent = smasConfig.employeeName;
        }
        if (smasConfig.schoolYearStartDate) {
          const el = document.getElementById("smas-sync-start-date");
          if (el) el.value = smasConfig.schoolYearStartDate;
        }
      }

      // 2. Nạp Thời Khóa Biểu
      await loadScheduleData();

      // 3. Nạp PPCT DB
      await loadPpctDatabase();

      // 4. Kiểm tra Token
      if (smasConfig.bearerToken) {
        checkTokenStatus(smasConfig.bearerToken);
      } else {
        updateTokenBadge(false, "Chưa nhập Bearer Token");
      }
    } catch (err) {
      console.error("Lỗi khởi tạo SMAS module:", err);
    }
  }

  // 3. Quản lý Token & Trạng thái kết nối
  function updateTokenBadge(isValid, message) {
    const badge = document.getElementById("smas-token-badge");
    const msg = document.getElementById("smas-token-msg");
    if (!badge) return;

    if (isValid) {
      badge.className = "badge badge-success";
      badge.textContent = "✅ Đang kết nối SMAS";
      badge.style.background = "#10b981";
      badge.style.color = "#ffffff";
      if (msg) {
        msg.textContent = message || "Token hợp lệ!";
        msg.style.color = "#10b981";
      }
    } else {
      badge.className = "badge badge-danger";
      badge.textContent = "⚠️ Token chưa hợp lệ";
      badge.style.background = "#ef4444";
      badge.style.color = "#ffffff";
      if (msg) {
        msg.textContent = message || "Vui lòng dán Bearer Token từ F12";
        msg.style.color = "#ef4444";
      }
    }
  }

  async function checkTokenStatus(token) {
    try {
      const res = await fetch("/api/smas/check-token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: token })
      });
      const data = await res.json();
      updateTokenBadge(data.valid, data.message);
    } catch (e) {
      updateTokenBadge(false, "Không thể kết nối đến máy chủ SMAS");
    }
  }

  // 4. Nạp và Render Thời Khóa Biểu
  async function loadScheduleData() {
    try {
      const res = await fetch("/api/smas/schedule");
      const data = await res.json();
      if (data.success) {
        smasSchedule = data.slots || [];
        renderTimetableGrid(smasSchedule);
        updateScheduleStats(smasSchedule);
      }
    } catch (e) {
      console.error("Lỗi tải TKB:", e);
    }
  }

  function updateScheduleStats(slots) {
    let tinCount = 0;
    let gdtcCount = 0;
    let hdtnCount = 0;

    slots.forEach((s) => {
      const sub = s.subjectCode || "";
      if (sub === "1024" || sub === "1044") tinCount++;
      else if (sub === "1795") gdtcCount++;
      else if (sub === "1796") hdtnCount++;
    });

    const elTotal = document.getElementById("smas-stat-total");
    const elTin = document.getElementById("smas-stat-tin");
    const elGdtc = document.getElementById("smas-stat-gdtc");
    const elHdtn = document.getElementById("smas-stat-hdtn");

    if (elTotal) elTotal.textContent = slots.length;
    if (elTin) elTin.textContent = tinCount;
    if (elGdtc) elGdtc.textContent = gdtcCount;
    if (elHdtn) elHdtn.textContent = hdtnCount;
  }

  function renderTimetableGrid(slots) {
    const tbody = document.getElementById("smas-tkb-tbody");
    if (!tbody) return;

    // Slot map: key = `${section}_${period}_${dayOfWeek}`
    const slotMap = {};
    slots.forEach((s) => {
      const k = `${s.section}_${s.period}_${s.dayOfWeek}`;
      slotMap[k] = s;
    });

    let html = "";

    // Sáng: Tiết 1 - 5
    for (let p = 1; p <= 5; p++) {
      html += `<tr>`;
      if (p === 1) {
        html += `<td rowspan="5" class="font-bold text-center" style="background: #f8fafc; vertical-align: middle;">SÁNG</td>`;
      }
      html += `<td class="font-bold text-center" style="background: #f8fafc;">${p}</td>`;

      // Thứ 2 đến Thứ 7 (dayOfWeek 1 to 6)
      for (let d = 1; d <= 6; d++) {
        const slot = slotMap[`0_${p}_${d}`];
        if (slot) {
          let badgeClass = "smas-slot-tin";
          let icon = "💻";
          if (slot.subjectCode === "1795") {
            badgeClass = "smas-slot-gdtc";
            icon = "⚽";
          } else if (slot.subjectCode === "1796") {
            badgeClass = "smas-slot-hdtn";
            icon = "🎯";
          }
          html += `
            <td>
              <div class="smas-slot-badge ${badgeClass}" title="${slot.subjectName} - ${slot.gradeName}">
                <span>${icon} <strong>${slot.className}</strong></span>
                <span style="font-size: 0.75rem; opacity: 0.85;">${slot.subjectName}</span>
              </div>
            </td>`;
        } else {
          html += `<td><span class="smas-slot-empty">-</span></td>`;
        }
      }
      html += `</tr>`;
    }

    // Chiều: Tiết 1 - 4
    for (let p = 1; p <= 4; p++) {
      html += `<tr>`;
      if (p === 1) {
        html += `<td rowspan="4" class="font-bold text-center" style="background: #f8fafc; vertical-align: middle;">CHIỀU</td>`;
      }
      html += `<td class="font-bold text-center" style="background: #f8fafc;">${p}</td>`;

      for (let d = 1; d <= 6; d++) {
        const slot = slotMap[`1_${p}_${d}`];
        if (slot) {
          let badgeClass = "smas-slot-tin";
          let icon = "💻";
          if (slot.subjectCode === "1795") {
            badgeClass = "smas-slot-gdtc";
            icon = "⚽";
          } else if (slot.subjectCode === "1796") {
            badgeClass = "smas-slot-hdtn";
            icon = "🎯";
          }
          html += `
            <td>
              <div class="smas-slot-badge ${badgeClass}" title="${slot.subjectName} - ${slot.gradeName}">
                <span>${icon} <strong>${slot.className}</strong></span>
                <span style="font-size: 0.75rem; opacity: 0.85;">${slot.subjectName}</span>
              </div>
            </td>`;
        } else {
          html += `<td><span class="smas-slot-empty">-</span></td>`;
        }
      }
      html += `</tr>`;
    }

    tbody.innerHTML = html;
  }

  // 5. Nạp và hiển thị PPCT DB
  async function loadPpctDatabase() {
    try {
      const res = await fetch("/api/smas/ppct-db");
      const data = await res.json();
      if (data.success) {
        smasPpctDb = data.ppct || {};
        populatePpctDropdown(smasPpctDb);
      }
    } catch (e) {
      console.error("Lỗi tải PPCT DB:", e);
    }
  }

  function populatePpctDropdown(db) {
    const select = document.getElementById("smas-select-ppct-class");
    if (!select) return;

    select.innerHTML = "";
    const keys = Object.keys(db);
    keys.sort();

    keys.forEach((k) => {
      const item = db[k];
      const opt = document.createElement("option");
      opt.value = k;
      opt.textContent = `${item.className} - ${item.subjectName} (${item.lessons ? item.lessons.length : 0} tiết)`;
      select.appendChild(opt);
    });

    if (keys.length > 0) {
      select.value = keys[0];
      renderPpctTable(db[keys[0]]);
    }

    select.onchange = () => {
      const selKey = select.value;
      if (smasPpctDb[selKey]) {
        renderPpctTable(smasPpctDb[selKey]);
      }
    };
  }

  function renderPpctTable(group) {
    const tbody = document.getElementById("smas-ppct-tbody");
    if (!tbody) return;

    const lessons = (group && group.lessons) || [];
    if (lessons.length === 0) {
      tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted py-4">Chưa có bài học nào trong môn này</td></tr>`;
      return;
    }

    let html = "";
    lessons.forEach((les) => {
      html += `
        <tr>
          <td class="font-bold text-center">${les.period || ""}</td>
          <td class="text-center">${les.weekNumber ? "Tuần " + les.weekNumber : "-"}</td>
          <td class="font-semibold">${les.name || ""}</td>
          <td class="font-mono text-xs text-muted">${les.id || ""}</td>
        </tr>`;
    });
    tbody.innerHTML = html;
  }

  // 6. Xử lý Sinh Lịch Báo Giảng & Xem Trước
  async function generateAndPreviewPayloads(isSilent = false) {
    const startWeek = parseInt(document.getElementById("smas-sync-start-week")?.value || "1");
    const endWeek = parseInt(document.getElementById("smas-sync-end-week")?.value || "35");
    const startDate = document.getElementById("smas-sync-start-date")?.value || "2026-09-07";
    const statusMsg = document.getElementById("smas-sync-status-msg");

    if (startWeek > endWeek) {
      if (!isSilent) showSmasToast("Tuần bắt đầu không thể lớn hơn tuần kết thúc!", "warning");
      return;
    }

    if (statusMsg && !isSilent) statusMsg.textContent = "Đang sinh dữ liệu lịch báo giảng...";

    const cardsContainer = document.getElementById("smas-cards-container");
    if (cardsContainer && (!generatedWeeks || generatedWeeks.length === 0)) {
      cardsContainer.innerHTML = `
        <div class="text-center py-6" style="grid-column: 1 / -1; padding: 40px; color: #94a3b8;">
          <div style="font-size: 32px; margin-bottom: 12px;">⏳</div>
          <div class="font-bold" style="font-size: 15px; color: #60a5fa;">Đang ghép nối Thời Khóa Biểu & PPCT thật từ SMAS...</div>
          <div style="font-size: 13px; margin-top: 6px; color: #64748b;">Hệ thống đang tính toán ngày dạy và bài học thực tế cho 35 tuần</div>
        </div>`;
    }

    try {
      const res = await fetch("/api/smas/generate-payloads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          startWeek: startWeek,
          endWeek: endWeek,
          startDate: startDate
        })
      });

      const data = await res.json();
      if (!data.success) {
        throw new Error(data.error || "Không thể sinh dữ liệu");
      }

      generatedWeeks = data.weeks || [];
      const countEl = document.getElementById("smas-preview-weeks-count");
      if (countEl) countEl.textContent = generatedWeeks.length;

      // Populate preview week select dropdown
      const weekSelect = document.getElementById("smas-preview-week-select");
      if (weekSelect) {
        weekSelect.innerHTML = "";
        generatedWeeks.forEach((w) => {
          const opt = document.createElement("option");
          opt.value = w.weekNumber;
          opt.textContent = `Tuần ${w.weekNumber}: ${w.dateRangeLabel}`;
          weekSelect.appendChild(opt);
        });

        weekSelect.onchange = () => {
          const selectedWNum = parseInt(weekSelect.value);
          const found = generatedWeeks.find((x) => x.weekNumber === selectedWNum);
          if (found) renderWeekPreviewTable(found);
        };
      }

      // Render week 1 preview by default
      if (generatedWeeks.length > 0) {
        renderWeekPreviewTable(generatedWeeks[0]);
      }

      if (statusMsg) {
        statusMsg.textContent = `Đã sinh sẵn ${generatedWeeks.length} tuần lịch báo giảng!`;
        statusMsg.style.color = "#10b981";
      }
      if (!isSilent) {
        showSmasToast(`Đã sinh xong dữ liệu cho ${generatedWeeks.length} tuần!`, "success");
      }
    } catch (e) {
      if (statusMsg) {
        statusMsg.textContent = `Lỗi: ${e.message}`;
        statusMsg.style.color = "#ef4444";
      }
      if (!isSilent) showSmasToast(e.message, "error");
    }
  }

  // Helper render 1 thẻ tiết học trực quan cho chế độ Cards
  function renderLessonCardItem(d) {
    const subName = (d.subjectName || "").toLowerCase();
    let subType = "tin";
    let icon = "💻";
    if (subName.includes("thể dục") || subName.includes("gdtc")) {
      subType = "gdtc";
      icon = "⚽";
    } else if (subName.includes("hướng nghiệp") || subName.includes("trải nghiệm") || subName.includes("hdtn")) {
      subType = "hdtn";
      icon = "🎯";
    }

    const isPrimary = d.gradeCode === "03" || d.gradeCode === "04" || d.gradeCode === "05";
    const toolText = d.toolName ? `${d.toolName} (${d.totalTool || 1})` : "Phòng máy / SGK";

    return `
      <div class="smas-lesson-card ${subType}">
        <div class="smas-lesson-top lesson-top">
          <div class="flex-gap align-center" style="gap: 6px;">
            <span class="smas-lesson-period-tag lesson-period">Tiết ${d.period}</span>
            <span class="smas-lesson-class-badge lesson-class">${d.className}</span>
            <span class="lesson-subject font-bold" style="font-size: 12.5px;">${icon} ${d.subjectName}</span>
          </div>
          <span class="smas-lesson-ppct-badge lesson-ppct">PPCT: Tiết ${d.distributeProgramPeriod}</span>
        </div>
        <div class="smas-lesson-title lesson-name" title="${d.distributeProgramName || ''}">
          ${d.distributeProgramName || 'Chưa có tên bài dạy'}
        </div>
        <div class="smas-lesson-bottom lesson-footer">
          <div class="smas-lesson-tool lesson-tool" title="${toolText}">
            <span>🛠️</span>
            <span>${toolText}</span>
          </div>
          <span class="badge ${isPrimary ? 'badge-info' : 'badge-warning'}" style="font-size: 11px; padding: 2px 8px; border-radius: 4px;">
            ${isPrimary ? 'Tiểu học' : 'THCS'}
          </span>
        </div>
      </div>
    `;
  }

  // 6. Trình hiển thị Sổ Báo Giảng Trực Quan (3 Chế Độ: Thẻ Ngày, Mẫu Sổ A4, Bảng)
  function renderWeekPreviewTable(weekData) {
    if (!weekData) return;

    const p02Details = (weekData.payload_level02 && weekData.payload_level02.teachingScheduleDetails) || [];
    const p03Details = (weekData.payload_level03 && weekData.payload_level03.teachingScheduleDetails) || [];
    const allDetails = [...p02Details, ...p03Details];

    // Sắp xếp thứ tự sư phạm: Thứ tự ngày (dayOfWeek) -> Buổi sáng trước chiều (section) -> Tiết (period)
    allDetails.sort((a, b) => {
      if (a.dayOfWeek !== b.dayOfWeek) return a.dayOfWeek - b.dayOfWeek;
      if (a.section !== b.section) return a.section - b.section;
      return a.period - b.period;
    });

    const weekNum = weekData.weekNumber || 1;
    const dateFrom = weekData.dateFrom || "";
    const dateTo = weekData.dateTo || "";

    // 6.1. Cập nhật thông số tóm tắt tuần (Summary Bar)
    const badgeWeek = document.getElementById("smas-preview-weeks-count-badge");
    if (badgeWeek) badgeWeek.textContent = `Tuần ${weekNum}`;

    const sumDateRange = document.getElementById("smas-sum-date-range");
    if (sumDateRange) {
      sumDateRange.innerHTML = `📅 <b>Tuần ${weekNum}:</b> ${dateFrom} ➔ ${dateTo}`;
    }

    const sumTotal = document.getElementById("smas-sum-total-slots");
    if (sumTotal) sumTotal.textContent = `Tổng ${allDetails.length} tiết`;

    const tinCount = allDetails.filter(d => (d.subjectName || "").toLowerCase().includes("tin")).length;
    const gdtcCount = allDetails.filter(d => (d.subjectName || "").toLowerCase().includes("thể dục") || (d.subjectName || "").toLowerCase().includes("gdtc")).length;
    const hdtnCount = allDetails.filter(d => (d.subjectName || "").toLowerCase().includes("trải nghiệm") || (d.subjectName || "").toLowerCase().includes("hướng nghiệp") || (d.subjectName || "").toLowerCase().includes("hdtn")).length;

    const elTin = document.getElementById("smas-sum-tin-slots");
    if (elTin) elTin.textContent = `Tin học: ${tinCount} tiết`;
    const elGdtc = document.getElementById("smas-sum-gdtc-slots");
    if (elGdtc) elGdtc.textContent = `GDTC: ${gdtcCount} tiết`;
    const elHdtn = document.getElementById("smas-sum-hdtn-slots");
    if (elHdtn) elHdtn.textContent = `HĐTN: ${hdtnCount} tiết`;

    const teacherName = (smasConfig && smasConfig.employeeName) || "Trần Đức Tình";
    const elTeacher = document.getElementById("smas-sum-teacher-school");
    if (elTeacher) {
      elTeacher.innerHTML = `Giáo viên: <b>${teacherName}</b> | Trường: <b>TH&THCS Đăk Trôi</b>`;
    }

    // 6.2. CHẾ ĐỘ 1: RENDER DẠNG THẺ THEO NGÀY (Visual Day Cards)
    const cardsContainer = document.getElementById("smas-cards-container");
    if (cardsContainer) {
      const dayNames = {
        1: "Thứ Hai", 2: "Thứ Ba", 3: "Thứ Tư",
        4: "Thứ Năm", 5: "Thứ Sáu", 6: "Thứ Bảy", 7: "Chủ Nhật"
      };

      const groupedDays = {};
      allDetails.forEach((d) => {
        const dow = d.dayOfWeek;
        if (!groupedDays[dow]) {
          groupedDays[dow] = {
            name: dayNames[dow] || `Thứ ${dow + 1}`,
            dateStudy: d.dateStudy || "",
            morning: [],
            afternoon: []
          };
        }
        if (d.section === 0) {
          groupedDays[dow].morning.push(d);
        } else {
          groupedDays[dow].afternoon.push(d);
        }
      });

      let cardsHtml = "";
      const sortedDows = Object.keys(groupedDays).map(Number).sort((a, b) => a - b);

      if (sortedDows.length === 0) {
        cardsHtml = `
          <div class="text-center text-muted py-6" style="grid-column: 1 / -1; padding: 40px;">
            <div style="font-size: 32px; margin-bottom: 8px;">📭</div>
            <div>Không có tiết dạy nào được phân công trong Tuần ${weekNum}</div>
          </div>`;
      } else {
        sortedDows.forEach((dow) => {
          const day = groupedDays[dow];
          const totalDaySlots = day.morning.length + day.afternoon.length;

          cardsHtml += `
            <div class="smas-day-card">
              <div class="smas-day-header">
                <span class="smas-day-title day-title">${day.name}</span>
                <div class="flex-gap align-center" style="gap: 6px;">
                  <span class="smas-day-date day-date">${day.dateStudy}</span>
                  <span class="badge badge-primary font-bold" style="padding: 2px 8px; font-size: 11px;">${totalDaySlots} tiết</span>
                </div>
              </div>
              <div class="smas-day-body">`;

          if (day.morning.length > 0) {
            cardsHtml += `
              <div class="smas-session-group">
                <div class="smas-session-title">☀️ Buổi Sáng (${day.morning.length} tiết)</div>`;
            day.morning.forEach((d) => {
              cardsHtml += renderLessonCardItem(d);
            });
            cardsHtml += `</div>`;
          }

          if (day.afternoon.length > 0) {
            cardsHtml += `
              <div class="smas-session-group">
                <div class="smas-session-title">🌤️ Buổi Chiều (${day.afternoon.length} tiết)</div>`;
            day.afternoon.forEach((d) => {
              cardsHtml += renderLessonCardItem(d);
            });
            cardsHtml += `</div>`;
          }

          cardsHtml += `</div></div>`;
        });
      }
      cardsContainer.innerHTML = cardsHtml;
    }

    // 6.3. CHẾ ĐỘ 2: RENDER MẪU SỔ BÁO GIẢNG CHUẨN A4 (Official Document Sheet)
    const sheetContainer = document.getElementById("smas-sheet-printable");
    if (sheetContainer) {
      const dayNames = {
        1: "Thứ Hai", 2: "Thứ Ba", 3: "Thứ Tư",
        4: "Thứ Năm", 5: "Thứ Sáu", 6: "Thứ Bảy", 7: "Chủ Nhật"
      };

      // Nhóm tiết theo từng ngày để rowspan Thứ & Ngày
      const dayMap = new Map();
      allDetails.forEach((d) => {
        if (!dayMap.has(d.dayOfWeek)) {
          dayMap.set(d.dayOfWeek, []);
        }
        dayMap.get(d.dayOfWeek).push(d);
      });

      let rowsHtml = "";
      dayMap.forEach((slots, dow) => {
        const dName = dayNames[dow] || `Thứ ${dow + 1}`;
        const dDate = slots[0]?.dateStudy || "";
        const rSpan = slots.length;

        slots.forEach((s, idx) => {
          const isFirstOfGroup = idx === 0;
          const sectionLabel = s.section === 0 ? "Sáng" : "Chiều";
          const toolText = s.toolName ? `${s.toolName} (${s.totalTool || 1})` : "Phòng máy / SGK";

          rowsHtml += `<tr>`;
          if (isFirstOfGroup) {
            rowsHtml += `
              <td class="sheet-dow-cell" rowspan="${rSpan}">${dName}</td>
              <td class="sheet-date-cell" rowspan="${rSpan}">${dDate}</td>`;
          }
          rowsHtml += `
              <td class="text-center">${sectionLabel}</td>
              <td class="text-center font-bold">${s.period}</td>
              <td class="text-center font-bold">${s.className}</td>
              <td>${s.subjectName}</td>
              <td class="text-center font-bold">${s.distributeProgramPeriod}</td>
              <td class="font-semibold">${s.distributeProgramName || ''}</td>
              <td class="text-xs">${toolText}</td>
              <td class="text-center text-xs"></td>
            </tr>`;
        });
      });

      if (rowsHtml === "") {
        rowsHtml = `<tr><td colspan="10" class="text-center text-muted py-4">Không có dữ liệu lịch báo giảng tuần này</td></tr>`;
      }

      sheetContainer.innerHTML = `
        <div class="smas-sheet-header">
          <div class="left">
            <p><b>TRƯỜNG TH & THCS ĐĂK TRÔI</b></p>
            <p>TỔ: KHOA HỌC TỰ NHIÊN</p>
          </div>
          <div class="right">
            <p><b>CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</b></p>
            <p><i>Độc lập - Tự do - Hạnh phúc</i></p>
          </div>
        </div>
        <div class="smas-sheet-title">
          <h3>LỊCH BÁO GIẢNG TUẦN ${weekNum}</h3>
          <p>Từ ngày <b>${dateFrom}</b> đến ngày <b>${dateTo}</b></p>
          <p>Giáo viên: <b>${teacherName}</b> | Năm học: <b>2026 - 2027</b></p>
        </div>
        <table class="smas-sheet-table">
          <thead>
            <tr>
              <th style="width: 75px;">Thứ</th>
              <th style="width: 85px;">Ngày</th>
              <th style="width: 55px;">Buổi</th>
              <th style="width: 45px;">Tiết</th>
              <th style="width: 60px;">Lớp</th>
              <th style="width: 120px;">Môn Học</th>
              <th style="width: 65px;">Tiết PPCT</th>
              <th>Tên Bài Dạy (Theo Chuẩn SMAS)</th>
              <th style="width: 140px;">Đồ Dùng Dạy Học</th>
              <th style="width: 65px;">Ghi Chú</th>
            </tr>
          </thead>
          <tbody>
            ${rowsHtml}
          </tbody>
        </table>
        <div class="smas-sheet-footer">
          <div class="sign-col">
            <p><b>TỔ TRƯỞNG CHUYÊN MÔN</b></p>
            <p class="sign-hint">(Ký và ghi rõ họ tên)</p>
          </div>
          <div class="sign-col">
            <p><i>Đăk Trôi, ngày ${dateFrom}</i></p>
            <p><b>NGƯỜI LẬP KẾ HOẠCH</b></p>
            <p class="sign-hint">(Ký và ghi rõ họ tên)</p>
            <br><br><br>
            <p><b>${teacherName}</b></p>
          </div>
        </div>
      `;
    }

    // 6.4. CHẾ ĐỘ 3: RENDER BẢNG DỮ LIỆU ĐẦY ĐỦ (Data Table)
    const tbody = document.getElementById("smas-preview-tbody");
    if (tbody) {
      const dayNames = ["", "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"];
      let html = "";
      allDetails.forEach((d) => {
        const isPrimary = d.gradeCode === "03" || d.gradeCode === "04" || d.gradeCode === "05";
        const levelLabel = isPrimary ? "Tiểu học" : "THCS";
        const sectionLabel = d.section === 0 ? "Sáng" : "Chiều";

        html += `
          <tr>
            <td class="font-bold">${dayNames[d.dayOfWeek] || d.dayOfWeek}</td>
            <td class="font-bold" style="color: #3b82f6;">${d.dateStudy || ""}</td>
            <td>${sectionLabel}</td>
            <td class="text-center font-bold">${d.period}</td>
            <td><span class="badge badge-primary font-bold">${d.className}</span></td>
            <td>${d.subjectName}</td>
            <td class="text-center font-bold" style="color: #ec4899;">${d.distributeProgramPeriod}</td>
            <td class="font-semibold">${d.distributeProgramName || ''}</td>
            <td class="text-xs text-muted">${d.toolName || 'SGK'} (${d.totalTool || 1})</td>
            <td><span class="badge ${isPrimary ? 'badge-info' : 'badge-warning'}">${levelLabel}</span></td>
          </tr>`;
      });

      if (html === "") {
        html = `<tr><td colspan="10" class="text-center text-muted py-4">Không có dữ liệu trong tuần này</td></tr>`;
      }
      tbody.innerHTML = html;
    }
  }

  // 7. Đồng bộ trực tiếp Lịch Báo Giảng Lên SMAS
  async function executeSmasSync() {
    if (!generatedWeeks || generatedWeeks.length === 0) {
      showSmasToast("Vui lòng bấm 'Sinh Lịch & Xem Trước' trước khi đồng bộ!", "warning");
      return;
    }

    const token = (document.getElementById("smas-input-token").value || "").trim();
    if (!token) {
      showSmasToast("Chưa có Bearer Token! Vui lòng nhập token SMAS.", "error");
      return;
    }

    const level = document.getElementById("smas-sync-level").value || "all";
    const confirmed = confirm(`Bạn có chắc chắn muốn đồng bộ ${generatedWeeks.length} tuần lịch báo giảng lên hệ thống SMAS?`);
    if (!confirmed) return;

    const logCard = document.getElementById("smas-sync-log-card");
    const logContent = document.getElementById("smas-sync-log-content");
    const statusMsg = document.getElementById("smas-sync-status-msg");

    if (logCard) logCard.classList.remove("hidden");
    if (logContent) logContent.innerHTML = "";
    if (statusMsg) {
      statusMsg.textContent = "Đang đồng bộ lên SMAS...";
      statusMsg.style.color = "#f59e0b";
    }

    function appendLog(line, color = "#e2e8f0") {
      if (!logContent) return;
      const div = document.createElement("div");
      div.style.color = color;
      div.style.marginBottom = "4px";
      div.textContent = `[${new Date().toLocaleTimeString()}] ${line}`;
      logContent.appendChild(div);
      logContent.scrollTop = logContent.scrollHeight;
    }

    appendLog(`Bắt đầu đồng bộ ${generatedWeeks.length} tuần lên SMAS...`, "#60a5fa");

    try {
      const res = await fetch("/api/smas/sync", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          weeks: generatedWeeks,
          bearerToken: token,
          level: level
        })
      });

      const data = await res.json();
      if (!data.success) {
        throw new Error(data.error || "Lỗi đồng bộ SMAS");
      }

      const results = data.results || [];
      let successCount = 0;

      results.forEach((r) => {
        if (r.level02) {
          if (r.level02.success) {
            appendLog(`[Tuần ${r.weekNumber}] Cấp Tiểu học (02): ${r.level02.message}`, "#10b981");
            successCount++;
          } else {
            appendLog(`[Tuần ${r.weekNumber}] Cấp Tiểu học (02) THẤT BẠI: ${r.level02.message}`, "#ef4444");
          }
        }
        if (r.level03) {
          if (r.level03.success) {
            appendLog(`[Tuần ${r.weekNumber}] Cấp THCS (03): ${r.level03.message}`, "#10b981");
            successCount++;
          } else {
            appendLog(`[Tuần ${r.weekNumber}] Cấp THCS (03) THẤT BẠI: ${r.level03.message}`, "#ef4444");
          }
        }
      });

      appendLog(`Hoàn thành đồng bộ! Tổng số lượt thành công: ${successCount}`, "#60a5fa");
      if (statusMsg) {
        statusMsg.textContent = `Đồng bộ hoàn tất (${successCount} lượt thành công)!`;
        statusMsg.style.color = "#10b981";
      }
      showSmasToast("Đã đồng bộ lịch báo giảng lên SMAS thành công!", "success");
    } catch (e) {
      appendLog(`LỖI: ${e.message}`, "#ef4444");
      if (statusMsg) {
        statusMsg.textContent = `Lỗi đồng bộ: ${e.message}`;
        statusMsg.style.color = "#ef4444";
      }
      showSmasToast(`Lỗi: ${e.message}`, "error");
    }
  }

  // 8. Đăng ký các sự kiện nút bấm
  function setupSmasEvents() {
    // Nút Kiểm tra & Đồng bộ Token
    const btnCheckToken = document.getElementById("btn-smas-check-token");
    if (btnCheckToken) {
      btnCheckToken.addEventListener("click", async () => {
        const tok = (document.getElementById("smas-input-token").value || "").trim();
        if (!tok) {
          showSmasToast("Vui lòng dán Bearer Token!", "warning");
          return;
        }
        btnCheckToken.disabled = true;
        btnCheckToken.textContent = "⏳ Đang kiểm tra...";

        try {
          const res = await fetch("/api/smas/token-sync", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token: tok })
          });
          const data = await res.json();
          if (data.success) {
            updateTokenBadge(true, data.message);
            showSmasToast(data.message, "success");

            // Cập nhật giao diện nếu có
            const el = document.getElementById("smas-stat-teacher");
            if (el) el.textContent = data.fullname;

            // Đồng bộ sang trường Cấu hình KHBD
            const teacherInput = document.getElementById("cfg-teacher-name");
            if (teacherInput) teacherInput.value = data.fullname;
            const yearInput = document.getElementById("cfg-school-year");
            if (yearInput) yearInput.value = data.schoolYear;
          } else {
            updateTokenBadge(false, data.error || "Token không hợp lệ");
            showSmasToast(data.error || "Token không hợp lệ", "error");
          }
        } catch (e) {
          updateTokenBadge(false, e.message);
          showSmasToast(e.message, "error");
        } finally {
          btnCheckToken.disabled = false;
          btnCheckToken.textContent = "⚡ Kiểm Tra & Đồng Bộ Hồ Sơ Giáo Viên";
        }
      });
    }

    // Nút Tải PPCT Thật Từ SMAS
    const btnLoadPpct = document.getElementById("btn-smas-load-ppct");
    if (btnLoadPpct) {
      btnLoadPpct.addEventListener("click", async () => {
        const tok = (document.getElementById("smas-input-token").value || "").trim();
        if (!tok) {
          showSmasToast("Chưa có Bearer Token!", "warning");
          return;
        }

        btnLoadPpct.disabled = true;
        btnLoadPpct.textContent = "⏳ Đang tải PPCT...";
        try {
          const res = await fetch("/api/smas/refresh-ppct", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token: tok })
          });
          const data = await res.json();
          if (data.success) {
            showSmasToast(data.message, "success");
            await loadPpctDatabase();
          } else {
            showSmasToast(data.error || "Lỗi tải PPCT", "error");
          }
        } catch (e) {
          showSmasToast(e.message, "error");
        } finally {
          btnLoadPpct.disabled = false;
          btnLoadPpct.textContent = "📥 Tải PPCT Thật Từ SMAS";
        }
      });
    }

    // Nút Nhập TKB Từ Excel
    const btnImportExcel = document.getElementById("btn-smas-import-excel");
    const inputTkbExcel = document.getElementById("input-smas-tkb-excel");
    const btnSampleTkb = document.getElementById("btn-smas-sample-tkb");

    if (btnImportExcel && inputTkbExcel) {
      btnImportExcel.addEventListener("click", () => {
        inputTkbExcel.value = "";
        inputTkbExcel.click();
      });

      inputTkbExcel.addEventListener("change", async (e) => {
        const file = e.target.files && e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);
        if (smasConfig && smasConfig.employeeName) {
          formData.append("teacherName", smasConfig.employeeName);
        }

        showSmasToast(`Đang phân tích file ${file.name}...`, "info");
        btnImportExcel.disabled = true;
        btnImportExcel.textContent = "⏳ Đang trích xuất...";

        try {
          const res = await fetch("/api/smas/schedule/import-excel", {
            method: "POST",
            body: formData
          });
          const data = await res.json();
          if (data.success) {
            smasSchedule = data.slots || [];
            renderTimetableGrid(smasSchedule);
            updateScheduleStats(smasSchedule);
            showSmasToast(data.message, "success");
            // Tự động làm mới Sổ Báo Giảng đồng bộ theo TKB mới
            generateAndPreviewPayloads(true);
          } else {
            showSmasToast(data.error || "Không thể phân tích file Excel TKB!", "error");
          }
        } catch (err) {
          console.error("Lỗi upload TKB Excel:", err);
          showSmasToast("Lỗi kết nối khi gửi file TKB!", "error");
        } finally {
          btnImportExcel.disabled = false;
          btnImportExcel.innerHTML = "📥 Nhập TKB Từ File Excel";
        }
      });
    }

    if (btnSampleTkb) {
      btnSampleTkb.addEventListener("click", async () => {
        showSmasToast('Đang nạp TKB từ file mẫu "thơi khóa biểu 1.xls"...', "info");
        btnSampleTkb.disabled = true;
        try {
          const res = await fetch("/api/smas/schedule/import-excel", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filePath: "thơi khóa biểu 1.xls" })
          });
          const data = await res.json();
          if (data.success) {
            smasSchedule = data.slots || [];
            renderTimetableGrid(smasSchedule);
            updateScheduleStats(smasSchedule);
            showSmasToast(data.message, "success");
            generateAndPreviewPayloads(true);
          } else {
            showSmasToast(data.error || "Không thể nạp file mẫu TKB!", "error");
          }
        } catch (err) {
          console.error("Lỗi nạp file mẫu TKB:", err);
          showSmasToast("Lỗi nạp file mẫu TKB!", "error");
        } finally {
          btnSampleTkb.disabled = false;
        }
      });
    }

    // Nút Khôi phục TKB gốc
    const btnResetTkb = document.getElementById("btn-smas-reset-tkb");
    if (btnResetTkb) {
      btnResetTkb.addEventListener("click", async () => {
        if (!confirm("Khôi phục lại Thời khóa biểu gốc (19 tiết)?")) return;
        const res = await fetch("/api/smas/schedule/reset", { method: "POST" });
        const data = await res.json();
        if (data.success) {
          smasSchedule = data.slots || [];
          renderTimetableGrid(smasSchedule);
          updateScheduleStats(smasSchedule);
          showSmasToast(data.message, "success");
        }
      });
    }

    // Nút Lưu TKB
    const btnSaveTkb = document.getElementById("btn-smas-save-tkb");
    if (btnSaveTkb) {
      btnSaveTkb.addEventListener("click", async () => {
        const res = await fetch("/api/smas/schedule", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ slots: smasSchedule })
        });
        const data = await res.json();
        if (data.success) {
          showSmasToast(data.message, "success");
        }
      });
    }

    // Nút Sinh Lịch & Xem trước
    const btnPreview = document.getElementById("btn-smas-preview-payloads");
    if (btnPreview) {
      btnPreview.addEventListener("click", () => generateAndPreviewPayloads(false));
    }

    // Nút Đồng bộ lên SMAS
    const btnExecuteSync = document.getElementById("btn-smas-execute-sync");
    if (btnExecuteSync) {
      btnExecuteSync.addEventListener("click", executeSmasSync);
    }

    // Chuyển đổi chế độ xem: Thẻ Ngày / Mẫu Sổ / Bảng
    const viewBtns = document.querySelectorAll(".smas-view-btn");
    viewBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        viewBtns.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        const targetView = btn.getAttribute("data-view");

        const allViews = document.querySelectorAll(".smas-preview-view");
        allViews.forEach((v) => v.classList.add("hidden"));

        const targetContainer = document.getElementById(`smas-view-${targetView}`);
        if (targetContainer) targetContainer.classList.remove("hidden");
      });
    });

    // Nút Tuần Trước / Tuần Sau
    const btnPrevWeek = document.getElementById("btn-smas-prev-week");
    const btnNextWeek = document.getElementById("btn-smas-next-week");
    const weekSelect = document.getElementById("smas-preview-week-select");

    if (btnPrevWeek && weekSelect) {
      btnPrevWeek.addEventListener("click", () => {
        if (weekSelect.selectedIndex > 0) {
          weekSelect.selectedIndex -= 1;
          const selectedWNum = parseInt(weekSelect.value);
          const found = generatedWeeks.find((x) => x.weekNumber === selectedWNum);
          if (found) renderWeekPreviewTable(found);
        }
      });
    }

    if (btnNextWeek && weekSelect) {
      btnNextWeek.addEventListener("click", () => {
        if (weekSelect.selectedIndex < weekSelect.options.length - 1) {
          weekSelect.selectedIndex += 1;
          const selectedWNum = parseInt(weekSelect.value);
          const found = generatedWeeks.find((x) => x.weekNumber === selectedWNum);
          if (found) renderWeekPreviewTable(found);
        }
      });
    }

    // Nút In Sổ Báo Giảng A4
    const btnPrintLbg = document.getElementById("btn-smas-print-lbg");
    if (btnPrintLbg) {
      btnPrintLbg.addEventListener("click", () => {
        const sheetContainer = document.getElementById("smas-sheet-printable");
        if (!sheetContainer || !sheetContainer.innerHTML.trim()) {
          showSmasToast("Chưa có nội dung sổ báo giảng để in!", "warning");
          return;
        }

        const printWin = window.open("", "_blank");
        if (!printWin) {
          showSmasToast("Trình duyệt chặn mở cửa sổ in! Vui lòng cho phép popup.", "error");
          return;
        }

        const teacherName = (smasConfig && smasConfig.employeeName) || "Trần Đức Tình";
        printWin.document.write(`
          <!DOCTYPE html>
          <html>
          <head>
            <meta charset="utf-8">
            <title>Sổ Báo Giảng - ${teacherName}</title>
            <style>
              @page { size: A4 landscape; margin: 10mm 12mm; }
              * { box-sizing: border-box; }
              body { font-family: 'Times New Roman', Times, serif; color: #000; background: #fff; margin: 0; padding: 15px; }
              .smas-sheet-header { display: flex; justify-content: space-between; margin-bottom: 12px; }
              .smas-sheet-header .left, .smas-sheet-header .right { text-align: center; }
              .smas-sheet-header p { margin: 2px 0; font-size: 13pt; }
              .smas-sheet-title { text-align: center; margin: 8px 0 16px 0; }
              .smas-sheet-title h3 { margin: 0; font-size: 16pt; font-weight: bold; text-transform: uppercase; }
              .smas-sheet-title p { margin: 3px 0; font-size: 11.5pt; }
              table.smas-sheet-table { width: 100%; border-collapse: collapse; font-size: 10.5pt; margin-bottom: 16px; }
              table.smas-sheet-table th, table.smas-sheet-table td { border: 1px solid #000; padding: 5px 6px; text-align: left; }
              table.smas-sheet-table th { background: #f2f2f2; text-align: center; font-weight: bold; }
              .text-center { text-align: center; }
              .sheet-dow-cell { font-weight: bold; text-align: center; vertical-align: middle; }
              .sheet-date-cell { text-align: center; vertical-align: middle; }
              .smas-sheet-footer { display: flex; justify-content: space-between; margin-top: 25px; page-break-inside: avoid; }
              .sign-col { text-align: center; width: 42%; }
              .sign-col p { margin: 3px 0; font-size: 11.5pt; }
              .sign-hint { font-size: 9.5pt; font-style: italic; color: #555; }
            </style>
          </head>
          <body>
            ${sheetContainer.innerHTML}
          </body>
          </html>
        `);
        printWin.document.close();
        printWin.focus();
        setTimeout(() => {
          printWin.print();
          printWin.close();
        }, 400);
      });
    }
  }

  // Khởi động khi DOM sẵn sàng
  document.addEventListener("DOMContentLoaded", async () => {
    initSubtabs();
    setupSmasEvents();
    await loadInitialSmasData();
    // Tự động sinh dữ liệu xem trước ngầm để có ngay Tuần 1 trực quan
    generateAndPreviewPayloads(true);
  });
})();
