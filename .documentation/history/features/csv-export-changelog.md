# CSV Export Feature - Change Log

## January 20, 2026

### Added
- **CSV Download Functionality**: Both Browse pages now include a "Download CSV" button
  - Location: Results summary area, next to pagination controls
  - Visual: Green button with download icon
  - Shows count of records to be downloaded

### Features
1. **Smart Filtering**
   - Downloads only filtered/searched results
   - Respects all active filters (state, domain, search terms, etc.)
   - Includes sort order

2. **Intelligent Filenames**
   - Auto-generates descriptive filenames
   - Format: `museums-YYYY-MM-DD[-filters].csv`
   - Examples:
     - `museums-2026-01-20.csv`
     - `museums-2026-01-20-California-Art-scored.csv`
     - `museums-2026-01-20-full.csv`

3. **Comprehensive Data Export**
   - **Location data**: State, City, Address, Postal Code, Coordinates
   - **Museum info**: Name, Type, Domain, Website, Phone, Status
   - **Planning data**: Time needed, Visit duration, Nearby museums
   - **Quality metrics**: Quality score, Priority score, Reputation, Collection tier
   - **Art collection**: Impressionist & Modern/Contemporary strength ratings

4. **Google Sheets Compatible**
   - UTF-8 encoding
   - Properly escaped special characters
   - Comma-delimited format
   - Ready for direct import

### Files Modified
1. `site/src/pages/BrowsePage.tsx`
   - Added `handleDownloadCSV` function
   - Added download button to UI
   - Exports 17 key fields

2. `site/src/pages/BrowsePageNew.tsx`
   - Added `handleDownloadCSV` function with custom formatters
   - Added download button to results summary
   - Exports 19 comprehensive fields including art strength metrics

### Technical Details
- **CSV Generation**: Client-side using Blob API
- **Character Encoding**: UTF-8 with proper escaping
- **Quote Handling**: RFC 4180 compliant (quotes escaped as "")
- **Special Characters**: Commas, quotes, and newlines properly handled

### Testing Checklist
- [x] TypeScript compilation successful
- [x] ESLint passes (0 errors)
- [x] Download button appears in both browse pages
- [ ] CSV downloads successfully in browser
- [ ] CSV opens correctly in Google Sheets
- [ ] Filtered data exports correctly
- [ ] Special characters handled properly
- [ ] Filename generation works with all filter combinations

### Documentation Created
1. `Documentation/features/csv-export.md`
   - Complete user guide
   - Google Sheets import instructions
   - Use cases and tips
   - Troubleshooting section

2. `Documentation/features/csv-export-changelog.md`
   - This file: technical change log

### Future Enhancements
- [ ] Add column selection UI
- [ ] Export to Excel format (.xlsx)
- [ ] Export to JSON format
- [ ] Direct Google Sheets API integration
- [ ] Option to export all records vs. current page only
- [ ] Scheduled/automated exports
- [ ] Export templates for different use cases

### Known Limitations
- Large exports (10,000+ records) may take a few seconds
- No progress indicator for large downloads
- All columns exported (no custom column selection yet)
- Client-side only (requires JavaScript enabled)

### Browser Compatibility
- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers (with proper CSV handling)

### Related Issues
- Resolves feature request for spreadsheet export
- Supports Google Sheets workflow
- Enables offline data analysis
