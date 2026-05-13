# 📊 Stock Market News Collector

跨市場股市新聞自動收集系統，支援 **美國**、**日本**、**韓國**、**歐洲** 股票市場。

## ✨ 功能

- 🌍 多市場覆蓋：美國、日本、韓國、歐洲股市
- 📡 RSS 新聞源自動收集
- 📝 Markdown 格式報告
- ⏰ 定時自動運行（Cron Job）
- 🚀 輕量級，無需資料庫

## 🚀 快速開始

### 1. 安裝依賴

```bash
cd stock-news-collector
pip install -r requirements.txt
```

### 2. 運行收集器

```bash
python collector.py
```

### 3. 查看報告

報告會保存在 `reports/` 目錄，格式為 `report_YYYY-MM-DD_HH-MM.md`。

## ⚙️ 配置

編輯 `config.yaml` 來自定義：

- **新聞來源**：新增或移除 RSS feed
- **每來源新聞數量**：`max_items_per_source`
- **時區**：`time_zone`（預設 Asia/Hong_Kong）

## 📁 專案結構

```
stock-news-collector/
├── collector.py          # 主程式
├── config.yaml           # 配置檔案
├── requirements.txt      # Python 依賴
├── README.md            # 說明文件
├── .gitignore           # Git 忽略規則
└── reports/             # 生成的報告（自動建立）
    └── report_*.md
```

## 🔄 自動化

透過 Hermes Agent Cron Job 定時運行：

```bash
# 每 4 小時收集一次
hermes cron create --schedule "0 */4 * * *" --prompt "Run python ~/projects/stock-news-collector/collector.py and commit any new reports to GitHub"
```

## 📊 支援的市場

| 市場 | 新聞來源 |
|------|----------|
| 🇺🇸 美國 | Reuters, CNBC, MarketWatch |
| 🇯🇵 日本 | Reuters Asia, Nikkei Asia, Bloomberg |
| 🇰🇷 韓國 | Korea Herald, Yonhap News, Reuters Asia |
| 🇪🇺 歐洲 | Reuters, Financial Times, Bloomberg |

## 📄 許可證

MIT License
