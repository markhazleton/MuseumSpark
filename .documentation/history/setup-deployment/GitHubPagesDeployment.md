# GitHub Pages Deployment Guide

This guide explains how to deploy MuseumSpark to GitHub Pages.

## Prerequisites

- GitHub repository with the MuseumSpark code
- Repository is public (required for free GitHub Pages)
- Push access to the repository

## One-Time Setup

### 1. Enable GitHub Pages

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Pages**
3. Under "Build and deployment":
   - **Source**: Select "GitHub Actions"
   - (Do not select "Deploy from a branch" - we're using Actions)
4. Click **Save**

### 2. Update Vite Configuration

If your repository is `https://github.com/username/MuseumSpark`, the site will be served from `https://username.github.io/MuseumSpark/`.

You need to set the correct base path in `site/vite.config.ts`:

```typescript
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

export default defineConfig({
  // Set base to match your repo name
  base: '/MuseumSpark/',  // Change this to match YOUR repo name
  plugins: [react(), tailwindcss()],
  server: {
    host: 'localhost',
    port: 5173,
    strictPort: true,
  },
})
```

**Important**: 
- If deploying to a custom domain, set `base: '/'`
- If deploying to `username.github.io` (root), set `base: '/'`
- If deploying to `username.github.io/RepoName`, set `base: '/RepoName/'`

### 3. Test Local Build

Before pushing, test that the build works:

```bash
cd site
npm run build
npm run preview
```

Open http://localhost:4173/MuseumSpark/ (or your base path) and verify:
- Site loads correctly
- Museum data loads
- Navigation works
- Detail pages work

## Deployment

### Automatic Deployment (Recommended)

The workflow is already configured in `.github/workflows/deploy.yml`.

**To deploy**:
1. Commit your changes
2. Push to the `main` branch

```bash
git add .
git commit -m "Deploy to GitHub Pages"
git push origin main
```

3. GitHub Actions will automatically:
   - Install dependencies
   - Sync data to public folder
   - Build the site
   - Deploy to GitHub Pages

4. Check deployment status:
   - Go to **Actions** tab in GitHub
   - Watch the "Deploy to GitHub Pages" workflow
   - Deployment takes 1-3 minutes

5. Visit your site:
   - `https://username.github.io/RepoName/`

### Manual Deployment (Alternative)

If you prefer manual deployment:

1. Build locally:
```bash
cd site
npm run build
```

2. Push `dist/` to a `gh-pages` branch:
```bash
cd site/dist
git init
git add -A
git commit -m 'Deploy'
git push -f git@github.com:username/MuseumSpark.git main:gh-pages
```

3. Configure GitHub Pages:
   - Settings → Pages
   - Source: "Deploy from a branch"
   - Branch: `gh-pages` / `/ (root)`

## Troubleshooting

### Site shows 404 errors for assets

**Problem**: Assets (JS, CSS) fail to load with 404 errors.

**Solution**: Check `base` in `vite.config.ts` matches your repository name.

```typescript
// For username.github.io/MuseumSpark/
base: '/MuseumSpark/'

// For custom domain or username.github.io
base: '/'
```

### Museum data fails to load

**Problem**: Console shows "Failed to fetch /data/index/all-museums.json"

**Solution**: 
1. Verify `npm run sync-data` runs in the workflow
2. Check that `site/public/data/` exists after build
3. Verify `base` URL is correct

### Workflow fails on "npm ci"

**Problem**: GitHub Actions fails at install step

**Solution**:
1. Ensure `site/package-lock.json` is committed
2. Try deleting `package-lock.json` and running `npm install` locally
3. Commit the new lockfile and push

### Site works locally but not on GitHub Pages

**Problem**: Site works in dev/preview but fails on Pages

**Checklist**:
- [ ] `base` is set correctly in `vite.config.ts`
- [ ] All assets use relative paths (not absolute `/path`)
- [ ] Data files are in `site/public/data/` before build
- [ ] `sync-data` script runs successfully
- [ ] Build completes without errors
- [ ] Preview with `npm run preview` works with base path

## Custom Domain (Optional)

To use a custom domain like `museumspark.com`:

1. Add a `CNAME` file to `site/public/`:
```
museumspark.com
```

2. Update `vite.config.ts`:
```typescript
base: '/'  // Use root for custom domain
```

3. Configure DNS:
   - Add an A record pointing to GitHub Pages IPs:
     - `185.199.108.153`
     - `185.199.109.153`
     - `185.199.110.153`
     - `185.199.111.153`
   - Or add a CNAME record pointing to `username.github.io`

4. In GitHub Settings → Pages:
   - Custom domain: Enter your domain
   - Enforce HTTPS: Check this box

## Verification

After deployment, verify these features work:

- [ ] Home page loads at `https://username.github.io/RepoName/`
- [ ] Museum list displays
- [ ] Search and filters work
- [ ] Clicking a museum opens detail page
- [ ] Detail page loads museum data
- [ ] Progress page shows correct statistics
- [ ] Browser console shows no errors
- [ ] All navigation links work
- [ ] Back button works correctly

## Monitoring

Check deployment status:
- **GitHub Actions**: Repository → Actions tab
- **Pages Status**: Repository → Settings → Pages
- **Build logs**: Click on workflow run for detailed logs

## Updates

To deploy updates:

1. Make changes locally
2. Test with `npm run dev`
3. Commit and push to `main`
4. GitHub Actions deploys automatically
5. Changes appear in 1-3 minutes

## Rollback

If a deployment breaks the site:

1. Find the last working commit
2. Revert or fix the issue
3. Push the fix
4. New deployment runs automatically

Or manually revert:
```bash
git revert HEAD
git push origin main
```

## Resources

- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [Vite Deployment Guide](https://vitejs.dev/guide/static-deploy.html#github-pages)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

---

**Status**: Workflow ready, deployment pending repository configuration
