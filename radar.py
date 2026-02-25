import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import warnings

warnings.filterwarnings('ignore')

st.set_page_config(page_title="BIST Pusu Radarı", layout="wide")
st.title("🏛️ AKADEMİK FİNANS KONSEYİ")
st.subheader("Borsa İstanbul (BIST Likit) Kuantitatif Radarı (V7.0)")

# BELLEK YÖNETİMİ
if 'bist_df' not in st.session_state:
    st.session_state.bist_df = None

@st.cache_data(ttl=3600)
def bist_listesini_getir():
    # BIST'in en hacimli ve güvenilir şirketleri
    bist_hisseler = [
        "AKBNK", "ARCLK", "ASELS", "ASTOR", "BIMAS", "BRISA", "CCOLA", "CWENE", "DOAS", "DOHOL", 
        "EKGYO", "ENJSA", "ENKAI", "EREGL", "FROTO", "GARAN", "GESAN", "GUBRF", "HEKTS", 
        "ISCTR", "KCHOL", "KONTR", "KOZAA", "KOZAL", "KRDMD", "MGROS", "ODAS", "PETKM", 
        "PGSUS", "SAHOL", "SASA", "SISE", "SMRTG", "SOKM", "TAVHL", "TCELL", "THYAO", 
        "TKFEN", "TOASO", "TSKB", "TTKOM", "TUPRS", "VAKBN", "VESTL", "YKBNK"
    ]
    return [hisse + ".IS" for hisse in bist_hisseler]

def radar_taramasi():
    tickers = bist_listesini_getir()
    macro_limit, micro_limit = 35, 30
    ilerleme_cubugu = st.progress(0)
    durum_metni = st.empty()
    liste = []

    for i, ticker in enumerate(tickers):
        ilerleme_cubugu.progress((i + 1) / len(tickers))
        hisse_adi = ticker.replace('.IS', '')
        durum_metni.text(f"🔍 Denetleniyor: {hisse_adi} ({i+1}/{len(tickers)})")
        
        try:
            hisse = yf.Ticker(ticker)
            d_gunluk = hisse.history(period="60d")
            if d_gunluk.empty: continue
            d_gunluk['RSI'] = ta.momentum.RSIIndicator(d_gunluk['Close']).rsi()
            rsi_g = d_gunluk['RSI'].iloc[-1]
            
            if rsi_g < macro_limit:
                d_15m = hisse.history(period="5d", interval="15m")
                if d_15m.empty: continue
                d_15m['RSI'] = ta.momentum.RSIIndicator(d_15m['Close']).rsi()
                rsi_m = d_15m['RSI'].iloc[-1]
                
                fiyat = d_15m['Close'].iloc[-1]
                liste.append({
                    "Durum": "🟢 PUSU" if rsi_m < micro_limit else "🟡 İZLE",
                    "Hisse": hisse_adi,
                    "Makro RSI": round(rsi_g, 1),
                    "Mikro RSI": round(rsi_m, 1),
                    "Fiyat (₺)": round(fiyat, 2),
                    "Pusu Limiti (₺)": round(fiyat * 0.995, 2),
                    "Kâr Al (₺)": round(fiyat * 1.07, 2)
                })
        except: pass
    
    durum_metni.empty()
    ilerleme_cubugu.empty()
    return pd.DataFrame(liste)

if st.button("🚀 BIST RADARINI ATEŞLE (Canlı Tarama)"):
    with st.spinner("Borsa İstanbul canlı taranıyor, lütfen bekleyin..."):
        res = radar_taramasi()
        st.session_state.bist_df = res

if st.session_state.bist_df is not None:
    df = st.session_state.bist_df
    if len(df) > 0:
        st.success(f"Analiz Tamamlandı: {len(df)} adet 'Aşırı Cezalandırılmış' Türk şirketi bulundu.")
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Sonuçları CSV Olarak İndir", csv, "bist_pusu_adaylari.csv", "text/csv")
    else:
        st.warning("Bugün hiçbir BIST Likit hissesi Konsey'in katı ucuzluk kriterlerini karşılamadı. Nakitte kalıyoruz.")
