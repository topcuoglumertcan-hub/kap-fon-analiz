import pdfplumber
import re

def parse_pdf(pdf_file):
    extracted_data = {
        "fon_kodu": "",
        "fon_adi": "",
        "portfoy_sirketi": "",
        "donem": "",
        "hisseler": []
    }
    
    raw_hisseler = []
    
    with pdfplumber.open(pdf_file) as pdf:
        full_text = ""
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                full_text += t + "\n"

        # Kurucunun Ünvanı / Portföy Şirketi
        kurucu_match = re.search(r"Kurucunun\s*Ünvanı\s*:\s*(.+)", full_text, re.IGNORECASE)
        if kurucu_match:
            sirket_raw = kurucu_match.group(1).strip()
            sirket_clean = re.sub(r"\s*(YÖNETİMİ|A\.Ş\.|ANONİM\s*ŞİRKETİ).*", "", sirket_raw, flags=re.IGNORECASE).strip()
            extracted_data["portfoy_sirketi"] = sirket_clean if sirket_clean else sirket_raw
        else:
            extracted_data["portfoy_sirketi"] = "PORTFÖY"

        # Fon Kodu & Dönem
        code_match = re.search(r"\b([A-Z0-9]{3,5})\b\s*-\s*", full_text)
        if code_match:
            extracted_data["fon_kodu"] = code_match.group(1)
            
        period_match = re.search(r"(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s*[-:]?\s*(20\d{2})", full_text, re.IGNORECASE)
        if period_match:
            extracted_data["donem"] = f"{period_match.group(1).capitalize()} {period_match.group(2)}"

        lines = full_text.split("\n")
        in_hisse_section = False
        
        for i, line in enumerate(lines):
            line_str = line.strip()
            
            if "HİSSE SENETLERİ" in line_str.upper() or "Hisse Türk" in line_str:
                in_hisse_section = True
                continue
            if "GRUP TOPLAMI" in line_str.upper() or "TÜREV" in line_str.upper():
                in_hisse_section = False
                
            isin_match = re.search(r"(TR[A-Z0-9]{10})", line_str)
            
            if isin_match or (in_hisse_section and re.search(r"[-+]?\d{1,3}(?:\.\d{3})+,\d{2}", line_str)):
                hisse_kodu = ""
                search_scope = [line_str]
                if i > 0: search_scope.append(lines[i-1].strip())
                if i > 1: search_scope.append(lines[i-2].strip())
                
                for scope in search_scope:
                    tokens = scope.split()
                    for t in tokens:
                        clean_t = re.sub(r'[^A-Z0-9]', '', t)
                        if clean_t.isupper() and 3 <= len(clean_t) <= 5 and clean_t not in ["TL", "TAS", "AS", "INC", "TRY", "TRA", "TRE"]:
                            hisse_kodu = clean_t
                            break
                    if hisse_kodu:
                        break
                
                if not hisse_kodu:
                    continue

                numbers = re.findall(r'[-+]?\s*\d{1,3}(?:\.\d{3})*,\d+', line_str)
                
                def parse_tr_float(val_str):
                    try:
                        clean_str = val_str.replace(' ', '').replace('.', '').replace(',', '.')
                        return float(clean_str)
                    except:
                        return 0.0

                parsed_numbers = [parse_tr_float(n) for n in numbers]
                
                if len(parsed_numbers) >= 2:
                    lot = parsed_numbers[0]
                    maliyet = parsed_numbers[1]
                    hisse_fiyati = parsed_numbers[2] if len(parsed_numbers) > 2 else maliyet
                    grup_agirligi = parsed_numbers[-3] if len(parsed_numbers) >= 5 else (parsed_numbers[-1] if len(parsed_numbers) >= 3 else 0.0)

                    raw_hisseler.append({
                        "hisse": hisse_kodu,
                        "lot": lot,
                        "maliyet": maliyet,
                        "hisse_fiyati": hisse_fiyati,
                        "grup_agirligi": grup_agirligi
                    })

    # PDF İÇİNDEKİ MÜKERRER HİSSELERİ (KTLEV +, KTLEV -) NETLEŞTİRME
    hisse_dict = {}
    for item in raw_hisseler:
        hk = item["hisse"]
        if hk not in hisse_dict:
            hisse_dict[hk] = {
                "hisse": hk,
                "lot": 0.0,
                "grup_agirligi": 0.0,
                "maliyet": item["maliyet"],       # Ana pozisyon maliyeti
                "hisse_fiyati": item["hisse_fiyati"] # Ana pozisyon fiyatı
            }
        
        # Lot ve Grup Ağırlıklarını Netleştir (Topla)
        hisse_dict[hk]["lot"] += item["lot"]
        hisse_dict[hk]["grup_agirligi"] += item["grup_agirligi"]
        
        # Eğer büyük/pozitif lotlu satır gelirse Maliyet ve Fiyatı o ana satırdan al
        if item["lot"] > 0:
            hisse_dict[hk]["maliyet"] = item["maliyet"]
            hisse_dict[hk]["hisse_fiyati"] = item["hisse_fiyati"]

    extracted_data["hisseler"] = list(hisse_dict.values())
    return extracted_data
