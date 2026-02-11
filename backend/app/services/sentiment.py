"""
Vantage Backend - Sentiment Analysis Service
Uses VADER for lightweight sentiment scoring on news headlines.
FinBERT can be integrated in Phase 3 for higher accuracy.
"""
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from app.services.market_data import get_news_headlines


_analyzer = SentimentIntensityAnalyzer()


def analyze_sentiment(ticker: str) -> dict:
    """
    Fetch news headlines for a ticker and score them for sentiment.

    Scoring:
        score < -0.5  →  Crash Warning / Panic
        score < -0.1  →  Bearish
        -0.1 ≤ score ≤ 0.1  →  Neutral
        score > 0.1   →  Bullish
        score > 0.5   →  Surge Alert / Hype

    Returns:
        dict with score, label, headline_count, and top_headlines.
    """
    headlines = get_news_headlines(ticker)

    if not headlines:
        return {
            "score": 0.0,
            "label": "Neutral",
            "headline_count": 0,
            "top_headlines": [],
        }

    # Score each headline and average
    scores = []
    for headline in headlines:
        sentiment = _analyzer.polarity_scores(headline)
        scores.append(sentiment["compound"])  # compound is -1 to +1

    avg_score = sum(scores) / len(scores)

    # Map score to label
    if avg_score < -0.5:
        label = "Panic"
    elif avg_score < -0.1:
        label = "Bearish"
    elif avg_score > 0.5:
        label = "Hype"
    elif avg_score > 0.1:
        label = "Bullish"
    else:
        label = "Neutral"

    return {
        "score": round(avg_score, 4),
        "label": label,
        "headline_count": len(headlines),
        "top_headlines": headlines[:5],
    }
