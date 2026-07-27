import streamlit as st
import pandas as pd
import io
from pdf_parser import parse_pdf
from portfolio_builder import build_portfolio_matrix

st.set_page_config(page_title="KAP Fon Analiz Platformu", layout="wide")

st.title("📊 KAP Fon Analiz Platformu")
st.write("Aylık KAP Fon Portföy Dağılım Raporlarını (PDF) yükleyerek hisse bazlı lot ve maliyet matrisinizi oluşturun.")

uploaded_files = st.file_uploader(
    "PDF Dosyalarını Seç (Birden fazla seçebilirsiniz)",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:
    st.success(f"Toplam {len(uploaded_files)} adet PDF seçildi.")
    
    if st.button("🚀 Analizi Başlat", type="primary"):
        all_results = []
        
        progress_bar = st.progress(0)
        for idx, pdf_file in enumerate(uploaded_files):
            # PDF Ayrıştırma
            parsed = parse_pdf(pdf_file)
            all_results.append(parsed)
            progress_bar.progress((idx + 1) / len(uploaded_files))
            
        st.subheader("📋 Birleştirilmiş Portföy & Hisse Dağılım Tablosu")
        
        # Verileri Matris Yapısına Dönüştür
        matrix_df = build_portfolio_matrix(all_results)
        
        if not matrix_df.empty:
            # Tabloyu Ekrana Bas
            st.dataframe(matrix_df, use_container_width=True)
            
            # Excel İndirme Butonu
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                matrix_df.to_excel(writer, index=False, sheet_name='Fon_Analiz')
            
            st.download_button(
                label="📥 Excel Olarak İndir (.xlsx)",
                data=buffer.getvalue(),
                file_name="KAP_Fon_Portfoy_Analiz.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("PDF'lerden hisse tablosu verisi çıkarılamadı. Formatları kontrol edin.")
