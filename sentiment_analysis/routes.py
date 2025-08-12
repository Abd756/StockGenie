# Sentiment analysis routes will be added here
from flask import Blueprint, render_template, request
from .utils import fetch_all_news
from .sentiment.analyzer import analyze_sentiment

sentiment_bp = Blueprint('sentiment', __name__)

@sentiment_bp.route('/', methods=['GET', 'POST'])
def sentiment_home():
    sentiment_result = None
    articles = []

    if request.method == "POST":
        articles = fetch_all_news()
        combined_text = " ".join(article.get("content", "") for article in articles)
        sentiment_result = analyze_sentiment(combined_text)

    return render_template('sentiment.html', sentiment=sentiment_result, articles=articles)