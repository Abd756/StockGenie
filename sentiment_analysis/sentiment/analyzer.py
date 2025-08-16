import os
import json
import time

def analyze_sentiment(combined_text: str, articles: list = None) -> dict:
    """
    Analyze sentiment using Gemini 1.5 Pro for comprehensive financial sentiment analysis
    """
    try:
        # Import Gemini dependencies
        import google.generativeai as genai
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        
        # Configure Gemini API
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        print("🤖 Analyzing financial news content with Gemini 1.5 Pro...")
        
        # Create a completely AI-driven prompt - NO hardcoded sentiment extraction
        prompt = f"""
        You are a professional financial analyst reviewing Pakistani stock market news. 
        
        Analyze this content and respond in EXACTLY this JSON format:
        
        {{
            "sentiment_label": "one of: Positive, Negative, Neutral, or Mixed",
            "confidence_score": "number from 0-100",
            "reasoning": "your professional reasoning for this sentiment",
            "key_factors": ["list of 2-3 key factors that influenced your decision"],
            "market_outlook": "brief outlook for Pakistani markets",
            "companies_mentioned": ["any specific companies or sectors mentioned"],
            "economic_impact": "potential economic implications"
        }}
        
        NEWS CONTENT:
        {combined_text}
        
        Base your analysis purely on the content provided. Be natural and professional.
        """
        
        # Generate response with Gemini
        response = model.generate_content(prompt)
        
        # Parse Gemini's structured JSON response (completely AI-driven)
        try:
            import json
            import re
            
            # Extract JSON from response (sometimes Gemini wraps it in markdown)
            json_text = response.text
            if "```json" in json_text:
                json_text = re.search(r'```json\s*(.*?)\s*```', json_text, re.DOTALL).group(1)
            elif "```" in json_text:
                json_text = re.search(r'```\s*(.*?)\s*```', json_text, re.DOTALL).group(1)
            
            gemini_analysis = json.loads(json_text)
            
            # Use Gemini's natural decisions
            sentiment_label = gemini_analysis.get("sentiment_label", "Neutral")
            confidence = int(gemini_analysis.get("confidence_score", 70))
            
            # Return completely AI-driven results
            return {
                "overall_sentiment": {
                    "label": sentiment_label,
                    "confidence": confidence,
                    "reasoning": gemini_analysis.get("reasoning", "AI analysis completed")
                },
                "key_findings": gemini_analysis.get("key_factors", [
                    "Advanced AI analysis using Gemini 1.5 Pro",
                    f"Processed {len(articles) if articles else 'multiple'} financial news articles"
                ]),
                "market_factors": {
                    "companies_mentioned": gemini_analysis.get("companies_mentioned", []),
                    "economic_impact": gemini_analysis.get("economic_impact", "Impact assessment completed"),
                    "market_outlook": gemini_analysis.get("market_outlook", "Analysis completed")
                },
                "summary": gemini_analysis.get("market_outlook", response.text),
                "full_response": response.text,
                "analysis_method": "gemini_1.5_pro_structured",
                "content_analyzed": len(combined_text),
                "ai_driven": True
            }
            
        except (json.JSONDecodeError, AttributeError) as e:
            # Fallback: if JSON parsing fails, use the raw response
            print(f"⚠️ JSON parsing failed, using raw response: {e}")
            return {
                "overall_sentiment": {
                    "label": "Analysis Complete",
                    "confidence": 75,
                    "reasoning": "Gemini provided natural language analysis (JSON parsing failed)"
                },
                "key_findings": [
                    "Natural language analysis by Gemini 1.5 Pro",
                    f"Processed {len(combined_text)} characters of financial news"
                ],
                "market_factors": {
                    "analysis_note": "Natural AI analysis - see full response below"
                },
                "summary": response.text,
                "full_response": response.text,
                "analysis_method": "gemini_1.5_pro_natural",
                "content_analyzed": len(combined_text),
                "ai_driven": True
            }
        
    except ImportError:
        print("⚠️ Gemini dependencies not available")
        return {
            "overall_sentiment": {
                "label": "Service Unavailable",
                "confidence": 0,
                "reasoning": "Gemini API requires: pip install google-generativeai python-dotenv"
            },
            "summary": "Cannot access Gemini API. Please install required packages and ensure API key is configured.",
            "analysis_method": "dependency_error"
        }
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        return {
            "overall_sentiment": {
                "label": "Error",
                "confidence": 0,
                "reasoning": f"Analysis failed: {str(e)}"
            },
            "summary": "Could not complete sentiment analysis due to API error",
            "error": str(e),
            "analysis_method": "api_error"
        }

def analyze_individual_articles(articles: list) -> list:
    """
    Individual article analysis (future enhancement)
    For now, returns empty list as we focus on combined analysis
    """
    return []

        