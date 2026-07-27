import yfinance as yf
import pandas as pd

def get_bist_live_prices(hisse_listesi):
    """
    Verilen BIST hisse kodları (ASELS, HALKB vb.) için
    güncel son kapanış/canlı fiyatları getirir.
    """
    prices = {}
    if not hisse_listesi:
        return prices

    # Temiz ve benzersiz hisse kodları
    clean_symbols = set([str(s).strip().upper() for s in hisse_listesi if s and str(s).strip() != "-"])

    for symbol in clean_symbols:
        ticker_code = f"{symbol}.IS"
        price_found = None
        
        try:
            ticker = yf.Ticker(ticker_code)
            
            # 1. Yöntem: Fast Info (Çok hızlı ve engellere takılmaz)
            if hasattr(ticker, 'fast_info') and 'lastPrice' in ticker.fast_info:
                price_found = ticker.fast_info['lastPrice']
            elif hasattr(ticker, 'fast_info') and 'previousClose' in ticker.fast_info:
                price_found = ticker.fast_info['previousClose']
                
            # 2. Yöntem: History (Yedek)
            if price_found is None or pd.isna(price_found):
                hist = ticker.history(period="5d")
                if not hist.empty and "Close" in hist.columns:
                    price_found = hist["Close"].iloc[-1]

            if price_found is not None and not pd.isna(price_found) and price_found > 0:
                prices[symbol] = float(price_found)
            else:
                prices[symbol] = None

        except Exception as e:
            print(f"{symbol} fiyat çekme hatası: {e}")
            prices[symbol] = None

    return prices
