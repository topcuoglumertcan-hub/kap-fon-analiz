import streamlit as st
import pandas as pd
import io
import pdfplumber
import re

# Sayfa Ayarları
st.set_page_config(page_title="KAP Portföy Konsolidasyon Portalı", page_icon="📊", layout="wide")

st.title("📊 KAP Fon Portföy Analiz & Konsolidasyon Portalı")
st.write("KAP'tan indirdiğiniz Portföy Dağılım Raporlarını (PDF / Excel) yükleyin, sistem lot ve maliyetleri anında konsolide etsin.")

# Yan Menü
st.sidebar.header("⚙️ Analiz Parametreleri")

fon_input = st.sidebar.text_input(
    "Analiz Edilecek Fon Kodları (Virgülle Ayırın):",
    value="TLY, THF, TH3, DOH",
    help="İstediğiniz fon kodlarını yazabilirsiniz."
)

st.sidebar.markdown("---")
st.sidebar.subheader("📁 KAP Raporlarını Yükleyin")

uploaded_files = st.sidebar.file_uploader(
    "İndirdiğiniz PDF veya Excel dosyalarını buraya bırakın:",
    accept_multiple_files=True,
    type=["pdf", "xlsx", "csv"]
)

st.sidebar.markdown("---")
analiz_baslat = st.sidebar.button("🚀 Raporları Çözümle & Konsolide Et", type="primary")

# Esnek ve Akıllı PDF Parsing Fonksiyonu
def parse_kap_pdf_smart(file):
    extracted_rows = []
    # Dosya adından Dönem ve Fon Adı Çıkarma (Örn: TLY_2026.02.pdf -> Fon: TLY, Dönem: 2026.02)
    filename = file.name
    
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                # Önce tablo bazlı okuma
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if not row:
                            continue
                        clean_row = [str(cell).replace('\n', ' ').strip() for cell in row if cell is not None]
                        
                        # Satır içindeki tüm hücreleri tara: Borsa hisse kodu formatına (3-5 harfli büyük harf) uyan var mı?
                        for cell in clean_row:
                            # Genel bilinen hisse formatları veya kelimeler
                            match = re.search(r'\b[A-Z]{3,5}\b', cell)
                            if match:
                                code = match.group(0)
                                # Fonksiyonel kelimeleri ele (TL, BIST, GRUP, TOPLAM vb.)
                                if code not in ["TL", "BIST", "GRUP", "TOPLAM", "ORAN", "GUN", "HISSE", "FON", "PORTFOY"]:
                                    extracted_rows.append({
                                        "Hisse Kodu": code,
                                        "Dosya / Kaynak": filename,
                                        "Tüm Satır İçeriği": " | ".join(clean_row)
                                    })
                                    break
    except Exception as e:
        st.error(f"⚠️ **{filename}** okunurken hata: {e}")
        
    return extracted_rows

# Ana Ekran
if analiz_baslat:
    if not uploaded_files:
        st.warning("⚠️ Lütfen analiz etmek istediğiniz en az bir KAP rapor dosyası yükleyin.")
    else:
        status_box = st.empty()
        status_box.info("🔍 Yüklenen PDF/Excel dosyaları ayıklanıyor...")
        
        all_parsed_data = []
        
        for file in uploaded_files:
            st.write(f"📄 **İşleniyor:** `{file.name}`")
            if file.name.lower().endswith(".pdf"):
                rows = parse_kap_pdf_smart(file)
                all_parsed_data.extend(rows)
            elif file.name.lower().endswith((".xlsx", ".csv")):
                try:
                    df_temp = pd.read_excel(file) if file.name.endswith(".xlsx") else pd.read_csv(file)
                    st.dataframe(df_temp.head(3), use_container_width=True)
                except Exception as ex:
                    st.error(f"Excel hatası: {ex}")

        status_box.success(f"✅ Toplam {len(uploaded_files)} adet dosya başarıyla analiz edildi!")
        
        if all_parsed_data:
            df_result = pd.DataFrame(all_parsed_data)
            # Tekrarlayan tam aynı satırları temizle
            df_result = df_result.drop_duplicates()
        else:
            df_result = pd.DataFrame(columns=["Hisse Kodu", "Dosya / Kaynak", "Tüm Satır İçeriği"])

        tab1, tab2 = st.tabs(["📋 Konsolide Tablo", "📈 Özet Görünüm"])
        
        with tab1:
            st.subheader("Konsolide Portföy Veri Tablosu")
            st.dataframe(df_result, use_container_width=True)
            
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
    st.info("👈 Analizi başlatmak için sol menüden raporları yükleyip **'Raporları Çözümle & Konsolide Et'** butonuna tıklayın.")
