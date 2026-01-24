# Copilot Documentation

This folder contains GitHub Copilot-specific documentation and session notes for the MuseumSpark project.

## 📁 Folder Structure

- **[../copilot-instructions.md](../copilot-instructions.md)** - Main GitHub Copilot instructions (project root)
- **session-YYYYMMDD/** - Daily session notes and copilot-generated documentation

## 📝 Session Notes

Session folders capture copilot-generated documentation that doesn't fit into other `/Documentation` folders:

- Exploratory analysis and investigations
- Refactoring proposals and considerations
- Temporary design notes
- Copilot conversation summaries
- Ad-hoc research and findings

### Naming Convention

Session folders use ISO date format: `session-YYYYMMDD`

**Example**: `session-20260124` for January 24, 2026

## 📋 Guidelines

### When to Create Session Documentation

**Use session folders for**:
- Exploratory work that may inform future specifications
- Temporary notes during feature development
- Copilot-assisted research and analysis
- Documentation that doesn't yet have a permanent home

**Don't use session folders for**:
- Feature specifications → Use `/Documentation/features/`
- Architecture documentation → Use `/Documentation/architecture/`
- Setup guides → Use `/Documentation/setup-deployment/`
- Reference materials → Use `/Documentation/reference/`

### Session Documentation Best Practices

1. **One folder per date**: Create a new session folder for each day
2. **Descriptive filenames**: Use clear names like `api-refactoring-analysis.md` or `scoring-algorithm-investigation.md`
3. **Link to related specs**: Reference specifications, plans, or issues when applicable
4. **Archive when obsolete**: Move to archive folder or delete when no longer relevant
5. **Promote to permanent**: Move to appropriate `/Documentation` subfolder when finalized

### Cleanup Policy

- **Monthly review**: Review session folders older than 30 days
- **Archive after 90 days**: Move to archive if not promoted to permanent documentation
- **Delete after 1 year**: Remove archived sessions unless historically significant

## 🔗 Related Documentation

- [Parent: Documentation Home](../README.md)
- [GitHub Copilot Instructions](../copilot-instructions.md)
- [SpecKit Constitution](../../.specify/memory/constitution.md)
- [Development Workflow](../CLAUDE.md)

---

**Version**: 1.0.0 | **Created**: 2026-01-24
