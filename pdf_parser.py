import pdfplumber
import re
import os

def parse_pdf(pdf_file):
    extracted_data = {
        "fon_kodu": "",
        "fon_adi": "",
        "donem": "",
        "hisseler": []
    }
    
    # 1. Dosya adından yedek Fon Kodu ve Dönem çıkarma (Örn: DOH_2026.06.pdf)
    file_name = getattr(pdf_file, "name", "")
    if file_name:
        fn_match = re.search(r"([A-Z0-9]{3,5})_(\d{4})\.(\d{2})", file_name)
        if fn_match:
            extracted_data["fon_kodu"] = fn_match.group(1)
            months = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
                      "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
            m_idx = int(fn_match.group(3)) - 1
            if 0 <= m_idx < 12:
                extracted_data["donem"] = f"{months[m_idx]} {fn_match.group(2)}"

    with pdfplumber.open(pdf_file) as pdf:
        full_text = ""
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                full_text += t + "\n"

        # PDF İçinden Dönem Bulma (Yedek olarak)
        if not extracted_data["donem"]:
            period_match = re.search(r"(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s*[-:]?\s*(20\d{2})", full_text, re.IGNORECASE)
            if period_match:
                extracted_data["donem"] = f"{period_match.group(1).capitalize()} {period_match.group(2)}"

        # PDF İçinden Fon Kodu Bulma
        code_match = re.search(r"\b([A-Z0-9]{3})\b\s*-\s*", full_text)
        if code_match:
            extracted_data["fon_kodu"] = code_match.group(1)

        lines = full_text.split("\n")
        
        # Hisse Senedi Bölümünü Taramaya Başla
        in_hisse_section = False
        
        for i, line in enumerate(lines):
            line_str = line.strip()
            
            # Bölüm Başlangıcı
            if "HİSSE SENETLERİ" in line_str.upper() or "Hisse Türk" in line_str:
                in_hisse_section = True
                continue
            
            # Bölüm Bitişi (Grup Toplamı veya Türev araçlara gelince dur)
            if "GRUP TOPLAMI" in line_str.upper() or "TÜREV" in line_str.upper():
                in_hisse_section = False
                
            # Eğer Hisse Senetleri alanındaysak veya ISIN Kodu Yakaladıysak
            isin_match = re.search(r"(TR[A-Z0-9]{10})", line_str)
            
            if isin_match or (in_hisse_section and re.search(r"\d{1,3}(?:\.\d{3})+,\d{2}", line_str)):
                # Hisse Kodunu Arama (AKBNK, AKSEN, ALKLC vb. 3-5 harfli büyük kelime)
                hisse_kodu = ""
                
                # Mevcut satır, 1 üst satır ve 2 üst satıra bak
                search_scope = [line_str]
                if i > 0: search_scope.append(lines[i-1].strip())
                if i > 1: search_scope.append(lines[i-2].strip())
                
                for scope in search_scope:
                    tokens = scope.split()
                    for t in tokens:
                        # Temiz kelime
                        clean_t = re.sub(r'[^A-Z0-9]', '', t)
                        if clean_t.isupper() and 3 <= len(clean_t) <= 5 and clean_t not in ["TL", "TAS", "AS", "INC", "TRY", "TRA", "TRE"]:
                            hisse_kodu = clean_t
                            break
                    if hisse_kodu:
                        break
                
                if not hisse_kodu:
                    continue

                # Sayısal Değerleri Ayrıştırma
                # Formatlar: 36.540.242,00 veya -800.000,00 veya 73,919844
                numbers = re.findall(r'[-+]?\s*\d{1,3}(?:\.\d{3})*,\d+', line_str)
                
                def parse_tr_float(val_str):
                    try:
                        clean_str = val_str.replace(' ', '').replace('.', '').replace(',', '.')
                        return float(clean_str)
                    except:
                        return 0.0

                parsed_numbers = [parse_tr_float(n) for n in numbers]
                
                # KAP Tablosundaki Standart Sütunlar:
                # Lot (Nominal), Birim Alış Fiyatı (Maliyet), Günlük BR Değer, Toplam Değer, Grup %...
                if len(parsed_numbers) >= 2:
                    lot = parsed_numbers[0]
                    maliyet = parsed_numbers[1]
                    
                    # Son sayısal değerler genelde Grup % ve Fiyattır
                    hisse_fiyati = parsed_numbers[2] if len(parsed_numbers) > 2 else maliyet
                    grup_agirligi = parsed_numbers[-3] if len(parsed_numbers) >= 5 else 0.0

                    # Aynı hisseyi mükerrer eklememek için kontrol
                    extracted_data["hisseler"].append({
                        "hisse": hisse_kodu,
                        "lot": lot,
                        "maliyet": maliyet,
                        "hisse_fiyati": hisse_fiyati,
                        "grup_agirligi": grup_agirligi
                    })

    return extracted_data
