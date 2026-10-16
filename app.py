"""College Information Assistant - web server.

Run:  python app.py      then open http://127.0.0.1:5000
"""

from __future__ import annotations

import logging

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

from chatbot.answer import ChatEngine, InputError
from chatbot.config import PROJECT_DIR, Settings, load_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("app")


def create_app(settings: Settings | None = None, engine: ChatEngine | None = None) -> Flask:
    settings = settings or load_settings()
    engine = engine or ChatEngine(settings.knowledge_dir, settings.model, settings.llm_requested)
    app = Flask(__name__, static_folder=str(PROJECT_DIR / "static"), static_url_path="/static")
    app.config["ENGINE"] = engine

    @app.get("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    @app.get("/api/status")
    def status():
        return jsonify(engine.status())

    @app.get("/api/knowledge")
    def knowledge():
        return jsonify(engine.knowledge())

    @app.post("/api/chat")
    def chat():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(error="Send JSON like {\"message\": \"your question\"}."), 400
        mode = data.get("mode")  # "llm", "offline", or omitted for the server default
        use_llm = {"llm": True, "offline": False}.get(mode)
        try:
            return jsonify(engine.answer(data.get("message"), data.get("history"), use_llm=use_llm))
        except InputError as exc:
            return jsonify(error=str(exc)), 400

    @app.errorhandler(HTTPException)
    def http_error(exc):
        return jsonify(error=exc.description), exc.code

    @app.errorhandler(Exception)
    def unexpected(exc):
        log.exception("Unexpected error while handling %s", request.path)
        return jsonify(error="Something went wrong on the server. Check the terminal for details."), 500

    return app


if __name__ == "__main__":
    settings = load_settings()
    app = create_app(settings)
    st = app.config["ENGINE"].status()
    print(f"\n  College Information Assistant")
    print(f"  Knowledge: {st['passages']} passages from {len(st['files'])} files in {settings.knowledge_dir}")
    for w in st["warnings"]:
        print(f"  WARNING: {w}")
    mode = f"LLM ({settings.model}) with retrieval fallback" if st["mode"] == "llm" else "offline retrieval (no LLM)"
    print(f"  Answer mode: {mode}")
    print(f"  Open http://{settings.host}:{settings.port} in your browser (Ctrl+C to stop)\n")
    app.run(host=settings.host, port=settings.port, debug=False)
