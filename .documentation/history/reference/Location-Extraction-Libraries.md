# Python Libraries for Extracting Location Data from Web Pages

## Currently Using ✅

1. **extruct** - Extracts structured data (JSON-LD, Microdata, RDFa)
   - Great for Schema.org PostalAddress objects
   - We're already using this!

2. **usaddress** - ML-based parser for US addresses
   - Parses unstructured address text into components
   - Already integrated

3. **geopy** - Geocoding (address → coordinates)
   - Uses Nominatim, Google, etc.
   - Already available

4. **googlemaps** - Google Places API
   - Most reliable for finding addresses by business name
   - Already integrated

## Should Consider Adding 🎯

### 1. **pyap** (Python Address Parser)

```bash
pip install pyap
```

**Purpose**: Specifically designed to extract addresses from unstructured text
**Advantages**:

- Supports multiple countries (US, Canada, UK, etc.)
- Uses regex patterns optimized for address extraction
- Can find multiple addresses in a document
- Less ML overhead than usaddress

**Example**:

```python
import pyap
text = "Visit us at 108 E Reconciliation Way, Tulsa, OK 74103 for great art!"
addresses = pyap.parse(text, country='US')
for address in addresses:
    print(address.full_address)
# Output: "108 E Reconciliation Way, Tulsa, OK 74103"
```

### 2. **libpostal** (via postal)

```bash
# Requires C library installation first
# On Ubuntu: apt-get install libpostal
pip install postal
```

**Purpose**: International address parsing (trained on OpenStreetMap data)
**Advantages**:

- Handles 60+ countries
- Very robust parsing
- Can normalize addresses
- Better than pyap for international

**Example**:

```python
from postal.parser import parse_address
parse_address('108 E Reconciliation Way Tulsa OK 74103')
# Returns: [('108', 'house_number'), ('e', 'road'), ('reconciliation', 'road'), ...]
```

**Downside**: Requires system-level C library installation (harder to deploy)

### 3. **trafilatura**

```bash
pip install trafilatura
```

**Purpose**: Extracts main content from web pages (better than raw BeautifulSoup)
**Advantages**:

- Filters out navigation, ads, boilerplate
- Focuses on main content area
- Makes it easier to find relevant sections
- Supports metadata extraction

**Example**:

```python
import trafilatura
downloaded = trafilatura.fetch_url('https://108contemporary.org')
text = trafilatura.extract(downloaded)
# Returns cleaned main content only
```

### 4. **commonregex**

```bash
pip install commonregex
```

**Purpose**: Prebuilt regex patterns for common data types
**Advantages**:

- Patterns for addresses, phones, emails, dates, times
- One-line extraction
- No ML needed

**Example**:

```python
import commonregex
text = "Call us at 918-555-1234 or visit 108 E Reconciliation Way"
parsed = commonregex.CommonRegex(text)
print(parsed.phones)  # ['918-555-1234']
print(parsed.street_addresses)  # ['108 E Reconciliation Way']
```

### 5. **advertools**

```bash
pip install advertools
```

**Purpose**: SEO and web scraping toolkit
**Advantages**:

- Extract structured data from multiple pages at once
- Built-in crawling with politeness
- Good for bulk operations

## Recommendation for MuseumSpark 🚀

**Add immediately**:

1. **pyap** - Best balance of power and ease of use for US addresses
   - No C dependencies
   - Purpose-built for address extraction
   - Works well with our current pipeline

2. **trafilatura** - Better content extraction
   - Will help us find the "main" content vs boilerplate
   - Makes subsequent extraction more accurate

**Consider later**:
3. **commonregex** - If we need quick phone/email extraction
4. **libpostal** - Only if we expand internationally (requires C library)

## Proposed Integration

```python
# In enrich-open-data.py

# Add optional imports
try:
    import pyap
    HAS_PYAP = True
except ImportError:
    HAS_PYAP = False

try:
    import trafilatura
    HAS_TRAFILATURA = True
except ImportError:
    HAS_TRAFILATURA = False

def _extract_addresses_with_pyap(html: str, state_code: str) -> list[str]:
    """Extract addresses using pyap."""
    if not HAS_PYAP:
        return []
    
    # Get clean text
    if HAS_TRAFILATURA:
        text = trafilatura.extract(html) or html
    else:
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
    
    # Extract addresses
    addresses = pyap.parse(text, country='US')
    
    # Filter to addresses in the expected state
    valid = []
    for addr in addresses:
        if state_code in str(addr.full_address).upper():
            valid.append(addr.full_address)
    
    return valid

# Add as Priority 2.5 in patch_from_official_website()
# Between extruct and usaddress
```

## Why These Are Better Than Pure Regex

1. **Context-aware**: ML models understand address structure
2. **Ambiguity handling**: "St" could be "Street" or "Saint"
3. **Normalization**: "North Main St" vs "N Main Street"
4. **International**: Different countries have different formats
5. **Garbage filtering**: Won't match "123 Error Code"

## Testing Strategy

```python
# Test each library on known-good examples
test_cases = [
    ("108 E Reconciliation Way, Tulsa, OK 74103", "simple"),
    ("Visit us at 2727 S Rockford Rd, Tulsa, Oklahoma 74114", "full_state"),
    ("3500 Batfish Rd\\nMuskogee, OK 74403", "multiline"),
]

# Compare extraction rates and quality
```

## Implementation Priority

1. ✅ **Week 1**: Add pyap + trafilatura (low risk, high value)
2. 📊 **Week 2**: Measure improvement in extraction rates
3. 🔧 **Week 3**: Tune extraction order and fallback strategy
4. 🌍 **Future**: Consider libpostal if expanding internationally

---

**Bottom Line**: We should add **pyap** and **trafilatura** to requirements.txt. They're purpose-built for this problem and will likely double our address extraction success rate.
