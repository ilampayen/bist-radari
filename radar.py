import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import warnings

warnings.filterwarnings('ignore')

# 1. SAYFA YAPISI VE BAŞLIK
st.set_page_config(page_title="BIST 100 Zaman Motorlu Radar V8.6", layout="wide")
st.title("🏛️ AKADEMİK FİNANS KONSEYİ")
st.subheader("BIST 100 Kuantitatif Pusu ve Zaman Maliyeti Radarı (V8.6)")

# BELLEK YÖNETİMİ
if 'bist_df' not in st.session_state: 
    st.session_state.bist_df = None

# 2. BIST 100 LİSTESİ
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

# 3. ZAMAN MOTORU (V8.6)
def backtest_hesapla(data, limit=35, hedef_yuzde=1.07, max_bekleme=30):
    try:
        sinyaller = data[data['RSI'] < limit]
        if len(sinyaller) == 0: return 0.0, 0.0, 0
        
        kazanc, toplam, adet = 0, 0.0, 0
        toplam_hedef_gun, hedefe_ulasan_adet = 0, 0
        
        for idx, row in sinyaller.iterrows():
            loc = data.index.get_loc(idx)
            alis_fiyati = row['Close']
            hedef_fiyat = alis_fiyati * hedef_yuzde
            
            # Zaman Maliyeti: Hedefe ulaştığı ilk gün
            if loc + 1 < len(data):
                end_loc = min(loc + max_bekleme, len(data) - 1)
                gelecek_veri = data.iloc[loc+1 : end_loc+1]
                
                hedefi_vuranlar = gelecek_veri[gelecek_veri['High'] >= hedef_fiyat]
                
                if not hedefi_vuranlar.empty:
                    ilk_vurus_idx = hedefi_vuranlar.index[0]
                    gecen_gun = data.index.get_loc(ilk_vurus_idx) - loc
                    toplam_hedef_gun += gecen_gun
                    hedefe_ulasan_adet += 1

            # Klasik 10 Günlük Getiri Testi
            bekleme = 10
            if loc + bekleme < len(data):
                ret = (data.iloc[loc + bekleme]['Close'] - alis_fiyati) / alis_fiyati
                toplam += ret
                if ret > 0: kazanc += 1
                adet += 1
                
        tarihsel_k = round((kazanc/adet)*100, 1) if adet > 0 else 0.0
        ort_getiri = round((toplam/adet)*100, 2) if adet > 0 else 0.0
        ort_hedef_gun = round(toplam_hedef_gun / hedefe_ulasan_adet, 1) if hedefe_ulasan_adet > 0 else 0
        
        return tarihsel_k, ort_getiri, ort_hedef_gun
    except: return 0.0, 0.0, 0

# 4. ANALİZ VE TARAMA
def analiz_et(ticker):
    try:
        hisse = yf.Ticker(ticker)
        d_gunluk = hisse.history(period="1y")
        if len(d_gunluk) < 50: return None
        
        d_gunluk['RSI'] = ta.momentum.RSIIndicator(d_gunluk['Close']).rsi()
        rsi_g = d_gunluk['RSI'].iloc[-1]
        
        if rsi_g < 35:
            d_15m = hisse.history(period="5d", interval="15m")
            if d_15m.empty: return None
            
            d_15m['RSI'] = ta.momentum.RSIIndicator(d_15m['Close']).rsi()
            rsi_m = d_15m['RSI'].iloc[-1]
            fiyat = d_15m['Close'].iloc[-1]
            
            durum = "🟢 PUSU" if rsi_m < 30 else ("🟡 İZLE" if rsi_m < 40 else "⚪ NÖTR")
            
            k, o, gun = backtest_hesapla(d_gunluk)
            hisse_adi = ticker.replace(".IS", "")
            
            return {
                "Durum": durum,
                "Hisse": hisse_adi,
                "Makro RSI": round(rsi_g, 1),
                "Mikro RSI": round(rsi_m, 1),
                "Tarihsel Başarı (%)": k,
                "Ort. Getiri (%)": o,
                "Tahmini Kâr Al (Gün)": f"{gun} Gün" if gun > 0 else "Ulaşamadı",
                "Fiyat (₺)": round(fiyat, 2),
                "Pusu Limiti (₺)": round(fiyat * 0.995, 2),
                "Kâr Al (₺)": round(fiyat * 1.07, 2)
            }
    except: return None

# 5. KONTROL PANELİ VE ATEŞLEME
if st.button("🚀 BIST 100 PUSU RADARINI ATEŞLE (Derin Analiz)"):
    with st.spinner("Borsa İstanbul taranıyor ve zaman maliyeti hesaplanıyor... (1-2 dk)"):
        market_res = []
        tickers = bist_listesini_getir()
        prog = st.progress(0)
        durum_m = st.empty()
        
        for i, t in enumerate(tickers):
            prog.progress((i+1)/len(tickers))
            durum_m.text(f"🔍 İnceleniyor: {t.replace('.IS', '')}")
            r = analiz_et(t)
            if r: market_res.append(r)
            
        st.session_state.bist_df = pd.DataFrame(market_res)
        prog.empty()
        durum_m.empty()
        st.success("Tarama ve Zaman Analizi Tamamlandı.")

# 6. GÖRSELLEŞTİRME
st.markdown("---")
if st.session_state.bist_df is not None:
    df = st.session_state.bist_df
    if not df.empty:
        st.markdown("### 🔍 BIST 100 GÜNCEL PUSU ADAYLARI")
        st.dataframe(df.sort_values(by="Tarihsel Başarı (%)", ascending=False), use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Sonuçları İndir (CSV)", csv, "bist100_v86_zaman_motoru.csv", "text/csv")
    else:
        st.info("Kriterlere uyan hisse bulunamadı. Endeks aşırı fiyatlanmış olabilir.")
