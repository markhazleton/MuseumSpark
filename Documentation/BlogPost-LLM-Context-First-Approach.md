# Building MuseumSpark: Why Context Matters More Than the Latest LLM

## A Lesson from My Daughter

It started with a text from my daughter: "Dad, I ran out of ChatGPT tokens. Can I use your Pro account to finish this prompt?"

She was trying to build something ambitious: a complete, structured museum dataset with scoring and filtering capabilities for travel planning. Her vision was clear:

- A master list of all museums with consistent structure
- Normalized data: location, type, reputation, collection tier, visit time
- Expert scoring for art museums (Impressionist/Modern strength, historical context)
- Priority rankings where lower scores = better matches for her interests
- Sortable, searchable, decision-ready for efficient trip planning

Her approach? Ask ChatGPT to generate it all - the museums, the data, the scores, the structure. Process it state by state, city by city, alphabetically through all 50 states.

But after burning through her token limit somewhere around Arizona, she had:
- Incomplete museum lists (ChatGPT "hallucinating" museums or missing real ones)
- Inconsistent formatting (structure changed between states)
- Unverifiable data (no way to confirm if museums actually existed)
- Mixed scoring criteria (definitions drifted across conversations)
- No path to finish (hitting token limits with 47 states to go)

That text message became my wake-up call: **trying to extract structured, authoritative data from LLM conversations is fundamentally the wrong approach**.

Instead of giving her my Pro account credentials, I built MuseumSpark - a systematic pipeline that gathers museum data from authoritative sources (Google Places, Wikipedia, IRS 990 filings, museum websites) and *then* uses LLMs strategically for judgment and content generation.

The irony? She exhausted her ChatGPT quota trying to generate a museum dataset. I built a system that enriched 1,269 verified museums for $32 total, with data she could actually trust.

This is the story of how I learned that **success with LLMs isn't about having unlimited tokens or the latest model. It's about knowing when and how to use them.**

And yes - MuseumSpark produces exactly what she was trying to build: a sortable, scorable, travel-ready museum dataset. Just with a completely different architecture.

## The Failed First Attempt

When I started MuseumSpark, I made a classic mistake: I threw powerful LLMs at the problem and expected magic. Using GPT-4o and GPT-4o-mini, I asked the models to simultaneously:
- Research museum collections
- Evaluate art strengths
- Assign numerical scores
- Fill in missing data

The result? Hallucinations, inconsistencies, and the dreaded `impressionist_strength: null` responses I started seeing as `imp=?` in my outputs. Museums I knew had world-class impressionist collections were returning nulls. The models were refusing to score when they lacked "sufficient evidence" - even when that evidence existed on Wikipedia or the museum's own website.

**The fundamental flaw:** I was asking LLMs to be researchers AND judges at the same time, feeding them noisy, unstructured data and hoping they'd figure it out.

## The Wake-Up Call

After running my pipeline on Colorado (19 museums, 4.4 minutes, ~$1.14), I discovered a pattern:

```
Denver Art Museum: imp=? mod=?
Fort Collins MoCA: imp=3 mod=3 ✓
Boulder Museum: imp=? mod=?
```

Five out of seven museums were returning null scores. That's a 71% failure rate. For a dataset of 1,269 museums, this would mean over 900 museums with unusable scoring data.

The analysis was brutal but clarifying:
1. **Phase 2 (LLM Scoring) was doing too much** - asking models to research facts and make judgments simultaneously
2. **Context wasn't prioritized** - Wikipedia extracts, website content, and structured data weren't being gathered first
3. **Prompts were too strict** - "return null if insufficient evidence" caused models to give up rather than use their training
4. **No separation of concerns** - research, enrichment, and scoring were tangled together

## The Redo: Context First, Judge Second

I rebuilt the pipeline with one guiding principle: **Gather context first, then ask LLMs to judge.**

### The New Architecture: 10-Phase Modular Pipeline

```
Phase 0:   Google Places (identity, coordinates)
Phase 0.5: Wikidata (website, postal code, address)
Phase 0.7: Website Content (hours, admission, collections)
Phase 1:   Backbone (city tier, time needed, clustering)
Phase 1.5: Wikipedia Enrichment (for art museums)
Phase 1.8: CSV Database (IRS 990 data, phone numbers)
------- Context Gathered, Now Judge -------
Phase 2:   LLM Scoring (judgment only, NOT research)
Phase 2.5: Content Generation (web-ready descriptions)
Phase 3:   Priority Scoring (deterministic math)
Phase 4+:  Additional enrichment
```

**The key insight:** Phases 0-1.8 build a rich, curated evidence packet. Only after this foundation is solid do we invoke expensive LLM APIs in Phases 2 and 2.5.

### Building Evidence Packets for LLM Judgment

Instead of asking GPT-5.2 to "research and score this museum," I now give it:

```json
{
  "museum_name": "Art Institute of Chicago",
  "museum_type": "art",
  "wikipedia_extract": "...one of the oldest and largest art museums...",
  "wikipedia_categories": ["Impressionist museums", "Modern art museums"],
  "website_content": {
    "collections": ["French Impressionism", "Modern Art"],
    "hours": "10am-5pm daily",
    "admission": "$25 adults"
  },
  "context": "Located in Chicago, IL. 4 nearby art museums."
}
```

The prompt changed from:
> ❌ "Research this museum and assign scores. Return null if you lack evidence."

To:
> ✅ "You are a museum expert. Use your expert knowledge combined with the evidence provided to make informed assessments. Focus on permanent collections."

**Result:** The Art Institute now correctly returns `imp=4, mod=4` instead of null.

## The Caching Strategy That Saved the Budget

Here's where early architectural decisions paid off: **I made state JSON files the single source of truth from day one.**

Every museum lives in `data/states/{STATE}.json`. Every phase checks: "Does this museum already have the data I'm about to generate?" If yes, skip. If no, enrich.

```python
# Phase 2: LLM Scoring
def is_already_scored(museum: dict) -> bool:
    return any([
        museum.get("impressionist_strength") is not None,
        museum.get("modern_contemporary_strength") is not None,
    ])

if not force and is_already_scored(museum):
    print(f"SKIPPED (already scored)")
    continue
```

This simple pattern means:
- **Rerunning the pipeline costs $0** (unless you use `--force`)
- **Incremental improvements are free** - fix Phase 0.7, rerun, Phases 2-3 skip because data exists
- **Experimentation is cheap** - test prompt changes on one state, scale when confident

### The Cost Evolution

**First Attempt (GPT-4o/4o-mini):**
- No systematic caching
- Repeated API calls for same museums
- Estimated: $50-100 for test runs alone

**Redo V1 (All GPT-5.2):**
- Smart caching in place
- Phase 2: $25 (1,250 museums)
- Phase 2.5: $72.84 (1,214 museums)
- **Total: $97.84**

**Redo V2 (GPT-5.2 + gpt-5-nano):**
- Same caching strategy
- Phase 2: $25 (premium scoring for art museums)
- Phase 2.5: $1.14 art + $5.80 standard museums
- **Total: $31.94** (67% cost reduction!)

The caching strategy didn't just save money - it enabled rapid iteration. I could test prompt improvements, scoring algorithm changes, and data validation rules without re-spending API budget.

## The Analysis That Led to the Final Model

The turning point came when I ran a comprehensive status check across all 52 states:

```
Total Museums: 1,269
Phase 2 Cached: 19 museums ✓
Phase 2 Needed: 1,250 museums ($25)
Phase 2.5 Cached: 55 museums ✓  
Phase 2.5 Needed: 1,214 museums ($72.84 → $6.94 with gpt-5-nano)
```

This analysis revealed three critical insights:

### 1. Most Work Was Redundant
Phases 0.5 (Wikidata) and early phases showed `Updated: 0, Skipped: X` for almost every state. The infrastructure was working - data was cached and reusable.

### 2. LLM Phases Were the Bottleneck
- Phase 0.7 (Website): 304.9s for IL (30 museums) - slow but free
- Phase 2 (Scoring): 34.4s - fast but expensive
- Phase 2.5 (Content): 386.6s - **dominant cost AND time**

The data gathering was time-intensive but free. The LLM calls were fast but costly. This led to the decision: **optimize LLM costs with model selection** (gpt-5-nano for standard museums).

### 3. Separation of Concerns Was Working
Illinois showed the power of modular phases:
- Art Institute: `imp=4 mod=4` ✓ (from Wikipedia + evidence)
- Loyola LUMA: `imp=1 mod=1` ✓ (from sparse Wikipedia)
- 28 websites scraped successfully
- 30 content descriptions generated
- 6 priority scores calculated

Each phase built on the last. Failures in one phase (2 empty website responses) didn't cascade to later phases.

## The Final Model: A Reusable Pattern

What emerged isn't just a museum enrichment pipeline - it's a **reusable pattern for any LLM-powered data enrichment project**:

### 1. **Context Before Judgment**
Gather structured data (APIs, databases) and unstructured data (websites, Wikipedia) BEFORE asking LLMs to make decisions. LLMs are excellent judges when given good evidence, poor researchers when given vague instructions.

### 2. **Modular Phases with Clear Responsibilities**
- Phase 0-1: Identity and backbone (free APIs)
- Phase 1.5-1.8: Enrichment (web scraping, open data)
- Phase 2: Judgment (expensive LLMs, curated input)
- Phase 3+: Derivation (deterministic math, no API)

### 3. **Smart Caching as First-Class Citizen**
Not an afterthought - the core architecture. State JSON files as single source of truth. Every phase checks before enriching. Rerunning is free.

### 4. **Model Selection by Use Case**
- GPT-5.2: Premium judgments (art museum scoring, flagship content)
- gpt-5-nano: Standard tasks (general museum descriptions)
- Deterministic: Math that doesn't need LLMs (priority scoring)

### 5. **Validation Through Iteration**
- Small state (RI: 6 museums) - validate logic
- Medium state (CO: 19 museums) - test scale
- Large state (IL: 30 museums) - prove production-ready
- Full run (52 states, 1,269 museums) - confident execution

## The Results

**Illinois Test Run (30 Museums):**
```
Phase 0.7: 304.9s - 28 websites scraped
Phase 1.5: 9.3s - 10 art museums enriched
Phase 2: 34.4s - 10 art museums scored ($0.60)
Phase 2.5: 386.6s - 30 content generated ($1.80)
Phase 3: 0.1s - 6 priority scores (FREE)
Total: 12.4 minutes, $2.40
```

**Art Institute of Chicago:**
- Before: `imp=? mod=?` ❌
- After: `imp=4 mod=4, priority=7, quality=20` ✓
- Content: Rich 300-word description with markdown formatting
- Cost: $0.06 for premium content generation

**Scale Metrics:**
- **Time:** ~25 seconds per museum average
- **Cost:** $0.025 per museum ($31.94 for all 1,269)
- **Success Rate:** 95%+ (up from 29% in first attempt)
- **Rerun Cost:** $0 (cached data)

## Lessons Learned

### 1. **LLMs Are Judges, Not Researchers**
The biggest mistake was asking models to discover facts AND make judgments. Separate these concerns. Build evidence packets, then ask for judgment.

### 2. **Context Is Expensive to Gather But Free to Reuse**
Website scraping takes 10 seconds per museum. But run once, cache forever. Prioritize context gathering in early phases - the ROI compounds.

### 3. **Prompt Engineering Matters More Than Model Selection**
Changing from "return null if insufficient evidence" to "use expert knowledge with evidence" improved success rate more than upgrading from GPT-4o to GPT-5.2. Get the prompt right first, then optimize costs with model selection.

### 4. **Caching Enables Experimentation**
When rerunning costs nothing, you can iterate freely. Test phase improvements, validate scoring changes, refine prompts - all without budget anxiety.

### 5. **Modular Phases Beat Monolithic Scripts**
10 focused phases beat 1 mega-script. Each phase has clear input, output, and responsibility. Failures are isolated. Improvements are surgical.

## The Bigger Picture

MuseumSpark started as a trip planning tool. It became a case study in **context-first LLM architecture**.

The pattern works because it respects what LLMs do well (judgment with evidence) and what they struggle with (research from vague instructions). By gathering context first and caching aggressively, we built a system that:
- Costs $32 to enrich 1,269 museums
- Costs $0 to rerun with improvements
- Succeeds 95%+ of the time (vs 29% initially)
- Scales to any dataset size

The failed first attempt taught me more than immediate success would have. Sometimes you need to build the wrong thing to understand what the right thing looks like.

And in the age of rapidly evolving LLMs (GPT-5.2 launched while I was mid-project!), a modular architecture with smart caching isn't just nice to have - it's the only sustainable approach.

---

**Key Takeaways:**
1. ✅ Gather context before asking LLMs to judge
2. ✅ Design for caching from day one
3. ✅ Modular phases > monolithic scripts  
4. ✅ Prompt engineering > model selection (initially)
5. ✅ Validate incrementally (small → medium → large → full)
6. ✅ LLMs are judges, not researchers

**Pipeline Running Now:**
As I write this, the complete enrichment pipeline is processing all 1,269 museums. Phases 0-1.8 are gathering context (free). Phases 2-2.5 will make ~1,200 LLM calls ($32 total). And if I need to rerun tomorrow? $0.

That's the power of context-first architecture.

---

*MuseumSpark is open source: [github.com/MarkHazleton/MuseumSpark](https://github.com/MarkHazleton/MuseumSpark)*
