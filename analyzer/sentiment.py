"""
Sentiment Analysis Engine for Customer Email Analyzer
Uses TextBlob for sentiment scoring and custom rules for emotion detection
"""

from textblob import TextBlob
import re
from typing import Dict, List, Tuple

# Threat detection keywords
CHARGEBACK_KEYWORDS = [
    "chargeback", "dispute", "credit card company", "bank",
    "paypal claim", "reverse the charge", "fraud", "unauthorized",
    "call my bank", "dispute this charge", "get my money back through",
    "credit card dispute", "charge back"
]

LEGAL_KEYWORDS = [
    "lawyer", "attorney", "legal action", "sue", "lawsuit",
    "court", "legal department", "hear from my lawyer",
    "legal team", "take legal", "my attorney"
]

REGULATORY_KEYWORDS = [
    "bbb", "better business bureau", "attorney general",
    "state attorney general", "ftc", "federal trade commission",
    "fda", "report you to", "file a complaint with",
    "consumer protection", "health department", "report this to"
]

REPUTATION_KEYWORDS = [
    "review", "yelp", "google review", "facebook", "twitter", "instagram",
    "tiktok", "social media", "tell everyone", "warn people",
    "post about this", "go viral", "influencer", "followers",
    "bad review", "negative review", "one star"
]

# Emotion indicator words
ANGER_WORDS = [
    "angry", "furious", "outraged", "unacceptable", "ridiculous",
    "terrible", "awful", "horrible", "worst", "disgusting", "pathetic",
    "incompetent", "useless", "garbage", "trash", "scam", "fraud",
    "stealing", "thieves", "liars", "joke"
]

FRUSTRATION_WORDS = [
    "frustrated", "annoying", "annoyed", "irritated", "disappointing",
    "disappointed", "upset", "unhappy", "dissatisfied", "fed up",
    "sick of", "tired of", "had enough", "can't believe", "seriously"
]

SATISFACTION_WORDS = [
    "thank", "thanks", "appreciate", "grateful", "happy", "pleased",
    "excellent", "great", "amazing", "wonderful", "fantastic", "perfect",
    "love", "awesome", "impressed", "satisfied", "helpful", "quick"
]

URGENCY_WORDS = [
    "asap", "immediately", "urgent", "now", "today", "emergency",
    "right away", "critical", "important", "need this", "can't wait"
]


def analyze_message(text: str) -> Dict:
    """
    Analyze sentiment and emotions in a single message.

    Returns:
        {
            "polarity": float (-1 to 1),
            "subjectivity": float (0 to 1),
            "emotions": {
                "anger": float (0 to 1),
                "frustration": float (0 to 1),
                "satisfaction": float (0 to 1),
                "urgency": float (0 to 1)
            },
            "threats": {
                "chargeback": bool,
                "legal": bool,
                "regulatory": bool,
                "reputational": bool
            },
            "threat_keywords_found": list,
            "has_caps_rage": bool,
            "exclamation_count": int
        }
    """
    text_lower = text.lower()
    blob = TextBlob(text)

    # Basic sentiment
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity

    # Emotion detection
    emotions = {
        "anger": calculate_emotion_score(text_lower, ANGER_WORDS),
        "frustration": calculate_emotion_score(text_lower, FRUSTRATION_WORDS),
        "satisfaction": calculate_emotion_score(text_lower, SATISFACTION_WORDS),
        "urgency": calculate_emotion_score(text_lower, URGENCY_WORDS)
    }

    # Threat detection
    threats, threat_keywords = detect_threats(text_lower)

    # Caps rage detection (multiple words in all caps)
    caps_words = re.findall(r'\b[A-Z]{2,}\b', text)
    has_caps_rage = len(caps_words) >= 2

    # Exclamation analysis
    exclamation_count = text.count('!')

    # Adjust polarity based on detected emotions and threats
    if emotions["anger"] > 0.3 or any(threats.values()):
        polarity = min(polarity, -0.3)  # Cap positivity if threats detected

    if has_caps_rage:
        polarity -= 0.2
        emotions["anger"] = min(1.0, emotions["anger"] + 0.2)

    if exclamation_count >= 3:
        emotions["urgency"] = min(1.0, emotions["urgency"] + 0.2)

    return {
        "polarity": round(max(-1, min(1, polarity)), 2),
        "subjectivity": round(subjectivity, 2),
        "emotions": {k: round(v, 2) for k, v in emotions.items()},
        "threats": threats,
        "threat_keywords_found": threat_keywords,
        "has_caps_rage": has_caps_rage,
        "exclamation_count": exclamation_count
    }


def calculate_emotion_score(text: str, keywords: List[str]) -> float:
    """Calculate emotion score based on keyword presence."""
    count = sum(1 for word in keywords if word in text)
    # Normalize: 0 keywords = 0, 3+ keywords = 1.0
    return min(1.0, count / 3)


def detect_threats(text: str) -> Tuple[Dict[str, bool], List[str]]:
    """
    Detect different types of threats in text.

    Returns:
        (threat_flags, keywords_found)
    """
    keywords_found = []

    threats = {
        "chargeback": False,
        "legal": False,
        "regulatory": False,
        "reputational": False
    }

    for keyword in CHARGEBACK_KEYWORDS:
        if keyword in text:
            threats["chargeback"] = True
            keywords_found.append(keyword)

    for keyword in LEGAL_KEYWORDS:
        if keyword in text:
            threats["legal"] = True
            keywords_found.append(keyword)

    for keyword in REGULATORY_KEYWORDS:
        if keyword in text:
            threats["regulatory"] = True
            keywords_found.append(keyword)

    for keyword in REPUTATION_KEYWORDS:
        if keyword in text:
            threats["reputational"] = True
            keywords_found.append(keyword)

    return threats, list(set(keywords_found))


def analyze_thread_trajectory(messages: List[Dict]) -> Dict:
    """
    Analyze how sentiment changes through a thread.

    Args:
        messages: List of message dicts with 'role' and 'body' keys

    Returns:
        {
            "initial_sentiment": float,
            "final_sentiment": float,
            "sentiment_change": float,
            "trajectory": "improving" | "declining" | "stable" | "volatile",
            "customer_sentiments": list of floats,
            "turning_point": message_id or None
        }
    """
    customer_messages = [m for m in messages if m.get("role") == "customer"]

    if not customer_messages:
        return {
            "initial_sentiment": 0,
            "final_sentiment": 0,
            "sentiment_change": 0,
            "trajectory": "stable",
            "customer_sentiments": [],
            "turning_point": None
        }

    sentiments = []
    for msg in customer_messages:
        analysis = analyze_message(msg.get("body", ""))
        sentiments.append({
            "message_id": msg.get("message_id"),
            "polarity": analysis["polarity"]
        })

    initial = sentiments[0]["polarity"]
    final = sentiments[-1]["polarity"]
    change = final - initial

    # Determine trajectory
    if len(sentiments) == 1:
        trajectory = "stable"
    elif change > 0.3:
        trajectory = "improving"
    elif change < -0.3:
        trajectory = "declining"
    else:
        # Check for volatility (big swings)
        if len(sentiments) >= 3:
            swings = [abs(sentiments[i]["polarity"] - sentiments[i-1]["polarity"])
                      for i in range(1, len(sentiments))]
            if max(swings) > 0.5:
                trajectory = "volatile"
            else:
                trajectory = "stable"
        else:
            trajectory = "stable"

    # Find turning point (biggest sentiment change after agent response)
    turning_point = None
    if len(sentiments) >= 2:
        max_change = 0
        for i in range(1, len(sentiments)):
            change_at_point = sentiments[i]["polarity"] - sentiments[i-1]["polarity"]
            if abs(change_at_point) > abs(max_change):
                max_change = change_at_point
                turning_point = sentiments[i]["message_id"]

    return {
        "initial_sentiment": round(initial, 2),
        "final_sentiment": round(final, 2),
        "sentiment_change": round(change, 2),
        "trajectory": trajectory,
        "customer_sentiments": [s["polarity"] for s in sentiments],
        "turning_point": turning_point
    }


def calculate_risk_level(thread_analysis: Dict, message_analyses: List[Dict]) -> str:
    """
    Calculate overall risk level for a thread.

    Returns: "low", "medium", "high", or "critical"
    """
    risk_score = 0

    # Check trajectory
    if thread_analysis["trajectory"] == "declining":
        risk_score += 2
    elif thread_analysis["trajectory"] == "volatile":
        risk_score += 1

    # Check final sentiment
    if thread_analysis["final_sentiment"] < -0.5:
        risk_score += 2
    elif thread_analysis["final_sentiment"] < -0.2:
        risk_score += 1

    # Check for threats in any message
    for analysis in message_analyses:
        threats = analysis.get("threats", {})
        if threats.get("chargeback"):
            risk_score += 3
        if threats.get("legal"):
            risk_score += 3
        if threats.get("regulatory"):
            risk_score += 3
        if threats.get("reputational"):
            risk_score += 2

    # Check for caps rage
    caps_rage_count = sum(1 for a in message_analyses if a.get("has_caps_rage"))
    risk_score += caps_rage_count

    # Determine level
    if risk_score >= 6:
        return "critical"
    elif risk_score >= 4:
        return "high"
    elif risk_score >= 2:
        return "medium"
    else:
        return "low"


def get_dominant_emotion(emotions: Dict[str, float]) -> str:
    """Get the dominant emotion from emotion scores."""
    if not emotions:
        return "neutral"

    max_emotion = max(emotions.items(), key=lambda x: x[1])
    if max_emotion[1] < 0.2:
        return "neutral"
    return max_emotion[0]


if __name__ == "__main__":
    # Test the sentiment analyzer
    test_messages = [
        "Hi, I just received my order but one item is missing. Can you help?",
        "Are you SERIOUS?? I've been waiting 3 days for a response! This is UNACCEPTABLE!",
        "I'm going to dispute this charge with my bank and report you to the BBB!",
        "Thank you so much for the quick response! Really appreciate your help.",
        "Fine. I understand the policy. Thanks for explaining."
    ]

    print("Sentiment Analysis Tests:")
    print("=" * 60)

    for msg in test_messages:
        result = analyze_message(msg)
        print(f"\nMessage: {msg[:50]}...")
        print(f"  Polarity: {result['polarity']}")
        print(f"  Emotions: {result['emotions']}")
        print(f"  Threats: {[k for k, v in result['threats'].items() if v]}")
        print(f"  Caps rage: {result['has_caps_rage']}")
