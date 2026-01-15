import { cp, rm, stat } from 'node:fs/promises'
import { existsSync } from 'node:fs'
import path from 'node:path'
import url from 'node:url'

const __filename = url.fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const siteRoot = path.resolve(__dirname, '..')
const repoRoot = path.resolve(siteRoot, '..')

const srcDataDir = path.join(repoRoot, 'data')
const destDataDir = path.join(siteRoot, 'public', 'data')

async function main() {
  if (!existsSync(srcDataDir)) {
    throw new Error(`Expected data directory at: ${srcDataDir}`)
  }

  // Remove existing generated copy to avoid stale files.
  if (existsSync(destDataDir)) {
    await rm(destDataDir, { recursive: true, force: true })
  }

  // Copy the repo's data/ into site/public/data so Vite serves it.
  await cp(srcDataDir, destDataDir, { recursive: true })

  // Quick sanity check for key artifacts.
  const mustExist = [
    path.join(destDataDir, 'index', 'all-museums.json'),
    path.join(destDataDir, 'index', 'progress.json'),
  ]
  for (const p of mustExist) {
    await stat(p)
  }

  console.log(`[OK] Synced data -> ${path.relative(repoRoot, destDataDir)}`)
}

main().catch((err) => {
  console.error('[ERROR] sync-data failed')
  console.error(err)
  process.exitCode = 1
})
