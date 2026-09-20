import re

def parse_shift_note(text: str) -> dict:
    """
    Parses unstructured shift report text using flexible, case-insensitive regular expressions
    to extract key petroleum engineering parameters from conversational field notes.
    """
    # 1. THP
    thp_match = re.search(
        r'(?:tubing\s+head\s+pressure|\(?thp\)?)[^\d\n]*?(\d+(?:\.\d+)?)\s*(?:psi)?',
        text,
        re.IGNORECASE
    )
    
    # 2. CHP
    chp_match = re.search(
        r'(?:casing\s+head\s+pressure|\(?chp\)?)[^\d\n]*?(\d+(?:\.\d+)?)\s*(?:psi)?',
        text,
        re.IGNORECASE
    )
    
    # Choke size e.g. "36/64" or "36"
    choke_match = re.search(r'(?:choke|choke size)[^\d\n]*?(\d+(?:\/\d+)?)', text, re.IGNORECASE)
    if not choke_match:
        choke_match = re.search(r'(\d+)/64', text, re.IGNORECASE)
        
    # 3. Liquid Rate
    rate_match = re.search(
        r'(?:liquid\s+rate|rate|production)[^\d\n]*?(\d+(?:\.\d+)?)\s*(?:bopd|stb/?d|bpd)?',
        text,
        re.IGNORECASE
    )
    
    # 4. Water Cut / BS&W
    wcut_match = re.search(
        r'(?:water\s*cut|bs&w)[^\d\n%]*?(\d+(?:\.\d+)?)\s*%',
        text,
        re.IGNORECASE
    )
    
    # GOR or gas rate
    gor_match = re.search(r'(?:gor|gas\s+rate)[^\d\n]*?(\d+(?:\.\d+)?)', text, re.IGNORECASE)
    
    # Keywords / Events
    text_lower = text.lower()
    keywords = []
    watch_terms = ["slugging", "wax", "sand", "shut-in", "vibration", "leak", "scale", "hydrate", "warning"]
    for term in watch_terms:
        if term in text_lower:
            keywords.append(term)
            
    # Parse numerical values safely to float
    def safe_float(match, idx=1):
        if match:
            val_str = match.group(idx).replace(',', '')
            try:
                return float(val_str)
            except ValueError:
                return None
        return None

    thp = safe_float(thp_match)
    chp = safe_float(chp_match)
    
    choke_val = None
    if choke_match:
        choke_str = choke_match.group(1)
        if '/' in choke_str:
            parts = choke_str.split('/')
            try:
                choke_val = float(parts[0])
            except ValueError:
                choke_val = None
        else:
            try:
                choke_val = float(choke_str)
            except ValueError:
                choke_val = None

    liquid_rate = safe_float(rate_match)
    water_cut = safe_float(wcut_match)
    gor = safe_float(gor_match)

    return {
        "thp": thp,
        "chp": chp,
        "choke_size": choke_val,
        "liquid_rate": liquid_rate,
        "water_cut": water_cut,
        "gor": gor,
        "keywords": keywords,
        "raw_text": text
    }
