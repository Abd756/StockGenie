# Sentiment analysis routes with Gemini integration
from flask import Blueprint, render_template, request, jsonify
from .utils import fetch_all_news
from .sentiment.analyzer import analyze_sentiment, analyze_individual_articles

sentiment_bp = Blueprint('sentiment', __name__)

@sentiment_bp.route('/', methods=['GET', 'POST'])
def sentiment_home():
    sentiment_result = None
    articles = []
    article_count = 0
    processing_time = None

    if request.method == "POST":
        import time
        start_time = time.time()
        
        # Fetch articles from news sources
        print("📥 Fetching news articles...")
        articles = fetch_all_news()
        article_count = len(articles)
        
        if articles:
            # Combine all article content for comprehensive analysis
            combined_text = " ".join(article.get("content", "") for article in articles)
            
            # Analyze sentiment with Gemini
            print(f"🧠 Analyzing {article_count} articles with Gemini...")
            sentiment_result = analyze_sentiment(combined_text, articles)
            
            # Add metadata
            sentiment_result['metadata'] = {
                'article_count': article_count,
                'sources': ['Brecorder', 'Dawn News'],
                'analysis_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'processing_time': round(time.time() - start_time, 2)
            }
            
            processing_time = sentiment_result['metadata']['processing_time']
            
        else:
            sentiment_result = {
                "overall_sentiment": {
                    "label": "No Data",
                    "confidence": 0,
                    "reasoning": "No relevant financial articles found from news sources"
                },
                "summary": "No recent financial news available for analysis",
                "metadata": {
                    "article_count": 0,
                    "sources": ['Brecorder', 'Dawn News'],
                    "analysis_timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
                }
            }

    return render_template('sentiment.html', 
                         sentiment=sentiment_result, 
                         articles=articles,
                         article_count=article_count,
                         processing_time=processing_time)