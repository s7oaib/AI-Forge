/*
 * Greenfield College — embeddable chat widget (single file, zero dependencies).
 * Include anywhere:
 *   <script src="/static/chat_widget.js" data-endpoint="/api/v1/query"></script>
 */
(function () {
  "use strict";
  var script = document.currentScript;
  var ENDPOINT = (script && script.getAttribute("data-endpoint")) || "/api/v1/query";
  var STYLE_ID = "gfc-chat-widget-style";

  var css = [
    ".gfc-fab{position:fixed;bottom:20px;right:20px;z-index:99999;background:#1e3a8a;color:#fff;",
    "border:none;border-radius:24px;padding:12px 20px;font-size:14px;cursor:pointer;",
    "box-shadow:0 4px 16px rgba(0,0,0,.3)}",
    ".gfc-panel{position:fixed;bottom:76px;right:20px;width:340px;max-height:70vh;",
    "background:#fff;color:#111827;border-radius:12px;z-index:99999;display:none;",
    "flex-direction:column;box-shadow:0 8px 30px rgba(0,0,0,.35);overflow:hidden}",
    ".gfc-panel.gfc-open{display:flex}",
    ".gfc-header{background:#1e3a8a;color:#fff;padding:12px 16px;font-weight:600}",
    ".gfc-log{flex:1;overflow-y:auto;padding:12px;display:flex;gap:8px;flex-direction:column}",
    ".gfc-msg{padding:8px 12px;border-radius:10px;max-width:88%;font-size:13px;line-height:1.4;white-space:pre-wrap}",
    ".gfc-msg.user{align-self:flex-end;background:#e0e7ff}",
    ".gfc-msg.bot{align-self:flex-start;background:#f3f4f6}",
    ".gfc-src{font-size:11px;color:#4b5563;margin-top:4px}",
    ".gfc-input{display:flex;border-top:1px solid #e5e7eb}",
    ".gfc-input textarea{flex:1;border:none;padding:10px;font-size:13px;resize:none;outline:none}",
    ".gfc-input button{border:none;background:#1e3a8a;color:#fff;padding:0 18px;cursor:pointer}"
  ].join("");

  var style = document.createElement("style");
  style.id = STYLE_ID;
  style.textContent = css;
  document.head.appendChild(style);

  var panel = document.createElement("div");
  panel.className = "gfc-panel";
  panel.innerHTML =
    '<div class="gfc-header">Greenfield College Assistant</div>' +
    '<div class="gfc-log" aria-live="polite"></div>' +
    '<div class="gfc-input"><textarea rows="2" placeholder="Ask about admissions, fees, faculty..."></textarea>' +
    '<button type="button">Ask</button></div>';

  var fab = document.createElement("button");
  fab.className = "gfc-fab";
  fab.type = "button";
  fab.textContent = "Chat";
  fab.addEventListener("click", function () {
    panel.classList.toggle("gfc-open");
  });

  var log = panel.querySelector(".gfc-log");
  var input = panel.querySelector("textarea");
  var send = panel.querySelector("button");
  var history = [];

  function addMsg(role, text, src) {
    var el = document.createElement("div");
    el.className = "gfc-msg " + (role === "user" ? "user" : "bot");
    el.textContent = text;
    if (src && src.length) {
      var s = document.createElement("div");
      s.className = "gfc-src";
      s.textContent = "Source: " + src.map(function (x) { return x.doc_path + " > " + x.heading; }).join(", ");
      el.appendChild(s);
    }
    log.appendChild(el);
    log.scrollTop = log.scrollHeight;
  }

  function ask() {
    var msg = input.value.trim();
    if (!msg) return;
    input.value = "";
    addMsg("user", msg);
    send.disabled = true;
    fetch(ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg, history: history.slice(-6) }),
    })
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then(function (data) {
        addMsg("bot", data.answer, data.sources);
        history.push({ role: "user", content: msg });
        history.push({ role: "assistant", content: data.answer });
      })
      .catch(function (e) {
        addMsg("bot", "Sorry, the assistant is unreachable right now (" + e.message + ").");
      })
      .finally(function () {
        send.disabled = false;
      });
  }

  send.addEventListener("click", ask);
  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      ask();
    }
  });

  document.body.appendChild(panel);
  document.body.appendChild(fab);
  addMsg("bot", "Hello! Ask me about admissions, fees, faculty, facilities or campus life.");
})();
