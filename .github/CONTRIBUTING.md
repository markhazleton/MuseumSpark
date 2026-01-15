# Contributing to MuseumSpark

First off, thanks for taking the time to contribute! 🎉

MuseumSpark is a personal but open-source project aiming to build the most useful art museum travel prioritization system. We welcome contributions in the form of code, data enrichment, and documentation.

## Code of Conduct

This project and everyone participating in it is governed by the [MuseumSpark Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### 🏛️ Data Enrichment

The core of MuseumSpark is the dataset. You can contribute by:

1. **Reporting Errors**: Use the [Data Correction Issue Template](https://github.com/markhazleton/MuseumSpark/issues/new?template=data_correction.yml).
2. **Enriching Records**: Run the enrichment scripts or manually update state JSON files following the [Schema](data/schema/museum.schema.json).

### 🐛 Reporting Bugs

This section guides you through submitting a bug report.

- Use a clear and descriptive title.
- Describe the exact steps which reproduce the problem.
- Provide specific examples to demonstrate the steps.

### 🚀 Suggesting Enhancements

- Use a clear and descriptive title.
- Provide a step-by-step description of the suggested enhancement.
- Explain why this enhancement would be useful to most users.

## Development Setup

1. Clone the repo.
2. Install dependencies:

    ```bash
    cd site
    npm install
    ```

3. Run the development server:

    ```bash
    npm run dev
    ```

## Python Environment (for Data Scripts)

1. Create a virtual environment:

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # or .venv\Scripts\activate on Windows
    ```

2. Install requirements:

    ```bash
    pip install -r scripts/requirements.txt
    ```

## Styleguides

### Git Commit Messages

- Use the imperative mood ("Add feature" not "Added feature").
- Limit the first line to 72 characters or less.
- Reference issues and pull requests liberally after the first line.

### Documentation

- Use Markdown.
- Keep the `masterRequirements.md` as the source of truth for scope.
