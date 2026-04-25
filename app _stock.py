import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import os
from datetime import date
from pathlib import Path

st.set_page_config(page_title="台股持股紀錄", page_icon="📈", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans TC', sans-serif; }
.block-container { padding-top: 2rem; }
.stDataFrame { border-radius: 10px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ── 股票代碼對照表 ─────────────────────────────────────────
TW_STOCKS = {
    "0050":"元大台灣50","0056":"元大高股息","00878":"國泰永續高股息","00881":"國泰台灣5G+",
    "6757":"台灣虎航","00900":"富邦特選高股息30","00919":"群益台灣精選高息","00929":"中信美國500",
    "1101":"台灣水泥","1102":"亞洲水泥","1216":"統一企業","1301":"台塑","1303":"南亞","1326":"台化",
    "1402":"遠東新","1476":"儒鴻","1477":"聚陽","1503":"士電","1504":"東元","1519":"華城",
    "2002":"中鋼","2049":"上銀","2059":"川湖","2101":"南港","2105":"正新","2201":"裕隆",
    "2204":"中華","2207":"和泰車","2208":"台船","2301":"光寶科","2303":"聯電","2308":"台達電",
    "2312":"金寶","2313":"華通","2317":"鴻海","2324":"仁寶","2327":"國巨","2330":"台積電",
    "2337":"旺宏","2344":"華邦電","2345":"智邦","2347":"聯強","2352":"佳世達","2353":"宏碁",
    "2354":"鴻準","2356":"英業達","2357":"華碩","2360":"致茂","2376":"技嘉","2377":"微星",
    "2379":"瑞昱","2382":"廣達","2385":"群光","2395":"研華","2397":"聯詠","2408":"南亞科",
    "2409":"友達","2412":"中華電","2454":"聯發科","2458":"義隆","2474":"可成","2481":"強茂",
    "2492":"華新科","2498":"宏達電","2603":"長榮海運","2606":"裕民","2609":"陽明","2610":"華航",
    "2615":"萬海","2618":"長榮航","2633":"台灣高鐵","2634":"漢翔","2727":"王品","2729":"瓦城",
    "2801":"彰銀","2880":"華南金","2881":"富邦金","2882":"國泰金","2883":"開發金","2884":"玉山金",
    "2885":"元大金","2886":"兆豐金","2887":"台新金","2888":"新光金","2890":"永豐金",
    "2891":"中信金","2892":"第一金","2912":"統一超","3008":"大立光","3045":"台灣大",
    "3231":"緯創","3481":"群創","3711":"日月光投控","4966":"譜瑞-KY","5483":"中美晶",
    "5876":"上海商銀","5880":"合庫金","6488":"環球晶","6505":"台塑石化","6669":"緯穎",
    "6770":"力積電","9904":"寶成","9910":"豐泰","9914":"美利達","9921":"巨大",
    "9933":"中鼎","9940":"信義","9941":"裕融","9945":"潤泰全","9958":"世紀鋼",
}

# ── SQLite 資料庫 ──────────────────────────────────────────
# Streamlit Cloud 可用 /tmp（重啟會消失）；本機/VPS 改成 ./data/ 永久保存
DATA_DIR = Path(os.environ.get("STOCK_DATA_DIR", "./data"))
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "stocks.db"

@st.cache_resource
def get_conn():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_date TEXT NOT NULL,
            code      TEXT NOT NULL,
            name      TEXT NOT NULL,
            trade_type TEXT NOT NULL,
            shares    REAL NOT NULL,
            net_amount REAL NOT NULL,
            fee       REAL NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    return conn

conn = get_conn()

def load_records() -> pd.DataFrame:
    df = pd.read_sql("SELECT * FROM trades ORDER BY trade_date DESC, id DESC", conn)
    return df

def add_record(trade_date, code, name, trade_type, shares, net_amount, fee):
    conn.execute(
        "INSERT INTO trades (trade_date,code,name,trade_type,shares,net_amount,fee) VALUES (?,?,?,?,?,?,?)",
        (str(trade_date), code, name, trade_type, float(shares), float(net_amount), float(fee))
    )
    conn.commit()

def update_record(rid, trade_date, code, name, trade_type, shares, net_amount, fee):
    conn.execute(
        "UPDATE trades SET trade_date=?,code=?,name=?,trade_type=?,shares=?,net_amount=?,fee=? WHERE id=?",
        (str(trade_date), code, name, trade_type, float(shares), float(net_amount), float(fee), rid)
    )
    conn.commit()

def delete_record(rid):
    conn.execute("DELETE FROM trades WHERE id=?", (rid,))
    conn.commit()

# ── Session state ──────────────────────────────────────────
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

# ── 標題 ───────────────────────────────────────────────────
st.markdown("## 📈 台股持股紀錄")
st.caption(f"💾 資料儲存於：`{DB_PATH.resolve()}`")
st.markdown("---")

# ── 讀取資料 ───────────────────────────────────────────────
df = load_records()

# ── 統計卡片 ──────────────────────────────────────────────
buy_df  = df[df["trade_type"] == "買入"] if not df.empty else pd.DataFrame()
sell_df = df[df["trade_type"] == "賣出"] if not df.empty else pd.DataFrame()
total_buy  = buy_df["net_amount"].sum()  if not buy_df.empty  else 0
total_sell = sell_df["net_amount"].sum() if not sell_df.empty else 0
total_fee  = df["fee"].sum() if not df.empty else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("📋 交易筆數", f"{len(df)} 筆")
c2.metric("🟢 買入總額", f"NT$ {total_buy:,.0f}")
c3.metric("🔴 賣出總額", f"NT$ {total_sell:,.0f}")
c4.metric("💰 手續費合計", f"NT$ {total_fee:,.0f}")

st.markdown("---")

# ── 新增 / 編輯表單 ────────────────────────────────────────
edit_id = st.session_state.edit_id
is_editing = edit_id is not None

if is_editing:
    edit_row = df[df["id"] == edit_id].iloc[0]
    default_date   = pd.to_datetime(edit_row["trade_date"]).date()
    default_code   = edit_row["code"]
    default_name   = edit_row["name"]
    default_type   = edit_row["trade_type"]
    default_shares = int(edit_row["shares"])
    default_amount = float(edit_row["net_amount"])
    default_fee_v  = float(edit_row["fee"])
    expander_label = "✏️ 編輯交易紀錄"
else:
    default_date   = date.today()
    default_code   = ""
    default_name   = ""
    default_type   = "買入"
    default_shares = 0
    default_amount = 0.0
    default_fee_v  = 0.0
    expander_label = "➕ 新增交易紀錄"

with st.expander(expander_label, expanded=True):
    col1, col2 = st.columns(2)

    with col1:
        trade_date = st.date_input("📅 交易日期", value=default_date)
        trade_type = st.selectbox("⬆⬇ 買入／賣出", ["買入", "賣出"],
                                  index=0 if default_type == "買入" else 1)
        shares = st.number_input("📊 成交股數（股）", min_value=0, value=default_shares, step=1)

    with col2:
        code_input = st.text_input("🏷️ 股票代碼", value=default_code, placeholder="如：2330")
        # 自動帶入名稱
        auto_name = TW_STOCKS.get(code_input.strip(), "")
        if auto_name:
            st.caption(f"✅ 自動帶入：**{auto_name}**")
            resolved_name = auto_name
        else:
            resolved_name = default_name if is_editing and not code_input != default_code else ""
            if len(code_input) >= 4:
                st.caption("⚠️ 未收錄代碼，請手動輸入名稱")

        stock_name = st.text_input("📛 股票名稱", value=resolved_name,
                                   placeholder="輸入代碼後自動帶入，或手動填寫")
        net_amount = st.number_input("💵 淨收付金額（元）", min_value=0.0,
                                     value=default_amount, step=100.0, format="%.0f")
        fee = st.number_input("💸 手續費（元）", min_value=0.0,
                              value=default_fee_v, step=1.0, format="%.0f")

    b1, b2, _ = st.columns([1, 1, 5])
    with b1:
        submit = st.button("💾 儲存" if is_editing else "✅ 新增",
                           use_container_width=True, type="primary")
    with b2:
        if is_editing and st.button("❌ 取消", use_container_width=True):
            st.session_state.edit_id = None
            st.rerun()

    if submit:
        err = []
        if not code_input.strip(): err.append("請輸入股票代碼")
        if not stock_name.strip(): err.append("請輸入股票名稱")
        if shares <= 0:            err.append("成交股數須大於 0")
        if net_amount <= 0:        err.append("淨收付金額須大於 0")
        if err:
            for e in err: st.error(e)
        else:
            if is_editing:
                update_record(edit_id, trade_date, code_input.strip(), stock_name.strip(),
                              trade_type, shares, net_amount, fee)
                st.session_state.edit_id = None
                st.success("✅ 已更新")
            else:
                add_record(trade_date, code_input.strip(), stock_name.strip(),
                           trade_type, shares, net_amount, fee)
                st.success("✅ 已新增")
            st.rerun()

st.markdown("---")

# ── 交易紀錄 ──────────────────────────────────────────────
st.markdown("### 📋 交易紀錄")
df = load_records()

if df.empty:
    st.info("尚無交易紀錄，請在上方表單新增。")
else:
    search = st.text_input("🔍 搜尋代碼或名稱", placeholder="輸入關鍵字...")
    disp = df.copy()
    if search:
        disp = disp[disp["code"].str.contains(search, na=False) |
                    disp["name"].str.contains(search, na=False)]

    show = disp[["trade_date","code","name","trade_type","shares","net_amount","fee"]].copy()
    show.columns = ["交易日期","代碼","名稱","類型","股數","淨收付金額(元)","手續費(元)"]
    show["股數"]        = show["股數"].apply(lambda x: f"{int(x):,}")
    show["淨收付金額(元)"] = show["淨收付金額(元)"].apply(lambda x: f"{x:,.0f}")
    show["手續費(元)"]   = show["手續費(元)"].apply(lambda x: f"{x:,.0f}")

    st.dataframe(show.reset_index(drop=True), use_container_width=True, hide_index=True)

    # 編輯 / 刪除
    st.markdown("**操作：**")
    for _, row in disp.iterrows():
        r1, r2, r3 = st.columns([6, 1, 1])
        with r1:
            st.caption(
                f"{row['trade_date']}　**{row['code']}** {row['name']}　"
                f"{row['trade_type']}　{int(row['shares']):,}股　NT${row['net_amount']:,.0f}"
            )
        with r2:
            if st.button("✏️", key=f"e{row['id']}", help="編輯", use_container_width=True):
                st.session_state.edit_id = int(row["id"])
                st.rerun()
        with r3:
            if st.button("🗑️", key=f"d{row['id']}", help="刪除", use_container_width=True):
                delete_record(int(row["id"]))
                st.rerun()

st.markdown("---")

# ── 圓餅圖 ────────────────────────────────────────────────
st.markdown("### 🥧 買入持股分布")
df = load_records()
buy_df = df[df["trade_type"] == "買入"] if not df.empty else pd.DataFrame()

if buy_df.empty:
    st.info("新增買入交易後，圓餅圖會顯示在這裡。")
else:
    chart_mode = st.radio("依據", ["金額", "股數"], horizontal=True)
    val_col = "net_amount" if chart_mode == "金額" else "shares"

    pie = (buy_df.groupby(["code","name"])[val_col]
           .sum().reset_index())
    pie["label"] = pie["code"] + " " + pie["name"]
    pie = pie.sort_values(val_col, ascending=False)

    fig = px.pie(pie, values=val_col, names="label", hole=0.45,
                 color_discrete_sequence=px.colors.qualitative.Set2 +
                                         px.colors.qualitative.Pastel)
    fig.update_traces(
        textposition="inside", textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>" + (
            "金額：NT$ %{value:,.0f}<extra></extra>" if chart_mode == "金額"
            else "股數：%{value:,.0f} 股<extra></extra>"),
        pull=[0.03] * len(pie),
    )
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="v", x=1.02, y=0.5),
        margin=dict(t=20, b=20, l=20, r=140),
        height=440,
        font=dict(family="Noto Sans TC, sans-serif", size=13),
    )
    st.plotly_chart(fig, use_container_width=True)

    # 明細表
    total = pie[val_col].sum()
    pie["佔比"] = (pie[val_col] / total * 100).map(lambda x: f"{x:.1f}%")
    if chart_mode == "金額":
        pie["金額"] = pie[val_col].map(lambda x: f"NT$ {x:,.0f}")
        st.dataframe(pie[["label","金額","佔比"]].rename(columns={"label":"股票"}),
                     use_container_width=True, hide_index=True)
    else:
        pie["股數"] = pie[val_col].map(lambda x: f"{int(x):,} 股")
        st.dataframe(pie[["label","股數","佔比"]].rename(columns={"label":"股票"}),
                     use_container_width=True, hide_index=True)

# ── 匯出 CSV ──────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📥 匯出資料")
df = load_records()
if not df.empty:
    csv = df.drop(columns=["id"]).rename(columns={
        "trade_date":"交易日期","code":"代碼","name":"名稱",
        "trade_type":"類型","shares":"股數","net_amount":"淨收付金額","fee":"手續費"
    }).to_csv(index=False, encoding="utf-8-sig")
    st.download_button("⬇️ 下載 CSV", data=csv,
                       file_name="台股持股紀錄.csv", mime="text/csv")
else:
    st.caption("尚無資料可匯出")
