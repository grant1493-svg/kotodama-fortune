#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
from datetime import date
from flask import Flask, request, render_template, jsonify
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
import line_tasks

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    pass


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
