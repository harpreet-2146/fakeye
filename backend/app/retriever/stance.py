# app/retriever/stance.py
"""
Strict stance detection that verifies actual claim relationships
Focuses on avoiding false positives while catching true matches
"""

import re
from typing import Set, List

def extract_entities(text: str) -> Set[str]:
    """Extract capitalized words (potential names/places)"""
    words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
    return set(w.lower() for w in words if len(w) > 2)

def normalize_text(text: str) -> str:
    """Normalize synonyms and variations"""
    text = text.lower()
    text = text.replace('united states', 'usa')
    text = text.replace('united kingdom', 'uk')
    return text

def check_death_claim(text: str, claim: str) -> str:
    """Special handling for death claims - very strict"""
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

def check_role_claim(text: str, claim: str) -> str:
    """Special handling for role claims (PM, President, CEO, etc)"""
    text_lower = normalize_text(text)
    claim_lower = normalize_text(claim)
    
    # Role keywords
    roles = ['prime minister', 'pm', 'president', 'ceo', 'chairman', 'minister',
             'king', 'queen', 'leader', 'head', 'governor', 'mayor']
    
    claim_has_role = any(role in claim_lower for role in roles)
    if not claim_has_role:
        return None  # Not a role claim
    
    # Extract locations
    locations = ['india', 'africa', 'china', 'usa', 'america', 'europe', 'asia',
                 'australia', 'canada', 'mexico', 'brazil', 'russia', 'japan',
                 'france', 'germany', 'spain', 'italy', 'uk', 'britain', 'ghana',
                 'south africa', 'nigeria', 'kenya', 'egypt']
    
    claim_locations = [loc for loc in locations if loc in claim_lower]
    text_locations = [loc for loc in locations if loc in text_lower]
    
    # If claim specifies a location, text MUST have the SAME location
    if claim_locations:
        # Check if any claim location is in text
        location_match = any(loc in text_locations for loc in claim_locations)
        
        if not location_match and text_locations:
            # Text mentions different location = CONTRADICT
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
        # Mentions role but not confirming = neutral (could be visiting, meeting, etc.)
        return "neutral"
    
    return "neutral"

def check_contradictions(text: str, claim: str) -> bool:
    """Check for explicit contradictions"""
    text_lower = text.lower()
    
    contradict_patterns = [
        'not true', 'false', 'hoax', 'debunk', 'fake', 'misinformation',
        'no evidence', 'incorrect', 'never', 'was not', 'is not', 'are not',
        'denied', 'refuted', 'disputed'
    ]
    
    return any(pattern in text_lower for pattern in contradict_patterns)

def simple_improved_stance(text: str, claim: str) -> str:
    """
    Main stance detection function - strict verification of claims
    Returns: "support", "contradict", or "neutral"
    """
    if not text or not claim:
        return "neutral"
    
    # === PRIORITY 1: Check for explicit contradictions ===
    if check_contradictions(text, claim):
        return "contradict"
    
    # === PRIORITY 2: Death claims (STRICT) ===
    death_result = check_death_claim(text, claim)
    if death_result is not None:
        return death_result
    
    # === PRIORITY 3: Role claims (STRICT) ===
    role_result = check_role_claim(text, claim)
    if role_result is not None:
        return role_result
    
    # === PRIORITY 4: General claims (moderate strictness) ===
    text_lower = normalize_text(text)
    claim_lower = normalize_text(claim)
    
    # Extract important words (> 3 chars)
    stop_words = {'that', 'this', 'with', 'from', 'have', 'been', 'were',
                  'they', 'there', 'their', 'what', 'when', 'where', 'which',
                  'about', 'would', 'could', 'should'}
    
    claim_words = [w for w in claim_lower.split() if len(w) > 3 and w not in stop_words]
    
    if not claim_words:
        return "neutral"
    
    # Count matches
    matches = sum(1 for w in claim_words if w in text_lower)
    match_ratio = matches / len(claim_words)
    
    # Strong support keywords
    strong_keywords = ['confirmed', 'verified', 'official', 'announced', 'reported']
    has_strong_keyword = any(kw in text_lower for kw in strong_keywords)
    
    # Decision logic - MUCH STRICTER
    if has_strong_keyword and match_ratio >= 0.6:
        return "support"
    elif match_ratio >= 0.75:  # Very high match required without strong keyword
        return "support"
    else:
        return "neutral"  # Default to neutral unless strong evidence


# Backward compatible wrapper
def simple_stance_heuristic(text: str, claim: str) -> str:
    """Drop-in replacement for old function"""
    return simple_improved_stance(text, claim)


# Backward compatible function name
def simple_stance_heuristic(text: str, claim: str) -> str:
    """Drop-in replacement for the old function"""
    return simple_improved_stance(text, claim)