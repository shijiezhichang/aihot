"""
AI Hot 实时大屏 v1 — 沉浸式数据看板
Streamlit + DuckDB · 深色炫彩风格 · 大屏展示优化
"""

import streamlit as st
import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

st.set_page_config(
    page_title="AI Hot · 实时数据看板 v1",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────── 深色大屏样式 ────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400;500;600;700;800;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, sans-serif;
        background: #0a0e1a !important;
        color: #e2e8f0;
    }
    .main { background: #0a0e1a !important; }
    .main > div { padding: 0.8rem 1.5rem; max-width: 100%; }

    /* 隐藏 Streamlit 默认元素 */
    #MainMenu, header, footer { visibility: hidden; }
    .stAppDeployButton, .stDeployButton { display: none; }

    /* 顶部导航条 */
    .top-bar {
        display: flex; align-items: center; justify-content: space-between;
        padding: 0.6rem 0; margin-bottom: 1rem;
        border-bottom: 1px solid rgba(255,255,255,0.06);
    }
    .top-bar .logo-area { display:flex; align-items:center; gap:12px; }
    .top-bar .logo-icon { font-size:1.8rem; }
    .top-bar .logo-text { font-size:1.3rem; font-weight:800; background: linear-gradient(135deg,#667eea,#a78bfa,#f472b6); -webkit-background-clip:text; -webkit-text-fill-color:transparent; letter-spacing:-0.5px; }
    .top-bar .logo-sub { font-size:0.75rem; color:#6b7280; font-weight:400; -webkit-text-fill-color:#6b7280; margin-left:6px; }
    .top-bar .top-right { display:flex; align-items:center; gap:20px; font-size:0.8rem; color:#6b7280; }
    .top-bar .top-right .live-dot {
        display:inline-block; width:8px; height:8px; border-radius:50%;
        background:#22c55e; margin-right:6px; animation: pulse-dot 1.5s ease-in-out infinite;
    }

    @keyframes pulse-dot {
        0%,100% { opacity:1; transform:scale(1); box-shadow:0 0 0 0 rgba(34,197,94,0.4); }
        50% { opacity:0.7; transform:scale(1.1); box-shadow:0 0 0 6px rgba(34,197,94,0); }
    }

    /* KPI 卡片 — 玻璃质感 */
    .kpi-grid { display:grid; grid-template-columns:repeat(5,1fr); gap:12px; margin-bottom:1.2rem; }
    .kpi-card {
        background: rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.06);
        border-radius:16px; padding:1rem 1.2rem;
        backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
        transition: all 0.25s ease; position:relative; overflow:hidden;
    }
    .kpi-card:hover { background: rgba(255,255,255,0.07); transform:translateY(-2px); border-color:rgba(102,126,234,0.3); }
    .kpi-card .kpi-glow {
        position:absolute; top:-50%; right:-30%; width:80px; height:80px;
        border-radius:50%; filter:blur(30px); opacity:0.15;
    }
    .kpi-card .kpi-top { display:flex; align-items:center; justify-content:space-between; margin-bottom:0.3rem; }
    .kpi-card .kpi-icon { font-size:1.4rem; }
    .kpi-card .kpi-label { font-size:0.75rem; color:#6b7280; font-weight:500; letter-spacing:0.3px; text-transform:uppercase; }
    .kpi-card .kpi-value { font-size:1.9rem; font-weight:800; letter-spacing:-0.5px; line-height:1.2; }
    .kpi-card .kpi-delta { font-size:0.7rem; margin-top:0.1rem; display:flex; align-items:center; gap:4px; }

    /* 图表容器 */
    .chart-box {
        background: rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06);
        border-radius:16px; padding:1rem 1.2rem 0.6rem 1.2rem;
        backdrop-filter: blur(8px); margin-bottom:1rem;
        transition: border-color 0.2s;
    }
    .chart-box:hover { border-color:rgba(102,126,234,0.2); }
    .chart-box .chart-title {
        font-size:0.8rem; font-weight:600; color:#9ca3af; letter-spacing:0.5px;
        text-transform:uppercase; margin-bottom:0.3rem; display:flex; align-items:center; gap:8px;
    }
    .chart-box .chart-title .title-dot {
        display:inline-block; width:6px; height:6px; border-radius:50%;
    }

    /* 新闻卡片 — 暗色 */
    .news-card {
        background: rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06);
        border-left:3px solid #667eea;
        border-radius:12px; padding:0.9rem 1.2rem; margin-bottom:0.6rem;
        transition: all 0.2s ease; cursor:default;
    }
    .news-card:hover {
        background: rgba(255,255,255,0.06); border-color:rgba(102,126,234,0.25);
        transform:translateX(3px);
    }
    .news-card .news-title {
        font-size:0.9rem; font-weight:600; color:#f1f5f9;
        margin-bottom:0.2rem; line-height:1.4;
    }
    .news-card .news-title a { color:inherit; text-decoration:none; }
    .news-card .news-title a:hover { color:#a78bfa; }
    .news-card .news-meta {
        font-size:0.7rem; color:#6b7280; display:flex; gap:12px; flex-wrap:wrap; align-items:center;
    }
    .news-card .cat-tag {
        font-size:0.65rem; padding:1px 10px; border-radius:20px; font-weight:500;
    }
    .news-card .news-summary {
        font-size:0.8rem; color:#9ca3af; margin-top:0.3rem; line-height:1.5;
        display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;
    }

    /* 滚动条 */
    ::-webkit-scrollbar { width:4px; height:4px; }
    ::-webkit-scrollbar-track { background:#0a0e1a; }
    ::-webkit-scrollbar-thumb { background:rgba(255,255,255,0.1); border-radius:4px; }
    ::-webkit-scrollbar-thumb:hover { background:rgba(255,255,255,0.2); }

    /* tabs 自定义 */
    .stTabs [data-baseweb="tab-list"] { gap:2px; background:rgba(255,255,255,0.03); border-radius:12px; padding:4px; border:1px solid rgba(255,255,255,0.06); }
    .stTabs [data-baseweb="tab"] { border-radius:8px; padding:6px 18px; font-size:0.8rem; font-weight:500; color:#6b7280; }
    .stTabs [aria-selected="true"] { background:rgba(102,126,234,0.25) !important; color:#e2e8f0 !important; }

    /* sidebar 覆写 */
    section[data-testid="stSidebar"] {
        background: #0f1322 !important; border-right:1px solid rgba(255,255,255,0.06);
    }
    section[data-testid="stSidebar"] .block-container { padding-top:1.5rem; }

    /* 空状态 */
    .empty-state { text-align:center; color:#4b5563; padding:2rem 0; font-size:0.9rem; }

    /* section divider */
    .section-label {
        font-size:0.75rem; font-weight:600; color:#6b7280; letter-spacing:0.8px;
        text-transform:uppercase; margin:0.8rem 0 0.6rem 0; padding-bottom:0.4rem;
        border-bottom:1px solid rgba(255,255,255,0.05);
    }

    /* 滚动资讯条 */
    .ticker-wrap {
        background: rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06);
        border-radius:12px; padding:0.5rem 1rem; margin-bottom:1rem;
        overflow:hidden; white-space:nowrap;
    }
    .ticker-content {
        display:inline-block; animation: ticker-scroll 30s linear infinite;
        font-size:0.8rem; color:#9ca3af;
    }
    .ticker-content span { margin-right:40px; }
    .ticker-content .hl { color:#a78bfa; font-weight:500; }
    @keyframes ticker-scroll {
        0% { transform:translateX(100vw); }
        100% { transform:translateX(-100%); }
    }

    /* word cloud 替代 — 标签云 */
    .tag-cloud { display:flex; flex-wrap:wrap; gap:6px; padding:0.5rem 0; }
    .tag-cloud .tag-item {
        padding:3px 14px; border-radius:20px; font-size:0.75rem; font-weight:500;
        background: rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.06);
        color:#d1d5db; transition:all 0.2s;
    }
    .tag-cloud .tag-item:hover { background:rgba(102,126,234,0.2); border-color:rgba(102,126,234,0.3); color:#fff; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────── 数据加载 ────────────────────────────
@st.cache_data(ttl=30)
def load_data():
    conn = duckdb.connect(r"/var/www/aihot/aihot.db", read_only=True)
    items = conn.execute("SELECT * FROM aihot_items ORDER BY published_at DESC").fetchdf()
    daily = conn.execute("SELECT * FROM aihot_daily_items ORDER BY fetched_at DESC").fetchdf()
    conn.close()

    # 类型转换
    items["published_at"] = pd.to_datetime(items["published_at"])
    items["published_date"] = items["published_at"].dt.date
    items["published_hour"] = items["published_at"].dt.hour
    items["category"] = items["category"].fillna("未分类")
    items["source_short"] = items["source"].apply(lambda x: x.split("（")[0].split(":")[0][:18] if pd.notna(x) else "未知")

    daily["fetched_at"] = pd.to_datetime(daily["fetched_at"])
    daily["section_label"] = daily["section_label"].fillna("其他")

    return items, daily

items, daily = load_data()

# ──────────────────────────── 分类配色 ────────────────────────────
CAT_COLORS = {
    "tip": "#F59E0B", "ai-products": "#3B82F6", "industry": "#8B5CF6",
    "ai-models": "#10B981", "paper": "#EC4899",
}
CAT_COLORS_HEX = {
    "tip": "#f59e0b", "ai-products": "#3b82f6", "industry": "#8b5cf6",
    "ai-models": "#10b981", "paper": "#ec4899",
}
CAT_LABELS = {
    "tip": "技巧观点", "ai-products": "AI 产品", "industry": "行业动态",
    "ai-models": "模型发布", "paper": "论文研究",
}
CAT_ICONS = {
    "tip": "💡", "ai-products": "🛠", "industry": "🏭",
    "ai-models": "🧠", "paper": "📄",
}

# ──────────────────────────── 侧边栏 ────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:0.5rem 0 1rem 0;">
        <div style="font-size:2.2rem;">🔥</div>
        <div style="font-weight:800;font-size:1.2rem;background:linear-gradient(135deg,#667eea,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">AI Hot</div>
        <div style="font-size:0.7rem;color:#6b7280;margin-top:2px;">实时数据看板 v1</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    date_min = items["published_date"].min()
    date_max = items["published_date"].max()

    # 快捷日期
    quick_date = st.radio("快捷筛选", ["全部时间", "近 24 小时", "近 3 天", "自定义"], index=0, label_visibility="collapsed")

    if quick_date == "自定义":
        dr = st.date_input("日期范围", value=(date_min, date_max), label_visibility="collapsed")
        if len(dr)==2: start_date, end_date = dr
        else: start_date, end_date = date_min, date_max
    elif quick_date == "近 24 小时":
        end_date = date_max
        start_date = end_date - timedelta(days=1)
    elif quick_date == "近 3 天":
        end_date = date_max
        start_date = end_date - timedelta(days=3)
    else:
        start_date, end_date = date_min, date_max

    sel_cat = st.selectbox("分类", ["全部"] + sorted(items["category"].unique().tolist()), index=0)

    search_q = st.text_input("🔍", placeholder="搜索标题/摘要...", label_visibility="collapsed")

    auto_refresh = st.checkbox("🔄 自动刷新 (30s)", value=False)

    st.markdown("---")
    st.markdown(f"""
    <div style="font-size:0.7rem;color:#4b5563;text-align:center;">
        数据源: RSS · HuggingFace · X · 公众号<br>
        更新于 {items['fetched_at'].max().strftime('%m-%d %H:%M') if not items.empty else '-'}<br>
        共 {len(items)} 条资讯
    </div>
    """, unsafe_allow_html=True)

    if st.button("⟳ 立即刷新", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# ──────────────────────────── 数据过滤 ────────────────────────────
def filter_df(df):
    df = df.copy()
    df["published_date"] = pd.to_datetime(df["published_at"]).dt.date
    if sel_cat != "全部":
        df = df[df["category"] == sel_cat]
    df = df[(df["published_date"] >= start_date) & (df["published_date"] <= end_date)]
    if search_q:
        mask = df["title"].str.contains(search_q, case=False, na=False) | df["summary"].str.contains(search_q, case=False, na=False)
        df = df[mask]
    return df

filtered = filter_df(items)

# 自动刷新
if auto_refresh:
    st.markdown("""
    <meta http-equiv="refresh" content="30">
    """, unsafe_allow_html=True)
    time.sleep(0.1)


# ──────────────────────────── 顶部导航条 ────────────────────────────
st.markdown("""
<div class="top-bar">
    <div class="logo-area">
        <span class="logo-icon">🔥</span>
        <span class="logo-text">AI HOT</span>
        <span class="logo-sub">实时数据看板</span>
    </div>
    <div class="top-right">
        <span><span class="live-dot"></span>LIVE</span>
        <span>📡 {} 条 · {} 分类</span>
        <span style="font-size:0.7rem;color:#4b5563;">{}</span>
    </div>
</div>
""".format(
    len(filtered),
    filtered["category"].nunique() if not filtered.empty else 0,
    datetime.now().strftime("%Y-%m-%d %H:%M"),
), unsafe_allow_html=True)


# ──────────────────────────── KPI 卡片行 ────────────────────────────
trending = len(items[items["published_date"] >= (date_max - timedelta(days=1))]) if not items.empty else 0
src_cnt = items["source"].nunique()
cat_cnt = items["category"].nunique()

st.markdown(f"""
<div class="kpi-grid">
    <div class="kpi-card">
        <div class="kpi-glow" style="background:#667eea;"></div>
        <div class="kpi-top"><span class="kpi-icon">📰</span><span class="kpi-label">总资讯数</span></div>
        <div class="kpi-value" style="color:#667eea;">{len(filtered)}</div>
        <div class="kpi-delta" style="color:#6b7280;">筛选后 · 全部 {len(items)}</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-glow" style="background:#22c55e;"></div>
        <div class="kpi-top"><span class="kpi-icon">⚡</span><span class="kpi-label">近 24h 热点</span></div>
        <div class="kpi-value" style="color:#22c55e;">{trending}</div>
        <div class="kpi-delta" style="color:#22c55e;">{"↑ 活跃" if trending>5 else "● 正常"}</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-glow" style="background:#a78bfa;"></div>
        <div class="kpi-top"><span class="kpi-icon">📂</span><span class="kpi-label">覆盖分类</span></div>
        <div class="kpi-value" style="color:#a78bfa;">{cat_cnt}</div>
        <div class="kpi-delta" style="color:#6b7280;">{', '.join(CAT_LABELS.get(c,c) for c in sorted(items['category'].unique()))}</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-glow" style="background:#f59e0b;"></div>
        <div class="kpi-top"><span class="kpi-icon">🌐</span><span class="kpi-label">数据源</span></div>
        <div class="kpi-value" style="color:#f59e0b;">{src_cnt}</div>
        <div class="kpi-delta" style="color:#6b7280;">RSS · 社交 · 媒体</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-glow" style="background:#f472b6;"></div>
        <div class="kpi-top"><span class="kpi-icon">📋</span><span class="kpi-label">每日精选</span></div>
        <div class="kpi-value" style="color:#f472b6;">{len(daily)}</div>
        <div class="kpi-delta" style="color:#6b7280;">今日汇总</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────── 滚动资讯条 ────────────────────────────
if not filtered.empty:
    ticker_titles = "  ·  ".join(
        f'<span class="hl">{r["title"][:40]}</span>' for _, r in filtered.head(8).iterrows()
    )
    st.markdown(f"""
    <div class="ticker-wrap">
        <div class="ticker-content">{ticker_titles}</div>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# 第 1 行：环形图 + 时间趋势 + 分类时段热力图
# ═══════════════════════════════════════════════════════════════
c1, c2 = st.columns([1, 1.5])

with c1:
    st.markdown('<div class="chart-box">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title"><span class="title-dot" style="background:#a78bfa;"></span>分类分布</div>', unsafe_allow_html=True)

    if not filtered.empty:
        cat_data = filtered["category"].value_counts().reset_index()
        cat_data.columns = ["cat", "cnt"]
        cat_data["label"] = cat_data["cat"].map(CAT_LABELS).fillna(cat_data["cat"])
        cat_data["color"] = cat_data["cat"].map(CAT_COLORS_HEX).fillna("#6b7280")

        fig = go.Figure()
        fig.add_trace(go.Pie(
            labels=cat_data["label"],
            values=cat_data["cnt"],
            marker=dict(colors=cat_data["color"], line=dict(color="#0a0e1a", width=2)),
            textinfo="label+percent",
            textfont=dict(size=11, color="#e2e8f0"),
            hole=0.6,
            rotation=45,
            hovertemplate="<b>%{label}</b><br>%{value} 条 · %{percent}<extra></extra>",
        ))
        fig.update_layout(
            height=280, margin=dict(l=5, r=5, t=5, b=5),
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e2e8f0"),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown('<div class="empty-state">暂无数据</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


with c2:
    st.markdown('<div class="chart-box">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title"><span class="title-dot" style="background:#22c55e;"></span>发布时间趋势</div>', unsafe_allow_html=True)

    if not filtered.empty:
        ts_items = filtered.copy()
        ts_items["date"] = ts_items["published_at"].dt.date
        timeline = ts_items.groupby(["date", "category"]).size().reset_index(name="count")
        timeline["date"] = pd.to_datetime(timeline["date"])
        timeline["cat_label"] = timeline["category"].map(CAT_LABELS).fillna(timeline["category"])

        fig = px.area(
            timeline, x="date", y="count", color="category",
            color_discrete_map=CAT_COLORS_HEX,
            line_shape="spline",
            labels={"date": "", "count": "", "category": ""},
        )
        fig.update_traces(
            mode="lines+markers",
            marker=dict(size=5, line=dict(width=1, color="#0a0e1a")),
            line=dict(width=2.5),
            fill="tozeroy",
            opacity=0.85,
        )
        fig.update_layout(
            height=280, margin=dict(l=5, r=10, t=5, b=5),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                        font=dict(size=9, color="#9ca3af"), bgcolor="rgba(0,0,0,0)"),
            hovermode="x unified",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=10, color="#6b7280")),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=10, color="#6b7280")),
            font=dict(color="#e2e8f0"),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown('<div class="empty-state">暂无数据</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# 第 2 行：来源柱状图 + 时段分布 + 分类关键词云
# ═══════════════════════════════════════════════════════════════
c1, c2, c3 = st.columns([1.3, 1, 1])

with c1:
    st.markdown('<div class="chart-box">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title"><span class="title-dot" style="background:#f59e0b;"></span>热门来源 Top 12</div>', unsafe_allow_html=True)

    if not filtered.empty:
        src_data = filtered["source_short"].value_counts().head(12).reset_index()
        src_data.columns = ["src", "cnt"]

        fig = px.bar(
            src_data.sort_values("cnt"),
            y="src", x="cnt",
            orientation="h", text="cnt",
            color="cnt",
            color_continuous_scale=["#1e1b4b", "#4c1d95", "#7c3aed", "#a78bfa", "#c4b5fd"],
            labels={"cnt": "", "src": ""},
        )
        fig.update_traces(textposition="outside", textfont=dict(size=10, color="#9ca3af"))
        fig.update_layout(
            height=280, margin=dict(l=5, r=40, t=5, b=5),
            yaxis=dict(autorange="reversed", tickfont=dict(size=9, color="#9ca3af")),
            xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=9, color="#6b7280")),
            coloraxis_showscale=False,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown('<div class="empty-state">暂无数据</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


with c2:
    st.markdown('<div class="chart-box">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title"><span class="title-dot" style="background:#3b82f6;"></span>时段分布</div>', unsafe_allow_html=True)

    if not filtered.empty:
        h = filtered.groupby("published_hour").size().reset_index(name="count")

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=h["published_hour"], y=h["count"],
            marker=dict(
                color=h["count"], colorscale="Viridis",
                showscale=False, line=dict(width=0),
            ),
            text=h["count"], textposition="outside", textfont=dict(size=9, color="#9ca3af"),
            hovertemplate="<b>%{x}:00</b><br>%{y} 条<extra></extra>",
        ))
        fig.update_layout(
            height=280, margin=dict(l=5, r=5, t=5, b=5),
            xaxis=dict(
                tickvals=list(range(0,24,3)),
                ticktext=[f"{h:02d}:00" for h in range(0,24,3)],
                showgrid=False, tickfont=dict(size=9, color="#6b7280"),
            ),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=9, color="#6b7280")),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown('<div class="empty-state">暂无数据</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


with c3:
    st.markdown('<div class="chart-box">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title"><span class="title-dot" style="background:#f472b6;"></span>分类关键词</div>', unsafe_allow_html=True)

    if not filtered.empty:
        # 从标题中提取关键词（取每个分类的文章标题关键词）
        from collections import Counter
        stopwords = {"的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都",
                     "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你",
                     "会", "着", "没有", "看", "好", "自己", "这", "他", "她", "它",
                     "们", "那", "些", "什么", "怎么", "如何", "与", "及", "等", "为",
                     "将", "发布", "上线", "推出", "更新", "新增"}

        def extract_keywords(title, n=3):
            if pd.isna(title) or not title: return []
            import re
            words = re.findall(r'[\u4e00-\u9fffA-Za-z0-9]+', title)
            return [w for w in words if len(w) > 1 and w.lower() not in stopwords][:n]

        all_tags = Counter()
        for _, r in filtered.iterrows():
            tags = extract_keywords(r.get("title","") or r.get("title_en",""))
            cat = r.get("category","其他")
            for t in tags:
                all_tags[f"{CAT_ICONS.get(cat,'')}{t}"] += 1

        top_tags = [t for t, _ in all_tags.most_common(30)]
        if top_tags:
            # 分两行展示
            mid = len(top_tags)//2
            tags_html = '<div class="tag-cloud">'
            for i, tag in enumerate(top_tags[:mid]):
                tags_html += f'<span class="tag-item">{tag}</span>'
            tags_html += '</div><div class="tag-cloud">'
            for i, tag in enumerate(top_tags[mid:mid+20]):
                tags_html += f'<span class="tag-item">{tag}</span>'
            tags_html += '</div>'
            st.markdown(tags_html, unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty-state">暂无关键词</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state">暂无数据</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# Tab 区域：每日精选 + 最新资讯
# ═══════════════════════════════════════════════════════════════
tab1, tab2 = st.tabs(["📋 每日精选汇总", "📰 全部资讯流"])

with tab1:
    if not daily.empty:
        for _, row in daily.head(25).iterrows():
            label = row.get("section_label", "")
            lc = {"模型发布/更新": "#10B981", "产品发布/更新": "#3B82F6",
                  "技巧与观点": "#F59E0B", "论文研究": "#EC4899", "行业动态": "#8B5CF6"}.get(label, "#6b7280")
            summary = row.get("summary", "") or ""
            src = row.get("source_name", "")
            ts = row["fetched_at"].strftime("%m-%d %H:%M") if pd.notna(row.get("fetched_at")) else ""
            st.markdown(f"""
            <div class="news-card" style="border-left-color:{lc};">
                <div class="news-title"><a href="{row.get('source_url','#')}" target="_blank">{row.get("title","")}</a></div>
                <div class="news-meta">
                    <span class="cat-tag" style="background:{lc}20;color:{lc};">{label}</span>
                    <span>📰 {src}</span>
                    <span>🕐 {ts}</span>
                </div>
                <div class="news-summary">{summary[:200]}{"…" if len(summary)>200 else ""}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state">暂无每日精选数据</div>', unsafe_allow_html=True)


with tab2:
    if not filtered.empty:
        for _, row in filtered.head(80).iterrows():
            cat = row.get("category", "未分类")
            cc = CAT_COLORS_HEX.get(cat, "#6b7280")
            title = row.get("title", "") or row.get("title_en", "")
            summary = row.get("summary", "") or ""
            src = row.get("source", "")
            ts = row["published_at"].strftime("%m-%d %H:%M") if pd.notna(row.get("published_at")) else ""
            url = row.get("url", "")
            st.markdown(f"""
            <div class="news-card" style="border-left-color:{cc};">
                <div class="news-title"><a href="{url}" target="_blank">{title}</a></div>
                <div class="news-meta">
                    <span class="cat-tag" style="background:{cc}20;color:{cc};">{CAT_LABELS.get(cat,cat)}</span>
                    <span>📰 {src}</span>
                    <span>🕐 {ts}</span>
                </div>
                <div class="news-summary">{summary[:200]}{"…" if len(summary)>200 else ""}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state">📭 暂无匹配资讯</div>', unsafe_allow_html=True)


# ──────────────────────────── Footer ────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#374151;font-size:0.7rem;padding:0.5rem 0;">
    🔥 AI Hot 实时数据看板 v1 · Streamlit + DuckDB · 数据每 30s 自动刷新
</div>
""", unsafe_allow_html=True)
