# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MuseumSpark is a Museum Trip Planning Application designed to help **Walker Art Reciprocal Program members** rank, document, and plan visits to **every museum in the reciprocal program**. The application enables filtering, sorting, and evaluating reciprocal museums based on collection relevance, cultural significance, and visit practicality.

The authoritative seed roster is stored in `data/index/walker-reciprocal.csv` (extracted from Walker’s reciprocal membership page). MuseumSpark enriches these rows into complete museum records matching the schema and API.

## Dataset Workflow

1. Validate `data/index/walker-reciprocal.csv`
2. Add all museums to `data/index/all-museums.json` (master list)
3. Add museums by state to `data/states/{state}.json` and enrich each record until complete

## Current Project Status

This is an early-stage project with comprehensive design documentation but no implemented code yet. The project uses a specification-driven development approach with the Speckit workflow.

## Development Workflow

This project uses **Speckit** for specification-driven development. Speckit commands are available as skills:

- `speckit.specify` - Create or update feature specifications
- `speckit.clarify` - Identify underspecified areas and ask clarification questions
- `speckit.plan` - Execute implementation planning workflow
- `speckit.tasks` - Generate actionable, dependency-ordered tasks
- `speckit.implement` - Execute implementation based on tasks
- `speckit.analyze` - Cross-artifact consistency and quality analysis
- `speckit.checklist` - Generate custom checklists for features
- `speckit.taskstoissues` - Convert tasks to GitHub issues

The typical workflow is: Specify → Clarify → Plan → Tasks → Implement → Analyze

Templates for specifications, plans, tasks, and checklists are located in `.specify/templates/`.

## Architecture Design

### Data Model

The core entity is a **Museum** record with the following key components:

**Core Identity**: Country, State/Province, City, Museum Name, Museum Type

**Travel Planning**: Time Needed (Quick stop/Half day/Full day), Nearby Museum Count

**Reputation & Scope**: Reputation tier (Local/Regional/National/International), Collection Tier (Small/Moderate/Strong/Flagship)

**Collection Focus**: Impressionism Strength, Contemporary/Modern Strength, Primary Art Focus, Historical Context Score (1-5)

**Computed Metrics**: Priority Score (lower = higher priority)

Full data model specification is in `Documentation/DataSetDesign.md`.

### Prioritization Algorithm

The priority score formula weights multiple factors to rank museums:

```
Priority Score =
  (10 - Impressionism Weight × 3)
  × (10 - Modern/Contemporary Weight × 3)
  × (5 - Historical Context Score × 2)
  × (5 - Reputation Score)
  × (5 - Collection Tier Score)
  - Dual Collection Bonus
  - Nearby Cluster Bonus
```

This ensures high-value institutions rank highest while revealing hidden gems with relevant strengths.

### API Design

RESTful API specification is defined in `Documentation/MuseumAPI.md` with:

- Base resource: `/museums`
- Full CRUD operations (GET, POST, PUT, PATCH, DELETE)
- Query filtering by location, type, reputation, collection tier, and priority score
- JWT bearer token authentication (OAuth2-style) with role-based access (admin/editor/viewer)
- JSON format with pagination support

## Key Design Decisions

1. **Dataset Scope**: All museums in the Walker Art Reciprocal Program (seeded from `data/index/walker-reciprocal.csv`)
2. **Geographic Focus**: Wherever the reciprocal program includes members (US + international)
3. **Modular Structure**: Enrich records progressively; keep source roster and derived data rebuildable
4. **Data Validation**: Manual verification and cross-validation for consistency
5. **Travel Integration**: Time estimates, cluster analysis, and practical visit planning metadata

## Documentation

- `Documentation/DataSetDesign.md` - Complete dataset structure, scoring methodology, and field definitions
- `Documentation/MuseumAPI.md` - Canonical REST API specification (dataset + personalization + admin)
- `Documentation/MusuemAPI.md` - Deprecated stub kept for backwards compatibility
- `Documentation/MuseumSpark_ React + ChatGPT-Powered Trip Planner on Azure.pdf` - Original project concept (historical source; older naming)
- `Documentation/MuseumSpark_ Deployment and Architecture Plan.pdf` - Deployment architecture

## Technology Stack

The technology stack has not yet been implemented. When implementing, consider:

- Frontend: React-based trip planner interface
- Backend: RESTful API service
- AI Integration: OpenAI API integration (ChatGPT-class models) for conversational discovery
- Deployment: Azure cloud infrastructure
- Authentication: JWT bearer tokens (OAuth2-style)

## Getting Started with Development

Since this is a greenfield project:

1. Use Speckit workflow to create detailed specifications before coding
2. Reference the data model in `Documentation/DataSetDesign.md` for entity design
3. Follow the API schema in `Documentation/MuseumAPI.md` for endpoint implementation
4. Ensure the priority scoring algorithm is implemented exactly as specified
5. Plan for both U.S. and international museum data from the start
