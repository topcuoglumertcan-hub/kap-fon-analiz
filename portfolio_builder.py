import pandas as pd

# Kronolojik Ay Sıralaması
MONTH_ORDER = [
    "Ocak Lot", "Şubat Lot", "Mart Lot", "Nisan Lot", 
    "Mayıs Lot", "Haziran Lot", "Temmuz Lot", "Ağustos Lot", 
    "Eylül Lot", "Ekim Lot", "Kasım Lot", "Aralık Lot"
]

def build_portfolio_matrix(all_parsed_data):
    records = []
    
    for item in all_parsed_data:
        fon_kodu = item.get("fon_kodu", "BİLİNMİYOR")
        portfoy_sirketi = item.get("portfoy_sirketi", "Genel Portföy") # Örn: Pusula, Tera, İş Yatırım
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
        return pd.DataFrame(), pd.DataFrame()
        
    df = pd.DataFrame(records)
    
    # 1. Pivot İşlemi
    pivot_lot = df.pivot_table(
        index=["Hisse Kodu", "Portföy Şirketi", "Fon Kodu"],
        columns="Dönem",
        values="Lot",
        aggfunc="sum"
    ).fillna(0)
    
    # 2. Sütunları Kronolojik Sıralama (Ocak'tan Aralık'a)
    existing_months = [m for m in MONTH_ORDER if m in pivot_lot.columns]
    other_cols = [c for c in pivot_lot.columns if c not in MONTH_ORDER]
    ordered_columns = existing_months + other_cols
    pivot_lot = pivot_lot[ordered_columns]
    
    # 3. Güncel Metrikler
    latest_metrics = df.groupby(["Hisse Kodu", "Portföy Şirketi", "Fon Kodu"]).agg({
        "Grup Ağ. (%)": "last",
        "Ort. Maliyet (TL)": "mean",
        "Rapor Tarihindeki Hisse Fiyatı": "last"
    }).reset_index()
    
    # Detay Tablo
    detail_df = pd.merge(pivot_lot.reset_index(), latest_metrics, on=["Hisse Kodu", "Portföy Şirketi", "Fon Kodu"], how="left")
    
    # 4. Excel (Görsel 2) Formatında Toplam Satırlı Ana Tablo Hazırlığı
    flat_rows = []
    for hisse, group in detail_df.groupby("Hisse Kodu"):
        # Toplam Satırı
        total_row = {
            "Hisse Kodu": f"Toplam {hisse}",
            "Fon Adı": "",
            "Portföy Şirketi": ""
        }
        for m in existing_months:
            total_row[m] = group[m].sum()
            
        total_row["Grup Ağ. (%)"] = None
        total_row["Ort. Maliyet (TL)"] = None
        total_row["Rapor Tarihindeki Hisse Fiyatı"] = None
        
        flat_rows.append(total_row)
        
        # Alt Kırılım Satırları (Pusula - PHE, Tera - TLY vb.)
        for _, row in group.iterrows():
            sub_row = {
                "Hisse Kodu": f"  └ {row['Portföy Şirketi']}", # Görsel 2 Akışına Uygun
                "Fon Adı": row["Fon Kodu"],
                "Portföy Şirketi": row["Portföy Şirketi"]
            }
            for m in existing_months:
                # 0 olan lotlara '-' koyarak Görsel 2 biçimine getirme
                val = row[m]
                sub_row[m] = val if val > 0 else "-"
                
            sub_row["Grup Ağ. (%)"] = f"%{row['Grup Ağ. (%)']:.2f}" if pd.notnull(row["Grup Ağ. (%)"]) else "-"
            sub_row["Ort. Maliyet (TL)"] = row["Ort. Maliyet (TL)"]
            sub_row["Rapor Tarihindeki Hisse Fiyatı"] = row["Rapor Tarihindeki Hisse Fiyatı"]
            flat_rows.append(sub_row)
            
    summary_df = pd.DataFrame(flat_rows)
    return summary_df, detail_df
