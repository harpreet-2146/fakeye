# app/retriever/stance.py
"""
Strict stance detection that verifies actual claim relationships
Focuses on avoiding false positives while catching true matches

MERGED VERSION:
- Previous political/role detection (Modi PM of Africa = FALSE)
- Previous death/alive detection
- NEW geographic claim detection (Florida in India = FALSE)
"""

import re
from typing import Set, List, Optional, Tuple

def extract_numbers(text: str) -> Set[str]:
    """Extract all numbers from text"""
    numbers = re.findall(r'\b\d+\.?\d*\b', text)
    return set(numbers)

def normalize_text(text: str) -> str:
    """Normalize synonyms and variations"""
    text = text.lower()
    replacements = {
        'united states': 'usa',
        'united states of america': 'usa', 
        'u.s.a.': 'usa',
        'u.s.': 'usa',
        'america': 'usa',
        'united kingdom': 'uk',
        'u.k.': 'uk',
        'britain': 'uk',
        'great britain': 'uk',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

# ========== GEOGRAPHIC LOCATIONS DATABASE ==========
COUNTRIES = {
    'usa', 'canada', 'mexico', 'brazil', 'argentina', 'chile', 'colombia', 'peru',
    'uk', 'france', 'germany', 'italy', 'spain', 'portugal', 'netherlands', 'belgium',
    'russia', 'china', 'japan', 'india', 'pakistan', 'bangladesh', 'indonesia',
    'australia', 'new zealand', 'south africa', 'nigeria', 'kenya', 'egypt', 'morocco',
    'saudi arabia', 'iran', 'iraq', 'israel', 'palestine', 'turkey', 'greece',
    'poland', 'ukraine', 'sweden', 'norway', 'finland', 'denmark', 'switzerland',
    'thailand', 'vietnam', 'philippines', 'malaysia', 'singapore', 'south korea',
    'north korea', 'taiwan', 'afghanistan', 'syria', 'jordan', 'lebanon', 'uae',
    'qatar', 'kuwait', 'oman', 'yemen', 'ethiopia', 'ghana', 'tanzania', 'uganda',
    'africa'  # Treating as location for "PM of Africa" type queries
}

# US States
US_STATES = {
    'alabama', 'alaska', 'arizona', 'arkansas', 'california', 'colorado', 'connecticut',
    'delaware', 'florida', 'georgia', 'hawaii', 'idaho', 'illinois', 'indiana', 'iowa',
    'kansas', 'kentucky', 'louisiana', 'maine', 'maryland', 'massachusetts', 'michigan',
    'minnesota', 'mississippi', 'missouri', 'montana', 'nebraska', 'nevada', 'new hampshire',
    'new jersey', 'new mexico', 'new york', 'north carolina', 'north dakota', 'ohio',
    'oklahoma', 'oregon', 'pennsylvania', 'rhode island', 'south carolina', 'south dakota',
    'tennessee', 'texas', 'utah', 'vermont', 'virginia', 'washington', 'west virginia',
    'wisconsin', 'wyoming'
}

# Indian States
INDIA_STATES = {
    'andhra pradesh', 'arunachal pradesh', 'assam', 'bihar', 'chhattisgarh', 'goa',
    'gujarat', 'haryana', 'himachal pradesh', 'jharkhand', 'karnataka', 'kerala',
    'madhya pradesh', 'maharashtra', 'manipur', 'meghalaya', 'mizoram', 'nagaland',
    'odisha', 'punjab', 'rajasthan', 'sikkim', 'tamil nadu', 'telangana', 'tripura',
    'uttar pradesh', 'uttarakhand', 'west bengal', 'delhi', 'mumbai', 'bangalore',
    'chennai', 'kolkata', 'hyderabad'
}

# Major cities with their countries
CITY_COUNTRY_MAP = {
    # USA
    'new york': 'usa', 'los angeles': 'usa', 'chicago': 'usa', 'houston': 'usa',
    'miami': 'usa', 'seattle': 'usa', 'boston': 'usa', 'denver': 'usa',
    'san francisco': 'usa', 'las vegas': 'usa', 'washington dc': 'usa',
    # India
    'mumbai': 'india', 'delhi': 'india', 'bangalore': 'india', 'chennai': 'india',
    'kolkata': 'india', 'hyderabad': 'india', 'pune': 'india', 'ahmedabad': 'india',
    # UK
    'london': 'uk', 'manchester': 'uk', 'birmingham': 'uk', 'liverpool': 'uk',
    # Others
    'paris': 'france', 'berlin': 'germany', 'tokyo': 'japan', 'beijing': 'china',
    'shanghai': 'china', 'sydney': 'australia', 'toronto': 'canada', 'dubai': 'uae',
}

# State to country mapping
STATE_COUNTRY_MAP = {}
for state in US_STATES:
    STATE_COUNTRY_MAP[state] = 'usa'
for state in INDIA_STATES:
    STATE_COUNTRY_MAP[state] = 'india'

# Continents
CONTINENTS = {'asia', 'europe', 'africa', 'north america', 'south america', 'australia', 'antarctica', 'oceania'}

# Country to continent mapping
COUNTRY_CONTINENT = {
    'usa': 'north america', 'canada': 'north america', 'mexico': 'north america',
    'brazil': 'south america', 'argentina': 'south america', 'chile': 'south america',
    'uk': 'europe', 'france': 'europe', 'germany': 'europe', 'italy': 'europe',
    'spain': 'europe', 'russia': 'europe', 'poland': 'europe', 'ukraine': 'europe',
    'india': 'asia', 'china': 'asia', 'japan': 'asia', 'pakistan': 'asia',
    'indonesia': 'asia', 'thailand': 'asia', 'vietnam': 'asia', 'philippines': 'asia',
    'israel': 'asia', 'palestine': 'asia', 'iran': 'asia', 'iraq': 'asia',
    'saudi arabia': 'asia', 'turkey': 'asia', 'uae': 'asia',
    'australia': 'oceania', 'new zealand': 'oceania',
    'egypt': 'africa', 'south africa': 'africa', 'nigeria': 'africa', 'kenya': 'africa',
    'morocco': 'africa', 'ethiopia': 'africa', 'ghana': 'africa',
}

# ========== LOCATIONS LIST FOR ROLE DETECTION (FROM PREVIOUS CODE) ==========
LOCATIONS_FOR_ROLES = [
    'india', 'africa', 'china', 'usa', 'america', 'europe', 'asia',
    'australia', 'canada', 'mexico', 'brazil', 'russia', 'japan',
    'france', 'germany', 'spain', 'italy', 'uk', 'britain', 'ghana',
    'south africa', 'nigeria', 'kenya', 'egypt', 'pakistan', 'bangladesh',
    'indonesia', 'thailand', 'vietnam', 'philippines', 'malaysia',
    'singapore', 'south korea', 'north korea', 'iran', 'iraq', 'israel',
    'palestine', 'turkey', 'saudi arabia', 'uae', 'qatar'
]


def check_geographic_claim(text: str, claim: str) -> Optional[str]:
    """
    Special handling for geographic claims like:
    - "Is X in Y" (location containment)
    - "Is X part of Y"
    - "Is X located in Y"
    
    Returns: "support", "contradict", or None if not a geographic claim
    """
    claim_lower = normalize_text(claim)
    text_lower = normalize_text(text)
    
    # Detect geographic claim patterns
    geo_patterns = [
        r'is\s+(\w+(?:\s+\w+)?)\s+in\s+(\w+(?:\s+\w+)?)',
        r'is\s+(\w+(?:\s+\w+)?)\s+part\s+of\s+(\w+(?:\s+\w+)?)',
        r'is\s+(\w+(?:\s+\w+)?)\s+located\s+in\s+(\w+(?:\s+\w+)?)',
        r'does\s+(\w+(?:\s+\w+)?)\s+belong\s+to\s+(\w+(?:\s+\w+)?)',
    ]
    
    subject = None
    container = None
    
    for pattern in geo_patterns:
        match = re.search(pattern, claim_lower)
        if match:
            subject = match.group(1).strip()
            container = match.group(2).strip()
            break
    
    if not subject or not container:
        return None
    
    # Check if both are geographic entities (not roles like PM, President)
    # Skip if this looks like a role claim
    roles = ['prime minister', 'pm', 'president', 'ceo', 'chairman', 'minister',
             'king', 'queen', 'leader', 'head', 'governor', 'mayor']
    if any(role in claim_lower for role in roles):
        return None  # Let role detection handle this
    
    # Check if both are geographic entities
    all_locations = COUNTRIES | US_STATES | INDIA_STATES | set(CITY_COUNTRY_MAP.keys()) | CONTINENTS
    
    subject_is_geo = subject in all_locations
    container_is_geo = container in all_locations
    
    if not (subject_is_geo or container_is_geo):
        return None  # Not a geographic claim
    
    # === VALIDATE THE GEOGRAPHIC RELATIONSHIP ===
    
    # Case 1: US State claimed to be in non-US country
    if subject in US_STATES and container in COUNTRIES and container != 'usa':
        return "contradict"
    
    # Case 2: US State in USA = support
    if subject in US_STATES and container == 'usa':
        return "support"
    
    # Case 3: Indian State claimed to be in non-India country
    if subject in INDIA_STATES and container in COUNTRIES and container != 'india':
        return "contradict"
    
    # Case 4: Indian State in India = support
    if subject in INDIA_STATES and container == 'india':
        return "support"
    
    # Case 5: City in wrong country
    if subject in CITY_COUNTRY_MAP:
        actual_country = CITY_COUNTRY_MAP[subject]
        if container in COUNTRIES and container != actual_country:
            return "contradict"
        if container == actual_country:
            return "support"
    
    # Case 6: Country claimed to be in another country (always false unless territories)
    if subject in COUNTRIES and container in COUNTRIES:
        # Palestine is NOT in USA, India is NOT in China, etc.
        return "contradict"
    
    # Case 7: Country in continent
    if subject in COUNTRIES and container in CONTINENTS:
        actual_continent = COUNTRY_CONTINENT.get(subject)
        if actual_continent == container:
            return "support"
        elif actual_continent and actual_continent != container:
            return "contradict"
    
    # Case 8: Check text for explicit geographic relationships
    support_patterns = [
        rf'{re.escape(subject)}.*(?:is in|located in|part of|belongs to).*{re.escape(container)}',
        rf'{re.escape(container)}.*(?:contains|includes|has).*{re.escape(subject)}',
        rf'{re.escape(subject)}.*state.*{re.escape(container)}',
        rf'{re.escape(subject)}.*city.*{re.escape(container)}',
    ]
    
    contradict_patterns = [
        rf'{re.escape(subject)}.*(?:is not in|not located in|not part of).*{re.escape(container)}',
    ]
    
    for pattern in support_patterns:
        if re.search(pattern, text_lower):
            return "support"
    
    for pattern in contradict_patterns:
        if re.search(pattern, text_lower):
            return "contradict"
    
    # If we have a clear geographic claim but text doesn't confirm = lean contradict
    if subject_is_geo and container_is_geo:
        return "contradict"
    
    return None


def check_number_claim(text: str, claim: str) -> Optional[str]:
    """Special handling for numerical/quantity claims - VERY STRICT (FROM PREVIOUS CODE)"""
    claim_lower = claim.lower()
    text_lower = text.lower()
    
    # Detect if this is a quantity question
    quantity_patterns = [
        r'how many', r'are there \d+', r'is there \d+', 
        r'\d+ (?:months|days|years|hours|minutes|people|countries|states|weeks)',
    ]
    
    is_quantity_claim = any(re.search(pattern, claim_lower) for pattern in quantity_patterns)
    
    if not is_quantity_claim:
        return None
    
    # Extract numbers from both
    claim_numbers = extract_numbers(claim)
    text_numbers = extract_numbers(text)
    
    if not claim_numbers:
        return None
    
    # Get the main number from claim
    claim_nums_list = sorted(claim_numbers, key=lambda x: len(x), reverse=True)
    main_claim_number = claim_nums_list[0] if claim_nums_list else None
    
    if not main_claim_number:
        return None
    
    # Check for explicit contradiction patterns
    contradiction_phrases = [
        f"not {main_claim_number}",
        f"no {main_claim_number}",
        f"only {main_claim_number}",
        "incorrect",
        "false claim",
        "actually"
    ]
    
    for phrase in contradiction_phrases:
        if phrase in text_lower:
            return "contradict"
    
    # For "are there X months" type claims, need EXACT number match with confirmation
    unit_match = re.search(r'(\d+)\s+(months|days|years|hours|minutes|weeks|people|countries|states)', claim_lower)
    
    if unit_match:
        claimed_number = unit_match.group(1)
        unit = unit_match.group(2)
        
        confirmation_patterns = [
            rf'\bthere (?:are|is) {claimed_number} {unit}',
            rf'{claimed_number} {unit} in',
            rf'total of {claimed_number} {unit}',
            rf'exactly {claimed_number} {unit}',
        ]
        
        has_confirmation = any(re.search(pattern, text_lower) for pattern in confirmation_patterns)
        
        if has_confirmation:
            return "support"
        
        # Look for different number with same unit = contradiction
        different_number_pattern = rf'(?:there are|is|are) (\d+) {unit}'
        match = re.search(different_number_pattern, text_lower)
        if match and match.group(1) != claimed_number:
            return "contradict"
    
    # If text mentions the number but without clear confirmation = neutral
    if main_claim_number in text_numbers:
        return "neutral"
    
    return "neutral"


def check_death_claim(text: str, claim: str) -> Optional[str]:
    """Special handling for death claims - very strict (FROM PREVIOUS CODE)"""
    text_lower = text.lower()
    claim_lower = claim.lower()
    
    # Death keywords in claim
    death_keywords = ['dead', 'died', 'death', 'passed away', 'passed', 'killed', 'murdered']
    if not any(kw in claim_lower for kw in death_keywords):
        return None  # Not a death claim
    
    # Must have explicit death confirmation in text
    strong_death_evidence = [
        'has died', 'died at', 'died on', 'died in', 'died aged',
        'passed away', 'passed away at', 'death was', 'death of',
        'killed in', 'murdered in', 'found dead', 'confirmed dead',
        'pronounced dead', 'obituary'
    ]
    
    if any(evidence in text_lower for evidence in strong_death_evidence):
        return "support"
    
    # Check for contradiction - person is alive
    alive_keywords = ['is alive', 'still alive', 'not dead', 'false claim', 'hoax']
    if any(kw in text_lower for kw in alive_keywords):
        return "contradict"
    
    # No strong evidence = neutral (don't guess on deaths)
    return "neutral"


def check_role_claim(text: str, claim: str) -> Optional[str]:
    """Special handling for role claims (PM, President, CEO, etc) - FROM PREVIOUS CODE
    
    This is the ORIGINAL logic that correctly detected "Modi PM of Africa" as FALSE
    """
    text_lower = normalize_text(text)
    claim_lower = normalize_text(claim)
    
    # Role keywords
    roles = ['prime minister', 'pm', 'president', 'ceo', 'chairman', 'minister',
             'king', 'queen', 'leader', 'head', 'governor', 'mayor']
    
    claim_has_role = any(role in claim_lower for role in roles)
    if not claim_has_role:
        return None  # Not a role claim
    
    # Extract locations from claim and text
    claim_locations = [loc for loc in LOCATIONS_FOR_ROLES if loc in claim_lower]
    text_locations = [loc for loc in LOCATIONS_FOR_ROLES if loc in text_lower]
    
    # If claim specifies a location, text MUST have the SAME location
    if claim_locations:
        # Check if any claim location is in text
        location_match = any(loc in text_locations for loc in claim_locations)
        
        if not location_match and text_locations:
            # Text mentions different location = CONTRADICT
            # This is what makes "Modi PM of Africa" return FALSE when text says "India"
            return "contradict"
        
        if not location_match:
            # No location in text = NEUTRAL (not confirming the location)
            return "neutral"
    
    # Check for role confirmation keywords
    confirmation_keywords = [
        'is the', 'is a', 'serves as', 'serving as', 'continues to serve',
        'elected as', 'appointed as', 'sworn in as', 'current'
    ]
    
    has_confirmation = any(kw in text_lower for kw in confirmation_keywords)
    
    # Check if text mentions a role at all
    text_has_role = any(role in text_lower for role in roles)
    
    if text_has_role and has_confirmation:
        return "support"
    elif text_has_role and not has_confirmation:
        # Mentions role but not confirming = neutral
        return "neutral"
    
    return "neutral"


def check_contradictions(text: str, claim: str) -> bool:
    """Check for explicit contradictions (FROM PREVIOUS CODE)"""
    text_lower = text.lower()
    
    contradict_patterns = [
        'not true', 'false', 'hoax', 'debunk', 'fake', 'misinformation',
        'no evidence', 'incorrect', 'never', 'was not', 'is not', 'are not',
        'denied', 'refuted', 'disputed', 'myth', 'misconception'
    ]
    
    return any(pattern in text_lower for pattern in contradict_patterns)


def simple_improved_stance(text: str, claim: str) -> str:
    """
    Main stance detection function - strict verification of claims
    Returns: "support", "contradict", or "neutral"
    
    MERGED PRIORITY ORDER:
    1. Role claims (PM, President) - PREVIOUS CODE
    2. Geographic claims - NEW CODE
    3. Explicit contradictions - PREVIOUS CODE
    4. Number/quantity claims - PREVIOUS CODE
    5. Death claims - PREVIOUS CODE
    6. General claims - PREVIOUS CODE
    """
    if not text or not claim:
        return "neutral"
    
    # === PRIORITY 1: Role claims (PM, President, etc.) ===
    # This MUST come first to handle "Modi PM of Africa" correctly
    role_result = check_role_claim(text, claim)
    if role_result is not None:
        return role_result
    
    # === PRIORITY 2: Geographic claims (NEW) ===
    geo_result = check_geographic_claim(text, claim)
    if geo_result is not None:
        return geo_result
    
    # === PRIORITY 3: Check for explicit contradictions ===
    if check_contradictions(text, claim):
        return "contradict"
    
    # === PRIORITY 4: Number/quantity claims ===
    number_result = check_number_claim(text, claim)
    if number_result is not None:
        return number_result
    
    # === PRIORITY 5: Death claims ===
    death_result = check_death_claim(text, claim)
    if death_result is not None:
        return death_result
    
    # === PRIORITY 6: General claims ===
    text_lower = normalize_text(text)
    claim_lower = normalize_text(claim)
    
    # Extract important words (> 3 chars)
    stop_words = {'that', 'this', 'with', 'from', 'have', 'been', 'were',
                  'they', 'there', 'their', 'what', 'when', 'where', 'which',
                  'about', 'would', 'could', 'should', 'does', 'is', 'are'}
    
    claim_words = [w for w in claim_lower.split() if len(w) > 3 and w not in stop_words]
    
    if not claim_words:
        return "neutral"
    
    # Count matches
    matches = sum(1 for w in claim_words if w in text_lower)
    match_ratio = matches / len(claim_words)
    
    # Strong support keywords
    strong_keywords = ['confirmed', 'verified', 'official', 'announced', 'reported']
    has_strong_keyword = any(kw in text_lower for kw in strong_keywords)
    
    # Decision logic - STRICT
    if has_strong_keyword and match_ratio >= 0.6:
        return "support"
    elif match_ratio >= 0.75:
        return "support"
    else:
        return "neutral"


# Backward compatible wrapper
def simple_stance_heuristic(text: str, claim: str) -> str:
    """Drop-in replacement for old function"""
    return simple_improved_stance(text, claim)