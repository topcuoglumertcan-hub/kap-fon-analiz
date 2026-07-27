import streamlit as st
from datetime import date

st.set_page_config(
    page_title="KAP Fon Analiz Platformu",
    page_icon="📊",
    layout="wide"
)

st.title("📊 KAP Fon Analiz Platformu")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:

    st.subheader("Portföy Şirketi")

    portfolio_company = st.selectbox(
        "Portföy Yönetim Şirketi",
        [
            "Tera Portföy",
            "Pusula Portföy",
            "İş Portföy",
            "Ak Portföy",
            "Garanti Portföy"
        ]
    )

with col2:

    st.subheader("Fon Kodları")

    fund_codes = st.text_input(
        "Fon Kodları (Virgülle Ayır)",
        value="TLY,DOH"
    )

st.markdown("---")

c1, c2 = st.columns(2)

with c1:
    start_date = st.date_input(
        "Başlangıç Tarihi",
        value=date(2026,1,1)
    )

with c2:
    end_date = st.date_input(
        "Bitiş Tarihi",
        value=date.today()
    )

st.markdown("---")

if st.button(
    "🚀 KAP Bildirimlerini Tara",
    use_container_width=True,
    type="primary"
):

    st.info("KAP sorgusu başlatılıyor...")

    st.write("Portföy Şirketi :", portfolio_company)

    st.write("Fon Kodları :", fund_codes)

    st.write("Başlangıç :", start_date)

    st.write("Bitiş :", end_date)
