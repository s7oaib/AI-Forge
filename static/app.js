// College Information Assistant - browser side.
// The conversation lives only in this page (`history`). The server uses it to
// understand follow-up questions; it never becomes a "fact".

const $ = (id) => document.getElementById(id);
const messagesEl = $("messages");
const input = $("input");
const sendBtn = $("send");
const panel = $("panel");
const backdrop = $("sheet-backdrop");
const explainEl = $("panel-explain");
const filesEl = $("panel-files");
const narrow = window.matchMedia("(max-width: 960px)");

let history = [];        // [{role, content}] sent to the server
let turns = [];          // [{question, data, el}] for the explain panel
let selected = -1;
let busy = false;
let status = null;
let mode = "llm";        // used only when Claude is available
let lastQuestion = "";

const ICON = {
  file: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/></svg>',
  ban: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/><path d="M6 6l12 12"/></svg>',
  arrow: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h13M13 6l6 6-6 6"/></svg>',
};

// ---------- tiny, safe Markdown renderer (bold, code, lists, paragraphs) ----------
function esc(text) {
  return String(text).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function inline(text) {
  return esc(text).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/`([^`]+)`/g, "<code>$1</code>");
}
function markdown(md) {
  const out = [];
  let list = null, para = [];
  const flush = () => { if (para.length) { out.push(`<p>${inline(para.join(" "))}</p>`); para = []; } };
  const close = () => { if (list) { out.push(`</${list}>`); list = null; } };
  for (const raw of String(md).split("\n")) {
    const line = raw.trim();
    const m = line.match(/^([-*]|\d+[.)])\s+(.*)$/);
    if (m) {
      flush();
      const type = /\d/.test(m[1]) ? "ol" : "ul";
      if (list !== type) { close(); out.push(`<${type}>`); list = type; }
      out.push(`<li>${inline(m[2])}</li>`);
    } else if (!line) { flush(); close(); }
    else { close(); para.push(line); }
  }
  flush(); close();
  return out.join("");
}
const pct = (x) => `${Math.round(x * 100)}%`;

// ---------- chat rendering ----------
function scrollDown() { messagesEl.scrollTop = messagesEl.scrollHeight; }

function addUserTurn(text) {
  const el = document.createElement("div");
  el.className = "turn user";
  el.innerHTML = `<p>${esc(text)}</p>`;
  messagesEl.appendChild(el);
  scrollDown();
}

function addThinking() {
  const el = document.createElement("div");
  el.className = "turn";
  const n = status ? status.passages : "the";
  el.innerHTML = `<div class="answer thinking" aria-label="Working"><span class="label">Searching ${n} passages…</span>
    <div class="skeleton"></div><div class="skeleton"></div><div class="skeleton"></div></div>`;
  messagesEl.appendChild(el);
  scrollDown();
  return el;
}

function addAnswerTurn(question, data) {
  const index = turns.length;
  const main = data.sources.find((s) => s.role === "answer");
  const el = document.createElement("div");
  el.className = "turn";

  let tag;
  if (!data.grounded) tag = `<div class="source-tag">${ICON.ban}<span>Not in the knowledge base · nothing guessed</span></div>`;
  else if (data.mode === "llm") {
    const files = [...new Set(data.sources.map((s) => s.file))].map((f) => `<span class="file">${esc(f)}</span>`).join(", ");
    tag = `<div class="source-tag">${ICON.file}<span>Written by Claude from</span>${files}</div>`;
  } else {
    tag = `<div class="source-tag">${ICON.file}<span class="file">${esc(main.file)}</span><span class="sep">›</span><span>${esc(main.heading)}</span></div>`;
  }

  const foot = [`<button type="button" class="why">How I found this ${ICON.arrow}</button>`];
  foot.push(`<span>${data.mode === "llm" ? "Claude + retrieval" : "Retrieval only · no AI model"}</span>`);
  if (data.context_used) foot.push(`<span>Follow-up of “${esc(data.context_used)}”</span>`);

  el.innerHTML = `<article class="answer ${data.grounded ? "" : "fallback"}">
      ${tag}
      <div class="prose">${markdown(data.answer)}</div>
      ${data.notice ? `<div class="notice">${esc(data.notice)}</div>` : ""}
      <footer class="turn-foot">${foot.join("")}</footer>
    </article>`;
  el.querySelector(".why").addEventListener("click", () => { select(index); openSheet("explain"); });
  el.querySelector(".answer").addEventListener("click", (e) => { if (!e.target.closest("button")) select(index); });
  messagesEl.appendChild(el);
  turns.push({ question, data, el });
  select(index);
  scrollDown();
}

function addErrorTurn(message, canRetry) {
  const el = document.createElement("div");
  el.className = "turn";
  el.innerHTML = `<div class="answer error" role="alert"><div class="prose"><p>${esc(message)}</p></div>
    ${canRetry ? '<button type="button" class="btn-quiet retry">Try again</button>' : ""}</div>`;
  const retry = el.querySelector(".retry");
  if (retry) retry.addEventListener("click", () => { el.remove(); send(lastQuestion, { resend: true }); });
  messagesEl.appendChild(el);
  scrollDown();
}

function showWelcome() {
  messagesEl.innerHTML = "";
  const node = $("welcome-template").content.cloneNode(true);
  node.querySelectorAll(".starter").forEach((btn) => {
    const q = btn.lastChild.textContent.trim();
    btn.addEventListener("click", () => send(q));
  });
  messagesEl.appendChild(node);
}

// ---------- explain panel ----------
function select(index) {
  selected = index;
  turns.forEach((t, i) => t.el.querySelector(".answer").classList.toggle("selected", i === index));
  renderExplain();
}

function renderIntro() {
  const n = status ? `${status.passages} passages in ${status.files.length} files` : "the knowledge files";
  explainEl.innerHTML = `
    <h2>How I find answers</h2>
    <p class="panel-lead">Every answer goes through the same four steps. Ask something to watch them happen.</p>
    <ol class="intro-steps">
      <li><span><strong>Read the question</strong>Keep the important words, drop filler like “what” and “the”, and add synonyms.</span></li>
      <li><span><strong>Search the knowledge files</strong>Score each of ${esc(n)} by how well it matches.</span></li>
      <li><span><strong>Check the evidence</strong>A passage must cover at least half of the question's important words.</span></li>
      <li><span><strong>Answer, or say I don't know</strong>Show the passage and its source, or admit the answer isn't in the files.</span></li>
    </ol>
    <p class="panel-cta">Tip: click any answer to see its steps again.</p>`;
}

function renderExplain() {
  const turn = turns[selected];
  if (!turn) return renderIntro();
  const { question, data } = turn;
  const t = data.trace;
  const steps = [];

  const kws = t.keywords.map((k) =>
    `<span class="kw">${esc(k.word)}${k.synonyms.length ? ` <em>+ ${esc(k.synonyms.join(", "))}</em>` : ""}</span>`).join("");
  const igs = t.ignored.map((w) => `<span class="ig">${esc(w)}</span>`).join("");
  steps.push({
    cls: "done", title: "Read the question",
    body: `<p class="quote">“${esc(question)}”</p>
      <div class="chips">${kws || '<span class="hint">No important words found.</span>'}${igs}</div>
      <p class="hint">Green words are searched (with synonyms). Crossed-out words are ignored.</p>`,
  });

  if (t.context) {
    steps.push({
      cls: "done", title: "Used the conversation",
      body: `<p>This looks like a follow-up, so I also searched with your previous question: <span class="quote">“${esc(t.context)}”</span></p>`,
    });
  }

  const top = t.candidates.length ? Math.max(...t.candidates.map((c) => c.score)) : 1;
  const cands = t.candidates.map((c) => `
    <li class="cand ${c.passed ? "passed" : ""}">
      <div class="cand-title">${esc(c.heading)}<span class="cand-file">${esc(c.file)}</span></div>
      <div class="meter" title="Covers ${pct(c.coverage)} of the question; needs ${pct(t.threshold)}">
        <span class="fill" style="--w:${pct(c.coverage)}"></span><span class="bar" style="--t:${pct(t.threshold)}"></span>
      </div>
      <div class="cand-meta"><span title="Match score ${c.score} (best: ${top})">covers ${pct(c.coverage)} of the question</span>
        <span class="verdict">${c.passed ? "✓ evidence" : "too weak"}</span></div>
    </li>`).join("");
  steps.push({
    cls: "done", title: `Searched ${t.searched.passages} passages in ${t.searched.files} files`,
    body: t.candidates.length
      ? `<ul class="cands">${cands}</ul><p class="hint">The bar shows how much of the question a passage covers. It needs to pass the line at ${pct(t.threshold)}.</p>`
      : `<p>No passage shares a single important word with the question.</p>`,
  });

  const main = data.sources.find((s) => s.role === "answer");
  let decision;
  if (!data.grounded) {
    decision = `<div class="decision no"><strong>No passage had enough evidence</strong>, so I said I don't know instead of guessing, and pointed you to the contact procedure in the FAQ.</div>`;
  } else if (data.mode === "llm") {
    const used = data.sources.map((s) => `${esc(s.file)} › ${esc(s.heading)}`).join("; ");
    decision = `<div class="decision"><strong>Claude wrote the answer</strong> using only the passages above, and cited: ${used}.</div>`;
  } else {
    decision = `<div class="decision"><strong>Showed ${esc(main.file)} › ${esc(main.heading)}</strong> word for word. No AI model was used, so nothing was rephrased or invented.</div>`;
  }
  if (data.notice) decision += `<p class="hint after-decision">${esc(data.notice)}</p>`;
  steps.push({ cls: data.grounded ? "done" : "stop", title: data.grounded ? "Answered with a source" : "Refused to guess", body: decision });

  explainEl.innerHTML = `<h2>How I found this</h2>
    <p class="panel-lead">The steps behind answer ${selected + 1} of ${turns.length}.</p>
    <ol class="steps">${steps.map((s, i) => `
      <li class="step ${s.cls}"><span class="step-n">${i + 1}</span><div><h3>${s.title}</h3>${s.body}</div></li>`).join("")}
    </ol>`;
  explainEl.scrollTop = 0;
}

// ---------- knowledge files tab ----------
async function renderFiles(highlight) {
  filesEl.innerHTML = `<p class="panel-lead">Loading…</p>`;
  try {
    const res = await fetch("/api/knowledge");
    const data = await res.json();
    const total = data.files.reduce((n, f) => n + f.sections.length, 0);
    const warnings = data.warnings.length
      ? `<div class="notice files-warning">${data.warnings.map(esc).join("<br>")}</div>` : "";
    filesEl.innerHTML = `<h2>What I know</h2>
      <p class="panel-lead">${total} sections in ${data.files.length} files. Edit any file in <code>knowledge/</code>, save, and ask again. No restart needed.</p>
      ${warnings}
      ${data.files.map((f) => `
        <div class="file-group"><h3>${ICON.file}${esc(f.file)} <small>${f.sections.length} sections</small></h3>
          ${f.sections.map((s) => `<details data-key="${esc(f.file)}|${esc(s.heading)}"><summary>${esc(s.heading)}</summary>
            <div class="prose">${markdown(s.text)}</div></details>`).join("")}
        </div>`).join("")}`;
    if (highlight) {
      const d = [...filesEl.querySelectorAll("details")].find((x) => x.dataset.key === highlight);
      if (d) { d.open = true; d.classList.add("flash"); d.scrollIntoView({ block: "center" }); }
    }
  } catch (err) {
    filesEl.innerHTML = `<p class="notice">Couldn't load the knowledge files. Is the server running?</p>`;
    console.error(err);
  }
}

function showTab(name) {
  const files = name === "files";
  $("tab-explain").setAttribute("aria-selected", String(!files));
  $("tab-files").setAttribute("aria-selected", String(files));
  explainEl.hidden = files;
  filesEl.hidden = !files;
  if (files) {
    const turn = turns[selected];
    const main = turn && turn.data.sources.find((s) => s.role === "answer");
    renderFiles(main ? `${main.file}|${main.heading}` : null);
  }
}

function openSheet(tab) {
  showTab(tab);
  if (!narrow.matches) return;
  panel.classList.add("open");
  backdrop.hidden = false;
}
function closeSheet() { panel.classList.remove("open"); backdrop.hidden = true; }

// ---------- server calls ----------
async function send(text, { resend = false } = {}) {
  const question = text.trim();
  if (!question) { input.focus(); return; }
  if (busy) return;
  lastQuestion = question;
  const welcome = messagesEl.querySelector(".welcome");
  if (welcome) welcome.remove();
  if (!resend) addUserTurn(question);
  input.value = "";
  autoGrow();
  setBusy(true);
  const thinking = addThinking();

  const body = { message: question, history };
  if (claudeAvailable()) body.mode = mode;

  try {
    const res = await fetch("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    let data;
    try { data = await res.json(); } catch { data = { error: `The server sent an unreadable reply (HTTP ${res.status}).` }; }
    thinking.remove();
    if (!res.ok || data.error) {
      addErrorTurn(data.error || `Request failed (HTTP ${res.status}).`, res.status >= 500);
    } else {
      addAnswerTurn(question, data);
      history.push({ role: "user", content: question }, { role: "assistant", content: data.answer });
      history = history.slice(-8);
    }
  } catch (err) {
    thinking.remove();
    addErrorTurn("Couldn't reach the chatbot server. Check that python app.py is still running, then try again.", true);
    console.error(err);
  } finally {
    setBusy(false);
    input.focus();
    refreshStatus();
  }
}

function setBusy(value) {
  busy = value;
  sendBtn.disabled = value;
  messagesEl.setAttribute("aria-busy", String(value));
}

const claudeAvailable = () => !!status && status.llm_provider === "anthropic" && status.llm_key_present;

async function refreshStatus() {
  const el = $("mode-status");
  const label = el.querySelector(".label");
  try {
    status = await (await fetch("/api/status")).json();
  } catch (err) {
    el.className = "mode-status error";
    label.textContent = "Server offline";
    return;
  }
  const sw = $("mode-switch");
  sw.hidden = !claudeAvailable();
  sw.querySelectorAll("button").forEach((b) => b.setAttribute("aria-checked", String(b.dataset.mode === mode)));

  if (claudeAvailable() && mode === "llm") {
    el.className = status.last_llm_error ? "mode-status error" : "mode-status ok";
    label.textContent = status.last_llm_error ? "Claude unavailable · using retrieval" : `Claude · ${status.model}`;
    el.title = status.last_llm_error || "Claude writes answers from the retrieved passages";
  } else {
    el.className = "mode-status ok";
    label.textContent = `Offline · ${status.passages} passages`;
    el.title = "No AI model is used. Answers are the best-matching passages from the knowledge files.";
  }

  const warnings = [...status.warnings];
  if (!status.passages) warnings.unshift("No knowledge loaded, so every question will get the safe fallback.");
  $("kb-warning").hidden = !warnings.length;
  $("kb-warning").textContent = warnings.length ? `Knowledge base: ${warnings.join(" · ")}` : "";
  if (selected < 0) renderIntro();
}

// ---------- wiring ----------
function autoGrow() { input.style.height = "auto"; input.style.height = `${Math.min(input.scrollHeight, 160)}px`; }

$("composer").addEventListener("submit", (e) => { e.preventDefault(); send(input.value); });
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); send(input.value); }
});
input.addEventListener("input", autoGrow);
$("new-chat").addEventListener("click", () => {
  if (busy) return;
  history = []; turns = []; selected = -1;
  showWelcome(); renderIntro(); showTab("explain");
  input.value = ""; input.focus();
});
$("tab-explain").addEventListener("click", () => showTab("explain"));
$("tab-files").addEventListener("click", () => showTab("files"));
$("open-files").addEventListener("click", () => openSheet("files"));
$("close-panel").addEventListener("click", closeSheet);
backdrop.addEventListener("click", closeSheet);
document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeSheet(); });
narrow.addEventListener("change", () => { if (!narrow.matches) closeSheet(); });
$("mode-switch").addEventListener("click", (e) => {
  const b = e.target.closest("button[data-mode]");
  if (b) { mode = b.dataset.mode; refreshStatus(); }
});

showWelcome();
renderIntro();
refreshStatus();
input.focus();
