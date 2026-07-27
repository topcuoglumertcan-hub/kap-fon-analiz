import pandas as pd

MONTH_ORDER = [
    "Ocak Lot", "Şubat Lot", "Mart Lot", "Nisan Lot", 
    "Mayıs Lot", "Haziran Lot", "Temmuz Lot", "Ağustos Lot", 
    "Eylül Lot", "Ekim Lot", "Kasım Lot", "Aralık Lot"
]

def build_portfolio_matrix(all_parsed_data):
    records = []
    
    for item in all_parsed_data:
        fon_kodu = item.get("fon_kodu", "FON")
        portfoy_sirketi = item.get("portfoy_sirketi", "PORTFÖY") # TERA PORTFÖY vb.
        donem = item.get("donem", "")
        
        ay_adi = donem.split()[0] if donem else "Ocak"
        col_name = f"{ay_adi} Lot"
        
        for h in item.get("hisseler", []):
            records.append({
                "Hisse Kodu": h["hisse"],
                "Portföy Şirketi": portfoy_sirketi,
                "Fon Kodu": fon_kodu,
                "Dönem": col_name,
                "Lot": h["lot"],
                "Ort. Maliyet (TL)": h["maliyet"],
                "Rapor Tarihindeki Hisse Fiyatı": h["hisse_fiyati"],
                "Grup Ağ. (%)": h["grup_agirligi"]
            })
            
    if not records:
        return pd.DataFrame()
        
    df = pd.DataFrame(records)
    
    # Pivot Tablo
    pivot_lot = df.pivot_table(
        index=["Hisse Kodu", "Portföy Şirketi", "Fon Kodu"],
        columns="Dönem",
        values="Lot",
        aggfunc="sum"
    ).fillna(0)
    
    # Sütun Sıralaması
    existing_months = [m for m in MONTH_ORDER if m in pivot_lot.columns]
    other_cols = [c for c in pivot_lot.columns if c not in MONTH_ORDER]
    ordered_columns = existing_months + other_cols
    pivot_lot = pivot_lot[ordered_columns]
    
    # Metrikler
    latest_metrics = df.groupby(["Hisse Kodu", "Portföy Şirketi", "Fon Kodu"]).agg({
        "Grup Ağ. (%)": "last",
        "Ort. Maliyet (TL)": "mean",
        "Rapor Tarihindeki Hisse Fiyatı": "last"
    }).reset_index()
    
    detail_df = pd.merge(pivot_lot.reset_index(), latest_metrics, on=["Hisse Kodu", "Portföy Şirketi", "Fon Kodu"], how="left")
    
    # Şablon Tablosu Hazırlığı
    flat_rows = []
    for hisse, group in detail_df.groupby("Hisse Kodu"):
        # 1. Toplam Satırı
        total_row = {
            "Hisse Kodu": f"Toplam {hisse}",
            "Fon Adı": "",
            "Portföy Şirketi": ""
        }
        for m in existing_months:
            total_row[m] = group[m].sum()
            
        total_row["Grup Ağ. (%)"] = "-"
        total_row["Ort. Maliyet (TL)"] = "-"
        total_row["Rapor Tarihindeki Hisse Fiyatı"] = "-"
        
        flat_rows.append(total_row)
        
        # 2. Alt Kırılım Satırı (Girintili Portföy Adı)
        for _, row in group.iterrows():
            sub_row = {
                "Hisse Kodu": f"  └ {row['Portföy Şirketi']}", # Gerçek Portföy Şirketi
                "Fon Adı": row["Fon Kodu"],
                "Portföy Şirketi": row["Portföy Şirketi"]
            }
            for m in existing_months:
                val = row[m]
                sub_row[m] = val if val > 0 else "-"
                
            sub_row["Grup Ağ. (%)"] = f"%{row['Grup Ağ. (%)']:.2f}" if pd.notnull(row["Grup Ağ. (%)"]) else "-"
            sub_row["Ort. Maliyet (TL)"] = round(row["Ort. Maliyet (TL)"], 2) if pd.notnull(row["Ort. Maliyet (TL)"]) else "-"
            sub_row["Rapor Tarihindeki Hisse Fiyatı"] = round(row["Rapor Tarihindeki Hisse Fiyatı"], 2) if pd.notnull(row["Rapor Tarihindeki Hisse Fiyatı"]) else "-"
            flat_rows.append(sub_row)
            
    return pd.DataFrame(flat_rows)
