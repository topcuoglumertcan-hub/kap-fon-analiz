import pandas as pd

MONTH_ORDER = [
    "Ocak Lot", "Şubat Lot", "Mart Lot", "Nisan Lot", 
    "Mayıs Lot", "Haziran Lot", "Temmuz Lot", "Ağustos Lot", 
    "Eylül Lot", "Ekim Lot", "Kasım Lot", "Aralık Lot"
]

MONTH_MAP = {
    "Ocak": 1, "Şubat": 2, "Mart": 3, "Nisan": 4, 
    "Mayıs": 5, "Haziran": 6, "Temmuz": 7, "Ağustos": 8, 
    "Eylül": 9, "Ekim": 10, "Kasım": 11, "Aralık": 12
}

def build_portfolio_matrix(all_parsed_data):
    records = []
    
    for item in all_parsed_data:
        fon_kodu = item.get("fon_kodu", "FON")
        portfoy_sirketi = item.get("portfoy_sirketi", "PORTFÖY")
        donem = item.get("donem", "")
        
        ay_adi = donem.split()[0] if donem else "Ocak"
        ay_numarasi = MONTH_MAP.get(ay_adi, 1)
        col_name = f"{ay_adi} Lot"
        
        for h in item.get("hisseler", []):
            records.append({
                "Hisse Kodu": h["hisse"],
                "Fon Kodu": fon_kodu,
                "Portföy Şirketi": portfoy_sirketi,
                "Dönem": col_name,
                "Ay No": ay_numarasi,
                "Lot": h["lot"],
                "Ort. Maliyet (TL)": h["maliyet"],
                "Rapor Tarihindeki Hisse Fiyatı": h["hisse_fiyati"],
                "Grup Ağ. (%)": h["grup_agirligi"]
            })
            
    if not records:
        return pd.DataFrame()
        
    df = pd.DataFrame(records)
    
    # 1. Lot Pivot
    pivot_lot = df.pivot_table(
        index=["Hisse Kodu", "Fon Kodu", "Portföy Şirketi"],
        columns="Dönem",
        values="Lot",
        aggfunc="sum"
    ).fillna(0)
    
    existing_months = [m for m in MONTH_ORDER if m in pivot_lot.columns]
    pivot_lot = pivot_lot[existing_months]
    
    # 2. En Son Ayın Metriklerini Toplayarak Al
    df_sorted = df.sort_values(by="Ay No")
    
    # En son ay hangisiyse sadece o ayın verilerini çek
    max_ay = df_sorted["Ay No"].max()
    latest_month_df = df_sorted[df_sorted["Ay No"] == max_ay]
    
    latest_metrics = latest_month_df.groupby(["Hisse Kodu", "Fon Kodu", "Portföy Şirketi"]).agg({
        "Grup Ağ. (%)": "sum",                   # Net Grup Ağırlığı (11.35 + -0.08 = 11.27)
        "Ort. Maliyet (TL)": "last",
        "Rapor Tarihindeki Hisse Fiyatı": "last"
    }).reset_index()
    
    # Birleştir
    merged_df = pd.merge(pivot_lot.reset_index(), latest_metrics, on=["Hisse Kodu", "Fon Kodu", "Portföy Şirketi"], how="left")
    
    # 3. Formatlama
    for m in existing_months:
        merged_df[m] = merged_df[m].apply(lambda x: f"{x:,.0f}".replace(",", ".") if x > 0 else "-")
        
    merged_df["Grup Ağ. (%)"] = merged_df["Grup Ağ. (%)"].apply(lambda x: f"%{x:.2f}" if pd.notnull(x) and x != 0 else "-")
    merged_df["Ort. Maliyet (TL)"] = merged_df["Ort. Maliyet (TL)"].apply(lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notnull(x) and x > 0 else "-")
    merged_df["Rapor Tarihindeki Hisse Fiyatı"] = merged_df["Rapor Tarihindeki Hisse Fiyatı"].apply(lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notnull(x) and x > 0 else "-")
    
    final_cols = ["Hisse Kodu", "Fon Kodu", "Portföy Şirketi"] + existing_months + ["Grup Ağ. (%)", "Ort. Maliyet (TL)", "Rapor Tarihindeki Hisse Fiyatı"]
    return merged_df[final_cols]
