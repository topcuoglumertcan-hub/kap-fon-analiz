import pandas as pd

def build_portfolio_matrix(all_parsed_data):
    records = []
    
    for item in all_parsed_data:
        fon_kodu = item.get("fon_kodu", "FON")
        donem = item.get("donem", "Bilinmeyen Dönem")
        
        # Dönemden Ay ismini çek (ör: "Haziran 2026" -> "Haziran")
        ay_adi = donem.split()[0] if donem else "Birim"
        col_name = f"{ay_adi} Lot"
        
        for h in item.get("hisseler", []):
            records.append({
                "Hisse Kodu": h["hisse"],
                "Fon Adı": fon_kodu,
                "Dönem": col_name,
                "Lot": h["lot"],
                "Ort. Maliyet (TL)": h["maliyet"],
                "Rapor Tarihindeki Hisse Fiyatı": h["hisse_fiyati"],
                "Grup Ağ. (%)": h["grup_agirligi"]
            })
            
    if not records:
        return pd.DataFrame()
        
    df = pd.DataFrame(records)
    
    # Lotları Ay Bazlı Pivot Yap
    pivot_lot = df.pivot_table(
        index=["Hisse Kodu", "Fon Adı"],
        columns="Dönem",
        values="Lot",
        aggfunc="sum"
    ).fillna(0)
    
    # Son güncel Maliyet ve Hisse Fiyatlarını Al
    latest_metrics = df.groupby(["Hisse Kodu", "Fon Adı"]).agg({
        "Grup Ağ. (%)": "last",
        "Ort. Maliyet (TL)": "mean",
        "Rapor Tarihindeki Hisse Fiyatı": "last"
    }).reset_index()
    
    # Tabloları Birleştir
    final_df = pd.merge(pivot_lot.reset_index(), latest_metrics, on=["Hisse Kodu", "Fon Adı"], how="left")
    
    # Toplam Satırı (Görsel 5 formatına uygun)
    hisse_totals = final_df.groupby("Hisse Kodu").size()
    
    return final_df
