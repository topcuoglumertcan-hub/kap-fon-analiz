import pdfplumber
import re

def parse_pdf(pdf_file):
    extracted_data = {
        "fon_kodu": "",
        "fon_adi": "",
        "donem": "",
        "hisseler": []
    }
    
    with pdfplumber.open(pdf_file) as pdf:
        full_text = ""
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                full_text += t + "\n"
        
        # 1. Fon Kodu, Adı ve Dönem Tespiti
        # Örn: PHE-PUSULA PORT. HIS. SEN. FN. ... Haziran-2026
        header_match = re.search(r"^([A-Z0-9]{3,5})\s*-\s*(.+)$", full_text, re.MULTILINE)
        if header_match:
            extracted_data["fon_kodu"] = header_match.group(1).strip()
            extracted_data["fon_adi"] = header_match.group(2).strip()
            
        period_match = re.search(r"(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s*[-:]?\s*(20\d{2})", full_text, re.IGNORECASE)
        if period_match:
            extracted_data["donem"] = f"{period_match.group(1).capitalize()} {period_match.group(2)}"

        # 2. Tablo Satırlarını Yakalama
        # HİSSE SENETLERİ başlığı ile GRUP TOPLAMI arasındaki metni kes
        hisse_section = full_text
        if "HİSSE SENETLERİ" in full_text:
            hisse_section = full_text.split("HİSSE SENETLERİ")[-1]
        if "GRUP TOPLAMI" in hisse_section:
            hisse_section = hisse_section.split("GRUP TOPLAMI")[0]
            
        lines = hisse_section.split("\n")
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # ISIN Kodu barındıran satırlar hisse senedi verisidir (ör. TRAAKBNK91N6, TREAKSN00011)
            isin_match = re.search(r"(TR[A-Z0-9]{10})", line)
            
            if isin_match:
                isin_code = isin_match.group(1)
                
                # ISIN satırı öncesinde veya aynı satırda Hisse Kodu (3-5 Harf) arayalım
                # Örn: "AKBNK TL AKBANK TAS TRAAKBNK91N6 36.540.242,00 ..."
                tokens = line.split()
                hisse_kodu = ""
                
                for t in tokens:
                    if t.isupper() and 3 <= len(t) <= 5 and t not in ["TL", "TAS", "AŞ", "INC"]:
                        hisse_kodu = t
                        break
                
                # Eğer aynı satırda bulunamadıysa bir üst satıra bak
                if not hisse_kodu and i > 0:
                    prev_tokens = lines[i-1].strip().split()
                    if prev_tokens:
                        candidate = prev_tokens[0]
                        if candidate.isupper() and 3 <= len(candidate) <= 5:
                            hisse_kodu = candidate
                            
                if not hisse_kodu:
                    hisse_kodu = "BİLİNMİYOR"

                # Sayısal Değerleri Yakalama (Lot, Maliyet, Günlük Değer, Grup %)
                # Sayı formatı: 36.540.242,00 veya 73,919844 veya 4,88
                numbers = re.findall(r'[-+]?\d{1,3}(?:\.\d{3})*(?:,\d+)?|[-+]?\d+,\d+', line)
                
                # Türk formatı sayıları float yapısına çeviren yardımcı lambda
                def clean_num(val_str):
                    try:
                        return float(val_str.replace('.', '').replace(',', '.'))
                    except:
                        return 0.0

                cleaned_numbers = [clean_num(n) for n in numbers if n not in ['0', '0,00']]
                
                if len(cleaned_numbers) >= 3:
                    # KAP Tablo Dizilimi:
                    # [0]: Nominal Değer (Lot)
                    # [1]: Birim Alış Fiyatı (Maliyet)
                    # [2]: Günlük Birim Değer (Hisse Fiyatı)
                    # [-3]: Grup (%)
                    lot = cleaned_numbers[0]
                    maliyet = cleaned_numbers[1]
                    hisse_fiyati = cleaned_numbers[-2] if len(cleaned_numbers) >= 4 else cleaned_numbers[2]
                    grup_agirligi = cleaned_numbers[-3] if len(cleaned_numbers) >= 5 else 0.0

                    extracted_data["hisseler"].append({
                        "hisse": hisse_kodu,
                        "lot": lot,
                        "maliyet": maliyet,
                        "hisse_fiyati": hisse_fiyati,
                        "grup_agirligi": grup_agirligi
                    })

    return extracted_data
