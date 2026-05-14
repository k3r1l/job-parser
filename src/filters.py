KEYWORDS = [
    "data scientist",
    "data science",
    "machine learning",
    "ml engineer",
    "analytics engineer",
    "data analyst",
    # "senior data " with trailing space prevents matching "senior datawarehouse" etc.
    "senior data ",
    "lead data ",
    "principal data",
]

LOCATION_KEYWORDS = [
    "london",
    "uk",
    "united kingdom",
    "remote",
    "hybrid",
]

# If any of these appear in the text, the role is explicitly in the UK → always keep.
_UK_MARKERS = {
    "london", "united kingdom", "england", "wales", "scotland",
    "cardiff", "manchester", "edinburgh", "birmingham", "leeds", "bristol",
    "remote (uk)", "remote - uk", "hybrid (uk)", "(uk)", "uk only",
}

# Non-UK location signals. Only used to reject if NO UK marker is also present.
_NON_UK_MARKERS = {
    # USA cities
    "san francisco", "new york", "los angeles", "seattle", "sunnyvale",
    "palo alto", "mountain view", "santa clara", "cupertino", "san jose",
    "chicago", "boston", "austin", "atlanta", "denver", "miami",
    "washington, d", "washington dc",
    # USA country / state signals
    "united states", ", usa", " usa", "california", ", ca ",
    # European cities / countries (not UK)
    "paris", "berlin", "amsterdam", "lisbon", "barcelona", "madrid",
    "milan", "zurich", "frankfurt", "munich", "stockholm", "copenhagen",
    "oslo", "warsaw", "prague", "brussels",
    "portugal", "spain", "france", "germany", "netherlands",
    "sweden", "norway", "denmark", "finland", "poland",
    "austria", "switzerland", "belgium",
    # Eastern Europe
    "riga", "latvia", "tallinn", "estonia", "vilnius", "lithuania",
    "sofia", "bulgaria", "bucharest", "romania",
    # Asia / Pacific / Other
    "tokyo", "japan", "singapore", "sydney", "australia",
    "toronto", "vancouver", "canada",
    "dubai", "israel", "herzliya", "tel aviv",
    "bangalore", "india",
    # Ireland (not UK — if the role says "Dublin, Ireland" it's EU)
    ", ireland", "dublin, ",
}


def is_relevant_title(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in KEYWORDS)


def is_uk_relevant(text: str) -> bool:
    """
    Return False only when text names a non-UK location AND no UK location is present.
    Roles listed as 'London or Lisbon' are kept; 'Lisbon only' roles are dropped.
    """
    t = text.lower()
    if any(marker in t for marker in _UK_MARKERS):
        return True   # UK explicitly present — keep regardless of other cities
    if any(marker in t for marker in _NON_UK_MARKERS):
        return False  # non-UK only
    return True       # no location info — keep (scorer applies mild penalty)


def is_relevant_location(text: str) -> bool:
    t = text.lower()
    return not LOCATION_KEYWORDS or any(loc in t for loc in LOCATION_KEYWORDS)
