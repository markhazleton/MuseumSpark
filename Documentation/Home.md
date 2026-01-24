# MuseumSpark Documentation Home

Welcome to the MuseumSpark documentation. This documentation covers the complete system for ranking and documenting every museum in the Walker Art Reciprocal Program.

## 📚 Documentation Organization

### 🏗️ [Architecture](architecture/)
System design, API specifications, and data models

- **[Application Architecture](architecture/ApplicationArchitecture.md)** - Complete system design including React SPA, FastAPI backend, deployment architecture, and technology stack
- **[Museum API Specification](architecture/MuseumAPI.md)** - RESTful API endpoints for museum browsing, search, personalization, and trip planning
- **[Dataset Design](architecture/DataSetDesign.md)** - Museum dataset schema, field definitions, scoring methodology, and data quality requirements

### 🔄 [Data Pipeline](data-pipeline/)
Data enrichment strategies, LLM integration, and quality rules

- **[Data Enrichment Strategy](data-pipeline/DataEnrichmentStrategy.md)** - Comprehensive field-by-field enrichment approach prioritizing open data sources
- **[AI/LLM Enrichment Plan](data-pipeline/AI-LLM-Enrichment-Plan.md)** - Strategy for using Large Language Models for scoring, content generation, and data enhancement
- **[Data Quality Rule: Never Replace Known With Null](data-pipeline/DataQualityRule-NeverReplaceKnownWithNull.md)** - Core data protection rule preventing data loss during enrichment
- **[Data Quality Rules Quick Reference](data-pipeline/DataQualityRule-QuickReference.md)** - Quick reference guide for all data quality rules and patterns

### ⚙️ [Setup & Deployment](setup-deployment/)
Configuration guides and deployment procedures

- **[API Keys Setup](setup-deployment/API-Keys-Setup.md)** - Configuration guide for Google Places API, OpenAI API, and other required services
- **[GitHub Pages Setup](setup-deployment/GitHub-Pages-Setup.md)** - Instructions for hosting the static React site on GitHub Pages
- **[GitHub Pages Deployment](setup-deployment/GitHubPagesDeployment.md)** - Detailed deployment process and CI/CD workflow

### 📖 [Reference](reference/)
Technical references, API documentation, and requirements

- **[Master Requirements](reference/MasterRequirements.md)** - Complete project requirements, scope, and specifications
- **[Google Places Free Tier Impact](reference/Google-Places-Free-Tier-Impact.md)** - Cost analysis and optimization strategies for Google Places API usage
- **[Location Extraction Libraries](reference/Location-Extraction-Libraries.md)** - Technical reference for geocoding libraries and address parsing
- **[Museum Business Data APIs](reference/Museum-Business-Data-APIs.md)** - Available external APIs and data sources for museum information

### 🤖 [Copilot](copilot/)
GitHub Copilot instructions and session documentation

- **[GitHub Copilot Instructions](copilot-instructions.md)** - Comprehensive Copilot guidance integrating SpecKit constitution and repository patterns
- **[Copilot Documentation](copilot/)** - Session notes and copilot-generated exploratory documentation

## 🚀 Quick Start Paths

### For New Developers
1. Start with [Application Architecture](architecture/ApplicationArchitecture.md) to understand the system design
2. Review [Dataset Design](architecture/DataSetDesign.md) to understand the data model
3. Follow [API Keys Setup](setup-deployment/API-Keys-Setup.md) to configure your environment
4. Check the [scripts/README.md](../scripts/README.md) for pipeline usage

### For Data Contributors
1. Read [Data Enrichment Strategy](data-pipeline/DataEnrichmentStrategy.md) to understand the enrichment approach
2. Review [Data Quality Rules](data-pipeline/DataQualityRule-QuickReference.md) to ensure data integrity
3. See [AI/LLM Enrichment Plan](data-pipeline/AI-LLM-Enrichment-Plan.md) for LLM-based enrichment

### For Deployers
1. Follow [GitHub Pages Setup](setup-deployment/GitHub-Pages-Setup.md) for initial deployment
2. Review [GitHub Pages Deployment](setup-deployment/GitHubPagesDeployment.md) for the deployment workflow
3. Check [API Keys Setup](setup-deployment/API-Keys-Setup.md) for required configurations

### For AI-Assisted Development
1. Review [GitHub Copilot Instructions](copilot-instructions.md) for constitutional principles and best practices
2. Check [SpecKit Constitution](../.specify/memory/constitution.md) for non-negotiable requirements
3. See [CLAUDE.md](../CLAUDE.md) for runtime development guidance

## 🔗 Related Documentation

- **[Scripts README](../scripts/README.md)** - Data enrichment pipeline documentation
- **[Site README](../site/README.md)** - React frontend application documentation
- **[Project README](../README.md)** - Main project overview

## 📋 Current System Overview

**Data Pipeline**: 9-phase modular enrichment pipeline
1. Phase 0: Google Places API (identity, coordinates, phone, hours, ratings)
2. Phase 0.5: Wikidata enrichment (website, postal code, address)
3. Phase 0.7: Website scraping (hours, admission, accessibility)
4. Phase 1: Backbone fields (city_tier, time_needed, nearby_count)
5. Phase 1.5: Wikipedia enrichment (art museums)
6. Phase 1.8: CSV database lookup (IRS 990 data)
7. Phase 2: LLM scoring (reputation, collection_tier)
8. Phase 1.75: Heuristic fallback scoring
9. Phase 3: Priority scoring for trip planning

**Frontend**: React SPA with Vite, Tailwind CSS, TypeScript
**Backend** (Future): FastAPI with PydanticAI agents
**Deployment**: GitHub Pages (static) → Azure VM (full-stack future)

## 📝 Documentation Standards

All documentation in this folder follows these principles:
- **Accuracy**: Reflects the current state of the codebase
- **Clarity**: Written for developers familiar with the tech stack
- **Conciseness**: Focused on "what" and "why" without historical context
- **Currency**: Updated when corresponding code changes

---

*Last updated: January 24, 2026*
