# app/retriever/improved_stance.py
"""
Improved stance detection that verifies relationships between entities,
not just keyword presence.

This module replaces the simple keyword-based heuristic with contextual
analysis that:
1. Checks for contradictions (negations, location mismatches, past transitions)
2. Verifies entity-role relationships (person + role must both be present)
3. Calculates contextual match scores using weighted phrase matching
4. Handles synonyms (USA = United States, etc.)
"""

import re
from typing import Set, List, Tuple


def normalize_text_for_matching(text: str) -> str:
    """
    Normalize text by replacing common synonyms and aliases
    """
    text_lower = text.lower()
    
    # Country/location synonyms
    replacements = {
        'united states': 'usa',
        'united kingdom': 'uk',
        'great britain': 'uk',
        'britain': 'uk',
        'people\'s republic of china': 'china',
        'russian federation': 'russia',
    }
    
    for original, replacement in replacements.items():
        text_lower = text_lower.replace(original, replacement)
    
    return text_lower


def extract_entities(text: str) -> Set[str]:
    """
    Extract potential named entities (capitalized words, proper nouns)
    This is a simple heuristic - you could use spaCy NER for better results
    """
    # Remove common words that are capitalized but not entities
    stop_words = {'the', 'is', 'are', 'was', 'were', 'a', 'an', 'of', 'in', 'on', 'at', 'to', 'for', 
                  'this', 'that', 'these', 'those', 'and', 'or', 'but'}
    
    # Clean text - remove punctuation except spaces
    clean_text = re.sub(r'[^\w\s]', ' ', text)
    words = clean_text.split()
    
    entities = set()
    
    # Single-word entities
    for word in words:
        if word and word[0].isupper() and word.lower() not in stop_words and len(word) > 1:
            entities.add(word.lower())
    
    # Multi-word entities (2-3 consecutive capitalized words)
    for i in range(len(words)):
        if i < len(words) - 1:
            # Two-word entities
            if (words[i] and words[i][0].isupper() and 
                words[i+1] and words[i+1][0].isupper() and
                words[i].lower() not in stop_words):
                entities.add(f"{words[i].lower()} {words[i+1].lower()}")
    
    return entities


def extract_key_phrases(text: str) -> List[Tuple[str, float]]:
    """
    Extract key noun phrases and important terms from claim with weights
    Returns list of (phrase, weight) tuples
    """
    # Convert to lowercase for matching
    text_lower = text.lower()
    
    # Remove common question words and punctuation
    text_lower = re.sub(r'\b(is|are|was|were|the|a|an|of|in|on|at|to)\b', ' ', text_lower)
    text_lower = re.sub(r'[?!.,;:]', '', text_lower)
    
    # Split into words
    words = [w.strip() for w in text_lower.split() if len(w.strip()) > 2]
    
    phrases = []
    
    # Three-word combinations (highest weight - most specific)
    for i in range(len(words) - 2):
        phrases.append((f"{words[i]} {words[i+1]} {words[i+2]}", 3.0))
    
    # Two-word combinations (medium weight)
    for i in range(len(words) - 1):
        phrases.append((f"{words[i]} {words[i+1]}", 2.0))
    
    # Individual important words (lowest weight)
    for word in words:
        phrases.append((word, 1.0))
    
    return phrases


def calculate_contextual_match_score(snippet: str, claim: str) -> float:
    """
    Calculate how well the snippet matches the FULL CONTEXT of the claim,
    not just individual keywords. Uses weighted phrase matching with synonym support.
    """
    # Normalize both texts
    snippet_normalized = normalize_text_for_matching(snippet)
    claim_normalized = normalize_text_for_matching(claim)
    
    # Extract weighted key phrases from normalized claim
    claim_phrases = extract_key_phrases(claim_normalized)
    
    if not claim_phrases:
        return 0.0
    
    # Count how many key phrases appear in snippet
    matched_weight = 0.0
    total_weight = sum(weight for _, weight in claim_phrases)
    
    for phrase, weight in claim_phrases:
        if phrase in snippet_normalized:
            matched_weight += weight
    
    if total_weight == 0:
        return 0.0
    
    match_score = matched_weight / total_weight
    return match_score


def check_contradictory_context(snippet: str, claim: str) -> bool:
    """
    Check if snippet explicitly contradicts the claim with negations or opposites
    """
    snippet_lower = snippet.lower()
    claim_lower = claim.lower()
    
    # Check if claim is about current/present status
    is_current_claim = any(word in claim_lower for word in ['current', 'currently', 'now', 'present', 'today'])
    
    # Strong contradiction keywords
    contradiction_patterns = [
        "not true", "false", "hoax", "debunk", "fake", "lies", 
        "no evidence", "incorrect", "never", "was not", "is not",
        "are not", "disputed", "unverified", "denied", "not the",
        "not a", "former", "ex-"
    ]
    
    # For current claims, past tense transitions indicate contradiction
    past_transition_patterns = ["lost", "defeated", "resigned", "stepped down", "left office"]
    
    for pattern in contradiction_patterns:
        if pattern in snippet_lower:
            # Check if this contradiction is about the main subject
            context_score = calculate_contextual_match_score(snippet, claim)
            if context_score >= 0.10:  # Very low threshold for contradictions
                return True
    
    # Check for past transitions when claim asks about current status
    if is_current_claim:
        for pattern in past_transition_patterns:
            if pattern in snippet_lower:
                context_score = calculate_contextual_match_score(snippet, claim)
                if context_score >= 0.10:
                    return True
    
    # Check for entity mismatch (e.g., "Modi PM of India" vs snippet says "Modi PM of Africa")
    # Extract entities from both
    claim_entities = extract_entities(claim)
    snippet_entities = extract_entities(snippet)
    
    # If claim has specific location/entity and snippet has a different one
    location_words = {'india', 'africa', 'china', 'usa', 'america', 'europe', 'asia', 
                     'australia', 'canada', 'mexico', 'brazil', 'russia', 'japan',
                     'france', 'germany', 'spain', 'italy', 'uk', 'britain'}
    
    claim_locations = {e for e in claim_entities if e in location_words}
    snippet_locations = {e for e in snippet_entities if e in location_words}
    
    # If claim mentions a location but snippet mentions a DIFFERENT location
    if claim_locations and snippet_locations:
        if not claim_locations.intersection(snippet_locations):
            # Check if both mention the same person/entity
            common_entities = claim_entities.intersection(snippet_entities) - location_words
            if common_entities:  # Same person, different locations = contradiction
                return True
    
    return False


def improved_stance_heuristic(snippet: str, claim: str) -> str:
    """
    Improved stance detection that verifies RELATIONSHIPS between entities,
    not just keyword presence.
    
    Returns: "support", "contradict", or "neutral"
    
    Logic flow:
    1. Check for explicit contradictions first (negations, mismatches)
    2. Calculate contextual match score (how well snippet matches claim context)
    3. For role-based claims (PM, President, etc.):
       - Verify BOTH person AND role are mentioned together
       - Require confirmation keywords or high context score
    4. For general claims:
       - Use contextual match score with thresholds
    """
    if not snippet or not claim:
        return "neutral"
    
    snippet_lower = snippet.lower()
    claim_lower = claim.lower()
    
    # Step 1: Check for explicit contradiction signals
    if check_contradictory_context(snippet, claim):
        return "contradict"
    
    # Step 2: Calculate contextual match score
    context_score = calculate_contextual_match_score(snippet, claim)
    
    # Step 3: Extract claim structure to understand what's being asked
    # Check if claim asks about a specific role/position
    role_keywords = ['prime minister', 'pm', 'president', 'ceo', 'chairman', 'minister', 
                     'leader', 'head', 'governor', 'mayor', 'king', 'queen']
    
    claim_has_role = any(role in claim_lower for role in role_keywords)
    
    # Step 4: For role-based claims, verify BOTH person AND role are mentioned in snippet
    if claim_has_role:
        # Extract person names from claim (capitalized words)
        claim_entities = extract_entities(claim)
        snippet_entities = extract_entities(snippet)
        
        # Check if snippet mentions the person
        person_mentioned = bool(claim_entities.intersection(snippet_entities))
        
        # Check if snippet mentions the role
        role_mentioned = any(role in snippet_lower for role in role_keywords)
        
        # For role claims, BOTH person AND role must be present for support
        if person_mentioned and role_mentioned:
            # Now check for confirmation keywords
            if context_score >= 0.25:  # Lower threshold for initial check
                strong_support_kws = [
                    "confirmed", "verified", "official", "announced", "appointed",
                    "elected", "sworn in", "inaugurated", "serves as", "continues to serve",
                    "currently", "is the", "is a", "was inaugurated"
                ]
                
                # If strong support keyword found, need lower context score
                for kw in strong_support_kws:
                    if kw in snippet_lower and context_score >= 0.30:
                        return "support"
                
                # High context score with both person and role (no keyword needed)
                if context_score >= 0.55:
                    return "support"
            
            return "neutral"  # Person and role mentioned but no strong confirmation
        else:
            # Person mentioned but not with the role = neutral
            return "neutral"
    
    # Step 5: For non-role claims, check for strong support keywords
    if context_score >= 0.3:
        strong_support_kws = [
            "confirmed", "verified", "official", "announced",
            "is the", "is a", "has been"
        ]
        
        for kw in strong_support_kws:
            if kw in snippet_lower:
                return "support"
    
    # Step 6: Make stance decision based on contextual match for general claims
    if context_score >= 0.45:
        return "support"
    elif context_score >= 0.25:
        return "neutral"
    else:
        return "neutral"


# Keep the old function name for backward compatibility
def simple_stance_heuristic(text: str, claim: str) -> str:
    """
    Backward compatible wrapper for the improved stance detection.
    This replaces the old simple_stance_heuristic.
    """
    return improved_stance_heuristic(text, claim)