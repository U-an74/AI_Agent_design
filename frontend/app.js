"use strict";

// 로컬 기본값. Vercel 배포 시 config.js에서 window.APP_CONFIG.API_BASE_URL을 지정합니다.
const API_BASE_URL = (window.APP_CONFIG?.API_BASE_URL || "https://ai-lifestyle-manager-api.onrender.com").replace(/\/$/, "");
const $ = (selector) => document.querySelector(selector);
const state = { tab: "chat", conversationId: null, messages: [], data: [], summary: null, busy: false };
const titles = {
  chat: ["AI 채팅", "내 기록을 바탕으로 생활습관을 개선해 보세요."],
  summary: ["데이터 요약", "수면과 운동 추세를 한눈에 확인하세요."],
  data: ["데이터 관리", "나의 생활습관 기록을 안전하게 관리하세요."],
  history: ["대화 기록", "이전 AI 상담을 불러와 이어서 대화하세요."]
};
const form = $("#data-form");
let editingId = null;

function el(tag, className = "", text = null) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== null) node.textContent = String(text);
  return node;
}
function showNotice(message, error = false) {
  const box = $("#notice");
  box.textContent = message;
  box.classList.toggle("error", error);
  box.hidden = false;
  clearTimeout(showNotice.timeout);
  showNotice.timeout = setTimeout(() => { box.hidden = true; }, 6000);
}
async function api(path, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 90000); // Render 무료 인스턴스 재시작 대응
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      signal: controller.signal,
      headers: { "Content-Type": "application/json", ...(options.headers || {}) }
    });
    const payload = await response.json().catch(() => null);
    if (!response.ok) {
      const detail = payload?.detail;
      const reason = typeof detail === "string" ? detail : `HTTP ${response.status}`;
      throw new Error(reason);
    }
    return payload;
  } catch (error) {
    if (error.name === "AbortError") throw new Error("서버 응답 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요.");
    if (error instanceof TypeError) throw new Error("서버 연결에 실패했습니다. Render 서버 상태와 CORS 설정을 확인해 주세요.");
    throw error;
  } finally { clearTimeout(timeout); }
}
function switchTab(name) {
  state.tab = name;
  document.querySelectorAll(".nav-item").forEach(btn => {
    const active = btn.dataset.tab === name;
    btn.classList.toggle("active", active);
    if (active) btn.setAttribute("aria-current", "page");
    else btn.removeAttribute("aria-current");
  });
  document.querySelectorAll(".tab-panel").forEach(panel => {
    const active = panel.id === `tab-${name}`;
    panel.classList.toggle("active", active);
    panel.hidden = !active;
  });
  $("#page-title").textContent = titles[name][0];
  $("#page-description").textContent = titles[name][1];
  if (name === "summary") loadSummary();
  if (name === "data") loadData();
  if (name === "history") loadHistory();
}
function appendMessage(role, content) {
  const container = $("#chat-messages");
  if (container.querySelector(".empty")) container.replaceChildren();
  const message = el("div", `message ${role}`);
  message.append(el("div", "author", role === "user" ? "나" : "AI 매니저"));
  message.append(el("div", "content", content)); // textContent: API 답변으로 HTML 실행 방지
  container.append(message);
  container.scrollTop = container.scrollHeight;
}
function renderMessages() {
  const container = $("#chat-messages");
  container.replaceChildren();
  if (!state.messages.length) {
    const empty = el("div", "empty");
    empty.append(el("div", "empty-icon", "✦"), el("strong", "어떤 습관이 궁금하세요?"), el("p", "“내 최근 수면과 운동 습관을 분석해줘”처럼 질문해 보세요."));
    container.append(empty);
    return;
  }
  state.messages.forEach(m => appendMessage(m.role, m.content));
}
function setChatBusy(busy) {
  state.busy = busy;
  $("#chat-loading").hidden = !busy;
  $("#send-btn").disabled = busy;
  $("#chat-input").disabled = busy;
  $("#new-chat").disabled = busy;
}
async function sendChat(event) {
  event.preventDefault();
  if (state.busy) return;
  const input = $("#chat-input");
  const message = input.value.trim();
  if (!message) return;
  const conversationId = state.conversationId;
  input.value = "";
  appendMessage("user", message);
  setChatBusy(true);
  try {
    const response = await api("/api/chat", {
      method: "POST", body: JSON.stringify({ message, conversation_id: conversationId })
    });
    state.conversationId = response.conversation_id;
    state.messages.push({ role: "user", content: message }, { role: "assistant", content: response.answer });
    appendMessage("assistant", response.answer);
  } catch (error) {
    // 실패한 질문은 저장되지 않았으므로 화면에서도 제거하고 복구
    input.value = message;
    renderMessages();
    showNotice(`AI 응답 실패: ${error.message}`, true);
  } finally { setChatBusy(false); input.focus(); }
}
function newChat() {
  state.conversationId = null;
  state.messages = [];
  renderMessages();
  switchTab("chat");
  $("#chat-input").focus();
}
async function loadConversation(id) {
  try {
    const result = await api(`/api/conversations/${encodeURIComponent(id)}`);
    state.conversationId = result.id;
    state.messages = result.messages || [];
    switchTab("chat");
    renderMessages();
    showNotice("이전 대화를 불러왔습니다. 이어서 질문할 수 있습니다.");
  } catch (error) { showNotice(`대화 불러오기 실패: ${error.message}`, true); }
}
async function loadHistory() {
  const list = $("#history-list");
  list.replaceChildren(el("p", "muted", "대화 목록을 불러오는 중..."));
  try {
    const result = await api("/api/conversations");
    list.replaceChildren();
    const conversations = result.conversations || [];
    if (!conversations.length) { list.append(el("p", "muted", "저장된 대화가 없습니다.")); return; }
    conversations.forEach(conversation => {
      const card = el("div", "history-card");
      const info = el("div");
      info.append(el("strong", "", conversation.title || "제목 없는 대화"));
      const date = conversation.updated_at ? new Date(conversation.updated_at).toLocaleString("ko-KR") : "날짜 없음";
      info.append(el("small", "", `${date} · 메시지 ${conversation.message_count || 0}개`));
      const actions = el("div", "history-actions");
      const open = el("button", "btn secondary", "불러오기");
      open.type = "button";
      open.addEventListener("click", () => loadConversation(conversation.id));
      const del = el("button", "small-btn danger", "삭제");
      del.type = "button";
      del.addEventListener("click", async () => {
        if (!confirm("이 대화 기록을 삭제할까요?")) return;
        try {
          await api(`/api/conversations/${encodeURIComponent(conversation.id)}`, { method: "DELETE" });
          if (state.conversationId === conversation.id) newChat();
          showNotice("대화 기록을 삭제했습니다.");
          loadHistory();
        } catch (error) { showNotice(error.message, true); }
      });
      actions.append(open, del); card.append(info, actions); list.append(card);
    });
  } catch (error) { list.replaceChildren(el("p", "muted", `조회 실패: ${error.message}`)); }
}
function metric(label, value) {
  const card = el("div", "metric");
  card.append(el("div", "muted", label), el("strong", "", value));
  return card;
}
function detail(title, entries) {
  const card = el("div", "detail-card");
  card.append(el("h3", "", title));
  entries.forEach(([label, value]) => card.append(el("p", "", `${label}: ${value}`)));
  return card;
}
async function loadSummary() {
  const target = $("#summary-content");
  target.replaceChildren(el("p", "muted", "데이터 요약을 불러오는 중..."));
  try {
    const s = await api("/api/data/summary");
    state.summary = s;
    const period = `${s.period.start_date} ~ ${s.period.end_date}`;
    $("#chat-summary").textContent = `기록 ${s.total_count}개 · ${period} · 평균 수면 ${s.sleep_summary.average_minutes}분 · 운동 ${s.exercise_summary.average_minutes}분`;
    target.replaceChildren();
    const metrics = el("div", "metrics");
    metrics.append(
      metric("데이터 기록 수", `${s.total_count}개`),
      metric("평균 수면", `${s.sleep_summary.average_minutes}분`),
      metric("평균 운동", `${s.exercise_summary.average_minutes}분`),
      metric("취침 패턴 추세", s.recent_bedtime_trend.trend)
    );
    const details = el("div", "detail-grid");
    details.append(
      detail("분석 기간과 수면", [["기록 기간", period], ["최대 수면", `${s.sleep_summary.max_minutes}분`], ["최소 수면", `${s.sleep_summary.min_minutes}분`]]),
      detail("취침 패턴", [["목표 시간대", s.bedtime_summary.target_time], ["목표 준수율", `${s.bedtime_summary.target_rate_percent}%`], ["최근 7개 기록", `${s.recent_bedtime_trend.recent_rate_percent}%`], ["이전 7개 기록", `${s.recent_bedtime_trend.previous_rate_percent}%`]]),
      detail("운동 종류별 횟수", Object.entries(s.exercise_summary.exercise_type_counts).map(([k, v]) => [k, `${v}회`])),
      detail("운동 시간과 추세", [["최대 운동", `${s.exercise_summary.max_minutes}분`], ["최소 운동", `${s.exercise_summary.min_minutes}분`], ["최근 취침 추세", s.recent_bedtime_trend.trend]])
    );
    target.append(metrics, details);
  } catch (error) {
    target.replaceChildren(el("p", "muted", `요약 조회 실패: ${error.message}`));
    $("#chat-summary").textContent = "요약 조회 실패. 데이터 요약 탭에서 재시도해 주세요.";
  }
}
function td(value) { return el("td", "", value); }
function renderData() {
  const keyword = $("#data-search").value.trim().toLowerCase();
  const data = state.data.filter(r => r.date.includes(keyword) || r.exercise_type.toLowerCase().includes(keyword));
  $("#data-count").textContent = `${state.data.length}개 기록`;
  const tbody = $("#data-rows"); tbody.replaceChildren();
  if (!data.length) {
    const row = el("tr"); const cell = td("기록이 없습니다."); cell.colSpan = 6; row.append(cell); tbody.append(row); return;
  }
  [...data].reverse().forEach(item => {
    const row = el("tr");
    row.append(td(item.date), td(item.sleep_start_time), td(item.sleep_minutes), td(item.exercise_type), td(item.exercise_minutes));
    const actions = td("");
    const edit = el("button", "small-btn", "수정");
    edit.type = "button";
    edit.addEventListener("click", () => {
      editingId = item.id;
      ["date", "sleep_start_time", "sleep_minutes", "exercise_type", "exercise_minutes"].forEach(key => form.elements[key].value = item[key]);
      // API가 기존 선택지에 없는 운동명을 반환하면 기타로 표시
      if (![...form.elements.exercise_type.options].some(o => o.value === item.exercise_type)) {
        const option = new Option(item.exercise_type, item.exercise_type);
        form.elements.exercise_type.add(option);
        form.elements.exercise_type.value = item.exercise_type;
      }
      $("#data-form-title").textContent = "기록 수정";
      $("#save-data").textContent = "수정 저장";
      $("#cancel-edit").hidden = false;
      form.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    const del = el("button", "small-btn danger", "삭제");
    del.type = "button";
    del.addEventListener("click", async () => {
      if (!confirm(`${item.date} 기록을 삭제할까요?`)) return;
      try { await api(`/api/data/${encodeURIComponent(item.id)}`, { method: "DELETE" }); showNotice("기록이 삭제되었습니다."); await Promise.all([loadData(), loadSummary()]); }
      catch (error) { showNotice(`삭제 실패: ${error.message}`, true); }
    });
    actions.append(edit, del); row.append(actions); tbody.append(row);
  });
}
async function loadData() {
  try { state.data = await api("/api/data"); renderData(); }
  catch (error) { $("#data-rows").replaceChildren(el("tr")); showNotice(`데이터 조회 실패: ${error.message}`, true); }
}
function resetForm() {
  editingId = null; form.reset(); form.elements.sleep_start_time.value = "23:00";
  form.elements.sleep_minutes.value = 420; form.elements.exercise_minutes.value = 0;
  $("#data-form-title").textContent = "새 기록 추가";
  $("#save-data").textContent = "기록 추가"; $("#cancel-edit").hidden = true;
}
async function saveData(event) {
  event.preventDefault();
  const payload = {
    date: form.elements.date.value,
    sleep_start_time: form.elements.sleep_start_time.value,
    sleep_minutes: Number(form.elements.sleep_minutes.value),
    exercise_type: form.elements.exercise_type.value,
    exercise_minutes: Number(form.elements.exercise_minutes.value)
  };
  const button = $("#save-data"); button.disabled = true;
  try {
    await api(editingId ? `/api/data/${encodeURIComponent(editingId)}` : "/api/data", {
      method: editingId ? "PUT" : "POST", body: JSON.stringify(payload)
    });
    showNotice(editingId ? "기록을 수정했습니다." : "새 기록을 추가했습니다.");
    resetForm(); await Promise.all([loadData(), loadSummary()]);
  } catch (error) { showNotice(`저장 실패: ${error.message}`, true); }
  finally { button.disabled = false; }
}

document.querySelectorAll(".nav-item").forEach(btn => btn.addEventListener("click", () => switchTab(btn.dataset.tab)));
$("#chat-form").addEventListener("submit", sendChat);
$("#chat-input").addEventListener("keydown", event => { if (event.key === "Enter" && !event.shiftKey && !event.isComposing) { event.preventDefault(); $("#chat-form").requestSubmit(); } });
$("#new-chat").addEventListener("click", newChat);
$("#data-form").addEventListener("submit", saveData);
$("#cancel-edit").addEventListener("click", resetForm);
$("#data-search").addEventListener("input", renderData);
$("#summary-refresh").addEventListener("click", loadSummary);
$("#history-refresh").addEventListener("click", loadHistory);
$("#refresh-btn").addEventListener("click", () => {
  if (state.tab === "summary" || state.tab === "chat") loadSummary();
  if (state.tab === "data") loadData();
  if (state.tab === "history") loadHistory();
});
$("#api-url-label").textContent = API_BASE_URL;
loadSummary();
