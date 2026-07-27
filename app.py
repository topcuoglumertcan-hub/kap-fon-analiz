import streamlit as st
from pdf_parser import parse_pdf

st.set_page_config(page_title="KAP Fon Analiz", layout="wide")

st.title("📊 KAP Fon Analiz Platformu")

uploaded_files = st.file_uploader(
    "PDF Dosyalarını Seç",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:

    st.success(f"{len(uploaded_files)} adet PDF seçildi.")

    if st.button("Analizi Başlat"):

        for pdf in uploaded_files:

            st.subheader(pdf.name)

            result = parse_pdf(pdf)

            st.json(result)
