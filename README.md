# MuseumSpark 🏛️

> **The strategic travel planner for art lovers.**  
> Curate, prioritize, and optimize your museum visits across North America.

![Status](https://img.shields.io/badge/Status-Active_Development-brightgreen)
![Phase](https://img.shields.io/badge/Phase-1_Data_Enrichment-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Dataset](https://img.shields.io/badge/Museums-1,269_Tracked-purple)
![Data Quality](https://img.shields.io/badge/Enriched-0.08%25-orange)

**Live Site**: [https://museum.makeboldspark.com/](https://museum.makeboldspark.com/)

---

## 🎨 About MuseumSpark

**MuseumSpark** transforms the [Walker Art Center Reciprocal Program](https://walkerart.org/support/membership/reciprocal-membership/) membership list into an intelligent, data-rich travel planning resource for art enthusiasts.

### The Vision

Rather than a simple directory, MuseumSpark provides:

- **Priority Scoring**: Rank museums by artistic strength (Impressionist & Modern/Contemporary collections), historical context, and reputation
- **Smart Travel Planning**: City tier classification, visit duration estimates, and nearby museum clustering
- **Data Enrichment**: Multi-source pipeline combining Wikidata, Wikipedia, museum websites, and structured data extraction
- **Personalized Experience**: (Coming Phase 4) Save favorites, track visits, generate custom itineraries with AI assistance

Whether planning a 2-hour layover or a weekend art tour, MuseumSpark helps you discover the right museums for your interests and time constraints.

> Built by [Mark Hazleton](https://markhazleton.com) — Mark Hazleton, Solutions Architect
> MuseumSpark is part of the [Make Bold Spark](https://makeboldspark.com) portfolio of technical demonstrations.

---

## ✨ Current Features

### 🔍 Comprehensive Museum Browser
- **1,269 museums** from the Walker Art Reciprocal Program
- Browse by state/province, search by name, filter by attributes
- Detailed museum pages with contact info, hours, and enrichment data

### 📊 Data Quality Dashboard
- Real-time progress tracking of dataset enrichment
- State-by-state completeness metrics
- Transparency on data source and validation status

### 🛠️ Multi-Phase Enrichment Pipeline
**Phase 0**: Identity verification (Wikidata, website validation)  
**Phase 0.5**: Wikidata structured data extraction  
**Phase 0.7**: Official website metadata harvesting  
**Phase 1**: Backbone data (address, city tier, museum type)  
**Phase 1.5**: Wikipedia article extraction  
**Phase 1.75**: Heuristic fallback for missing data  
**Phase 1.8**: CSV lookup integration  
**Phase 1.9**: Museum planner metadata (product owner scores & notes)  
**Phase 2**: Expert scoring (collections, historical context)  
**Phase 2.5**: Rich content extraction  
**Phase 3**: Priority score calculation

### 🔐 Data Quality Assurance
- JSON Schema validation for all museum records
- Automated quality checks and evidence tracking
- "Never Replace Known With Null" data quality rule enforcement

---

## 🗺️ Development Roadmap

### ✅ Phase 0–1: Data Foundation (Current Phase — 80% Complete)
**Status**: Active development  
**Progress**: 1 of 1,269 museums fully enriched (0.08%)

**Completed**:
- ✅ React + Vite static site with browse/search/filter functionality
- ✅ Museum detail pages with state file drill-down
- ✅ Progress dashboard tracking enrichment status
- ✅ JSON Schema validation pipeline
- ✅ Multi-phase data enrichment architecture
- ✅ Wikidata, Wikipedia, and website scraping infrastructure
- ✅ Walker Art Reciprocal roster ingestion and indexing

**In Progress**:
- 🔄 Dataset enrichment (continuing Phase 0–1.8 pipeline runs)
- 🔄 GitHub Pages deployment configuration

**Next Steps**:
- Scale enrichment runs to complete remaining 1,268 museums
- Implement caching strategies for external API calls
- Begin Phase 2 scoring for art-focused museums

---

### 🧠 Phase 2: Expert Scoring (Planned Q2 2026)
**Goal**: Assign priority scores to art museums based on collection strength

**Key Activities**:
- Define scoring rubric for Impressionist and Modern/Contemporary collections
- Expert review of major museums (Tier 1 cities first)
- Historical context quality assessment
- Reputation and collection tier classification

---

### 🤖 Phase 2.5–3: AI-Assisted Content & Validation (Planned Q3 2026)
**Goal**: Leverage LLMs for deeper museum analysis

**Approach**:
- Claude/OpenAI agents to analyze museum websites for collection depth
- Automated extraction of signature artists, special exhibitions
- Quality validation and expert auditing of AI-generated scores

---

### 🚀 Phase 4: Interactive Platform (Planned Q4 2026)
**Goal**: Full-featured travel companion with personalization

**Features**:
- FastAPI backend with user authentication
- Save favorites and track visited museums
- Trip planning and itinerary generation
- AI travel agent for personalized recommendations
- SQLite persistence for user data

---

## 🛠️ Technology Stack

### Frontend
- **React 19** - Modern UI library
- **Vite 7** - Lightning-fast build tool
- **Tailwind CSS 4** - Utility-first styling
- **React Router 7** - Client-side routing

### Data Pipeline
- **Python 3.11+** - Core scripting language
- **Pydantic 2** - Data validation and schema management
- **JSON Schema** - Dataset validation framework
- **BeautifulSoup4** - HTML parsing and web scraping
- **html2text** - Clean markdown conversion for LLM input

### Data Sources
- **Wikidata** - Structured museum metadata
- **Wikipedia** - Article content and cultural context
- **Museum Websites** - Official hours, addresses, descriptions
- **Walker Art Center** - Reciprocal membership roster

### Future Backend (Phase 4)
- **FastAPI** - Modern Python API framework
- **SQLite** - Embedded database for user data
- **PydanticAI** - Structured LLM interactions
- **OpenAI/Anthropic** - AI-powered content generation

### Deployment
- **Phase 1**: GitHub Pages (static hosting)
- **Phase 4**: Azure Windows Server VM (self-hosted)

---

## 🚀 Getting Started

### Prerequisites
- **Node.js 18+** (for the website)
- **Python 3.11+** (for data scripts)
- **Git** (for version control)

### Quick Start

#### 1. Clone the Repository
```bash
git clone https://github.com/MakeBoldSolutions/MuseumSpark.git
cd MuseumSpark
```

#### 2. Run the Website Locally
```bash
cd site
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) to view the app.

The site will automatically sync data from `data/` to `site/public/data/` on startup.

#### 3. Work with Data Scripts (Optional)

**Windows (PowerShell)**:
```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r scripts\requirements.txt

# Validate dataset
python scripts\validation\validate-json.py

# Build indices
python scripts\builders\build-index.py
python scripts\builders\build-progress.py

# Run enrichment pipeline
python scripts\pipeline\run-complete-pipeline.py
```

**macOS/Linux**:
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r scripts/requirements.txt

# Validate dataset
python scripts/validation/validate-json.py

# Build indices
python scripts/builders/build-index.py
```

---

## 📂 Project Structure

```
MuseumSpark/
├── .github/              # GitHub configuration
├── data/                 # Museum dataset (single source of truth)
│   ├── archive/          # Historical data and old test runs
│   │   ├── old_runs_20260116-20260117/  # Archived test runs
│   │   └── temp_files_archive/          # Archived temp files
│   ├── cache/            # Runtime caches (gitignored)
│   │   ├── http/         # HTTP response cache
│   │   ├── wikidata/     # Wikidata query cache
│   │   ├── wikipedia_population/  # Wikipedia data cache
│   │   ├── open-data/    # OpenStreetMap cache
│   │   ├── phase0/       # Phase 0 enrichment cache
│   │   └── phase2/       # Phase 2 enrichment cache
│   ├── index/            # Generated indices for the app
│   │   ├── all-museums.json         # Master museum list
│   │   ├── all-museums-enriched.json  # Enriched master list
│   │   ├── progress.json             # Enrichment progress
│   │   ├── missing-report.json       # Data gap analysis
│   │   ├── tour-planning-scores.json # Priority scores
│   │   └── walker-reciprocal.csv     # Original roster
│   ├── runs/             # Pipeline run outputs (gitignored)
│   ├── schema/           # JSON Schema definitions
│   │   └── museum.schema.json
│   └── states/           # Per-state museum records (canonical)
│       ├── alabama.json
│       ├── alaska.json
│       └── ... (58 states/provinces/territories)
├── .documentation/       # Unified AI/user docs + DevSpark overrides
│   ├── history/          # Migrated legacy product/user-facing docs
│   ├── memory/           # Constitution and governance memory
│   ├── commands/         # DevSpark command overrides
│   ├── releases/         # Release artifacts
│   └── ...
├── scripts/              # Python data pipeline
│   ├── builders/         # Index building scripts
│   ├── phases/           # Enrichment phase implementations
│   ├── pipeline/         # Pipeline orchestration
│   ├── validation/       # Data validation tools
│   ├── analyze_*.py      # Analysis scripts
│   └── requirements.txt  # Python dependencies
├── site/                 # React frontend application
│   ├── public/           # Static assets
│   ├── scripts/          # Build scripts (data sync)
│   ├── src/              # React source code
│   │   ├── components/   # UI components
│   │   ├── pages/        # Route pages
│   │   └── App.jsx       # Main app component
│   ├── package.json
│   └── vite.config.ts
├── specs/                # Feature specifications
│   └── 001-museum-trip-planner/
├── CLEANUP.md            # Maintenance and cleanup guide
├── CLAUDE.md             # AI assistant context document
├── LICENSE               # MIT License
└── README.md             # This file
```

---

## 📊 Dataset Overview

### Current Status (as of January 18, 2026)
- **Total Museums**: 1,269
- **Fully Enriched**: 1 (0.08%)
- **Placeholder Records**: 1,268 (99.92%)

### Geographic Coverage
Museums across **58 jurisdictions**:
- **United States**: 50 states + DC + Puerto Rico
- **Canada**: All provinces and territories
- **International**: Bermuda, Mexico

### Data Quality Levels
- **FULL**: Complete enrichment with all required fields validated
- **PLACEHOLDER**: Basic name/state only; awaiting enrichment

### Enrichment Pipeline Phases
Each museum progresses through 10+ enrichment phases:
- **Phase 0**: Identity & website validation
- **Phase 0.5**: Wikidata integration
- **Phase 0.7**: Website metadata extraction
- **Phase 1**: Address, city tier, museum type
- **Phase 1.5**: Wikipedia article content
- **Phase 1.75**: Heuristic fallback for missing data
- **Phase 1.8**: CSV reference lookup
- **Phase 2**: Collection scoring (art museums only)
- **Phase 2.5**: Rich content extraction
- **Phase 3**: Priority score calculation

---

## 🧪 Data Quality & Validation

### Validation Framework
- **JSON Schema**: Structural validation for all museum records
- **Pydantic Models**: Runtime validation with type safety
- **Evidence Tracking**: Provenance metadata for all enriched fields
- **Quality Rules**: "Never Replace Known With Null" guardrail

### Key Validation Scripts
```bash
# Validate all museum records against schema
python scripts/validation/validate-json.py

# Check cache consistency with state files
python scripts/validate_cache_vs_state.py

# Analyze missing data gaps
python scripts/analyze_missing.py

# Review Wikipedia coverage
python scripts/check_wikipedia_coverage.py

# Generate Phase 2 validation report
python scripts/phase2_validation_report.py
```

### Quality Metrics
- Schema compliance: 100% (all records pass JSON Schema)
- Address completeness: Varies by state (tracked in progress.json)
- Wikidata coverage: ~85% of museums have Wikidata IDs
- Wikipedia articles: ~40% have associated articles

---

## Repo Story

An evidence-based narrative of this repository's development history, contributor patterns, and architecture:
- [Repo Story (2026-04-28)](.documentation/repo-story/repo-story-2026-04-28.md)
- [Repo Story (2026-04-12)](.documentation/repo-story/repo-story-2026-04-12.md)

---

## 🤝 Contributing

We welcome contributions from developers, data curators, and art enthusiasts!

### Ways to Contribute
- **Code**: Improve the website, add features, fix bugs
- **Data**: Correct museum information, add missing details
- **Documentation**: Clarify guides, add examples
- **Testing**: Report bugs, suggest improvements

### Getting Started
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes and test thoroughly
4. Commit with clear messages: `git commit -m "Add feature X"`
5. Push and open a Pull Request

### Data Corrections
Found incorrect museum info? Please:
1. Check the museum's official website for accurate data
2. Open an issue with the correction and source URL
3. Or submit a PR updating the relevant state JSON file

---

## 📄 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for details.

### Data Attribution
- **Walker Art Center**: Original reciprocal membership roster
- **Wikidata**: CC0 (Public Domain)
- **Wikipedia**: CC BY-SA 3.0
- **Museum Websites**: Factual data extraction (fair use)

---

## 🙏 Acknowledgments

- **Walker Art Center** - For maintaining the reciprocal membership program
- **Wikidata Community** - For comprehensive structured museum data
- **Wikipedia Contributors** - For detailed cultural institution articles
- **Open Source Community** - For the tools that make this possible

---

## 📞 Support & Contact

- **Issues**: [GitHub Issues](https://github.com/MakeBoldSolutions/MuseumSpark/issues)
- **Discussions**: [GitHub Discussions](https://github.com/MakeBoldSolutions/MuseumSpark/discussions)
- **Documentation**: [.documentation folder](.documentation/)
- **Project Updates**: Watch this repository for releases

---

## 🧹 Maintenance

For information on project cleanup, archiving old data, and maintaining a clean workspace:
- See [.documentation/copilot/harvest-2026-04-28.md](.documentation/copilot/harvest-2026-04-28.md) for recent maintenance actions
- Temp files and test runs are automatically gitignored
- Archive directories preserve historical data without cluttering the workspace

---

*Built with ❤️ for art lovers, by art lovers.*  
*Empowering smarter museum travel, one enriched record at a time.*
