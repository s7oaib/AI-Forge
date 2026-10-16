// College Information Assistant - browser side.
// The conversation lives only in this page (the `history` array). The server
// uses it to understand follow-up questions; it never becomes a "fact".

const messagesEl = document.getElementById("messages");
const form = document.getElementById("composer");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");
const newChatBtn = document.getElementById("new-chat");
const modeBadge = document.getElementById("mode-badge");
const llmToggleWrap = document.getElementById("llm-toggle-wrap");
const llmToggle = document.getElementById("llm-toggle");
const kbWarning = document.getElementById("kb-warning");

let history = [];
let busy = false;
let serverStatus = null;

// ---------- tiny, safe Markdown renderer (bold, code, lists, paragraphs) ----------
function escapeHtml(text) {
  return text.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function inline(text) {
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>");
}

function renderMarkdown(md) {
  const html = [];
  let list = null; // "ul" | "ol" | null
  let para = [];
  const flushPara = () => { if (para.length) { html.push(`<p>${inline(para.join(" "))}</p>`); para = []; } };
  const closeList = () => { if (list) { html.push(`</${list}>`); list = null; } };

  for (const raw of md.split("\n")) {
    const line = raw.trim();
    const bullet = line.match(/^[-*]\s+(.*)$/);
    const numbered = line.match(/^\d+[.)]\s+(.*)$/);
    if (bullet || numbered) {
      flushPara();
      const type = bullet ? "ul" : "ol";
      if (list !== type) { closeList(); html.push(`<${type}>`); list = type; }
      html.push(`<li>${inline((bullet || numbered)[1])}</li>`);
    } else if (!line) {
      flushPara(); closeList();
    } else {
      closeList(); para.push(line);
    }
  }
  flushPara(); closeList();
  return html.join("");
}

// ---------- rendering ----------
function scrollToBottom() { messagesEl.scrollTop = messagesEl.scrollHeight; }

function addMessage(role, content, extra = {}) {
  const wrap = document.createElement("div");
  wrap.className = `msg ${role}`;
  const who = document.createElement("div");
  who.className = "who";
  who.textContent = role === "user" ? "You" : "Assistant";
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  if (extra.className) bubble.classList.add(extra.className);
  if (role === "user") bubble.textContent = content;
  else if (extra.html) bubble.innerHTML = extra.html;
  else bubble.innerHTML = renderMarkdown(content);
  wrap.append(who, bubble);
  messagesEl.appendChild(wrap);
  scrollToBottom();
  return wrap;
}

function addAnswer(data) {
  const wrap = addMessage("assistant", data.answer, { className: data.grounded ? "" : "not-found" });

  const meta = document.createElement("div");
  meta.className = "meta";
  const answerSources = data.sources.filter((s) => s.role !== "related");
  const related = data.sources.filter((s) => s.role === "related");
  if (answerSources.length) {
    const label = document.createElement("span");
    label.className = "meta-label";
    label.textContent = data.grounded ? "Source:" : "Contact info from:";
    meta.appendChild(label);
    answerSources.forEach((s) => meta.appendChild(sourceChip(s, "")));
  } else if (!data.grounded) {
    const label = document.createElement("span");
    label.className = "meta-label";
    label.textContent = "No supporting source found";
    meta.appendChild(label);
  }
  if (related.length) {
    const label = document.createElement("span");
    label.className = "meta-label";
    label.textContent = "Related:";
    meta.appendChild(label);
    related.forEach((s) => meta.appendChild(sourceChip(s, "related")));
  }
  const mode = document.createElement("span");
  mode.className = "mode-chip";
  mode.textContent = data.mode === "llm" ? "LLM + retrieval" : "Retrieval only";
  mode.title = data.mode === "llm" ? "Written by the LLM from the retrieved passages" : "Passage shown directly from the knowledge file";
  meta.appendChild(mode);
  wrap.appendChild(meta);

  if (data.context_used) {
    const note = document.createElement("div");
    note.className = "context-note";
    note.textContent = `Follow-up understood using your previous question: "${data.context_used}"`;
    wrap.appendChild(note);
  }
  if (data.notice) {
    const notice = document.createElement("div");
    notice.className = "notice";
    notice.textContent = data.notice;
    wrap.appendChild(notice);
  }
  scrollToBottom();
}

function sourceChip(s, extraClass) {
  const chip = document.createElement("span");
  chip.className = `source ${extraClass}`.trim();
  chip.textContent = `📄 ${s.file} › ${s.heading}`;
  chip.title = s.score != null ? `Relevance score ${s.score}` : "";
  return chip;
}

function showWelcome() {
  messagesEl.innerHTML = "";
  const node = document.getElementById("welcome-template").content.cloneNode(true);
  node.querySelectorAll(".example").forEach((btn) =>
    btn.addEventListener("click", () => { if (!busy) send(btn.textContent); })
  );
  messagesEl.appendChild(node);
}

function setBusy(value) {
  busy = value;
  sendBtn.disabled = value;
  sendBtn.textContent = value ? "Thinking…" : "Send";
}

// ---------- talking to the server ----------
async function send(text) {
  const question = text.trim();
  if (!question || busy) {
    if (!question) input.focus();
    return;
  }
  addMessage("user", question);
  input.value = "";
  autoGrow();
  setBusy(true);
  const typing = addMessage("assistant", "", {
    html: '<span class="typing">Searching the knowledge files <span class="dots"><span></span><span></span><span></span></span></span>',
  });

  const body = { message: question, history };
  if (serverStatus && serverStatus.llm_key_present && serverStatus.llm_provider === "anthropic") {
    body.mode = llmToggle.checked ? "llm" : "offline";
  }

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    let data;
    try { data = await res.json(); } catch { data = { error: `The server sent an unreadable reply (HTTP ${res.status}).` }; }
    typing.remove();
    if (!res.ok || data.error) {
      addMessage("assistant", data.error || `Request failed (HTTP ${res.status}).`, { className: "error" });
    } else {
      addAnswer(data);
      history.push({ role: "user", content: question }, { role: "assistant", content: data.answer });
      history = history.slice(-8);
    }
  } catch (err) {
    typing.remove();
    addMessage("assistant", "Could not reach the chatbot server. Is `python app.py` still running?", { className: "error" });
    console.error(err);
  } finally {
    setBusy(false);
    input.focus();
    refreshStatus();
  }
}

async function refreshStatus() {
  try {
    const res = await fetch("/api/status");
    serverStatus = await res.json();
  } catch (err) {
    modeBadge.textContent = "Server offline";
    modeBadge.className = "badge error";
    return;
  }
  const s = serverStatus;
  const canUseLlm = s.llm_provider === "anthropic" && s.llm_key_present;
  llmToggleWrap.hidden = !canUseLlm;
  if (canUseLlm && llmToggle.dataset.init !== "1") { llmToggle.checked = true; llmToggle.dataset.init = "1"; }

  if (canUseLlm && llmToggle.checked) {
    modeBadge.textContent = s.last_llm_error ? "LLM error → retrieval fallback" : `LLM: ${s.model}`;
    modeBadge.className = s.last_llm_error ? "badge error" : "badge llm";
    modeBadge.title = s.last_llm_error || "Answers are written by the LLM from retrieved passages";
  } else {
    modeBadge.textContent = "Offline retrieval mode";
    modeBadge.className = "badge";
    modeBadge.title = "No LLM is used. Answers are the best-matching passages from the knowledge files.";
  }

  const warnings = [...s.warnings];
  if (!s.passages) warnings.unshift("No knowledge loaded - every question will get the safe fallback.");
  kbWarning.hidden = warnings.length === 0;
  kbWarning.textContent = warnings.length ? `Knowledge base: ${warnings.join(" · ")}` : "";
}

// ---------- input handling ----------
function autoGrow() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 160)}px`;
}

form.addEventListener("submit", (e) => { e.preventDefault(); send(input.value); });
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); send(input.value); }
});
input.addEventListener("input", autoGrow);
newChatBtn.addEventListener("click", () => {
  if (busy) return;
  history = [];
  showWelcome();
  input.value = "";
  input.focus();
});
llmToggle.addEventListener("change", refreshStatus);

showWelcome();
refreshStatus();
input.focus();
