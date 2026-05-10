# CSV Export Feature

## Overview

The MuseumSpark site now includes the ability to download filtered museum data as a CSV file, which can be easily imported into Google Sheets, Excel, or any other spreadsheet application.

## Features

### Download Functionality
- **Export Filtered Data**: Downloads only the museums that match your current filters
- **Smart Filename**: Automatically generates a descriptive filename based on:
  - Current date
  - Applied filters (state, domain, etc.)
  - Filter modes (e.g., "-scored", "-full")
- **Complete Data**: Includes comprehensive museum information in the export

### Accessing the Download Feature

The CSV download button is available on both browse pages:
1. **Browse Page** (`/browse`)
2. **Browse Page New** (`/browse-new`)

Look for the green "Download CSV" button with a download icon in the results summary area.

## Exported Data Fields

### Browse Page New (Comprehensive Export)
The export includes the following fields:
- **Location**: State, City, Address, Postal Code, Latitude, Longitude
- **Basic Info**: Museum Name, Type, Domain, Website, Phone
- **Visit Planning**: Time Needed, Status, Visit Duration
- **Quality Metrics**: 
  - Quality Score (higher is better)
  - Priority Score (lower is better hidden gem)
  - Nearby Museums Count
- **Collection Strength**: 
  - Reputation (International, National, Regional, Local)
  - Collection Tier (Flagship, Strong, Moderate, Small)
  - Impressionist Strength (1-5)
  - Modern/Contemporary Strength (1-5)

### Browse Page (Simplified Export)
Includes essential fields for basic museum information and planning.

## Using with Google Sheets

### Method 1: Direct Import
1. Click the "Download CSV" button
2. Open Google Sheets
3. Click File → Import
4. Select "Upload" tab
5. Drag and drop your downloaded CSV file
6. Choose import settings:
   - Import location: "Replace spreadsheet" or "Insert new sheet(s)"
   - Separator type: "Comma"
   - Convert text to numbers: Yes (recommended)
7. Click "Import data"

### Method 2: Quick Open
1. Download the CSV file
2. Go to [Google Sheets](https://sheets.google.com)
3. Drag the CSV file directly onto the Google Sheets homepage
4. Google Sheets will automatically create a new spreadsheet

## Use Cases

### Trip Planning
1. Filter museums by state and time needed
2. Download the filtered list
3. Import into Google Sheets
4. Add custom columns for:
   - Visit dates
   - Notes
   - Travel logistics
   - Priority rankings

### Research & Analysis
1. Use "AI-Scored Only" filter for museums with collection strength data
2. Download the complete dataset
3. Create pivot tables or charts in Google Sheets
4. Analyze patterns:
   - Geographic distribution of quality museums
   - Relationship between reputation and collection tier
   - Modern vs. Impressionist collection strengths

### Tour Planning
1. Filter by city or region
2. Sort by priority score to find hidden gems
3. Download and organize itineraries
4. Share with travel companions

## Tips

### Efficient Filtering
- **Combine filters**: State + Domain + Scored-only for targeted exports
- **Use search**: Find specific museums or cities before exporting
- **Check result count**: The download button shows how many records will be exported

### Data Management
- **Regular exports**: Download periodic snapshots as the database updates
- **Custom analysis**: Import into Google Sheets for advanced filtering and visualization
- **Collaboration**: Share exported spreadsheets with travel companions or researchers

### Google Sheets Features to Use
After importing:
- **Freeze headers**: View → Freeze → 1 row
- **Filters**: Data → Create a filter (dropdown arrows in headers)
- **Conditional formatting**: Highlight high-quality museums or specific regions
- **Pivot tables**: Summarize by state, domain, or quality metrics
- **Charts**: Visualize museum distributions and quality scores

## Technical Details

### CSV Format
- **Encoding**: UTF-8
- **Delimiter**: Comma (`,`)
- **Quote Character**: Double quote (`"`)
- **Special characters**: Properly escaped for compatibility

### Filename Convention
```
museums-YYYY-MM-DD[-state][-domain][-filter-mode].csv
```

Examples:
- `museums-2026-01-20.csv` (all museums)
- `museums-2026-01-20-California-Art-scored.csv` (filtered)
- `museums-2026-01-20-full.csv` (full records only)

## Troubleshooting

### CSV Won't Open Correctly
- Ensure you're using UTF-8 encoding
- Try Google Sheets instead of Excel (better UTF-8 support)
- Check that special characters (commas in addresses) are properly quoted

### Missing Data
- Some fields may be empty for certain museums
- Use filters to show only museums with complete data
- Check the "FULL only" checkbox on Browse Page for complete records

### Large Downloads
- Apply filters to reduce file size
- Consider downloading by state or region
- Most spreadsheet applications handle thousands of records easily

## Future Enhancements

Planned improvements:
- Additional export formats (Excel, JSON)
- Custom column selection
- Export all pages vs. current page option
- Direct Google Sheets integration via API
- Scheduled exports and updates
