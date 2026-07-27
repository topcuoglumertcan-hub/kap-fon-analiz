import pdfplumber
import re
import pandas as pd

def parse_pdf(pdf_file):
    """
    KAP Fon Dağılım Raporu PDF'inden fon bilgilerini ve 
    portföydeki hisse senedi detaylarını çekeler.
    """
    extracted_data = {
        "fon_kodu": "",
        "fon_adi": "",
        "donem": "",
        "hisseler": []  # List of dicts: {'hisse': ..., 'lot': ..., 'maliyet': ..., 'agirlik': ...}
    }
    
    with pdfplumber.open(pdf_file) as pdf:
        full_text = ""
        
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
            
            # Tabloları tara (Hisse senetlerinin bulunduğu tablolar)
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    # Boş veya çok kısa satırları atla
                    if not row or len(row) < 3:
                        continue
                    
                    # Satır birleştirme ve temizleme
                    row_clean = [str(cell).strip().replace('\n', ' ') if cell else '' for cell in row]
                    row_str = " ".join(row_clean)
                    
                    # Hisse senedi satırını tespit etmeye çalış
                    # Örn: THYAO, GARAN gibi hisse kodları veya Hisse Adı + Sayısal değerler
                    # Sadece sayı ve metin içeren geçerli finansal veri satırlarını yakala
                    if any(char.isdigit() for char in row_str):
                        # Portföy tablosundaki colon eşleşmesi (Hisse, Nominal/Lot, Birim Fiyat, Maliyet vs.)
                        # KAP rapor formatına göre indeksler uyarlanabilir:
                        try:
                            # Örnek sütun yapısı: [Sermaye Piyasası Aracı / Hisse, Lot/Nominal, Rayiç Değer, Oran(%)]
                            hisse_adi = row_clean[0]
                            
                            # Filtre: Başlık satırlarını ve ilgisiz toplamları ele
                            if "TOPLAM" in hisse_adi.upper() or "MENKUL" in hisse_adi.upper() or "AKSİYON" in hisse_adi.upper():
                                continue
                            
                            # Lot sayısı ve Maliyet sayılarını temizleme
                            lot_str = re.sub(r'[^\d,.-]', '', row_clean[1]).replace('.', '').replace(',', '.')
                            lot = float(lot_str) if lot_str else 0
                            
                            maliyet = 0
                            agirlik = 0
                            
                            if len(row_clean) > 2:
                                maliyet_str = re.sub(r'[^\d,.-]', '', row_clean[2]).replace('.', '').replace(',', '.')
                                maliyet = float(maliyet_str) if maliyet_str else 0
                                
                            if len(row_clean) > 3:
                                agirlik_str = re.sub(r'[^\d,.-]', '', row_clean[3]).replace('.', '').replace(',', '.')
                                agirlik = float(agirlik_str) if agirlik_str else 0

                            if hisse_adi and lot > 0:
                                extracted_data["hisseler"].append({
                                    "hisse": hisse_adi,
                                    "lot": lot,
                                    "maliyet": maliyet,
                                    "agirlik": agirlik
                                })
                        except Exception:
                            continue

        # Genel Fon Bilgilerini Regex ile bul
        fon_match = re.search(r"\b([A-Z]{3})\b\s*-\s*(.+)", full_text)
        if fon_match:
            extracted_data["fon_kodu"] = fon_match.group(1)
            extracted_data["fon_adi"] = fon_match.group(2).split('\n')[0].strip()
        else:
            # Alternatif arama
            code_match = re.search(r"FON KODU\s*:\s*([A-Z]{3})", full_text, re.IGNORECASE)
            if code_match:
                extracted_data["fon_kodu"] = code_match.group(1)

        period_match = re.search(r"(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s*20\d{2}", full_text, re.IGNORECASE)
        if period_match:
            extracted_data["donem"] = period_match.group(0).capitalize()

    return extracted_data
