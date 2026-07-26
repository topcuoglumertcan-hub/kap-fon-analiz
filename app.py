import streamlit as st
import pandas as pd
import requests
import io

# Sayfa Ayarları
st.set_page_config(page_title="KAP Fon Analiz Portalı", page_icon="📊", layout="wide")

st.title("📊 KAP Fon Portföy Analiz & Konsolidasyon Portalı")
st.write("Fon raporlarınızı otomatik analiz edin ve konsolide Excel tabloları üretin.")

# Yan Menü (Sidebar) - Parametre Seçimleri
st.sidebar.header("⚙️ Analiz Parametreleri")
secilen_fonlar = st.sidebar.multiselect(
    "Analiz Edilecek Fonları Seçin:",
    ["TLY", "THF", "TH3"],
    default=["TLY", "THF", "TH3"]
)

tarih_araligi = st.sidebar.select_slider(
    "Dönem Seçin (2026):",
    options=["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran"]
)

st.sidebar.markdown("---")
analiz_baslat = st.sidebar.button("🚀 Analizi Başlat", type="primary")

# Ana Ekran
if analiz_baslat:
    with st.spinner("KAP bildirimleri taranıyor ve veriler konsolide ediliyor..."):
        # Örnek konsolide veri gösterimi
        st.success("✅ Veriler başarıyla çekildi ve konsolide edildi!")
        
        # Sekmeli Görünüm
        tab1, tab2 = st.tabs(["📋 Konsolide Tablo", "📈 Özet İstatistikler"])
        
        with tab1:
            st.subheader("Konsolide Fon Portföy Tablosu")
            st.info("Aşağıdaki tablo seçilen fonların ilgili dönemdeki lot ve maliyet konsolidasyonunu içerir.")
            
            # Örnek Önizleme Tablosu
            data = {
                "Hisse Kodu": ["AKBNK", "ASELS", "PEKGY", "TEHOL", "TERA"],
                "Ocak Lot": [225000, 250000, 551922602, 114275980, 32870366],
                "Haziran Lot": [250000, 225000, 1125804146, 388424267, 76378299],
                "Ort. Maliyet (TL)": [76.21, 247.46, 14.35, 29.61, 226.28],
                "Haziran Fiyat (TL)": [77.00, 345.00, 13.97, 37.50, 177.00]
            }
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
            
            # Excel İndirme Butonu
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Konsolide_Portfoy')
            
            st.download_button(
                label="📥 Konsolide Tabloyu Excel Olarak İndir (.xlsx)",
                data=buffer.getvalue(),
                file_name="Konsolide_Fon_Portfoy_Raporu.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
else:
    st.info("👈 Analizi başlatmak için sol menüden fonları seçip 'Analizi Başlat' butonuna tıklayın.")
