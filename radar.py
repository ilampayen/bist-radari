import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import warnings

warnings.filterwarnings('ignore')

st.set_page_config(page_title="BIST 100 Pusu Radarı V8.0", layout="wide")
st.title("🏛️ AKADEMİK FİNANS KONSEYİ")
st.subheader("Borsa İstanbul (BIST 100) Kuantitatif Radar ve Backtest Motoru (V8.0)")

if 'bist_df' not in st.session_state:
    st.session_state.bist_df = None

@st.cache_data(ttl=3600)
def bist_listesini_getir():
    bist_hisseler = [
        "AEFES", "AGHOL", "AHGAZ", "AKBNK", "AKCNS", "AKFGY", "AKFYE", "AKSA", "AKSEN", "ALARK", 
        "ALBRK", "ALFAS", "ARCLK", "ASELS", "ASTOR", "ASUZU", "AYDEM", "BAGFS", "BASGZ", "BIMAS", 
        "BIOEN", "BOBET", "BRISA", "BRSAN", "BUCIM", "CANTE", "CCOLA", "CEMAS", "CIMSA", "CWENE", 
        "DOAS", "DOHOL", "ECILC", "EGEEN", "EKGYO", "ENJSA", "ENKAI", "EREGL", "EUPWR", "EUREN", 
        "FROTO", "GARAN", "GENIL", "GESAN", "GLYHO", "GUBRF", "GWIND", "HALKB", "HEKTS", "IMASM", 
        "IPEKE", "ISCTR", "ISDMR", "ISGYO", "ISMEN", "IZENR", "KAYSE", "KCAER", "KCHOL", "KMPUR", 
        "KONTR", "KONYA", "KOZAA", "KOZAL", "KRDMD", "KZBGY", "MAVI", "MGROS", "MIATK", "ODAS", 
        "OTKAR", "OYAKC", "PENTA", "PETKM", "PGSUS", "PSGYO", "QUAGR", "SAHOL", "SASA", "SDTTR", 
        "SISE", "SKBNK", "SMRTG", "SOKM", "TATGD", "TAVHL", "TCELL", "THYAO", "TKFEN", "TOASO", 
        "TSKB", "TTKOM", "TTRAK", "TUKAS", "TUPRS", "ULKER", "VAKBN", "VESBE", "VESTL", "YEOTK", 
        "YKBNK", "YYLGD", "ZOREN"
    ]
    return [hisse + ".IS" for hisse in bist_hisseler]

def backtest_hesapla(data, limit=35, bekleme_suresi=10):
    try:
        sinyaller = data[data['RSI'] < limit]
        if len(sinyaller) == 0: return 0.0, 0.0
        kazanc_sayisi, toplam_getiri, gecerli_islem = 0, 0.0, 0
        
        for idx, row in sinyaller.iterrows():
            sinyal_index = data.index.get_loc(idx)
            if sinyal_index + bekleme_suresi < len(data):
                alis = row['Close']
                satis = data.iloc[sinyal_index + bekleme_suresi]['Close']
                getiri = (satis - alis) / alis
                toplam_getiri += getiri
                if getiri > 0: kazanc_sayisi += 1
                gecerli_islem += 1
                
        if gecerli_islem == 0: return 0.0, 0.0
        return round((kazanc_sayisi / gecerli_islem) * 100, 1), round((toplam_getiri / gecerli_islem) * 100, 2)
    except:
        return 0.0, 0.0

def radar_taramasi():
    tickers = bist_listesini_getir()
    macro_limit, micro_limit = 35, 30
    ilerleme_cubugu = st.progress(0)
    durum_metni = st.empty()
    liste = []

    for i, ticker in enumerate(tickers):
        ilerleme_cubugu.progress((i + 1) / len(tickers))
        hisse_adi = ticker.replace('.IS', '')
        durum_metni.text(f"🔍 Taranıyor ve Test Ediliyor: {hisse_adi} ({i+1}/{len(tickers)})")
        
        try:
            hisse = yf.Ticker(ticker)
            d_gunluk = hisse.history(period="1y")
            if len(d_gunluk) < 50: continue
            d_gunluk['RSI'] = ta.momentum.RSIIndicator(d_gunluk['Close']).rsi()
            rsi_g = d_gunluk['RSI'].iloc[-1]
            
            if rsi_g < macro_limit:
                kazanma_orani, ortalama_getiri = backtest_hesapla(d_gunluk, macro_limit, 10)
                
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
                    "Tarihsel Kazanma (%)": kazanma_orani,
                    "Ortalama Getiri (%)": ortalama_getiri,
                    "Fiyat (₺)": round(fiyat, 2),
                    "Pusu Limiti (₺)": round(fiyat * 0.995, 2),
                    "Kâr Al (₺)": round(fiyat * 1.07, 2)
                })
        except: pass
    
    durum_metni.empty()
    ilerleme_cubugu.empty()
    return pd.DataFrame(liste)

if st.button("🚀 BIST 100 RADARINI VE BACKTESTİ ATEŞLE"):
    with st.spinner("Borsa İstanbul canlı taranıyor ve geçmişi sorgulanıyor..."):
        st.session_state.bist_df = radar_taramasi()

if st.session_state.bist_df is not None:
    df = st.session_state.bist_df
    if len(df) > 0:
        st.success(f"Analiz Tamamlandı: BIST 100 içinden {len(df)} aday bulundu.")
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 CSV İndir", df.to_csv(index=False).encode('utf-8'), "bist100_backtest.csv", "text/csv")
    else:
        st.warning("Kriterlere uyan hisse bulunamadı.")
