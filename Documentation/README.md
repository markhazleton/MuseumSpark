# MuseumSpark Documentation

This folder contains the canonical documentation for MuseumSpark.

MuseumSpark's purpose is to **rank and document every museum in the Walker Art Reciprocal Program**, using the extracted seed roster in `data/index/walker-reciprocal.csv` and enriching it into complete museum records.

## Data Pipeline

The system uses a modular phase-based pipeline to enrich museum data:

1. **Phase 0**: Google Places API (identity, coordinates, phone, hours, ratings)
2. **Phase 0.5**: Wikidata enrichment (website, postal code, address)
3. **Phase 0.7**: Website scraping (hours, admission, accessibility)
4. **Phase 1**: Backbone fields (city_tier, time_needed, nearby_count)
5. **Phase 1.5**: Wikipedia enrichment (art museums)
6. **Phase 1.8**: CSV database lookup (IRS 990 data)
7. **Phase 2**: LLM scoring (reputation, collection_tier)
8. **Phase 1.75**: Heuristic fallback scoring
9. **Phase 3**: Priority scoring for trip planning

See `../scripts/README.md` for detailed pipeline documentation.

## Core Documentation

### Architecture & Design
- **[ApplicationArchitecture.md](ApplicationArchitecture.md)** - System design: React SPA + FastAPI + OpenAI API, deployment architecture
- **[MuseumAPI.md](MuseumAPI.md)** - API specification for museum browsing, search, and personalization
- **[DataSetDesign.md](DataSetDesign.md)** - Dataset schema, field definitions, scoring methodology

### Data Strategy
- **[DataEnrichmentStrategy.md](DataEnrichmentStrategy.md)** - Field-by-field enrichment approach and data sources
- **[AI-LLM-Enrichment-Plan.md](AI-LLM-Enrichment-Plan.md)** - LLM integration strategy for scoring and content generation
- **[MasterRequirements.md](MasterRequirements.md)** - Core requirements and specifications

### Data Quality
- **[DataQualityRule-NeverReplaceKnownWithNull.md](DataQualityRule-NeverReplaceKnownWithNull.md)** - Core data protection rule
- **[DataQualityRule-QuickReference.md](DataQualityRule-QuickReference.md)** - Quick reference for data quality rules

### Setup & Deployment
- **[API-Keys-Setup.md](API-Keys-Setup.md)** - Configuration guide for API keys
- **[GitHub-Pages-Setup.md](GitHub-Pages-Setup.md)** - GitHub Pages hosting setup
- **[GitHubPagesDeployment.md](GitHubPagesDeployment.md)** - Deployment process and workflow

### Reference
- **[Google-Places-Free-Tier-Impact.md](Google-Places-Free-Tier-Impact.md)** - Cost analysis for Google Places API
- **[Location-Extraction-Libraries.md](Location-Extraction-Libraries.md)** - Technical reference for geocoding
- **[Museum-Business-Data-APIs.md](Museum-Business-Data-APIs.md)** - Available data APIs and resources
- **[Home.md](Home.md)** - Documentation home page

## Quick Start

1. **Review Architecture**: Start with [ApplicationArchitecture.md](ApplicationArchitecture.md) to understand the system design
2. **Understand Data**: Read [DataSetDesign.md](DataSetDesign.md) for the dataset schema
3. **Configure APIs**: Follow [API-Keys-Setup.md](API-Keys-Setup.md) to set up required API keys
4. **Run Pipeline**: See `../scripts/README.md` for data enrichment pipeline usage
