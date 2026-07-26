import streamlit as st
import pandas as pd
import io
import pdfplumber
import re

# Sayfa Ayarları
st.set_page_config(page_title="KAP Portföy Konsolidasyon Portalı", page_icon="📊", layout="wide")

st.title("📊 KAP Fon Portföy Analiz & Konsolidasyon Portalı")
st.write("KAP'tan indirdiğiniz PDF raporlarını yükleyin; sistem hisse bazlı aylık lot miktarlarını matris olarak konsolide etsin.")

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

# İstenmeyen Kelime Filtresi (Giderler, Başlıklar vs.)
BLACKLIST = [
    "SATIN", "TUTAR", "HAKKI", "TOPLAM", "GRUP", "ORAN", "BIST", "HISSE", "PORTFOY", 
    "GIDER", "UNVAN", "MENKUL", "KIYMET", "AÇIKLAMA", "FON", "NOMA", "VADE", "REPO"
]

def clean_number(val_str):
    """Metin içindeki sayısal lot değerini temiz bir floata/int'e çevirir."""
    if not val_str:
        return 0
    try:
        # 123.456.789,00 -> 123456789.00 dönüşümü
        clean = val_str.replace(".", "").replace(",", ".")
        return float(re.findall(r"[-+]?\d*\.\d+|\d+", clean)[0])
    except:
        return 0

def parse_pdf_to_lots(file):
    records = []
    filename = file.name # Örn: DOH_2026.01.pdf veya TLY_2026_02.pdf
    
    # Dosya adından Fon ve Dönem Bilgisini Ayıklama
    parts = re.findall(r"[A-Z0-9]+", filename.upper())
    fon_adi = parts[0] if parts else "BILINMEYEN"
    
    # Dönem tespiti (Örn: 2026.01 veya 2026_01)
    donem_match = re.search(r"202\d[._-]?\d{2}", filename)
    donem_adi = donem_match.group(0).replace("_", ".").replace("-", ".") if donem_match else "Bilinmeyen Dönem"

    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                
                # Tabloları tara
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if not row or len(row) < 3:
                            continue
                        
                        clean_row = [str(c).replace('\n', ' ').strip() for c in row if c is not None]
                        
                        # Borsa Hisse Kodu Tespiti (3-5 Harf, Büyük Harf)
                        for idx, cell in enumerate(clean_row):
                            cell_upper = cell.upper()
                            if re.match(r'^[A-Z]{3,5}$', cell_upper) and cell_upper not in BLACKLIST:
                                hisse_kodu = cell_upper
                                
                                # Satırdaki sayısal lot miktarını bulma (genelde 2. veya 3. sayısal sütun)
                                numbers = [c for c in clean_row if re.search(r'\d', c)]
                                lot_val = 0
                                if numbers:
                                    # En mantıklı lot sayısını al
                                    lot_val = clean_number(numbers[0])
                                
                                if lot_val > 0:
                                    records.append({
                                        "Hisse Kodu": hisse_kodu,
                                        "Fon Adı": fon_adi,
                                        "Dönem": donem_adi,
                                        "Lot": lot_val
                                    })
                                break
    except Exception as e:
        st.error(f"Hata ({filename}): {e}")
        
    return records

# Ana Ekran
if analiz_baslat:
    if not uploaded_files:
        st.warning("⚠️ Lütfen analiz etmek istediğiniz en az bir KAP rapor dosyası yükleyin.")
    else:
        status_box = st.empty()
        status_box.info("🔍 PDF'ler taranıyor, Hisse - Lot eşleşmeleri ayıklanıyor...")
        
        all_records = []
        for file in uploaded_files:
            if file.name.lower().endswith(".pdf"):
                recs = parse_pdf_to_lots(file)
                all_records.extend(recs)

        status_box.success(f"✅ Toplam {len(uploaded_files)} adet dosya işlendi!")
        
        if all_records:
            df_raw = pd.DataFrame(all_records)
            
            # MATRİS / PİVOT TABLO OLUŞTURMA (Hisse Kodu x Dönemler)
            pivot_df = df_raw.pivot_table(
                index=["Hisse Kodu", "Fon Adı"], 
                columns="Dönem", 
                values="Lot", 
                aggfunc="sum", 
                fill_value=0
            ).reset_index()
            
            # Sütun isimlerini düzenleme
            pivot_df.columns.name = None
            
            tab1, tab2 = st.tabs(["📋 Konsolide Lot Tablosu", "📊 Ham Veri"])
            
            with tab1:
                st.subheader("Hisse Bazlı Konsolide Aylık Lot Tablosu")
                st.dataframe(pivot_df, use_container_width=True)
                
                # Excel İndirme
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    pivot_df.to_excel(writer, index=False, sheet_name='Konsolide_Lot_Matrisi')
                
                st.download_button(
                    label="📥 Konsolide Matris Tablosunu Excel Olarak İndir (.xlsx)",
                    data=buffer.getvalue(),
                    file_name="Konsolide_Hisse_Lot_Matrisi.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
            with tab2:
                st.dataframe(df_raw, use_container_width=True)
        else:
            st.warning("Yüklenen PDF'lerde hisse ve lot verisi tespit edilemedi.")
else:
    st.info("👈 Analizi başlatmak için sol taraftaki alana KAP raporlarını yükleyip butona tıklayın.")
