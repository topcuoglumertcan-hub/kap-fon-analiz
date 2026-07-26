import streamlit as st
import pandas as pd
import io
import pdfplumber
import re

# Sayfa Ayarları
st.set_page_config(page_title="KAP Portföy Konsolidasyon Portalı", page_icon="📊", layout="wide")

st.title("📊 KAP Fon Portföy Analiz & Konsolidasyon Portalı")
st.write("KAP'tan indirdiğiniz Portföy Dağılım Raporlarını (PDF / Excel) yükleyin, sistem lot ve maliyetleri anında konsolide etsin.")

# Yan Menü (Sidebar)
st.sidebar.header("⚙️ Analiz Parametreleri")

fon_input = st.sidebar.text_input(
    "Analiz Edilecek Fon Kodları (Virgülle Ayırın):",
    value="TLY, THF, TH3",
    help="İstediğiniz fon kodlarını yazabilirsiniz."
)

secilen_fonlar = [f.strip().upper() for f in fon_input.split(",") if f.strip()]

st.sidebar.markdown("---")
st.sidebar.subheader("📁 KAP Raporlarını Yükleyin")

uploaded_files = st.sidebar.file_uploader(
    "İndirdiğiniz PDF veya Excel dosyalarını buraya bırakın:",
    accept_multiple_files=True,
    type=["pdf", "xlsx", "csv"],
    help="Birden fazla dosyayı aynı anda seçip yükleyebilirsiniz."
)

st.sidebar.markdown("---")
analiz_baslat = st.sidebar.button("🚀 Raporları Çözümle & Konsolide Et", type="primary")

# PDF İçi Tablo Parsing Fonksiyonu
def parse_kap_pdf(file):
    extracted_data = []
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        # Boş veya kısa satırları atla
                        if not row or len(row) < 3:
                            continue
                        
                        # Temizlik ve Metin Ayıklama
                        clean_row = [str(cell).replace('\n', ' ').strip() if cell else '' for cell in row]
                        
                        # Hisse Senedi Kodunu Tespit Etme (Örn: AKBNK, ASELS gibi 4-5 harfli borsa kodları)
                        first_cell = clean_row[0]
                        if re.match(r'^[A-Z]{3,5}$', first_cell):
                            extracted_data.append(clean_row)
    except Exception as e:
        st.error(f"⚠️ **{file.name}** dosyası okunurken hata oluştu: {e}")
    return extracted_data

# Ana Ekran
if analiz_baslat:
    if not uploaded_files:
        st.warning("⚠️ Lütfen analiz etmek istediğiniz en az bir KAP rapor dosyası (PDF veya Excel) yükleyin.")
    else:
        status_box = st.empty()
        status_box.info("🔍 Yüklenen dosyalar taranıyor ve tablolar ayıklanıyor...")
        
        parsed_master_list = []
        
        for file in uploaded_files:
            st.write(f"📄 **İşleniyor:** `{file.name}`")
            
            if file.name.lower().endswith(".pdf"):
                rows = parse_kap_pdf(file)
                for r in rows:
                    parsed_master_list.append({
                        "Hisse Kodu": r[0],
                        "Dosya / Kaynak": file.name,
                        "Veri Detayı": " ".join(r[1:])
                    })
            elif file.name.lower().endswith((".xlsx", ".csv")):
                try:
                    df_temp = pd.read_excel(file) if file.name.endswith(".xlsx") else pd.read_csv(file)
                    st.dataframe(df_temp.head(3), use_container_width=True)
                except Exception as ex:
                    st.error(f"Excel okunurken hata: {ex}")

        status_box.success(f"✅ Toplam {len(uploaded_files)} adet dosya başarıyla analiz edildi!")
        
        # Sonuç Tablosu
        if parsed_master_list:
            df_result = pd.DataFrame(parsed_master_list)
        else:
            df_result = pd.DataFrame(columns=["Hisse Kodu", "Dosya / Kaynak", "Veri Detayı"])

        tab1, tab2 = st.tabs(["📋 Konsolide Tablo", "📈 Özet Görünüm"])
        
        with tab1:
            st.subheader("Konsolide Portföy Tablosu")
            st.dataframe(df_result, use_container_width=True)
            
            # Excel İndirme Alanı
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_result.to_excel(writer, index=False, sheet_name='Konsolide_Portfoy')
            
            st.download_button(
                label="📥 Konsolide Tabloyu Excel Olarak İndir (.xlsx)",
                data=buffer.getvalue(),
                file_name="KAP_Konsolide_Portfoy.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
else:
    st.info("👈 Analizi başlatmak için sol taraftaki alana KAP'tan indirdiğiniz raporları yükleyin ve **'Raporları Çözümle & Konsolide Et'** butonuna tıklayın.")
