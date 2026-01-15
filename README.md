# MuseumSpark 🏛️

> **The strategic travel planner for art lovers.**  
> Curate, prioritize, and optimize your museum visits across North America.

![Status](https://img.shields.io/badge/Status-Pre--Alpha-orange)
![Phase](https://img.shields.io/badge/Phase-1_Open_Data-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Data](https://img.shields.io/badge/Dataset-1.2k+_Museums-purple)

---

## 🎨 About MuseumSpark

**MuseumSpark** transforms a simple list of museums into an intelligent travel planning engine. 

Built on the foundation of the **[Walker Art Reciprocal Program](https://walkerart.org/support/membership/reciprocal-membership/)**, MuseumSpark enriches standard museum data with a unique **Priority Scoring System**. We rank institutions based on:

1.  **Artistic Strength**: Depth of Impressionist and Modern/Contemporary collections.
2.  **Historical Context**: Quality of curatorial narrative and framing.
3.  **Travel Logistics**: "City Tier" classification (Major Hub vs. Small Town) and time-to-visit estimates.

Whether you have a 2-hour layover or a full weekend in a new city, MuseumSpark helps you decide where to go first.

---

## ✨ Key Features

### 🏆 Priority Scoring 
Don't just see a list; see what matters. Our custom algorithm weighs collection strength against reputation to highlight "Hidden Gems" over "Tourist Traps."

### 📍 Smart City Tiers
We classify cities into **Tier 1 (Major Hubs)**, **Tier 2 (Medium Cities)**, and **Tier 3 (Small Towns)**, helping you understand the scale of museum density in your destination.

### 📊 Enrichment Pipeline
A robust Python-based data pipeline aggregates info from **Wikidata**, **IMLS**, and **OpenStreetMap** to fill gaps in official records, ensuring you have accurate addresses, hours, and descriptions.

---

## 🗺️ Roadmap

We are building MuseumSpark in four strategic phases.

### 🏁 Phase 1: Open Data Public Records (Current)
*   **Goal:** Establish a verified baseline dataset.
*   **Focus:** Migrating the Walker Art Reciprocal list to a structured JSON schema.
*   **Tech:** Static React Site, Python ETL scripts, Wikidata integration.
*   **Status:** ~80% Complete.

### 🧠 Phase 2: AI & LLM Enrichment (Planned)
*   **Goal:** Deep qualitative analysis.
*   **Details:** Using **Claude** and **OpenAI** agents to read museum websites and score them against our "Master Requirements" (Impressionist Strength, Historical Context).
*   **Outcome:** A rich, nuanced dataset that goes beyond simple facts.

### ✅ Phase 3: Validation & Review (Planned)
*   **Goal:** Expert verification.
*   **Details:** Auditing the AI-generated scores with art historians and heavy users to ensure the "Priority Score" feels right.

### 🚀 Phase 4: Full Interactive Platform (Planned)
*   **Goal:** The ultimate travel companion.
*   **Tech:** Python **FastAPI** Backend, User Accounts.
*   **Features:** Save favorites, track "Visited" museums, and generate custom itineraries with an AI travel agent.

---

## 🛠️ Technology Stack

*   **Frontend**: [React](https://react.dev/), [Vite](https://vitejs.dev/), [Tailwind CSS](https://tailwindcss.com/)
*   **Data Pipeline**: Python 3.11+, Pydantic, Pandas
*   **Validation**: JSON Schema
*   **Deployment**: GitHub Pages
*   **Future Backend**: FastAPI, SQLite, Azure

---

## 🚀 Getting Started

### Prerequisites
*   Node.js 18+ (for the website)
*   Python 3.7+ (for data scripts)

### Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/markhazleton/MuseumSpark.git
    cd MuseumSpark
    ```

2.  **Run the Website**
    ```bash
    cd site
    npm install
    npm run dev
    ```
    Open `http://localhost:5173` to see the app.

3.  **Run Data Scripts (Optional)**
    ```bash
    # From root directory
    python -m venv .venv
    source .venv/bin/activate  # or .venv\Scripts\activate on Windows
    pip install -r scripts/requirements.txt
    
    # Validate the dataset
    python scripts/validate-json.py
    ```

---

## 📂 Project Structure

```text
├── data/               # The JSON Dataset (Single Source of Truth)
│   ├── index/          # Generated indices 
│   ├── schema/         # JSON Schemas
│   └── states/         # Individual State JSON files
├── Documentation/      # Architecture & Requirements
├── scripts/            # Python ETL & Enrichment Tools
├── site/               # React Application Source
└── specs/              # Feature Specifications
```

---

## 🤝 Contributing

We welcome contributions! Whether you're a developer fixing bugs or an art lover connecting data, your help is appreciated.

*   **[Contributing Guide](.github/CONTRIBUTING.md)**: How to get started.
*   **[Code of Conduct](.github/CODE_OF_CONDUCT.md)**: Our community standards.
*   **[Report a Bug](https://github.com/markhazleton/MuseumSpark/issues/new?template=bug_report.yml)**
*   **[Suggest a Feature](https://github.com/markhazleton/MuseumSpark/issues/new?template=feature_request.yml)**
*   **[Correct Museum Data](https://github.com/markhazleton/MuseumSpark/issues/new?template=data_correction.yml)**

---

## 📄 License & Support

*   **License**: Distributed under the MIT License. See `LICENSE` for more information.
*   **Support**: Need help? Check our [Support Guide](.github/SUPPORT.md) or open a [Discussion](https://github.com/markhazleton/MuseumSpark/discussions).

---

*Built with ❤️ for art lovers everywhere.*
