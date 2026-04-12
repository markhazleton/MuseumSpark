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

This is an early-stage project with comprehensive design documentation but no implemented code yet. The project uses a specification-driven development approach with the DevSpark workflow.

## Development Workflow

This project uses **DevSpark** for specification-driven development. DevSpark commands are available as skills:

- `DevSpark.specify` - Create or update feature specifications
- `DevSpark.clarify` - Identify underspecified areas and ask clarification questions
- `DevSpark.plan` - Execute implementation planning workflow
- `DevSpark.tasks` - Generate actionable, dependency-ordered tasks
- `DevSpark.implement` - Execute implementation based on tasks
- `DevSpark.analyze` - Cross-artifact consistency and quality analysis
- `DevSpark.checklist` - Generate custom checklists for features
- `DevSpark.taskstoissues` - Convert tasks to GitHub issues

The typical workflow is: Specify → Clarify → Plan → Tasks → Implement → Analyze

Templates for specifications, plans, tasks, and checklists are located in `.devspark/templates/`.

## Architecture Design

### Data Model

The core entity is a **Museum** record with the following key components:

**Core Identity**: Country, State/Province, City, Museum Name, Museum Type

**Travel Planning**: Time Needed (Quick stop / Half day / Most of the Day / All Day), Nearby Museum Count

**Reputation & Scope**: Reputation Level (Local / Supra-Local / Regional / National / International), Collection Level (Small / Moderate / Strong / Flagship)

**Collection Focus**: Impressionist Strength, Modern/Contemporary Strength, Historical Art Traditions (HAT) Strength, Historical Context Score (0-5), ECA (0-5), Collection-Based Strength (0-5)

**Computed Metrics**: Collection-Based PAS, Effective PAS, Priority Score (lower = higher priority), Outcome Tier (Must-See → Background)

Full data model specification is in `Documentation/DataSetDesign.md`.

### Prioritization Algorithm (MRD v3.1.T)

The priority score formula uses a PAS (Primary Art Strength) model:

```
Collection-Based PAS = MAX(impressionist_strength, modern_contemporary_strength, hat_strength)
Effective PAS        = MAX(Collection-Based PAS, eca_score)
Dual-Strength Bonus  = -2 if impressionist >= 3 AND modern_contemporary >= 3

Reputation Penalty: International/National=0, Regional=+2, Supra-Local=+3, Local=+4
Collection Penalty: Flagship/Strong=0, Moderate=+2, Small=+4

Priority Score = MAX(1,
    (6 - Effective PAS) × 2
  + (6 - Historical Context Score)
  + Reputation Penalty
  + Collection Penalty
  + Dual-Strength Bonus
)
```

Outcome Tier is assigned deterministically (Must-See / High Priority / Regionally Important / Detour / Consider / Background).

Full specification: `Documentation/architecture/MasterRequirements.md` (authoritative), `Documentation/architecture/DataSetDesign.md`.

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

1. Use DevSpark workflow to create detailed specifications before coding
2. Reference the data model in `Documentation/DataSetDesign.md` for entity design
3. Follow the API schema in `Documentation/MuseumAPI.md` for endpoint implementation
4. Ensure the priority scoring algorithm is implemented exactly as specified
5. Plan for both U.S. and international museum data from the start
