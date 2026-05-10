# API Keys Setup Guide

This document describes how to obtain and configure API keys for museum data enrichment.

## Required Environment Variables

Create a `.env` file in the project root or set these as system environment variables:

```bash
# OpenAI API (for LLM enrichment)
OPENAI_API_KEY=sk-...

# Anthropic API (for LLM enrichment) 
ANTHROPIC_API_KEY=sk-ant-...

# Google Maps API (for address lookup, hours, photos)
GOOGLE_MAPS_API_KEY=AIza...

# Yelp Fusion API (for business data: hours, phone, ratings)
YELP_API_KEY=...
```

---

## 🌟 Yelp Fusion API (HIGHLY RECOMMENDED)

**Cost**: **FREE** - 5,000 API calls per day  
**Best for**: Business hours, phone numbers, addresses, photos, reviews, ratings

### Why Yelp?

- Most museums are listed on Yelp with complete information
- Excellent for filling address/hours/phone when robots.txt blocks web scraping
- Free tier is generous (5,000 calls/day = ~150K museums/month)
- No credit card required for signup

### How to Get API Key

1. **Create Yelp Account**: Go to <https://www.yelp.com/signup>
2. **Register App**: Visit <https://www.yelp.com/developers/v3/manage_app>
3. **Create New App**:
   - App Name: `MuseumSpark`
   - Industry: `Education/Museums`
   - Description: `Museum data enrichment for trip planning`
   - Website: Your GitHub repo URL
4. **Get API Key**: Copy the API key from the app details page
5. **Set Environment Variable**:

   ```powershell
   # Windows PowerShell
   $env:YELP_API_KEY = "YOUR_KEY_HERE"
   
   # Or add to .env file
   echo "YELP_API_KEY=YOUR_KEY_HERE" >> .env
   ```

### What Data Does Yelp Provide?

- ✅ Street address, city, ZIP code
- ✅ Latitude/longitude coordinates  
- ✅ Phone number (formatted)
- ✅ **Business hours** (day-by-day schedule)
- ✅ Photos (URLs)
- ✅ Ratings & review count
- ✅ Price level (if applicable)

### Example Response

```json
{
  "street_address": "108 E Reconciliation Way",
  "city": "Tulsa",
  "postal_code": "74103",
  "latitude": 36.1540495,
  "longitude": -95.9925163,
  "phone": "9185853001",
  "rating": 4.5,
  "review_count": 89,
  "hours": "Monday: 10:00 AM - 6:00 PM\nTuesday: 10:00 AM - 6:00 PM\n..."
}
```

---

## 🗺️ Google Maps API

**Cost**: **$200 FREE credit/month** (~28K requests)  
**Best for**: Address validation, coordinates, place IDs, photos

### How to Get API Key

1. **Create Google Cloud Account**: <https://console.cloud.google.com>
2. **Enable APIs**:
   - Go to APIs & Services > Library
   - Enable "Places API"
   - Enable "Geocoding API"
3. **Create Credentials**:
   - APIs & Services > Credentials
   - Create API Key
   - Restrict key to Places API + Geocoding API
4. **Set Environment Variable**:

   ```powershell
   $env:GOOGLE_MAPS_API_KEY = "YOUR_KEY_HERE"
   ```

### What Data Does Google Provide?

- ✅ Formatted address
- ✅ Precise latitude/longitude
- ✅ Place ID (unique identifier)
- ✅ **Business hours** (with special hours/holidays)
- ✅ Phone number
- ✅ Website URL
- ✅ Photos (high quality)
- ✅ Ratings & review count

---

## 🤖 OpenAI API

**Cost**: Pay-per-use ($0.15 per 1M input tokens for GPT-4o-mini)  
**Best for**: Museum summaries, extracting complex data from text

### How to Get API Key

1. **Create OpenAI Account**: <https://platform.openai.com/signup>
2. **Add Payment Method**: Required even for small usage
3. **Create API Key**: <https://platform.openai.com/api-keys>
4. **Set Environment Variable**:

   ```powershell
   $env:OPENAI_API_KEY = "sk-..."
   ```

---

## 🧠 Anthropic API (Claude)

**Cost**: Pay-per-use ($0.25 per 1M input tokens for Claude Haiku)  
**Best for**: Structured data extraction, museum descriptions

### How to Get API Key

1. **Create Anthropic Account**: <https://console.anthropic.com>
2. **Add Credits**: $5 minimum
3. **Create API Key**: <https://console.anthropic.com/settings/keys>
4. **Set Environment Variable**:

   ```powershell
   $env:ANTHROPIC_API_KEY = "sk-ant-..."
   ```

---

## 🎯 Recommended Setup for Cost-Efficiency

### Phase 1: Free APIs Only

```
✅ YELP_API_KEY (free 5K/day)
✅ GOOGLE_MAPS_API_KEY (free $200/month)
❌ OPENAI_API_KEY (skip - use Yelp+Google first)
❌ ANTHROPIC_API_KEY (skip - use Yelp+Google first)
```

**Result**: ~90% of museums will get complete data from Yelp + Google alone!

### Phase 2: Add LLM for Remaining Museums

After running Yelp+Google enrichment, check how many museums still have null fields.  
Only then add OpenAI/Anthropic for the remaining edge cases.

---

## Testing Your API Keys

```powershell
# Test all API keys
python scripts/enrich-open-data.py --state OK --limit 1 --verbose

# You should see:
# ✅ Yelp: extracted street address
# ✅ Yelp: extracted operating hours  
# ✅ Google Places: extracted place_id
# ✅ Google Places: 4.5/5 rating with 250 reviews
```

---

## Rate Limits & Best Practices

| API | Free Tier | Rate Limit | Cost After Free |
|-----|-----------|------------|-----------------|
| **Yelp** | 5K calls/day | 5,000/day | N/A (always free) |
| **Google Places** | $200/month | ~500/sec | $17 per 1K requests |
| **OpenAI** | None | 3,500 RPM | $0.15 per 1M tokens |
| **Anthropic** | None | 50 req/min | $0.25 per 1M tokens |

### Tips

- ✅ Always use **Yelp FIRST** (most complete, 100% free)
- ✅ Use **Google Places** as backup (also mostly free)
- ⚠️ Only use **LLMs** for museums that Yelp+Google couldn't find
- ✅ Enable caching to avoid duplicate API calls
- ✅ Use `--limit` flag when testing

---

## Troubleshooting

### "HTTP 401 Unauthorized"

- Check API key is set correctly: `echo $env:YELP_API_KEY`
- Verify key hasn't expired in your developer console

### "Quota exceeded"

- Yelp: Wait until next day (resets at midnight PST)
- Google: Check usage in Cloud Console, may need to increase quota

### "Module not found: yelpapi"

```powershell
.venv\Scripts\pip install yelpapi
```

### "No businesses found"

- Museum may not be on Yelp (try Google Places as fallback)
- Try searching with different name variations
- Check if museum is actually open (Yelp removes closed businesses)

---

## Cost Estimation

For **~12,000 US museums**:

| Scenario | Yelp | Google Places | LLM | Total Cost |
|----------|------|---------------|-----|------------|
| **Yelp Only** | Free | - | - | **$0** |
| **Yelp + Google** | Free | Free ($200 credit) | - | **$0** |
| **All Sources** | Free | Free | ~$50 | **~$50** |

**Recommendation**: Start with Yelp + Google (100% free). Only add LLM if data coverage is insufficient.
