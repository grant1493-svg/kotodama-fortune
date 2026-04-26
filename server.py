#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
from datetime import date
from flask import Flask, request, render_template, jsonify
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

sys.path.insert(0, os.path.dirname(__file__))
import line_tasks

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "ファイルが送信されていません"}), 400

    f = request.files["file"]
    if not f.filename.endswith(".txt"):
        return jsonify({"error": ".txtファイルを選択してください"}), 400

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return jsonify({"error": ".envファイルにAPIキーを設定してください"}), 500

    raw_text = f.read().decode("utf-8", errors="replace")
    parsed = line_tasks.parse_line_log(raw_text)
    messages = parsed["messages"]

    if not messages:
        return jsonify({"error": "メッセージが見つかりませんでした。LINEのエクスポート形式を確認してください"}), 400

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    chunks = line_tasks.split_into_chunks(messages)
    all_tasks = []
    for chunk in chunks:
        tasks = line_tasks.extract_tasks_via_api(chunk, client)
        all_tasks.extend(tasks)

    all_tasks = line_tasks.deduplicate_tasks(all_tasks)

    if not all_tasks:
        return jsonify({"error": "タスクが見つかりませんでした"}), 200

    meta = {
        "start_date": parsed["start_date"],
        "end_date": parsed["end_date"],
        "generated_at": date.today().isoformat(),
    }
    html = line_tasks.generate_html(all_tasks, meta)
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
