import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

st.set_page_config(page_title="台股持股紀錄", page_icon="📈", layout="wide")

# ── 自訂 CSS ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans TC', sans-serif; }
.block-container { padding-top: 2rem; }
h1 { font-size: 1.6rem !important; }
.metric-card {
    background: #fff;
    border-radius: 12px;
    padding: 16px 20px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.stDataFrame { border-radius: 10px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ── 股票代碼對照表 ─────────────────────────────────────────
TW_STOCKS = {
    "0050":"元大台灣50","0056":"元大高股息","00878":"國泰永續高股息","00881":"國泰台灣5G+",
    "00891":"中信關鍵半導體","00900":"富邦特選高股息30","00919":"群益台灣精選高息","00929":"中信美國500",
    "1101":"台灣水泥","1102":"亞洲水泥","1216":"統一企業","1301":"台塑","1303":"南亞","1326":"台化",
    "1402":"遠東新","1476":"儒鴻","1477":"聚陽","1503":"士電","1504":"東元","1519":"華城",
    "2002":"中鋼","2049":"上銀","2059":"川湖","2101":"南港","2105":"正新","2201":"裕隆",
    "2204":"中華","2207":"和泰車","2208":"台船","2301":"光寶科","2303":"聯電","2308":"台達電",
    "2312":"金寶","2313":"華通","2317":"鴻海","2324":"仁寶","2327":"國巨","2330":"台積電",
    "2337":"旺宏","2344":"華邦電","2345":"智邦","2347":"聯強","2352":"佳世達","2353":"宏碁",
    "2354":"鴻準","2356":"英業達","2357":"華碩","2360":"致茂","2376":"技嘉","2377":"微星",
    "2379":"瑞昱","2382":"廣達","2385":"群光","2395":"研華","2397":"聯詠","2408":"南亞科",
    "2409":"友達","2412":"中華電","2454":"聯發科","2458":"義隆","2474":"可成","2481":"強茂",
    "2492":"華新科","2498":"宏達電","2501":"國建","2520":"冠德","2542":"興富發","2548":"華固",
    "2601":"益航","2603":"長榮海運","2606":"裕民","2609":"陽明","2610":"華航","2615":"萬海",
    "2618":"長榮航","2633":"台灣高鐵","2634":"漢翔","2702":"華園","2704":"國賓","2707":"晶華",
    "2727":"王品","2729":"瓦城","2801":"彰銀","2823":"中壽","2832":"台產","2880":"華南金",
    "2881":"富邦金","2882":"國泰金","2883":"開發金","2884":"玉山金","2885":"元大金","2886":"兆豐金",
    "2887":"台新金","2888":"新光金","2890":"永豐金","2891":"中信金","2892":"第一金","2912":"統一超",
    "3008":"大立光","3034":"聯詠","3035":"智原","3036":"文曄","3045":"台灣大","3105":"穩懋",
    "3231":"緯創","3293":"鈊象","3443":"創意電子","3454":"晶睿","3481":"群創","3488":"環旭電",
    "3529":"力旺","3532":"台勝科","3568":"元太","3661":"世芯-KY","3673":"TPK","3687":"宸鴻",
    "3702":"大聯大","3706":"神達電腦","3711":"日月光投控","4124":"保瑞","4136":"台灣神隆",
    "4147":"中裕","4162":"智擎","4966":"譜瑞-KY","5425":"台半","5483":"中美晶",
    "5876":"上海商銀","5880":"合庫金","6176":"瑞儀","6239":"力成科技","6269":"台郡科技",
    "6278":"台表科","6286":"立錡科技","6298":"崑鼎","6415":"矽力-KY","6446":"藥華醫藥",
    "6488":"環球晶","6505":"台塑石化","6515":"穎崴科技","6669":"緯穎","6670":"復旦",
    "6692":"宜鼎","6699":"九齊","6770":"力積電","8046":"南電","8069":"元太科技",
    "9904":"寶成","9910":"豐泰","9911":"櫻花","9914":"美利達","9917":"中保科",
    "9921":"巨大","9933":"中鼎","9940":"信義","9941":"裕融","9945":"潤泰全","9958":"世紀鋼",
}

# ── Session State ──────────────────────────────────────────
if "records" not in st.session_state:
    st.session_state.records = []
if "edit_idx" not in st.session_state:
    st.session_state.edit_idx = None

def get_df():
    if not st.session_state.records:
        return pd.DataFrame(columns=["交易日期","代碼","名稱","類型","成交股數","淨收付金額","手續費"])
    return pd.DataFrame(st.session_state.records)

# ── 標題 ───────────────────────────────────────────────────
st.markdown("## 📈 台股持股紀錄")
st.markdown("---")

# ── 統計卡片 ──────────────────────────────────────────────
df = get_df()
if not df.empty:
    buy_df  = df[df["類型"] == "買入"]
    sell_df = df[df["類型"] == "賣出"]
    total_buy  = buy_df["淨收付金額"].sum()  if not buy_df.empty  else 0
    total_sell = sell_df["淨收付金額"].sum() if not sell_df.empty else 0
    total_fee  = df["手續費"].sum()
else:
    total_buy = total_sell = total_fee = 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("📋 交易筆數", f"{len(st.session_state.records)} 筆")
c2.metric("🟢 買入總額", f"NT$ {total_buy:,.0f}")
c3.metric("🔴 賣出總額", f"NT$ {total_sell:,.0f}")
c4.metric("💰 手續費合計", f"NT$ {total_fee:,.0f}")

st.markdown("---")

# ── 新增／編輯表單 ─────────────────────────────────────────
edit_idx = st.session_state.edit_idx
is_editing = edit_idx is not None
form_title = "✏️ 編輯交易紀錄" if is_editing else "➕ 新增交易紀錄"

with st.expander(form_title, expanded=True):
    if is_editing:
        rec = st.session_state.records[edit_idx]
        default_date   = pd.to_datetime(rec["交易日期"]).date()
        default_code   = rec["代碼"]
        default_name   = rec["名稱"]
        default_type   = rec["類型"]
        default_shares = int(rec["成交股數"])
        default_amount = float(rec["淨收付金額"])
        default_fee    = float(rec["手續費"])
    else:
        default_date   = date.today()
        default_code   = ""
        default_name   = ""
        default_type   = "買入"
        default_shares = 0
        default_amount = 0.0
        default_fee    = 0.0

    col1, col2 = st.columns(2)
    with col1:
        trade_date = st.date_input("交易日期", value=default_date)
        trade_type = st.selectbox("買入／賣出", ["買入", "賣出"],
                                  index=0 if default_type == "買入" else 1)
        shares = st.number_input("成交股數（股）", min_value=0, value=default_shares, step=1)

    with col2:
        code_input = st.text_input("股票代碼", value=default_code, placeholder="如：2330")
        # 自動帶入股票名稱
        auto_name = TW_STOCKS.get(code_input.strip(), "")
        if auto_name and code_input != default_code:
            st.caption(f"✅ 自動帶入：{auto_name}")
            name_value = auto_name
        elif auto_name:
            name_value = auto_name
        else:
            name_value = default_name
            if code_input and len(code_input) >= 4 and not auto_name:
                st.caption("⚠️ 未收錄代碼，請手動輸入名稱")

        stock_name = st.text_input("股票名稱", value=name_value,
                                   placeholder="輸入代碼後自動帶入，或手動輸入")
        amount = st.number_input("淨收付金額（元）", min_value=0.0, value=default_amount, step=100.0, format="%.0f")
        fee    = st.number_input("手續費（元）", min_value=0.0, value=default_fee, step=1.0, format="%.0f")

    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 4])
    with btn_col1:
        submit = st.button("💾 儲存" if is_editing else "✅ 新增", use_container_width=True, type="primary")
    with btn_col2:
        if is_editing:
            if st.button("❌ 取消", use_container_width=True):
                st.session_state.edit_idx = None
                st.rerun()

    if submit:
        if not code_input.strip():
            st.error("請輸入股票代碼")
        elif not stock_name.strip():
            st.error("請輸入股票名稱")
        elif shares <= 0:
            st.error("成交股數須大於 0")
        elif amount <= 0:
            st.error("淨收付金額須大於 0")
        else:
            new_rec = {
                "交易日期": str(trade_date),
                "代碼": code_input.strip(),
                "名稱": stock_name.strip(),
                "類型": trade_type,
                "成交股數": shares,
                "淨收付金額": amount,
                "手續費": fee,
            }
            if is_editing:
                st.session_state.records[edit_idx] = new_rec
                st.session_state.edit_idx = None
                st.success("✅ 已更新交易紀錄")
            else:
                st.session_state.records.append(new_rec)
                st.success("✅ 已新增交易紀錄")
            st.rerun()

st.markdown("---")

# ── 交易紀錄列表 ──────────────────────────────────────────
st.markdown("### 📋 交易紀錄")

df = get_df()
if df.empty:
    st.info("尚無交易紀錄，請在上方表單新增。")
else:
    # 搜尋篩選
    search = st.text_input("🔍 搜尋代碼或名稱", placeholder="輸入代碼或股票名稱...")
    display_df = df.copy()
    if search:
        mask = (display_df["代碼"].str.contains(search, na=False) |
                display_df["名稱"].str.contains(search, na=False))
        display_df = display_df[mask]

    # 格式化顯示
    show_df = display_df.copy()
    show_df["淨收付金額"] = show_df["淨收付金額"].apply(lambda x: f"NT$ {x:,.0f}")
    show_df["手續費"]     = show_df["手續費"].apply(lambda x: f"NT$ {x:,.0f}")
    show_df["成交股數"]   = show_df["成交股數"].apply(lambda x: f"{x:,} 股")

    st.dataframe(
        show_df.reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
        column_config={
            "交易日期": st.column_config.TextColumn("📅 交易日期", width="small"),
            "代碼":     st.column_config.TextColumn("🏷️ 代碼", width="small"),
            "名稱":     st.column_config.TextColumn("📛 名稱"),
            "類型":     st.column_config.TextColumn("⬆⬇ 類型", width="small"),
            "成交股數": st.column_config.TextColumn("📊 成交股數", width="medium"),
            "淨收付金額": st.column_config.TextColumn("💵 淨收付金額", width="medium"),
            "手續費":   st.column_config.TextColumn("💸 手續費", width="medium"),
        }
    )

    # 編輯 / 刪除按鈕
    st.markdown("**選擇紀錄操作：**")
    for i, rec in enumerate(st.session_state.records):
        # 若有搜尋過濾，只顯示符合的
        if search:
            if search not in rec["代碼"] and search not in rec["名稱"]:
                continue
        ec1, ec2, ec3 = st.columns([5, 1, 1])
        with ec1:
            st.caption(f"{rec['交易日期']}　{rec['代碼']} {rec['名稱']}　{rec['類型']}　{int(rec['成交股數']):,}股　NT${rec['淨收付金額']:,.0f}")
        with ec2:
            if st.button("✏️ 編輯", key=f"edit_{i}", use_container_width=True):
                st.session_state.edit_idx = i
                st.rerun()
        with ec3:
            if st.button("🗑️ 刪除", key=f"del_{i}", use_container_width=True):
                st.session_state.records.pop(i)
                st.rerun()

st.markdown("---")

# ── 圓餅圖 ────────────────────────────────────────────────
st.markdown("### 🥧 買入持股分布圓餅圖")

df = get_df()
buy_df = df[df["類型"] == "買入"] if not df.empty else pd.DataFrame()

if buy_df.empty:
    st.info("新增買入交易後，圓餅圖會顯示在這裡。")
else:
    chart_mode = st.radio("顯示依據", ["金額", "股數"], horizontal=True)
    value_col = "淨收付金額" if chart_mode == "金額" else "成交股數"

    pie_df = (
        buy_df.groupby(["代碼", "名稱"])[value_col]
        .sum()
        .reset_index()
    )
    pie_df["標籤"] = pie_df["代碼"] + " " + pie_df["名稱"]
    pie_df = pie_df.sort_values(value_col, ascending=False)

    fig = px.pie(
        pie_df,
        values=value_col,
        names="標籤",
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Set2 + px.colors.qualitative.Pastel,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>" + (
            "金額：NT$ %{value:,.0f}<extra></extra>" if chart_mode == "金額"
            else "股數：%{value:,.0f} 股<extra></extra>"
        ),
        pull=[0.03] * len(pie_df),
    )
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="v", x=1.02, y=0.5),
        margin=dict(t=20, b=20, l=20, r=20),
        height=440,
        font=dict(family="Noto Sans TC, sans-serif", size=13),
    )
    st.plotly_chart(fig, use_container_width=True)

    # 明細表
    pie_df_display = pie_df[["標籤", value_col]].copy()
    total = pie_df_display[value_col].sum()
    pie_df_display["佔比"] = (pie_df_display[value_col] / total * 100).map(lambda x: f"{x:.1f}%")
    if chart_mode == "金額":
        pie_df_display[value_col] = pie_df_display[value_col].map(lambda x: f"NT$ {x:,.0f}")
    else:
        pie_df_display[value_col] = pie_df_display[value_col].map(lambda x: f"{x:,.0f} 股")
    pie_df_display.columns = ["股票", chart_mode, "佔比"]
    st.dataframe(pie_df_display, use_container_width=True, hide_index=True)
