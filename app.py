import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# ==========================================
# 1. 網頁基本設定 (極簡專業視覺)
# ==========================================
st.set_page_config(
    page_title="台股行動智慧盯盤", 
    page_icon="📈", 
    layout="centered"
)

st.markdown('''
<style>
    .stApp {
        background-color: #F8F9FA;
        color: #2D3748;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .main-title {
        font-size: 1.75rem;
        font-weight: 700;
        text-align: center;
        color: #1A2B4C;
        letter-spacing: -0.5px;
        margin-top: 5px;
        margin-bottom: 2px;
    }
    .sub-title {
        text-align: center;
        color: #718096;
        font-size: 0.82rem;
        font-weight: 400;
        margin-bottom: 18px;
    }
    .stock-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px 18px;
        margin-bottom: 14px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
    }
    .summary-card {
        background-color: #EBF8FF;
        border: 1px solid #BEE3F8;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 16px;
    }
    .fundamental-box {
        background-color: #EDF2F7;
        border-left: 3px solid #3182CE;
        padding: 10px 14px;
        margin-top: 10px;
        margin-bottom: 6px;
        border-radius: 6px;
        font-size: 0.82rem;
        color: #2D3748;
        line-height: 1.55;
    }
    div.stAlert {
        background-color: #EDF2F7;
        color: #2D3748;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 10px;
    }
</style>
''', unsafe_allow_html=True)

st.markdown('<p class="main-title">📈 台股行動智慧盯盤系統</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">多維度量化篩選 x 基本面精選分析 x 實時技術評分</p>', unsafe_allow_html=True)

# ==========================================
# 2. 篩選策略池與資料庫 (依討論優先順序排列)
# ==========================================
STRATEGIES = {
    "🚀 短線動能爆發策略": {
        "stocks": ["2330.TW", "3034.TW", "6187.TWO", "2449.TW", "3661.TW"],
        "desc": "聚焦量價突破、KD低檔黃金交叉與短天期均線發散之強勢動能標的。"
    },
    "📈 中線波段多頭策略": {
        "stocks": ["2382.TW", "3711.TW", "2327.TW", "2357.TW", "2308.TW"],
        "desc": "站穩月線(20MA)與季線(60MA)、MACD柱狀體持續擴增之中期趨勢好股。"
    },
    "🛡️ 長線價值收息策略": {
        "stocks": ["2412.TW", "2881.TW", "2882.TW", "1301.TW", "1101.TW"],
        "desc": "位處相對低基期、站穩年線防守區且具備穩健現金流與殖利率之防禦標的。"
    },
    "🌊 跨週期大波段飆股策略": {
        "stocks": ["2383.TW", "2059.TW", "6669.TW", "2330.TW", "3661.TW"],
        "desc": "聚焦具高產業壁壘、營收長期年增、站穩季線與半年線之多頭大波段主升段標的。"
    }
}

STOCK_INFO = {
    "2383.TW": {
        "name": "台光電 (銅箔基板龍頭)",
        "fundamental": "<b>最新基本面彙整：</b>全球高階 CCL 領導廠，受惠 AI 伺服器與 800G 交換器板材需求爆發，市占率高達六成以上，大波段趨勢極為明確。"
    },
    "2059.TW": {
        "name": "川湖 (伺服器導軌)",
        "fundamental": "<b>最新基本面彙整：</b>全球 AI 伺服器滑軌獨霸供應商，高毛利專利佈局完善，隨 Blackwell 架構量產，營收與獲利將迎來新一波極強增長週期。"
    },
    "6669.TW": {
        "name": "緯穎 (AI伺服器整機)",
        "fundamental": "<b>最新基本面彙整：</b>美系 CSP 巨頭主要供應商，高單價水冷 AI 伺服器整機櫃出貨爆發，毛利率與每股盈餘表現驚人。"
    },
    "2330.TW": {
        "name": "台積電 (晶圓代工)",
        "fundamental": "<b>最新基本面彙整：</b>先進製程與 CoWoS 產能供不應求，高效能運算 (HPC) 需求強勁，單月營收續創高，法人長線展望樂觀。"
    },
    "3034.TW": {
        "name": "聯詠 (IC設計)",
        "fundamental": "<b>最新基本面彙整：</b>OLED 驅動 IC 滲透率提高，車用與消費性電子庫存去化完成，產品組合優化帶動毛利率回升。"
    },
    "6187.TWO": {
        "name": "萬潤 (半導體設備)",
        "fundamental": "<b>最新基本面彙整：</b>受益於台積電先進封裝擴產，自動化貼合與測量設備出貨高峰，訂單能見度直達下半年。"
    },
    "2449.TW": {
        "name": "京元電子 (測試大廠)",
        "fundamental": "<b>最新基本面彙整：</b>AI 晶片測試時間倍增帶動 ASP 上升，出售中國廠房後專注高毛利的先進測試領域，籌碼結構穩健。"
    },
    "3661.TW": {
        "name": "世芯-KY (ASIC設計)",
        "fundamental": "<b>最新基本面彙整：</b>雲端服務巨頭 (CSP) 自研 AI 晶片需求帶動高階 ASIC 專案出貨，NRE 營收穩定成長。"
    },
    "2382.TW": {
        "name": "廣達 (AI伺服器)",
        "fundamental": "<b>最新基本面彙整：</b>整機櫃 AI 伺服器集中出貨，美系大廠訂單強勁，車用電子業務穩定增長，波段動能飽滿。"
    },
    "3711.TW": {
        "name": "日月光投控 (封測龍頭)",
        "fundamental": "<b>最新基本面彙整：</b>先進封裝 (SiP/2.5D) 營收比重大幅上升，半導體景氣復甦帶動測試產能利用率持續回升。"
    },
    "2327.TW": {
        "name": "國巨 (被動元件)",
        "fundamental": "<b>最新基本面彙整：</b>車用與工控高階被動元件稼動率提升，智慧型手機與 PC 復甦帶動 MLCC 與電阻急單進駐。"
    },
    "2357.TW": {
        "name": "華碩 (PC與伺服器)",
        "fundamental": "<b>最新基本面彙整：</b>AI PC 換機潮正式啟動，集團伺服器營收比重突破雙位數，品牌溢價力與消費端回溫顯著。"
    },
    "2308.TW": {
        "name": "台達電 (電源管理)",
        "fundamental": "<b>最新基本面彙整：</b>AI 伺服器電源與液冷散熱系統需求爆發，電動車充電樁長期趨勢看好，基本面結構極為優質。"
    },
    "2412.TW": {
        "name": "中華電 (電信防禦)",
        "fundamental": "<b>最新基本面彙整：</b>行動通訊與雲端IDC雙引擎帶動營收穩健成長，高股利配發率與抗通膨特性，為資產避險首選。"
    },
    "2881.TW": {
        "name": "富邦金 (金融龍頭)",
        "fundamental": "<b>最新基本面彙整：</b>壽險投資收益與資本利得維持高檔，銀行端放款利差穩定，獲利穩居金控每股盈餘 (EPS) 王者。"
    },
    "2882.TW": {
        "name": "國泰金 (金融巨頭)",
        "fundamental": "<b>最新基本面彙整：</b>資產重分類效益顯現，避險成本逐漸降溫，國泰世華銀行獲利創歷史新高，長線防禦力佳。"
    },
    "1301.TW": {
        "name": "台塑 (塑化權值)",
        "fundamental": "<b>最新基本面彙整：</b>石化基期已低，全球供應鏈供需逐漸改善，現金殖利率高且資產品質扎實，屬長線價值打底型標的。"
    },
    "1101.TW": {
        "name": "台泥 (綠能轉型)",
        "fundamental": "<b>最新基本面彙整：</b>歐洲儲能與綠能事業併購效益顯現，轉型低碳水泥逐漸收割，長線配息穩定。"
    }
}

selected_strategy = st.selectbox("🎯 選擇操作策略：", list(STRATEGIES.keys()))
st.info(f"💡 **策略核心邏輯：** {STRATEGIES[selected_strategy]['desc']}")

# ==========================================
# 3. 技術指標與動態評分排序引擎
# ==========================================
def calculate_all_indicators(df):
    df['5MA'] = df['Close'].rolling(window=5).mean()
    df['20MA'] = df['Close'].rolling(window=20).mean()
    df['60MA'] = df['Close'].rolling(window=60).mean()
    df['120MA'] = df['Close'].rolling(window=120).mean()
    df['240MA'] = df['Close'].rolling(window=240).mean()
    
    std20 = df['Close'].rolling(window=20).std()
    df['BB_UP'] = df['20MA'] + (std20 * 2)
    df['BB_DOWN'] = df['20MA'] - (std20 * 2)
    
    low_min = df['Low'].rolling(window=9).min()
    high_max = df['High'].rolling(window=9).max()
    rsv = (df['Close'] - low_min) / (high_max - low_min + 1e-9) * 100
    df['K'] = rsv.ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    
    ema12 = df['Close'].ewm(span=12).mean()
    ema26 = df['Close'].ewm(span=26).mean()
    df['MACD'] = ema12 - ema26
    df['Signal'] = df['MACD'].ewm(span=9).mean()
    df['Hist'] = df['MACD'] - df['Signal']
    
    return df

@st.cache_data(ttl=60)
def fetch_and_analyze(tickers):
    raw_results = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y")
            if hist.empty or len(hist) < 60:
                continue
                
            hist = calculate_all_indicators(hist)
            curr = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            chg_pct = (curr - prev) / prev * 100
            
            ma20 = hist['20MA'].iloc[-1]
            ma60 = hist['60MA'].iloc[-1]
            ma120 = hist['120MA'].iloc[-1] if not pd.isna(hist['120MA'].iloc[-1]) else curr
            ma240 = hist['240MA'].iloc[-1] if not pd.isna(hist['240MA'].iloc[-1]) else curr
            bb_up = hist['BB_UP'].iloc[-1]
            bb_down = hist['BB_DOWN'].iloc[-1]
            
            k_val = hist['K'].iloc[-1]
            d_val = hist['D'].iloc[-1]
            prev_k = hist['K'].iloc[-2]
            prev_d = hist['D'].iloc[-2]
            
            kd_cross = "黃金交叉 🟢" if (prev_k < prev_d and k_val >= d_val) else ("死亡交叉 🔴" if (prev_k > prev_d and k_val <= d_val) else ("多頭整理" if k_val > d_val else "空頭整理"))
            
            macd_val = hist['MACD'].iloc[-1]
            macd_hist = hist['Hist'].iloc[-1]
            prev_hist = hist['Hist'].iloc[-2]
            macd_status = "柱狀翻紅 🟢" if (prev_hist < 0 and macd_hist >= 0) else ("多方動能擴增" if macd_hist > 0 else "空方整理")
            
            score = 50
            if curr > ma20: score += 12
            if curr > ma60: score += 12
            if curr > ma120: score += 8
            if "黃金交叉" in kd_cross: score += 9
            if macd_hist > 0: score += 9
            score = min(max(score, 10), 98)
            
            rec = "🔥 強力買進" if score >= 80 else ("⚖️ 逢低分批" if score >= 60 else "⚠️ 觀望保守")

            info = STOCK_INFO.get(ticker, {})
            display_name = info.get("name", ticker) if isinstance(info, dict) else info
            fundamental_msg = info.get("fundamental", "<b>最新基本面彙整：</b> 公司營運獲利能力穩健，產業前景維持正常發展軌道。") if isinstance(info, dict) else "<b>最新基本面彙整：</b> 公司營運獲利能力穩健，產業前景維持正常發展軌道。"

            raw_results.append({
                "ticker": ticker,
                "name": display_name,
                "fundamental": fundamental_msg,
                "price": round(curr, 2),
                "change": f"{chg_pct:+.2f}%",
                "is_up": chg_pct >= 0,
                "ma20": round(ma20, 2),
                "ma60": round(ma60, 2),
                "ma120": round(ma120, 2),
                "ma240": round(ma240, 2),
                "bb_up": round(bb_up, 2),
                "bb_down": round(bb_down, 2),
                "k": round(k_val, 1),
                "d": round(d_val, 1),
                "kd_cross": kd_cross,
                "macd_val": round(macd_val, 2),
                "macd_status": macd_status,
                "score": score,
                "rec": rec,
                "hist_data": hist
            })
        except:
            continue
            
    sorted_results = sorted(raw_results, key=lambda x: x['score'], reverse=True)
    for idx, item in enumerate(sorted_results, start=1):
        item['rank'] = idx
        
    return sorted_results

# ==========================================
# 4. 介面渲染與圖表繪製 (優化重疊防撞問題)
# ==========================================
if st.button("🔄 載入最新盤中數據與技術指標", type="primary", use_container_width=True):
    with st.spinner("正在進行多維度技術指標與基本面總評彙整..."):
        stock_list = fetch_and_analyze(STRATEGIES[selected_strategy]["stocks"])
    
    st.success(f"運算完成！時間：{datetime.now().strftime('%H:%M:%S')}")
    st.markdown("---")
    
    # 選股摘要標的總覽
    summary_html = "<div class='summary-card'><b style='color: #1A2B4C; font-size: 1rem;'>📌 策略精選推薦標的總覽（依即時評分動態排序）：</b><ol style='margin-top: 8px; margin-bottom: 0px; padding-left: 20px; font-size: 0.88rem; color: #2D3748;'>"
    for item in stock_list:
        color = "#E53E3E" if item["is_up"] else "#38A169"
        summary_html += f"<li style='margin-bottom: 4px;'><b>{item['name']}</b> － <span style='color: {color}; font-weight: bold;'>{item['price']} ({item['change']})</span> ｜ 量化評分：<b>{item['score']}分</b> ({item['rec']})</li>"
    summary_html += "</ol></div>"
    st.markdown(summary_html, unsafe_allow_html=True)
    
    st.markdown("<p style='font-size: 0.9rem; font-weight: bold; color: #4A5568;'>👇 以下為個股詳細技術圖表與基本面彙整：</p>", unsafe_allow_html=True)
    
    for item in stock_list:
        color_style = "color: #E53E3E;" if item["is_up"] else "color: #38A169;"
        
        with st.container():
            st.markdown(f"""
            <div class="stock-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 1.15rem; font-weight: 700; color: #1A2B4C;">NO.{item['rank']} {item['name']}</span>
                    <span style="font-size: 1.05rem; font-weight: 700; {color_style}">{item['price']} ({item['change']})</span>
                </div>
                <hr style="margin: 10px 0; border: none; border-top: 1px solid #EDF2F7;">
                <div style="font-size: 0.83rem; color: #4A5568; line-height: 1.6;">
                    <b>量化評估：</b> <span style="color: #3182CE; font-weight: 700;">{item['score']} 分</span> ({item['rec']})<br>
                    <b>關鍵均線：</b> 月線: {item['ma20']} | 季線: {item['ma60']} | 半年線: {item['ma120']} | 年線: {item['ma240']}<br>
                    <b>布林通道：</b> 上軌: {item['bb_up']} | 下軌: {item['bb_down']}<br>
                    <b>動能指標：</b> KD ({item['k']}/{item['d']}) [{item['kd_cross']}] | MACD ({item['macd_val']}) [{item['macd_status']}]
                </div>
                <div class="fundamental-box">
                    {item['fundamental']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            df_plot = item["hist_data"]
            df_sub = df_plot.tail(66)
            date_strs = df_sub.index.strftime('%Y-%m-%d').tolist()
            
            # 最高價防頂線 (保留 8% 緩衝空間防止頂部重疊)
            max_price_in_window = df_sub['High'].max()
            limit_line_val = max_price_in_window * 1.08
            
            fig = make_subplots(
                rows=4, cols=1, 
                shared_xaxes=True, 
                vertical_spacing=0.03, 
                row_heights=[0.46, 0.18, 0.18, 0.18]
            )
            
            # 1. 主圖：K線與均線 (加粗且緊密相靠)
            fig.add_trace(go.Candlestick(
                x=date_strs, open=df_sub['Open'], high=df_sub['High'],
                low=df_sub['Low'], close=df_sub['Close'], name='K線',
                increasing_line_color='#E53E3E', decreasing_line_color='#38A169',
                increasing_fillcolor='#E53E3E', decreasing_fillcolor='#38A169',
                line=dict(width=1.5)
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(x=date_strs, y=df_sub['5MA'], name='5MA', line=dict(color='#DD6B20', width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=date_strs, y=df_sub['20MA'], name='月線(20)', line=dict(color='#3182CE', width=1.2)), row=1, col=1)
            fig.add_trace(go.Scatter(x=date_strs, y=df_sub['60MA'], name='季線(60)', line=dict(color='#805AD5', width=1.2)), row=1, col=1)
            fig.add_trace(go.Scatter(x=date_strs, y=df_sub['120MA'], name='半年線', line=dict(color='#319795', width=1, dash='dot')), row=1, col=1)
            fig.add_trace(go.Scatter(x=date_strs, y=df_sub['240MA'], name='年線(240)', line=dict(color='#4A5568', width=1, dash='dash')), row=1, col=1)
            
            # 防頂級距線
            fig.add_trace(go.Scatter(
                x=date_strs, 
                y=[limit_line_val] * len(date_strs), 
                name='防頂線', 
                line=dict(color='#CBD5E0', width=1, dash='dashdot')
            ), row=1, col=1)
            
            # 2. 副圖一：成交量
            vol_colors = ['#E53E3E' if c >= o else '#38A169' for c, o in zip(df_sub['Close'], df_sub['Open'])]
            fig.add_trace(go.Bar(x=date_strs, y=df_sub['Volume'], name='成交量', marker_color=vol_colors), row=2, col=1)
            
            # 3. 副圖二：KD
            fig.add_trace(go.Scatter(x=date_strs, y=df_sub['K'], name='K值', line=dict(color='#DD6B20', width=1.2)), row=3, col=1)
            fig.add_trace(go.Scatter(x=date_strs, y=df_sub['D'], name='D值', line=dict(color='#3182CE', width=1.2)), row=3, col=1)
            
            # 4. 副圖三：MACD
            macd_hist_colors = ['#E53E3E' if val >= 0 else '#38A169' for val in df_sub['Hist']]
            fig.add_trace(go.Bar(x=date_strs, y=df_sub['Hist'], name='MACD柱狀', marker_color=macd_hist_colors), row=4, col=1)
            fig.add_trace(go.Scatter(x=date_strs, y=df_sub['MACD'], name='MACD(DIF)', line=dict(color='#E53E3E', width=1.2)), row=4, col=1)
            fig.add_trace(go.Scatter(x=date_strs, y=df_sub['Signal'], name='Signal(DEM)', line=dict(color='#38A169', width=1.2)), row=4, col=1)
            
            # 【關鍵修復】：改善 Legend 位置與邊框背景，徹底解決與圖表頂部/控制 Bar 的重疊問題
            fig.update_layout(
                height=580,
                margin=dict(l=5, r=5, t=45, b=5), # t=45留出頂部控制Bar空間
                xaxis_rangeslider_visible=False,
                xaxis4_type='category',
                bargap=0.05, 
                bargroupgap=0,
                yaxis_range=[df_sub['Low'].min() * 0.98, limit_line_val * 1.02],
                legend=dict(
                    orientation="h", 
                    yanchor="bottom", 
                    y=1.03, 
                    xanchor="center", 
                    x=0.5, 
                    font=dict(size=8),
                    bgcolor='rgba(255, 255, 255, 0.9)', # 白色半透明背景隔開後方內容
                    bordercolor='#E2E8F0',
                    borderwidth=1
                ),
                template="plotly_white",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig, use_container_width=True, key=f"plotly_chart_{item['ticker']}")
            st.markdown("---")
else:
    st.markdown("<br><p style='text-align: center; color: #A0AEC0;'>👆 點擊上方按鈕載入最新技術分析與個股指標</p>", unsafe_allow_html=True)

st.markdown("---")
st.caption("⚠️ 聲明：本系統技術指標與基本面數據僅供策略參考，實際投資請自負風險。")
