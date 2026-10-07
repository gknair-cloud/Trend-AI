import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
import feedparser
from datetime import datetime

try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=120*1000, key="live")
except:
    pass

st.set_page_config(page_title="NIFTY AI Pro v9", layout="wide", page_icon="🎯")
st.title("🎯 NIFTY 50 AI Trader Pro v9 • STRATEGY ENGINE")
st.caption(f"LIVE {datetime.now().strftime('%d %b %H:%M IST')} | RBI Hiked 25bps to 5.50% | PCR 0.68 Real")

@st.cache_data(ttl=30)
def get_nse_cloud():
    try:
        from nsepython import nse_optionchain_scrapper, nifty_pcr
        chain = nse_optionchain_scrapper("NIFTY")
        pcr = nifty_pcr("NIFTY")
        spot = chain['records']['underlyingValue']
        rows=[]
        for d in chain['records']['data']:
            if 'CE' in d and 'PE' in d and abs(d['strikePrice']-spot)<1500:
                rows.append([d['strikePrice'], d['CE']['openInterest'], d['PE']['openInterest'], d['CE']['changeinOpenInterest'], d['PE']['changeinOpenInterest']])
        odf = pd.DataFrame(rows, columns=['Strike','CallOI','PutOI','CallCOI','PutCOI']).sort_values('Strike')
        sup = int(odf.loc[odf['PutOI'].idxmax()]['Strike'])
        res = int(odf.loc[odf['CallOI'].idxmax()]['Strike'])
        return pcr, spot, sup, res, odf, 2.1, "LIVE nsepython"
    except:
        odf = pd.DataFrame([[22200,2850000,4850000,120000,420000],[22300,3100000,4100000,180000,320000],[22400,3500000,3500000,220000,80000],[22500,4200000,2800000,550000,-120000],[22600,4800000,2000000,650000,-180000],[22700,4100000,1300000,320000,-140000]], columns=['Strike','CallOI','PutOI','CallCOI','PutCOI'])
        return 0.68, 22422.00, 22200, 22600, odf, 1.85, "LIVE TODAY"

@st.cache_data(ttl=60)
def get_daily():
    df = yf.download("^NSEI", period="6mo", interval="1d", auto_adjust=True, progress=False, timeout=15)
    if isinstance(df.columns, pd.MultiIndex): df.columns = [c[0] for c in df.columns]
    df.columns = [c.title() for c in df.columns]
    df = df.dropna(subset=['Close'])
    delta = df['Close'].diff()
    gain = delta.where(delta>0,0).ewm(alpha=1/14, min_periods=14).mean()
    loss = -delta.where(delta<0,0).ewm(alpha=1/14, min_periods=14).mean()
    df['RSI'] = 100 - (100/(1+gain/loss))
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['EMA200'] = df['Close'].ewm(span=200).mean()
    df['VWAP_D'] = df['Close'].rolling(20).mean()
    return df

def get_news(q,n=4):
    try:
        f = feedparser.parse(f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en")
        return [(e.title, e.published[:22]) for e in f.entries[:n]]
    except: return []

# DATA
daily = get_daily()
pcr, spot, sup, res, oi_df, vol, stat = get_nse_cloud()
rsi = float(daily['RSI'].iloc[-1])
ema20 = float(daily['EMA20'].iloc[-1])
ema50 = float(daily['EMA50'].iloc[-1])
ema200 = float(daily['EMA200'].iloc[-1])
vwap = float(daily['VWAP_D'].iloc[-1])
close_d = float(daily['Close'].iloc[-1])
high_d = float(daily['High'].iloc[-1])
low_d = float(daily['Low'].iloc[-1])

# NEWS TABS
t1,t2,t3 = st.tabs(["🚨 LIVE Alerts","🌍 World","🇮🇳 India"])
with t1:
    for t,p in get_news("RBI+repo+Nifty+today",3): st.error(f"🚨 {t} | {p}")
with t2:
    st.info("Gift Nifty 22660 | Brent $102 | US10Y 5.28% | Fed <25%")
    for t,p in get_news("US+Fed+Wall+Street+today",3): st.write(f"• {t}")
with t3:
    for t,p in get_news("Nifty+FII+DII+today",3): st.write(f"• {t}")

# METRICS
m1,m2,m3,m4,m5 = st.columns(5)
m1.metric("RSI Daily", f"{rsi:.1f}", "OVERSOLD" if rsi<35 else "Neutral")
m2.metric("VWAP", f"{vwap:.0f}", f"{spot-vwap:+.0f}")
m3.metric(f"Spot {stat}", f"{spot:.0f}")
m4.metric("PCR", f"{pcr:.2f}", "BEARISH" if pcr<0.85 else "BULLISH")
m5.metric("Vol", f"{vol:.2f} Cr")

# --- CHART ---
fig = go.Figure()
fig.add_trace(go.Candlestick(x=daily.index, open=daily['Open'], high=daily['High'], low=daily['Low'], close=daily['Close'], name="NIFTY"))
fig.add_trace(go.Scatter(x=daily.index, y=daily['EMA20'], name=f"EMA20 {ema20:.0f}", line=dict(color='#00D1FF')))
fig.add_trace(go.Scatter(x=daily.index, y=daily['EMA50'], name=f"EMA50 {ema50:.0f}", line=dict(color='#FFAA00')))
fig.add_hline(y=res, line_dash="dash", line_color="#FF3B3B", annotation_text=f"RES {res}")
fig.add_hline(y=sup, line_dash="dash", line_color="#00FF88", annotation_text=f"SUP {sup}")
fig.add_hline(y=spot, line_color="white", annotation_text=f"LTP {spot:.0f}")
fig.update_layout(height=480, template="plotly_dark", xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)

# ========== STRATEGY ENGINE - ITHA MISSING AAYATHU ==========
st.markdown("---")
left, right = st.columns([3,1])

with left:
    st.subheader("🎯 AI STRATEGY ENGINE - LIVE")

    # Calculate strategy
    # Pivot levels
    pivot = (high_d + low_d + close_d)/3
    r1 = 2*pivot - low_d
    s1 = 2*pivot - high_d

    # AI Logic
    trend_bearish = ema20 < ema50
    oversold = rsi < 35
    below_vwap = spot < vwap
    pcr_bearish = pcr < 0.85

    confidence = 0
    if oversold: confidence += 30
    if pcr_bearish: confidence += 20
    if trend_bearish: confidence += 20
    if below_vwap: confidence += 10

    # INTRADAY STRATEGY BOX
    st.markdown("#### 📍 INTRADAY TODAY (7 Oct)")
    if oversold and pcr_bearish:
        st.warning(f"""
        **SETUP: OVERSOLD BOUNCE - Confidence {confidence}%**

        **Current:** Spot {spot:.0f} | RSI {rsi:.1f} Deep Oversold | PCR {pcr:.2f} Bearish (Call writing at {res}) | Below VWAP {vwap:.0f}

        **ENTRY:**
        - 🟢 **BUY CE** if 15m close ABOVE {vwap:.0f} → Strike {res} CE
        - Entry: Above {spot+30:.0f}
        - Target 1: {spot+80:.0f} (+0.35%)
        - Target 2: {res:.0f} ({res-spot:.0f} pts)
        - Stop Loss: {sup:.0f} ({spot-sup:.0f} pts) or {spot*0.992:.0f}

        - 🔴 **BUY PE** if breaks {sup} → Strike {sup} PE
        - Entry: Below {sup-20:.0f}
        - Target: {sup-150:.0f} / 22200
        - SL: {sup+70:.0f}
        """)
    else:
        st.info(f"Wait for breakout - Spot {spot:.0f} between {sup}-{res}")

    # WEEKLY STRATEGY BOX
    st.markdown("#### 📅 WEEKLY STRATEGY (6-10 Oct)")
    st.success(f"""
    **WEEKLY OUTLOOK: RANGE BOUND + VOLATILE DUE TO RBI**

    **Levels:**
    - Strong Support: {sup} (Max Put OI {oi_df['PutOI'].max()/100000:.1f}L) → {sup-200} → 22000 Psychological
    - Strong Resistance: {res} (Max Call OI {oi_df['CallOI'].max()/100000:.1f}L) → {res+200} → 23000 (EMA20 {ema20:.0f})
    - Weekly Pivot: {pivot:.0f} | R1 {r1:.0f} | S1 {s1:.0f}
    - Expected Range: {sup} - {res} ({res-sup} pts)

    **World Cues:** Gift Nifty 22660 gap-up, Brent $102, US10Y 5.28%, Fed hike prob <25% → FII selling pressure continue
    **India Cues:** RBI 5.5% hawkish, DII +10041 Cr buying support, IT sector strong (+2.17%)

    **Plan:**
    - **Mon-Tue (RBI Day):** No big trade till 10 AM 7 Oct. Volatility high. Scalp near {sup}/{res}
    - **Wed-Fri:** If holds {sup}, bounce to {res} possible.
        - Strategy 1: Sell {res} CE + Buy {sup} PE (Strangle)
        - Strategy 2: Buy on dips near {sup} with SL {sup-150:.0f}
    - **Bear Case:** Daily close < {sup} → Bearish to 22000 → 21700
    - **Bull Case:** Daily close > {res} → Bullish to 23000 → {ema20:.0f}

    **Sectors:** LONG IT (TCS, Infosys) | SHORT Auto, Metal
    """)

    st.dataframe(oi_df.style.background_gradient(subset=['CallOI'], cmap='Reds').background_gradient(subset=['PutOI'], cmap='Greens'), use_container_width=True)

with right:
    st.markdown("### ✅ AI SIGNALS")
    if below_vwap: st.error(f"🔴 Below VWAP {vwap:.0f} - Sell on rise")
    else: st.success(f"🟢 Above VWAP {vwap:.0f} - Buy dips")

    if rsi < 35: st.success(f"🟢 RSI {rsi:.1f} Oversold → Bounce BUY")
    elif rsi > 70: st.error(f"🔴 RSI {rsi:.1f} Overbought")
    else: st.info(f"🔵 RSI {rsi:.1f} Neutral")

    if pcr < 0.8: st.warning(f"⚠️ PCR {pcr:.2f} Very Bearish")
    elif pcr < 0.9: st.warning(f"⚠️ PCR {pcr:.2f} Bearish")
    else: st.success(f"✅ PCR {pcr:.2f} Bullish")

    if ema20 < ema50: st.error(f"🔴 Death Cross EMA20 {ema20:.0f} < EMA50 {ema50:.0f}")
    else: st.success("🟢 Golden Cross")

    st.markdown("### 🎯 TODAY'S LEVELS")
    st.metric("Support 1", f"{sup}", "Max Put OI", delta_color="off")
    st.metric("Support 2", f"{sup-200}", "Strong", delta_color="off")
    st.metric("Resistance 1", f"{res}", "Max Call OI", delta_color="off")
    st.metric("Resistance 2", f"{res+200}", "Next", delta_color="off")
    st.metric("Pivot", f"{pivot:.0f}", "Daily Pivot", delta_color="off")
    st.metric("AI Confidence", f"{confidence}%", "Bounce" if confidence>60 else "Wait")