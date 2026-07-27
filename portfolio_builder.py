import pandas as pd

def build_portfolio_matrix(all_parsed_data):
    records = []
    
    for item in all_parsed_data:
        fon_kodu = item.get("fon_kodu", "PHE")
        fon_adi = item.get("fon_adi", "Fon")
        donem = item.get("donem", "Dönem") # Örn: "Haziran 2026"
        
        # Dönem bilgisinden sadece Ay ismini alma (ör. "Haziran 2026" -> "Haziran")
        ay_adi = donem.split()[0] if donem else "Bilinmeyen Ay"
        
        for h in item.get("hisseler", []):
            records.append({
                "Hisse Kodu": h["hisse"],
                "Fon Adı": fon_kodu, # Görseldeki Fon Kısa Adı
                "Dönem": f"{ay_adi} Lot",
                "Lot": h["lot"],
                "Ort. Maliyet (TL)": h["maliyet"],
                "Rapor Tarihindeki Hisse Fiyatı": h["hisse_fiyati"],
                "Grup Ağ. (%)": h["grup_agirligi"]
            })
            
    if not records:
        return pd.DataFrame()
        
    df = pd.DataFrame(records)
    
    # Aynı ay içerisinde birden fazla pozisyon varsa (alış/satış) hisse lotlarını topla
    pivot_lot = df.pivot_table(
        index=["Hisse Kodu", "Fon Adı"],
        columns="Dönem",
        values="Lot",
        aggfunc="sum"
    ).fillna(0)
    
    # Son ayın Maliyet, Hisse Fiyatı ve Grup Ağırlığı değerlerini alalım
    latest_metrics = df.groupby(["Hisse Kodu", "Fon Adı"]).agg({
        "Grup Ağ. (%)": "last",
        "Ort. Maliyet (TL)": "mean",
        "Rapor Tarihindeki Hisse Fiyatı": "last"
    }).reset_index()
    
    # Pivot Tablo ile Metrikleri Birleştir
    final_df = pd.merge(pivot_lot.reset_index(), latest_metrics, on=["Hisse Kodu", "Fon Adı"], how="left")
    
    # Sütunları düzenleme ve Toplam satırı hazırlama
    cols = list(final_df.columns)
    
    return final_df
