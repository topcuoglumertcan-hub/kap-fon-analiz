import yfinance as yf

def get_bist_live_prices(hisse_listesi):
    """
    Verilen BIST hisse kodları için (AKBNK, ASELS vb.) 
    Yahoo Finance üzerinden son kapanış fiyatlarını getirir.
    """
    prices = {}
    if not hisse_listesi:
        return prices

    # BIST sembol formatına çevirme (ör: AKBNK -> AKBNK.IS)
    tickers = [f"{symbol}.IS" for symbol in set(hisse_listesi) if symbol and len(symbol) <= 5]
    
    try:
        # Tüm hisseleri tek seferde çekiyoruz (Hızlı olması için)
        data = yf.download(tickers, period="1d", progress=False)["Close"]
        
        for symbol in set(hisse_listesi):
            ticker_symbol = f"{symbol}.IS"
            if ticker_symbol in data:
                # Son günün kapanış fiyatı
                val = data[ticker_symbol].iloc[-1]
                if not isinstance(val, float):
                    val = float(val)
                prices[symbol] = val if not pd.isna(val) else None
            else:
                prices[symbol] = None
    except Exception as e:
        print(f"Fiyat çekme hatası: {e}")
        
    return prices
