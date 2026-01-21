# Quick Start: Downloading Museum Data

## Finding the Download Button

The CSV download feature is available on the Browse pages:

### Browse Page (`/browse`)
1. Navigate to the Browse page
2. Apply any filters you want (state, city, domain, etc.)
3. Look for the green **"Download CSV"** button next to the pagination controls
4. Click to download your filtered data

### Browse Page New (`/browse-new`)
1. Navigate to the Browse Page New
2. Apply filters (state, domain, AI-scored only, etc.)
3. Find the **"Download CSV"** button in the results summary
4. The button shows how many records will be downloaded
5. Click to start download

## Quick Google Sheets Import

### Method 1: Drag & Drop (Fastest)
1. Download your CSV file
2. Go to [sheets.google.com](https://sheets.google.com)
3. Drag the CSV file onto the page
4. Done! Google Sheets creates a new spreadsheet automatically

### Method 2: File → Import
1. Download your CSV file
2. Open Google Sheets
3. Click **File** → **Import**
4. Select **Upload** tab
5. Choose your CSV file
6. Select import settings:
   - Separator: Comma
   - Convert text to numbers: Yes
7. Click **Import data**

## What Data Gets Exported?

### Essential Fields
- Museum name, city, state
- Contact info (website, phone, address)
- Museum type and domain

### Planning Data
- Time needed for visit
- Visit duration in minutes
- Nearby museums count

### Quality Metrics
- Overall quality score
- Priority score (hidden gem indicator)
- Reputation (International/National/Regional/Local)
- Collection tier (Flagship/Strong/Moderate/Small)

### Art Collection Ratings (Browse Page New)
- Impressionist strength (1-5)
- Modern/Contemporary strength (1-5)

## Tips for Better Exports

### 1. Filter First, Download Second
Apply filters before downloading to get exactly what you need:
- **State filter** → Museums in specific states
- **Domain filter** → Art museums, Science museums, etc.
- **AI-Scored Only** → Museums with collection strength data
- **Search** → Specific museum names or cities

### 2. Use Descriptive Filenames
The filename automatically includes your filters:
- `museums-2026-01-20-California-Art.csv`
- `museums-2026-01-20-scored.csv`

### 3. Organize in Google Sheets
After importing:
- **Freeze top row**: View → Freeze → 1 row
- **Add filters**: Click filter icon in toolbar
- **Sort data**: Click column headers
- **Color code**: Use conditional formatting for quality scores

## Common Use Cases

### Trip Planning
```
1. Filter by state: California
2. Filter by time: Full day
3. Download CSV
4. Import to Google Sheets
5. Add columns: "Visit Date", "Priority", "Notes"
6. Sort by quality score
7. Create your itinerary
```

### Finding Hidden Gems
```
1. Apply AI-Scored Only filter
2. Sort by Priority Score (ascending)
3. Download top results
4. Analyze in spreadsheet
5. Identify underrated museums
```

### Regional Analysis
```
1. Filter by region/state
2. Download all museums
3. Create pivot table in Google Sheets
4. Analyze by:
   - Museum type distribution
   - Quality score averages
   - Collection tier breakdown
```

## Need Help?

See the [complete documentation](csv-export.md) for:
- Detailed field descriptions
- Advanced Google Sheets techniques
- Troubleshooting tips
- Technical details
