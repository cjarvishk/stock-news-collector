#!/usr/bin/env python3
"""
Stock Market News Collector
Collects news from US, Japan, Korea, and European stock markets via RSS feeds.
Outputs formatted markdown report.
"""

import feedparser
import requests
import yaml
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import defaultdict

# Load configuration
def load_config(config_path=None):
    """Load configuration from YAML file."""
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def fetch_rss_feed(url, timeout=10):
    """Fetch and parse an RSS feed."""
    try:
        response = requests.get(url, timeout=timeout, headers={
            "User-Agent": "StockNewsCollector/1.0"
        })
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        return feed
    except Exception as e:
        print(f"⚠️  Failed to fetch {url}: {e}", file=sys.stderr)
        return None

def collect_news(config):
    """Collect news from all configured markets and sources."""
    markets = config.get("markets", {})
    max_items = config.get("output", {}).get("max_items_per_source", 5)
    tz = ZoneInfo(config.get("output", {}).get("time_zone", "Asia/Hong_Kong"))
    
    all_news = defaultdict(list)
    
    for market_key, market_info in markets.items():
        market_name = market_info.get("name", market_key.upper())
        sources = market_info.get("sources", [])
        
        for source in sources:
            source_name = source.get("name", "Unknown")
            feed_url = source.get("url", "")
            
            if not feed_url:
                continue
            
            feed = fetch_rss_feed(feed_url)
            if feed is None:
                continue
            
            for entry in feed.entries[:max_items]:
                title = entry.get("title", "No title")
                link = entry.get("link", "")
                published = entry.get("published", "")
                summary = entry.get("summary", "")
                
                # Clean up summary - remove HTML tags
                if "<" in summary:
                    import html
                    summary = html.unescape(summary)
                    import re
                    summary = re.sub(r'<[^>]+>', '', summary)
                    summary = summary[:200] + "..." if len(summary) > 200 else summary
                
                all_news[market_key].append({
                    "title": title,
                    "link": link,
                    "published": published,
                    "summary": summary,
                    "source": source_name
                })
    
    return all_news

def format_markdown(all_news, config):
    """Format collected news as markdown report."""
    markets = config.get("markets", {})
    tz = ZoneInfo(config.get("output", {}).get("time_zone", "Asia/Hong_Kong"))
    now = datetime.now(tz)
    
    report = []
    report.append(f"# 📊 股市新聞速報")
    report.append(f"")
    report.append(f"**📅 收集時間：** {now.strftime('%Y-%m-%d %H:%M')} (HKT)")
    report.append(f"")
    
    for market_key, market_info in markets.items():
        market_name = market_info.get("name", market_key.upper())
        news_items = all_news.get(market_key, [])
        
        report.append(f"## {market_name}")
        report.append(f"")
        
        if not news_items:
            report.append(f"*暫無新聞*")
            report.append(f"")
            continue
        
        for item in news_items:
            source = item.get("source", "Unknown")
            title = item.get("title", "No title")
            link = item.get("link", "")
            published = item.get("published", "")
            summary = item.get("summary", "")
            
            report.append(f"### [{title}]({link})")
            report.append(f"")
            report.append(f"- **來源：** {source}")
            report.append(f"- **時間：** {published}")
            if summary:
                report.append(f"- **摘要：** {summary}")
            report.append(f"")
    
    report.append("---")
    report.append(f"*由 Stock News Collector 自動生成*")
    
    return "\n".join(report)

def main():
    """Main entry point."""
    config = load_config()
    
    print("📡 正在收集股市新聞...")
    all_news = collect_news(config)
    
    print("📝 正在生成報告...")
    report = format_markdown(all_news, config)
    
    # Save to file
    output_dir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(output_dir, exist_ok=True)
    
    tz = ZoneInfo(config.get("output", {}).get("time_zone", "Asia/Hong_Kong"))
    now = datetime.now(tz)
    filename = f"report_{now.strftime('%Y-%m-%d_%H-%M')}.md"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"✅ 報告已保存至 {filepath}")
    print(f"📊 收集完成！")
    
    # Also print to stdout
    print("\n" + "="*50)
    print(report[:2000])  # Print first 2000 chars
    if len(report) > 2000:
        print("... (報告過長，請查看完整文件)")
    print("="*50)

if __name__ == "__main__":
    main()
