import logging
from typing import Dict, Any
import yfinance as yf
from app.tools.base import BaseTool

class FinancialTool(BaseTool):
    """Enhanced financial tool with better error handling."""
    def __init__(self):
        super().__init__(
            name="get_stock_info",
            description="Fetches comprehensive financial information for stock tickers with enhanced data validation."
        )

    async def execute(self, ticker: str) -> Dict[str, Any]:
        logging.info(f"Executing enhanced financial data fetch for ticker: {ticker}")
        try:
            # Clean and validate ticker
            ticker = ticker.upper().strip()
            
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Check if we got valid data
            if not info or 'symbol' not in info:
                return {"error": f"No valid data found for ticker '{ticker}'. Please check the symbol."}
            
            # Get additional data
            hist = stock.history(period="5d")
            
            result = {
                "symbol": info.get("symbol"),
                "longName": info.get("longName"),
                "currentPrice": info.get("currentPrice"),
                "previousClose": info.get("previousClose"),
                "open": info.get("open"),
                "dayHigh": info.get("dayHigh"),
                "dayLow": info.get("dayLow"),
                "volume": info.get("volume"),
                "marketCap": info.get("marketCap"),
                "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
                "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
                "forwardPE": info.get("forwardPE"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "currency": info.get("currency", "USD")
            }
            
            # Add price change calculation
            if result["currentPrice"] and result["previousClose"]:
                price_change = result["currentPrice"] - result["previousClose"]
                price_change_percent = (price_change / result["previousClose"]) * 100
                result["priceChange"] = round(price_change, 2)
                result["priceChangePercent"] = round(price_change_percent, 2)
            
            return result
            
        except Exception as e:
            logging.error(f"Error fetching financial data for {ticker}: {e}")
            return {"error": f"Could not fetch data for ticker '{ticker}'. Error: {str(e)}"}
