# MuseumSpark Documentation

This folder contains the canonical documentation for MuseumSpark.

MuseumSpark's purpose is to **rank and document every museum in the Walker Art Reciprocal Program**, using the extracted seed roster in `data/index/walker-reciprocal.csv` and enriching it into complete museum records.

## 📂 Documentation Structure

Documentation is organized into four main areas:

- **[architecture/](architecture/)** - System design, API specs, data models
- **[data-pipeline/](data-pipeline/)** - Enrichment strategies, LLM integration, quality rules
- **[setup-deployment/](setup-deployment/)** - Configuration and deployment guides  
- **[reference/](reference/)** - Technical references and requirements

## 🏠 Start Here

**[→ Browse the full documentation index at Home.md](Home.md)**

The Home.md provides:
- Complete index of all documentation organized by area
- Quick start paths for developers, data contributors, and deployers
- Current system overview
- Links to related documentation

## 🚀 Quick Links

### Essential Documents
- **System Design**: [architecture/ApplicationArchitecture.md](architecture/ApplicationArchitecture.md)
- **API Specification**: [architecture/MuseumAPI.md](architecture/MuseumAPI.md)
- **Dataset Schema**: [architecture/DataSetDesign.md](architecture/DataSetDesign.md)

### Getting Started
- **Setup Guide**: [setup-deployment/API-Keys-Setup.md](setup-deployment/API-Keys-Setup.md)
- **Pipeline Guide**: [../scripts/README.md](../scripts/README.md)
- **Enrichment Strategy**: [data-pipeline/DataEnrichmentStrategy.md](data-pipeline/DataEnrichmentStrategy.md)

## 📊 Data Pipeline Overview

The system uses a 9-phase modular pipeline:

1. **Phase 0**: Google Places API (identity, coordinates, phone, hours, ratings)
2. **Phase 0.5**: Wikidata enrichment (website, postal code, address)
3. **Phase 0.7**: Website scraping (hours, admission, accessibility)
4. **Phase 1**: Backbone fields (city_tier, time_needed, nearby_count)
5. **Phase 1.5**: Wikipedia enrichment (art museums)
6. **Phase 1.8**: CSV database lookup (IRS 990 data)
7. **Phase 2**: LLM scoring (reputation, collection_tier)
8. **Phase 1.75**: Heuristic fallback scoring
9. **Phase 3**: Priority scoring for trip planning

See [../scripts/README.md](../scripts/README.md) for detailed pipeline documentation.

---

For the complete documentation index and navigation guide, visit **[Home.md](Home.md)**
