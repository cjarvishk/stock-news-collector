#!/usr/bin/env python3
"""
跨市場股票新聞收集系統
Collects stock market news from US, Japan, Korea, and Europe via RSS feeds.
"""

import os
import sys
import yaml
import hashlib
import feedparser
import requests
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import List
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

@dataclass
class NewsItem:
    title: str
    link: str
    summary: str
    source: str
    region: str
    published: str  # ISO format
    published_dt: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def dedup_key(self) -> str:
        """Generate a hash-based dedup key from title."""
        return hashlib.md5(self.title.lower().strip().encode()).hexdigest()

def load_config(config_path: str = None) -> dict:
    """Load configuration from YAML file."""
    if config_path is None:
        config_path = os.path.join(PROJECT_DIR, "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def fetch_feed(feed_url: str, timeout: int = 30):
    """Fetch a single RSS feed with error handling."""
    try:
        # Some feeds need a proper User-Agent
        headers = {
            "User-Agent": "StockNewsCollector/1.0 (https://github.com/stock-news-collector)"
        }
        response = requests.get(feed_url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return feedparser.parse(response.content)
    except Exception as e:
        print(f"  ⚠️  Failed to fetch {feed_url}: {e}")
        return feedparser.parse("")  # Empty feed

def extract_items(feed, source_name: str, region: str, max_items: int = 10) -> List[NewsItem]:
    """Extract news items from a parsed feed."""
    items = []
    for entry in feed.entries[:max_items]:
        try:
            # Get published date
            published = ""
            published_dt = datetime.now(timezone.utc)
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                from time import mktime, timezone as time_tz
                ts = mktime(entry.published_parsed)
                published_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                published = published_dt.isoformat()
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                from time import mktime, timezone as time_tz
                ts = mktime(entry.updated_parsed)
                published_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                published = published_dt.isoformat()

            # Get summary/description
            summary = ""
            for attr in ["summary", "description"]:
                if hasattr(entry, attr) and getattr(entry, attr):
                    # Strip HTML tags
                    import re
                    text = re.sub(r'<[^>]+>', '', getattr(entry, attr))
                    summary = text.strip()[:500]  # Limit length
                    break

            items.append(NewsItem(
                title=getattr(entry, 'title', '無標題').strip(),
                link=getattr(entry, 'link', '#'),
                summary=summary,
                source=source_name,
                region=region,
                published=published,
                published_dt=published_dt
            ))
        except Exception as e:
            print(f"  ⚠️  Failed to parse entry: {e}")
            continue
    return items

def dedup_items(items: List[NewsItem], threshold: float = 0.85) -> List[NewsItem]:
    """Remove duplicate items based on title similarity (hash-based)."""
    seen = set()
    unique = []
    for item in items:
        key = item.dedup_key()
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique

def collect_news(config: dict) -> dict:
    """
    Collect news from all configured feeds.
    Returns dict: {region_code: [NewsItem, ...]}
    """
    settings = config.get("settings", {})
    max_per_feed = settings.get("max_items_per_feed", 10)
    max_per_region = settings.get("max_items_per_region", 15)
    dedup_threshold = settings.get("dedup_threshold", 0.85)

    results = {}

    for region_code, region_config in config["regions"].items():
        print(f"\n📡 收集 {region_config['flag']} {region_config['name']}...")
        all_items = []

        for feed_info in region_config["feeds"]:
            feed_name = feed_info["name"]
            feed_url = feed_info["url"]
            print(f"  📰 {feed_name}...", end=" ")

            feed = fetch_feed(feed_url)
            if feed.bozo and not feed.entries:
                print("❌ (解析失敗)")
                continue

            items = extract_items(feed, feed_name, region_code, max_per_feed)
            all_items.extend(items)
            print(f"✅ {len(items)} 則")

        # Dedup and limit
        all_items = dedup_items(all_items, dedup_threshold)
        # Sort by time (newest first)
        all_items.sort(key=lambda x: x.published_dt, reverse=True)
        results[region_code] = all_items[:max_per_region]
        print(f"  📊 {region_config['name']} 共 {len(results[region_code])} 則新聞")

    return results

def generate_report(results: dict, config: dict) -> str:
    """Generate a markdown report from collected news."""
    now = datetime.now(timezone.utc)
    report_time = now.strftime("%Y-%m-%d %H:%M UTC")

    lines = []
    lines.append(f"# 📈 全球股市新聞速報")
    lines.append(f"\n> 收集時間: {report_time}")
    lines.append(f"> 涵蓋市場: 🇺🇸 美國 | 🇯🇵 日本 | 🇰🇷 韓國 | 🇪🇺 歐洲\n")

    for region_code, region_config in config["regions"].items():
        items = results.get(region_code, [])
        if not items:
            continue

        lines.append(f"---\n")
        lines.append(f"## {region_config['flag']} {region_config['name']}\n")

        for i, item in enumerate(items, 1):
            time_str = ""
            if item.published:
                dt = datetime.fromisoformat(item.published.replace('Z', '+00:00'))
                time_str = dt.strftime("%m/%d %H:%M")

            lines.append(f"### {i}. {item.title}")
            if time_str:
                lines.append(f"*🕐 {time_str} | 📡 {item.source}*\n")
            else:
                lines.append(f"*📡 {item.source}*\n")

            if item.summary:
                lines.append(f"{item.summary}\n")

            lines.append(f"[🔗 閱讀全文]({item.link})\n")

    lines.append("---\n")
    lines.append(f"*由 Stock News Collector 自動生成*")

    return "\n".join(lines)

def save_report(report: str, output_dir: str = None) -> str:
    """Save report to a timestamped markdown file."""
    if output_dir is None:
        output_dir = os.path.join(PROJECT_DIR, "reports")
    os.makedirs(output_dir, exist_ok=True)

    now = datetime.now(timezone.utc)
    filename = now.strftime("report_%Y%m%d_%H%M.md")
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)

    return filepath

def main():
    """Main entry point."""
    print("=" * 60)
    print("📈 全球股市新聞收集系統")
    print("=" * 60)

    # Load config
    config = load_config()
    settings = config.get("settings", {})

    # Collect news
    results = collect_news(config)

    # Generate report
    report = generate_report(results, config)

    # Save report
    output_dir = os.path.join(PROJECT_DIR, settings.get("output_dir", "reports"))
    filepath = save_report(report, output_dir)

    # Count total
    total = sum(len(items) for items in results.values())
    print(f"\n{'=' * 60}")
    print(f"✅ 收集完成！共 {total} 則新聞")
    print(f"📄 報告已儲存: {filepath}")
    print(f"{'=' * 60}")

    # Print report to stdout
    print("\n" + report)

    return filepath

if __name__ == "__main__":
    main()
