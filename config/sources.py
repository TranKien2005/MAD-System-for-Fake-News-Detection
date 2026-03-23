"""
Source credibility whitelist.
Defines trusted news sources and their credibility tiers.
"""

# Credibility tiers for news sources
# Tier 1 (0.9 - 1.0): Hãng thông tấn quốc tế, tổ chức uy tín
# Tier 2 (0.7 - 0.89): Báo chính thống quốc gia
# Tier 3 (0.5 - 0.69): Wikipedia, trang tin phổ biến
# Tier 4 (0.2 - 0.49): Blog, forum, mạng xã hội

SOURCE_CREDIBILITY = {
    # Tier 1 - Rất cao
    "reuters.com": 0.95,
    "apnews.com": 0.95,
    "bbc.com": 0.92,
    "who.int": 0.95,
    "un.org": 0.93,

    # Tier 2 - Cao
    "vnexpress.net": 0.85,
    "tuoitre.vn": 0.83,
    "thanhnien.vn": 0.82,
    "nhandan.vn": 0.85,
    "cnn.com": 0.80,
    "nytimes.com": 0.85,

    # Tier 3 - Trung bình
    "wikipedia.org": 0.65,
    "medium.com": 0.50,

    # Tier 4 - Thấp
    "facebook.com": 0.25,
    "tiktok.com": 0.20,
    "twitter.com": 0.30,
}

# Default credibility for unknown sources
DEFAULT_CREDIBILITY = 0.3

# Domain list for search filtering (only Tier 1 + 2)
TRUSTED_DOMAINS = [
    domain for domain, score in SOURCE_CREDIBILITY.items()
    if score >= 0.7
]


def get_credibility(domain: str) -> float:
    """Get credibility score for a domain."""
    # Check exact match
    if domain in SOURCE_CREDIBILITY:
        return SOURCE_CREDIBILITY[domain]

    # Check subdomain match (e.g., "news.bbc.com" → "bbc.com")
    for source, score in SOURCE_CREDIBILITY.items():
        if domain.endswith(source):
            return score

    return DEFAULT_CREDIBILITY


def get_credibility_label(score: float) -> str:
    """Get human-readable label for a credibility score."""
    if score >= 0.9:
        return "Rất cao"
    elif score >= 0.7:
        return "Cao"
    elif score >= 0.5:
        return "Trung bình"
    elif score >= 0.3:
        return "Thấp"
    else:
        return "Rất thấp"
