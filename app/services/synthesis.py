import logging
import json
import re
from typing import Dict, Any, List

class InformationProcessingService:
    """Service to synthesize information from tool outputs into a coherent response."""
    
    def __init__(self, groq_client):
        self.groq_client = groq_client

    async def synthesize_response(self, query: str, tool_outputs: Dict[str, Any], conversation_history: List[Dict[str, str]], is_casual: bool = False) -> Dict[str, Any]:
        logging.info("Synthesizing final response...")
        
        if is_casual or not tool_outputs:
            # Handle casual conversation (same as before)
            casual_prompt = """
            You are a friendly and helpful AI assistant. 
            
            If the user's message is casual (greetings, small talk):
            - Respond naturally and conversationally, keeping it brief, warm, and friendly.
            
            If the user is asking about the conversation history (e.g., "what did I ask before?", "summarize our chat"):
            - Use the provided conversation history to answer accurately.
            - Be specific about what was discussed.
            
            Examples:
            - "Hi there" → "Hello! How can I help you today?"
            - "What was my first question?" → "Your first question was about..."
            
            Keep responses friendly and helpful.
            """
            
            # Use more history for context-aware responses
            messages = [
                {"role": "system", "content": casual_prompt},
                *conversation_history[-20:],  # Use last 20 turns for better context
                {"role": "user", "content": query}
            ]
            
            try:
                chat_completion = await self.groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=150
                )
                
                content = chat_completion.choices[0].message.content
                
                return {
                    "content": content,
                    "confidence_score": 95,
                    "sources": []
                }
                
            except Exception as e:
                logging.error(f"Error in casual response generation: {e}")
                return {
                    "content": "Hello! How can I assist you today?",
                    "confidence_score": 90,
                    "sources": []
                }
        
        # Check if we have any errors in tool outputs
        has_errors = any(
            isinstance(output, dict) and "error" in output 
            or (isinstance(output, list) and len(output) > 0 and isinstance(output[0], dict) and "error" in output[0])
            for output in tool_outputs.values()
        )
        
        if has_errors:
            # Enhanced error handling
            system_prompt = """
            The search tools couldn't find good results for this query. Provide a helpful response that:
            1. Acknowledges the limitation
            2. Suggests alternative approaches
            3. Offers to help with related questions
            4. Provides any general knowledge you might have (but clearly indicate it's general knowledge)
            
            Be honest about limitations while still being helpful.
            """
        else:
            # Enhanced success response
            system_prompt = """
            You are an AI assistant that synthesizes information from various sources to provide a comprehensive, well-structured, and coherent answer to the user's query.
            
            IMPORTANT FORMATTING RULES:
            - DO NOT include any URLs or links in your response text
            - Focus only on providing the factual information clearly
            - Use clean, readable formatting with proper paragraphs
            - DO NOT mention sources by URL in your response
            - Keep the response well-structured and easy to read
            - Use markdown formatting for better readability (bold, headers, lists when appropriate)
            - If you mention specific information, do NOT include the source URLs inline
            - If multiple tools provided similar information, synthesize it coherently
            - If there are conflicting results, mention the discrepancy
            
            Your job is to provide clean, informative content. The sources will be handled separately.
            """

        # Clean the tool outputs
        cleaned_outputs = self._clean_tool_outputs_for_prompt(tool_outputs)

        prompt = f"""
        User Query: {query}
        Information from Tools: {json.dumps(cleaned_outputs, indent=2)}
        
        Based on the above information, provide a clear and comprehensive answer. 
        Do not include any URLs or source references in your response.
        """

        messages = [
            {"role": "system", "content": system_prompt},
            *conversation_history,
            {"role": "user", "content": prompt}
        ]

        try:
            chat_completion = await self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                temperature=0.7,
            )

            content = chat_completion.choices[0].message.content

            # Adjust confidence based on whether we had errors
            base_confidence = 60 if has_errors else 85
            
            # Get confidence score
            confidence_score_prompt = f"Based on the following response and whether the search tools found good results (errors present: {has_errors}), what is your confidence score (0-100) in its accuracy and completeness?\n\nResponse: {content}\n\nConfidence Score:"
            try:
                score_completion = await self.groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": confidence_score_prompt}],
                    temperature=0.0,
                )
                score_text = score_completion.choices[0].message.content
                confidence = int(''.join(filter(str.isdigit, score_text))) if any(char.isdigit() for char in score_text) else base_confidence
            except:
                confidence = base_confidence

            return {
                "content": content,
                "confidence_score": confidence,
                "sources": self._extract_sources(tool_outputs)
            }

        except Exception as e:
            logging.error(f"Error in response synthesis: {e}")
            return {
                "content": "I apologize, but I encountered an error while processing your request. Please try rephrasing your question or ask something else.",
                "confidence_score": 20,
                "sources": []
            }

    def _clean_tool_outputs_for_prompt(self, tool_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Clean tool outputs by removing URLs to prevent them from appearing in the response."""
        cleaned_outputs = {}
        
        for tool_name, output in tool_outputs.items():
            if isinstance(output, list):
                cleaned_list = []
                for item in output:
                    if isinstance(item, dict):
                        cleaned_item = {k: v for k, v in item.items() if k not in ['url', 'query_used', 'search_query']}
                        cleaned_list.append(cleaned_item)
                    else:
                        cleaned_list.append(item)
                cleaned_outputs[tool_name] = cleaned_list
            elif isinstance(output, dict):
                cleaned_outputs[tool_name] = {k: v for k, v in output.items() if k not in ['url', 'query_used', 'search_query']}
            else:
                cleaned_outputs[tool_name] = output
        
        return cleaned_outputs

    def _extract_sources(self, tool_outputs: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract sources with better formatting and numbering."""
        sources = []
        source_counter = 1
        
        for tool_name, output in tool_outputs.items():
            if isinstance(output, list):
                for item in output:
                    if isinstance(item, dict) and 'url' in item and 'error' not in item:
                        title = item.get("title") or item.get("source") or f"Source {source_counter}"
                        # Clean up title - remove excessive whitespace and truncate if too long
                        title = re.sub(r'\s+', ' ', title.strip())
                        if len(title) > 100:
                            title = title[:97] + "..."
                        
                        sources.append({
                            "id": source_counter,
                            "title": title,
                            "url": item.get("url"),
                            "type": self._determine_source_type(tool_name, item.get("url", "")),
                            "platform": item.get("platform", "")
                        })
                        source_counter += 1
            elif isinstance(output, dict) and 'symbol' in output:
                sources.append({
                    "id": source_counter,
                    "title": f"Yahoo Finance - {output['symbol']}",
                    "url": f"https://finance.yahoo.com/quote/{output['symbol']}",
                    "type": "financial",
                    "platform": "yahoo_finance"
                })
                source_counter += 1
        
        return sources
    
    def _determine_source_type(self, tool_name: str, url: str) -> str:
        """Determine the type of source based on tool and URL."""
        if "financial" in tool_name or "stock" in tool_name:
            return "financial"
        elif "news" in tool_name:
            return "news"
        elif "social_media" in tool_name:
            return "social"
        elif any(domain in url.lower() for domain in ['instagram.com', 'twitter.com', 'facebook.com', 'tiktok.com']):
            return "social"
        else:
            return "web"
