from datetime import date


def get_recommendation():
    return {
        "recommendation": "HOLD",
        "bias": "Slightly bullish",
        "confidence": 74,
        "confidence_label": "High",
        "risk": 6,
        "risk_label": "Moderate",
        "probability": 68,
        "position": {
            "shares": 4020,
            "average_price": 12.85,
            "current_value": 20980.20,
            "profit_loss": -30687.00,
            "profit_loss_pct": -59.38,
        },
        "next_review": str(date.today()),
    }