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
            parsed = parse_pdf(pdf_file)
            all_results.append(parsed)
            progress_bar.progress((idx + 1) / len(uploaded_files))
            
        summary_df, detail_df = build_portfolio_matrix(all_results)
        
        if not summary_df.empty:
            st.subheader("📋 Birleştirilmiş Portföy & Hisse Dağılım Tablosu")
            
            # Görsel 2 Birebir Tablo Gösterimi
            st.dataframe(summary_df, use_container_width=True)
            
            st.divider()
            st.write("### 🔍 Interaktif Hisse / Portföy Şirketi Detayları")
            
            # ADESE vb. Tıklandığında Açılan Interaktif Yapı
            unique_hisseler = detail_df["Hisse Kodu"].unique()
            for hisse in unique_hisseler:
                hisse_data = detail_df[detail_df["Hisse Kodu"] == hisse]
                
                with st.expander(f"📌 Toplam {hisse} - Portföy Şirketi & Dosya/Fon Detayları"):
                    st.write(f"**{hisse}** hissesine sahip portföy şirketleri ve fon kodları:")
                    st.dataframe(
                        hisse_data.drop(columns=["Hisse Kodu"]), 
                        use_container_width=True
                    )
            
            # Excel İndirme
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                summary_df.to_excel(writer, index=False, sheet_name='Fon_Analiz_Ozet')
                detail_df.to_excel(writer, index=False, sheet_name='Detay_Veri')
            
            st.download_button(
                label="📥 Excel Olarak İndir (.xlsx)",
                data=buffer.getvalue(),
                file_name="KAP_Fon_Portfoy_Analiz.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("Veri okunamadı. Lütfen PDF dosyalarını kontrol edin.")
