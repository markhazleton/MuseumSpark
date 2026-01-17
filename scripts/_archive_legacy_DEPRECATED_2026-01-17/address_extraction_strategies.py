"""
Advanced address extraction strategies for museum websites.

This module provides multiple strategies for extracting physical addresses
from HTML, handling edge cases and unusual formats.
"""

import re
from typing import Optional, Dict, List, Tuple
from bs4 import BeautifulSoup


def extract_address_multi_strategy(html: str, state_code: str) -> Optional[Dict[str, str]]:
    """
    Extract address using multiple strategies in priority order.
    
    Args:
        html: Raw HTML content
        state_code: Two-letter state code (e.g., "OK")
        
    Returns:
        Dict with street_address, city, postal_code, or None if not found
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    strategies = [
        lambda: _strategy_semantic_html(soup, state_code),
        lambda: _strategy_contextual_search(soup, state_code),
        lambda: _strategy_zip_code_anchor(soup, state_code),
        lambda: _strategy_phone_number_proximity(soup, state_code),
        lambda: _strategy_relaxed_regex(soup.get_text(), state_code),
    ]
    
    for strategy in strategies:
        result = strategy()
        if result and result.get("street_address"):
            return result
    
    return None


def _strategy_semantic_html(soup: BeautifulSoup, state_code: str) -> Optional[Dict[str, str]]:
    """
    Strategy 1: Look for semantic HTML tags like <address>, schema.org markup.
    
    This is the most reliable when present.
    """
    # Check <address> tags
    for addr_tag in soup.find_all('address'):
        text = addr_tag.get_text(separator=' ', strip=True)
        parsed = _parse_address_text(text, state_code)
        if parsed:
            return parsed
    
    # Check elements with address-related classes
    for elem in soup.find_all(class_=re.compile(r'address|location|contact', re.I)):
        text = elem.get_text(separator=' ', strip=True)
        parsed = _parse_address_text(text, state_code)
        if parsed:
            return parsed
    
    # Check for Schema.org PostalAddress in itemprop
    for elem in soup.find_all(itemprop=re.compile(r'address', re.I)):
        text = elem.get_text(separator=' ', strip=True)
        parsed = _parse_address_text(text, state_code)
        if parsed:
            return parsed
    
    return None


def _strategy_contextual_search(soup: BeautifulSoup, state_code: str) -> Optional[Dict[str, str]]:
    """
    Strategy 2: Look for addresses near contextual keywords.
    
    Addresses are often found near words like "Visit", "Hours", "Location", etc.
    """
    keywords = [
        'visit us', 'location', 'address', 'directions', 'find us', 
        'hours', 'open', 'contact', 'come see us', 'our address'
    ]
    
    # Get all text nodes
    text = soup.get_text(separator='\n')
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        # Check if line contains a keyword
        if any(keyword in line_lower for keyword in keywords):
            # Check next few lines for address pattern
            context = '\n'.join(lines[i:i+10])
            parsed = _parse_address_text(context, state_code)
            if parsed:
                return parsed
    
    return None


def _strategy_zip_code_anchor(soup: BeautifulSoup, state_code: str) -> Optional[Dict[str, str]]:
    """
    Strategy 3: Find ZIP codes, then work backwards to find full address.
    
    ZIP codes are the most reliable anchor pattern (5 digits).
    """
    text = soup.get_text(separator=' ')
    
    # Find all 5-digit sequences that could be ZIP codes
    zip_pattern = r'\b(\d{5})(?:-\d{4})?\b'
    
    for match in re.finditer(zip_pattern, text):
        zip_code = match.group(1)
        start_pos = match.start()
        
        # Get 200 characters before the ZIP code
        context_start = max(0, start_pos - 200)
        context = text[context_start:match.end()]
        
        # Try to extract address from this context
        parsed = _parse_address_text(context, state_code)
        if parsed and parsed.get("postal_code") == zip_code:
            return parsed
    
    return None


def _strategy_phone_number_proximity(soup: BeautifulSoup, state_code: str) -> Optional[Dict[str, str]]:
    """
    Strategy 4: Look near phone numbers (often listed with addresses).
    """
    text = soup.get_text(separator='\n')
    lines = text.split('\n')
    
    # Phone number patterns
    phone_pattern = r'(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    
    for i, line in enumerate(lines):
        if re.search(phone_pattern, line):
            # Check surrounding lines (before and after)
            context_lines = lines[max(0, i-5):i+5]
            context = '\n'.join(context_lines)
            parsed = _parse_address_text(context, state_code)
            if parsed:
                return parsed
    
    return None


def _strategy_relaxed_regex(text: str, state_code: str) -> Optional[Dict[str, str]]:
    """
    Strategy 5: Relaxed regex patterns as last resort.
    """
    return _parse_address_text(text, state_code)


def _parse_address_text(text: str, state_code: str) -> Optional[Dict[str, str]]:
    """
    Parse address components from a text block.
    
    Uses flexible regex patterns that handle edge cases.
    """
    if not text or not state_code:
        return None
    
    # State name mapping
    state_names = {
        "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
        "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
        "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
        "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
        "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri",
        "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
        "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
        "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
        "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
        "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
        "DC": "District of Columbia"
    }
    state_name = state_names.get(state_code, state_code)
    
    # Common street suffixes
    street_suffix = r"(?:Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Drive|Dr|Boulevard|Blvd|Way|Court|Ct|Circle|Cir|Parkway|Pkwy|Plaza|Pl|Place|Terrace|Trail)"
    
    # Pattern 1: Full address with street type
    # Example: "108 E Reconciliation Way Tulsa, OK 74103"
    # More flexible: allows multiple words before street suffix
    pattern1 = rf"""
        \b(\d+\s+                          # Street number
        [A-Z]?\.?\s*                       # Optional direction (N, S, E, W)
        (?:[A-Z][a-z]*\s+)*                # Multiple words (e.g., "E Reconciliation")
        {street_suffix}\.?)                # Street type
        \s*,?\s*                           # Optional comma
        ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)   # City name
        \s*,?\s*                           # Optional comma
        (?:{state_name}|{state_code})      # State (name or code)
        \s+                                # Space
        (\d{{5}}(?:-\d{{4}})?)             # ZIP code
    """
    
    for match in re.finditer(pattern1, text, re.IGNORECASE | re.VERBOSE):
        street = match.group(1).strip()
        city = match.group(2).strip()
        zip_code = match.group(3).strip()
        
        # Validate
        if len(street) >= 5 and len(city) >= 2:
            return {
                "street_address": street,
                "city": city,
                "postal_code": zip_code
            }
    
    # Pattern 2: Address on multiple lines
    # Example:
    #   108 E Reconciliation Way
    #   Tulsa, OK 74103
    lines = text.split('\n')
    for i in range(len(lines) - 1):
        line1 = lines[i].strip()
        line2 = lines[i + 1].strip()
        
        # Check if line1 looks like a street address
        street_match = re.match(rf'^\d+\s+(?:[A-Z]\.?\s+)?(?:\w+\s+){{1,5}}{street_suffix}\.?$', line1, re.I)
        if street_match:
            # Check if line2 has city, state, zip
            city_state_zip = re.search(rf'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*,?\s*(?:{state_name}|{state_code})\s+(\d{{5}}(?:-\d{{4}})?)', line2, re.I)
            if city_state_zip:
                return {
                    "street_address": line1,
                    "city": city_state_zip.group(1).strip(),
                    "postal_code": city_state_zip.group(2).strip()
                }
    
    # Pattern 3: Just look for ZIP code and work backwards
    zip_matches = list(re.finditer(r'\b(\d{5})(?:-\d{4})?\b', text))
    for zip_match in zip_matches:
        zip_code = zip_match.group(1)
        
        # Get 150 chars before ZIP
        start = max(0, zip_match.start() - 150)
        context = text[start:zip_match.end()]
        
        # Look for street pattern
        street_pattern = rf'(\d+\s+(?:[NSEW]\.?\s+)?(?:\w+\s+){{1,6}}{street_suffix}\.?)'
        street_matches = list(re.finditer(street_pattern, context, re.I))
        if street_matches:
            # Get the last (closest) street match before ZIP
            street_match = street_matches[-1]
            street = street_match.group(1).strip()
            
            # Look for city between street and ZIP
            between = context[street_match.end():zip_match.start()]
            city_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', between)
            if city_match:
                city = city_match.group(1).strip()
                
                # Validate city isn't a street suffix or state
                if city.lower() not in [s.lower() for s in ['street', 'avenue', 'road', state_name, state_code]]:
                    return {
                        "street_address": street,
                        "city": city,
                        "postal_code": zip_code
                    }
    
    return None


def score_address_quality(address: Dict[str, str]) -> float:
    """
    Score an extracted address for quality (0.0 to 1.0).
    
    Higher scores indicate more complete and valid-looking addresses.
    """
    score = 0.0
    
    if address.get("street_address"):
        street = address["street_address"]
        # Has street number
        if re.match(r'^\d+', street):
            score += 0.3
        # Has street type
        if re.search(r'(Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Drive|Dr|Boulevard|Blvd|Way|Court|Ct)', street, re.I):
            score += 0.2
        # Reasonable length
        if 5 <= len(street) <= 80:
            score += 0.1
    
    if address.get("city"):
        city = address["city"]
        # Reasonable length
        if 2 <= len(city) <= 30:
            score += 0.2
        # Starts with capital
        if city[0].isupper():
            score += 0.1
    
    if address.get("postal_code"):
        zip_code = address["postal_code"]
        # Valid 5 or 5+4 format
        if re.match(r'^\d{5}(?:-\d{4})?$', zip_code):
            score += 0.1
    
    return score
