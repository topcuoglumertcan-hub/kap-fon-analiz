import pandas as pd

def build_portfolio_matrix(all_parsed_data):
    """
    Birden fazla PDF'ten gelen verileri birleştirerek
    Son görseldeki gibi Hisse Kodu -> Fon -> Aylık Lot Matrisi üretir.
    """
    records = []
    
    for item in all_parsed_data:
        fon_kodu = item.get("fon_kodu", "BİLİNMİYOR")
        fon_adi = item.get("fon_adi", "Bilinmeyen Fon")
        donem = item.get("donem", "Diğer") # Örn: "Ocak 2026", "Haziran"
        
        for h in item.get("hisseler", []):
            records.append({
                "Hisse Kodu": h["hisse"],
                "Fon Kodu": fon_kodu,
                "Fon Adı": fon_adi,
                "Dönem": donem,
                "Lot": h["lot"],
                "Maliyet": h["maliyet"],
                "Ağırlık": h["agirlik"]
            })
            
    if not records:
        return pd.DataFrame()
        
    df = pd.DataFrame(records)
    
    # Dönem bazında pivot tablo (Ocak Lot, Şubat Lot, Mart Lot...)
    pivot_lot = df.pivot_table(
        index=["Hisse Kodu", "Fon Adı", "Fon Kodu"],
        columns="Dönem",
        values="Lot",
        aggfunc="sum"
    ).fillna(0)
    
    # Sütun isimlerini 'X Lot' formatına getir
    pivot_lot.columns = [f"{col} Lot" for col in pivot_lot.columns]
    pivot_lot = pivot_lot.reset_index()
    
    # Son ay / Güncel veriler için Maliyet ve Ağırlık ekleme
    latest_metrics = df.groupby(["Hisse Kodu", "Fon Adı"]).agg({
        "Ağırlık": "last",
        "Maliyet": "mean"
    }).reset_index()
    
    # Tabloları Birleştir
    final_df = pd.merge(pivot_lot, latest_metrics, on=["Hisse Kodu", "Fon Adı"], how="left")
    
    # Sütun isimlerini düzenleme (Görsel 5 ile birebir aynı)
    final_df = final_df.rename(columns={
        "Ağırlık": "Haziran Grup Ağ. (%)",
        "Maliyet": "Ort. Maliyet (TL)"
    })
    
    return final_df
