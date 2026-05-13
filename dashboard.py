#!/usr/bin/env python3
"""
Stock News Dashboard - Web Interface
Serves a real-time dashboard for viewing stock market news reports.
"""

from flask import Flask, render_template, send_from_directory, jsonify
import os
import yaml
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import re

app = Flask(__name__)

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_latest_report():
    """Get the most recent report file."""
    reports = []
    for f in os.listdir(REPORTS_DIR):
        if f.startswith("report_") and f.endswith(".md"):
            filepath = os.path.join(REPORTS_DIR, f)
            reports.append((filepath, os.path.getmtime(filepath)))
    
    if not reports:
        return None
    
    reports.sort(key=lambda x: x[1], reverse=True)
    return reports[0][0]

def parse_markdown_report(filepath):
    """Parse markdown report into structured data."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    sections = []
    current_section = None
    current_items = []
    
    for line in content.split("\n"):
        if line.startswith("## ") and not line.startswith("### "):
            if current_section:
                sections.append({
                    "title": current_section,
                    "items": current_items
                })
            current_section = line[3:].strip()
            current_items = []
        elif line.startswith("### ["):
            item = {}
            # Extract title and link
            bracket_end = line.find("]")
            paren_end = line.find(")")
            if bracket_end != -1 and paren_end != -1:
                item["title"] = line[5:bracket_end]
                item["link"] = line[paren_end-1:paren_end]
            current_items.append(item)
        elif line.startswith("- **來源：**") and current_items:
            current_items[-1]["source"] = line.replace("- **來源：**", "").strip()
        elif line.startswith("- **時間：**") and current_items:
            current_items[-1]["time"] = line.replace("- **時間：**", "").strip()
        elif line.startswith("- **摘要：**") and current_items:
            current_items[-1]["summary"] = line.replace("- **摘要：**", "").strip()
    
    if current_section:
        sections.append({
            "title": current_section,
            "items": current_items
        })
    
    return sections

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/news")
def api_news():
    """API endpoint for real-time news data."""
    try:
        latest = get_latest_report()
        if not latest:
            return jsonify({"error": "暫無報告數據"})
        
        sections = parse_markdown_report(latest)
        tz = ZoneInfo("Asia/Hong_Kong")
        timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        
        return jsonify({
            "timestamp": timestamp,
            "sections": sections,
            "report_file": os.path.basename(latest)
        })
    except Exception as e:
        return jsonify({"error": f"載入失敗: {str(e)}"})

@app.route("/reports/<filename>")
def serve_report(filename):
    return send_from_directory(REPORTS_DIR, filename)

if __name__ == "__main__":
    os.makedirs(REPORTS_DIR, exist_ok=True)
    print("🚀 股市新聞 Dashboard 已啟動！")
    print("📱 訪問 http://localhost:8080 查看即時新聞")
    print("🔄 按 Ctrl+C 停止伺服器")
    app.run(host="0.0.0.0", port=8080, debug=True)
