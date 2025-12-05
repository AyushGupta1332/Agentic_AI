import logging
import re
from typing import Dict, Any
from app.agents.base import BaseSpecializedAgent
from app.tools.finance import FinancialTool

class AnalysisAgent(BaseSpecializedAgent):
    """Agent specialized in data analysis and insights."""
    def __init__(self):
        super().__init__("AnalysisAgent", "data_analysis")
        self.financial_tool = FinancialTool()

    async def can_handle(self, query: str) -> bool:
        analysis_keywords = ['analyze', 'compare', 'statistics', 'data', 'trends', 'insights', 'stock', 'price', 'financial', 'market']
        return any(keyword in query.lower() for keyword in analysis_keywords)

    async def process(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        logging.info(f"📊 AnalysisAgent processing: {query}")
        
        results = {}
        
        # Check if it's financial analysis
        ticker = None
        if any(keyword in query.lower() for keyword in ['stock', 'price', 'financial', 'market', 'dividend', 'earnings']):
            # Use LLM to extract ticker
            try:
                extraction_prompt = f"""
                Extract the stock ticker symbol from this query: "{query}"
                Return ONLY the ticker symbol (e.g., AAPL, TSLA). 
                If no specific company/ticker is mentioned, return "NONE".
                """
                completion = await self.groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": extraction_prompt}],
                    temperature=0.0,
                    max_tokens=10
                )
                extracted = completion.choices[0].message.content.strip().upper()
                # Clean up response
                import re
                match = re.search(r'\b[A-Z]{1,5}\b', extracted)
                if match and "NONE" not in extracted:
                    ticker = match.group()
            except Exception as e:
                logging.error(f"Ticker extraction failed: {e}")

        if ticker:
            logging.info(f"Executing enhanced financial data fetch for ticker: {ticker}")
            financial_data = await self.financial_tool.execute(ticker)
            results["financial_analysis"] = financial_data
        
        # Generate analytical insights
        analysis_prompt = f"""
        Analyze the following query for key analytical insights:
        Query: {query}
        
        Provide structured analysis focusing on:
        1. Key metrics to consider
        2. Comparative analysis approach
        3. Trend indicators
        
        Keep response concise and analytical.
        """
        
        try:
            analysis_response = await self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.3,
                max_tokens=300
            )
            results["analytical_insights"] = analysis_response.choices[0].message.content
        except Exception as e:
            logging.error(f"Analysis generation error: {e}")
            results["analytical_insights"] = "Analysis temporarily unavailable."

        return {
            "agent": self.name,
            "analysis_results": results,
            "analysis_type": "financial" if ticker else "general"
        }
