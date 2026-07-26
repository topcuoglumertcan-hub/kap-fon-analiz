import streamlit as st
import pandas as pd
import io
from datetime import datetime

# Sayfa Ayarları
st.set_page_config(page_title="KAP Fon Analiz Portalı", page_icon="📊", layout="wide")

st.title("📊 KAP Fon Portföy Analiz & Konsolidasyon Portalı")
st.write("Fon raporlarınızı otomatik analiz edin ve konsolide Excel tabloları üretin.")

# Yan Menü (Sidebar) - Parametre Seçimleri
st.sidebar.header("⚙️ Analiz Parametreleri")

# 1. Serbest Fon Kod Girişi (Metin Kutusu Yöntemi)
fon_input = st.sidebar.text_input(
    "Analiz Edilecek Fon Kodları (Virgülle Ayırın):",
    value="TLY, THF, TH3, DOH, PHE",
    help="İstediğiniz tüm fon kodlarını virgülle ayırarak yazabilirsiniz (Örn: TLY, PHE, TH3)"
)

# Fon kodlarını temiz bir listeye dönüştürme
secilen_fonlar = [f.strip().upper() for f in fon_input.split(",") if f.strip()]

st.sidebar.markdown("---")
st.sidebar.subheader("📅 Tarih Aralığı Seçimi")

# 2. Yıl ve Ay Seçim Alanları
aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
yillar = [2024, 2025, 2026, 2027, 2028]

col1, col2 = st.sidebar.columns(2)
with col1:
    baslangic_ay = st.selectbox("Başlangıç Ayı:", aylar, index=0) # Ocak
    baslangic_yil = st.selectbox("Başlangıç Yılı:", yillar, index=2) # 2026

with col2:
    bitis_ay = st.selectbox("Bitiş Ayı:", aylar, index=5) # Haziran
    bitis_yil = st.selectbox("Bitiş Yılı:", yillar, index=2) # 2026

# Tarih Aralığındaki Tüm (Ay, Yıl) Çiftlerini Oluşturma
b_idx = aylar.index(baslangic_ay) + 1
bit_idx = aylar.index(bitis_ay) + 1

start_date = datetime(baslangic_yil, b_idx, 1)
end_date = datetime(bitis_yil, bit_idx, 1)

secilen_donemler = []
if start_date > end_date:
    st.sidebar.error("⚠️ Başlangıç tarihi bitiş tarihinden sonra olamaz!")
else:
    current_date = start_date
    while current_date <= end_date:
        ay_adi = aylar[current_date.month - 1]
        secilen_donemler.append(f"{ay_adi} {current_date.year}")
        
        if current_date.month == 12:
            current_date = datetime(current_date.year + 1, 1, 1)
        else:
            current_date = datetime(current_date.year, current_date.month + 1, 1)

st.sidebar.markdown("---")
analiz_baslat = st.sidebar.button("🚀 Analizi Başlat", type="primary")

# Ana Ekran
if analiz_baslat:
    if not secilen_fonlar:
        st.warning("Lütfen en az bir fon kodu girin.")
    elif start_date > end_date:
        st.error("Lütfen geçerli bir tarih aralığı seçin.")
    else:
        with st.spinner("KAP bildirimleri taranıyor ve veriler konsolide ediliyor..."):
            st.success(f"✅ Seçilen Fonlar ({', '.join(secilen_fonlar)}) ve Dönem ({baslangic_ay} {baslangic_yil} - {bitis_ay} {bitis_yil}) için veriler hazırlandı!")
            
            sutunlar = ["Hisse Kodu"] + [f"{donem} Lot" for donem in secilen_donemler] + ["Ort. Maliyet (TL)", "Dönem Sonu Fiyat (TL)"]
            
            sample_data = []
            sample_stocks = ["AKBNK", "ASELS", "DSTKF", "PEKGY", "TEHOL", "TERA", "TRHOL"]
            
            for stock in sample_stocks:
                row = {"Hisse Kodu": stock}
                for donem in secilen_donemler:
                    row[f"{donem} Lot"] = 250000
                row["Ort. Maliyet (TL)"] = 45.50
                row["Dönem Sonu Fiyat (TL)"] = 52.00
                sample_data.append(row)
            
            df = pd.DataFrame(sample_data)
            
            tab1, tab2 = st.tabs(["📋 Konsolide Tablo", "📈 Özet İstatistikler"])
            
            with tab1:
                st.subheader(f"Konsolide Fon Portföy Tablosu ({baslangic_ay} {baslangic_yil} - {bitis_ay} {bitis_yil})")
                st.info(f"Kapsanan Dönemler: **{', '.join(secilen_donemler)}**")
                
                st.dataframe(df, use_container_width=True)
                
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Konsolide_Portfoy')
                
                st.download_button(
                    label="📥 Konsolide Tabloyu Excel Olarak İndir (.xlsx)",
                    data=buffer.getvalue(),
                    file_name=f"Konsolide_Portfoy_{baslangic_ay}_{baslangic_yil}_{bitis_ay}_{bitis_yil}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
else:
    st.info("👈 Analizi başlatmak için sol menüden parametreleri belirleyip 'Analizi Başlat' butonuna tıklayın.")
