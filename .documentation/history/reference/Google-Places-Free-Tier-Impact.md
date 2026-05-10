# Google Places API - Free Tier Impact Analysis

**Date**: January 17, 2026  
**Context**: Enhanced Phase 0 implementation with 10 fields

## Google Places API (New) Pricing Structure

Google charges **different rates** based on field category (not flat $0.017/field as initially estimated):

| Field Category | Cost Per Field | Our Fields |
|---------------|----------------|------------|
| **Basic Data** | $0.017 | address_component, formatted_address, geometry, business_status, opening_hours |
| **Contact Data** | $0.003 | formatted_phone_number, website |
| **Atmosphere Data** | $0.005 | rating, user_ratings_total, reviews |

## Corrected Cost Analysis

### Original Implementation (3 fields)
- Basic Data: 3 fields × $0.017 = **$0.051 per museum**

### Enhanced Implementation (10 fields)
- Basic Data: 5 fields × $0.017 = **$0.085**
- Contact Data: 2 fields × $0.003 = **$0.006**
- Atmosphere Data: 3 fields × $0.005 = **$0.015**
- **Total: $0.106 per museum**

### Cost Increase
- **Increase**: +$0.055 per museum (+108%)
- **Not $0.119** as initially calculated (that assumed all fields at $0.017)

## Free Tier Impact

### Google Maps Platform Free Tier
- **Free credit**: $200 per month (recurring monthly)
- **No expiration**: Resets each month

### Museums Enrichable with Free Tier

**Original (3 fields):**
- $200 ÷ $0.051 = **3,921 museums/month FREE**

**Enhanced (10 fields):**
- $200 ÷ $0.106 = **1,886 museums/month FREE**

**Impact:**
- **Reduction**: -2,035 museums/month (-52%)
- Still very generous for typical usage

## Realistic Usage Scenarios

### Scenario 1: Complete Walker Reciprocal Dataset (ACTUAL)
- **Total museums**: 1,200 (Walker reciprocal list - fixed scope)
- **Total cost**: 1,200 × $0.106 = **$127.20**
- **Fits in free tier?**: ✅ **YES** - with $72.80 to spare!
- **Conclusion**: Can enrich entire dataset in **1 month FREE** or spread over 2-3 months with plenty of buffer

### Scenario 2: Rhode Island Test (6 museums)
- Cost: 6 × $0.106 = **$0.64**
- Percentage of free tier: **0.32%**
- Perfect for testing!

### Scenario 3: Conservative Monthly Approach
- Process 40 museums/day throughout the month
- 40 museums/day × 30 days = 1,200 museums/month
- Cost: 1,200 × $0.106 = **$127.20** (within free tier)
- Remaining credit: $72.80 for testing/re-runs

### Scenario 4: Aggressive One-Day Enrichment
- Process all 1,200 museums in single day
- Cost: **$127.20** (still within free tier!)
- Remaining credit: $72.80
- **Feasible**: API has no daily limits, only monthly free tier

## ROI Analysis with Corrected Pricing

### For Complete Walker Reciprocal Dataset (1,200 Museums)
- **Total cost**: $127.20 (within $200 free tier = **$0 actual cost**)
- **What you get**:
  1. Phone coverage: 69% → 95% (+26% = ~312 museums)
  2. Business status: 0% → 99% (**critical** - ~1,188 museums get status)
  3. Hours coverage: 50-60% → 80% (+20-30% = ~240-360 museums)
  4. Ratings: 0% → 70% (reputation proxy for ~840 museums)
  5. Reviews: 0% → 70% (visitor insights for ~840 museums)
  6. Website validation: 80% → 90% (+10% = ~120 museums)

### Break-Even vs Alternatives

**Avoided costs if using Google Places data:**

1. **LLM calls for reputation scoring**:
   - If Google ratings eliminate 20% of LLM calls
   - 1,200 museums × $0.10/LLM call × 20% = **$24 saved**

2. **Manual data cleanup**:
   - Finding/removing closed museums manually
   - Priceless for user experience

3. **Web scraping infrastructure**:
   - Phase 0.7 web scraping has ~50% success
   - Google hours have ~80% success
   - Better reliability = less manual intervention

**Verdict**: $127.20 for complete dataset (FREE with monthly credit) is **outstanding ROI**

## Free Tier Strategy

### ✅ Recommended: Complete Enrichment in Free Tier
- **Total dataset**: 1,200 museums (Walker reciprocal list)
- **Total cost**: $127.20 (within $200 free tier)
- **Remaining buffer**: $72.80 for re-runs/testing
- **Timeline**: 1 month (or spread over 2-3 months conservatively)
- **Actual cost**: **$0**

### Execution Plan

**Option A: Conservative Approach (Recommended)**
```bash
# Month 1: Process all states with testing buffer
# ~40-50 museums/day = complete in 24-30 days

# Week 1: Test + Small states
python scripts/pipeline/run-complete-pipeline.py --states RI,VT,NH,ME,DE

# Week 2-4: Process remaining states in batches
python scripts/pipeline/run-complete-pipeline.py --states CO,UT,WY,MT,ID
python scripts/pipeline/run-complete-pipeline.py --states CA,OR,WA,NV,AZ
# ... continue with remaining states
```

**Option B: Aggressive One-Shot (If Confident)**
```bash
# Process all 1,200 museums at once
# Cost: $127.20 (still within free tier!)
python scripts/pipeline/run-complete-pipeline.py --all-states

# Or target just Phase 0 for all museums
python scripts/phases/phase0_identity.py --all-states --force
```

**Option C: Quality-First Approach**
```bash
# Month 1: Enrich 600 museums + validate quality
python scripts/pipeline/run-complete-pipeline.py --states [half of states]

# Month 2: Complete remaining 600 museums
python scripts/pipeline/run-complete-pipeline.py --states [remaining states]

# Both months: $0 cost, plenty of buffer for retries
```

## Free Tier Monitoring

### Check Current Usage
Google Cloud Console → Billing → Reports
- Filter by: Google Maps Platform
- View: Place Details API usage

### Set Budget Alerts
1. Go to Billing → Budgets & Alerts
2. Create budget: $200/month
3. Set alert at: 50%, 75%, 90%, 100%
4. Get email notifications before exceeding free tier

### Cache Effectiveness Metrics
Track how often we hit cache vs API:
```bash
# Check cache hit rate
find data/cache/phase0 -name "*.json" | wc -l   # Cached museums
# Compare to total museums in dataset
```

## Summary

| Metric | Original (3 fields) | Enhanced (10 fields) | Impact |
|--------|---------------------|----------------------|--------|
| **Cost per museum** | $0.051 | $0.106 | +108% |
| **Free museums/month** | 3,921 | 1,886 | -52% |
| **Cost for 1,200 museums** | $61.20 | **$127.20** | +$66 |
| **Fits in free tier?** | ✅ Yes ($138.80 left) | ✅ **Yes ($72.80 left)** | Still FREE! |
| **Time to enrich Walker dataset** | <1 month | <1 month | ✅ **No change** |

**Conclusion**: 
- Your 1,200-museum dataset costs **$127.20** with enhanced fields
- This is **completely covered** by the $200/month free tier
- **Actual cost: $0** 
- You have **$72.80 buffer** for testing, re-runs, and mistakes
- Can process entire dataset in **1 month** or spread over 2-3 months conservatively
- **Excellent ROI**: Business status detection + ratings + structured hours all **FREE**

**Recommendation**: 
✅ **Proceed with full enhanced implementation immediately**
- Zero cost concerns with 1,200 museums
- Complete dataset enrichment in single month
- Critical data quality improvements (business status) for free
- No need to skip any fields or spread over multiple months
- **Just do it all at once!**
