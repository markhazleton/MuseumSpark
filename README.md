# MuseumSpark

A web application for ranking, documenting, and planning visits to all museums in the [Walker Art Reciprocal Program](https://walkerart.org/support/membership/reciprocal-membership/).

**Current Phase**: Phase 1 — Static Dataset Browser (GitHub Pages)  
**Status**: ~80% complete (see [Implementation Status](specs/001-museum-trip-planner/implementation-status.md))

---

## What is MuseumSpark?

MuseumSpark is a personal project to:
- **Discover** all 1,269+ museums in the Walker Art Reciprocal Program
- **Browse and search** museums by location, domain, reputation, and collection strength
- **Track progress** on dataset enrichment (FULL vs placeholder records)
- **Plan visits** with priority scoring for art museum enthusiasts

### Walker Art Reciprocal Program

The [Walker Art Reciprocal Program](https://walkerart.org/support/membership/reciprocal-membership/) provides Walker Art Center members with free or discounted admission to participating museums across North America. MuseumSpark helps members discover and plan visits to these institutions.

---

## Features (Phase 1)

### ✅ Implemented
- **Browse Museums**: Paginated list with 1,269+ museums
- **Search & Filter**: By name, state, city, domain, reputation, collection tier, time needed
- **Sort**: By priority score, name, reputation, or collection tier
- **Museum Details**: Drill down to full museum records with all metadata
- **Progress Dashboard**: Track dataset enrichment status (FULL vs placeholder)
- **Data Validation**: JSON Schema validation for all museum records

### 🚧 In Progress
- GitHub Pages deployment
- Dataset enrichment (currently 0.6% FULL)

### 📋 Planned (Phase 2+)
- User accounts and authentication
- Save favorites and visited museums
- Trip planning and itineraries
- AI-powered trip recommendations
- Admin CRUD for museum records

---

## Quick Start

### Prerequisites
- **Node.js 18+** (for site development)
- **Python 3.7+** (for data scripts)

### Running the Site Locally

```bash
# Navigate to site directory
cd site

# Install dependencies
npm install

# Run development server
npm run dev
```

Site will be available at http://localhost:5173

### Data Pipeline

```bash
# Install Python dependencies
pip install -r scripts/requirements.txt

# Validate dataset
python scripts/validate-json.py

# Rebuild master index
python scripts/build-index.py

# Generate progress report
python scripts/build-progress.py

# Run full Phase 1 pipeline
python scripts/run-phase1-pipeline.py --state CA --only-placeholders --limit 25
```

---

## Dataset Status (2026-01-15)
- **Total museums**: 1,269
- **FULL records**: 7 (0.6%)
- **Placeholder records**: 1,262 (99.4%)
- **States/provinces**: 52

See [DataSetDesign.md](Documentation/DataSetDesign.md) for complete data model.

---

## Documentation

- **[Application Architecture](Documentation/ApplicationArchitecture.md)** - System design and components
- **[Data Set Design](Documentation/DataSetDesign.md)** - Museum data model and scoring methodology
- **[Museum API](Documentation/MuseumAPI.md)** - API specification (Phase 2+)
- **[Phase 1 Spec](specs/001-museum-trip-planner/spec.md)** - Feature specification
- **[Phase 1 Plan](specs/001-museum-trip-planner/plan.md)** - Implementation plan
- **[Implementation Status](specs/001-museum-trip-planner/implementation-status.md)** - Current progress
- **[Scripts README](scripts/README.md)** - Data management scripts

---

## Technology Stack

**Phase 1 (Current)**:
- **Frontend**: React 18, Vite 5, Tailwind CSS 4, TypeScript 5
- **Data**: Static JSON files
- **Scripts**: Python 3.7+ with jsonschema, beautifulsoup4, pdfplumber
- **Hosting**: GitHub Pages (pending)

**Phase 2+ (Planned)**: FastAPI backend, SQLite, PydanticAI, Azure hosting

---

## Project Structure

```
MuseumSpark/
├── site/                   # React static site (Phase 1)
│   ├── src/pages/         # Browse, Progress, Museum Detail
│   ├── src/lib/           # API, types, FULL logic
│   └── public/data/       # Synced from ../data/
├── data/                   # Museum dataset (JSON)
│   ├── index/             # all-museums.json, progress.json
│   ├── states/            # Per-state museum records
│   └── schema/            # museum.schema.json
├── scripts/               # Data management (Python)
├── Documentation/         # Architecture and design docs
└── specs/                 # Feature specifications
```

See full structure in [Implementation Status](specs/001-museum-trip-planner/implementation-status.md).

---

## Roadmap

### Phase 1 (Current) - Static Browser
- [x] React site with browse/search/filter
- [x] Museum detail pages
- [x] Progress dashboard
- [x] Data validation pipeline
- [ ] GitHub Pages deployment
- [ ] Dataset enrichment (goal: 10-20% FULL)

### Phase 2 (Future) - Backend & Authentication
- [ ] FastAPI backend
- [ ] User accounts
- [ ] Save favorites and visited museums

### Phase 3 (Future) - Trip Planning
- [ ] Trip creation and management
- [ ] AI-powered recommendations

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **Walker Art Center** for the [Reciprocal Membership Program](https://walkerart.org/support/membership/reciprocal-membership/)
- Museum data from official websites, Wikidata, OpenStreetMap, and public sources

---

**Note**: MuseumSpark is an independent project and is not affiliated with or endorsed by Walker Art Center.
