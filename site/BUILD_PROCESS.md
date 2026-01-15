# Site Build and Data Synchronization Process

## Build Process

The build process is managed via `npm run build` and includes the following steps:

1. **Data Synchronization** (`prebuild` script):
    - Executes `npm run sync-data`.
    - Ensures the site has the latest data from the repository before building.

2. **Linting**:
    - Executes `npm run lint`.
    - Checks code quality using ESLint.

3. **Vite Build**:
    - Executes `vite build`.
    - Compiles the React application into static assets.

## Data Synchronization

The `scripts/sync-data.mjs` script handles copying data from the main repository to the site's public directory.

- **Source**: `../data` (The root `data` directory of the repository)
- **Destination**: `./public/data` (The `public/data` directory within the `site` folder)

### Process Details

1. **Clean**: The destination directory (`public/data`) is completely removed if it exists. This ensures that any deleted data files are also removed from the site build (no stale data).
2. **Copy**: The entire contents of the source directory are recursively copied to the destination.
3. **Validation**: The script performs a sanity check to ensure key artifacts (like `index/all-museums.json`) exist in the destination.

This ensures that `http://localhost:5173/data/...` (or the production equivalent) accurately reflects the contents of the repository's `data/` folder.
