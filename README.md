# 台股持股紀錄

一個以 Streamlit 建立的台股持股與交易紀錄工具。資料會儲存在本機 SQLite 資料庫，適合用來記錄買入、賣出、手續費與持股分布。

## 功能

- 新增、編輯、刪除台股交易紀錄
- 股票代碼自動帶入常見台股名稱
- 統計交易筆數、買入總額、賣出總額與手續費合計
- 依買入金額或股數產生持股分布圓餅圖
- 匯出 CSV，方便備份或再分析

## 技術

- Python
- Streamlit
- Pandas
- Plotly
- SQLite

## 安裝

```bash
pip install -r requirements.txt
```

## 執行

```bash
streamlit run "app _stock.py"
```

預設資料會存在 `./data/stocks.db`。如果要指定資料夾，可以設定環境變數：

```bash
set STOCK_DATA_DIR=./data
```

## 檔案結構

```text
assets/
├── app _stock.py          # Streamlit 主程式
├── requirements.txt       # Python 依賴
└── .devcontainer/         # 開發容器設定
```

## 備註

此工具僅用於個人交易紀錄與視覺化，不提供投資建議。
