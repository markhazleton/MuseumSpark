import type { Museum, OutcomeTier, ReputationLevel, CollectionLevel } from "./types";

// ── Priority Score display helpers ───────────────────────────────────────────
// v3.1.T: Priority Score has a floor of 1. Lower = higher priority.

export function getPriorityScoreColor(score: number | null | undefined): string {
  if (score == null) return "text-slate-400";
  if (score <= 5) return "text-emerald-600 font-bold";
  if (score <= 9) return "text-blue-600 font-semibold";
  if (score <= 15) return "text-amber-600";
  return "text-slate-500";
}

export function getPriorityScoreBadgeColor(score: number | null | undefined): string {
  if (score == null) return "bg-slate-100 text-slate-500";
  if (score <= 5) return "bg-emerald-100 text-emerald-800 ring-emerald-600/20";
  if (score <= 9) return "bg-blue-100 text-blue-800 ring-blue-600/20";
  if (score <= 15) return "bg-amber-100 text-amber-800 ring-amber-600/20";
  return "bg-slate-100 text-slate-600";
}

export function getPriorityScoreLabel(score: number | null | undefined): string {
  if (score == null) return "Not Scored";
  if (score <= 5) return "Must-Visit";
  if (score <= 9) return "High Priority";
  if (score <= 15) return "Worth Visiting";
  return "If In Area";
}

// Legacy aliases (kept for backwards compat with existing components)
export const getScoreColor = getPriorityScoreColor;
export const getScoreBadgeColor = getPriorityScoreBadgeColor;
export const getScoreLabel = getPriorityScoreLabel;

// ── Outcome Tier display helpers ─────────────────────────────────────────────

export function getOutcomeTierColor(tier: OutcomeTier | string | null | undefined): string {
  switch (tier) {
    case "Must-See":         return "text-emerald-700 font-bold";
    case "High Priority":    return "text-blue-700 font-semibold";
    case "Regionally Important": return "text-violet-700 font-semibold";
    case "Detour":           return "text-orange-600 font-semibold";
    case "Consider":         return "text-amber-600";
    case "Background":       return "text-slate-500";
    default:                 return "text-slate-400";
  }
}

export function getOutcomeTierBadgeColor(tier: OutcomeTier | string | null | undefined): string {
  switch (tier) {
    case "Must-See":         return "bg-emerald-100 text-emerald-800 ring-emerald-600/20";
    case "High Priority":    return "bg-blue-100 text-blue-800 ring-blue-600/20";
    case "Regionally Important": return "bg-violet-100 text-violet-800 ring-violet-600/20";
    case "Detour":           return "bg-orange-100 text-orange-800 ring-orange-600/20";
    case "Consider":         return "bg-amber-100 text-amber-800 ring-amber-600/20";
    case "Background":       return "bg-slate-100 text-slate-600 ring-slate-400/20";
    default:                 return "bg-slate-100 text-slate-400";
  }
}

export function getOutcomeTierIcon(tier: OutcomeTier | string | null | undefined): string {
  switch (tier) {
    case "Must-See":         return "★";
    case "High Priority":    return "▲";
    case "Regionally Important": return "◆";
    case "Detour":           return "↗";
    case "Consider":         return "●";
    case "Background":       return "○";
    default:                 return "—";
  }
}

export function getOutcomeTierDescription(tier: OutcomeTier | string | null | undefined): string {
  switch (tier) {
    case "Must-See":
      return "Canon-defining collection or historical interpretation. A trip anchor.";
    case "High Priority":
      return "Exceptional collection or curatorial authority. Worth a dedicated visit.";
    case "Regionally Important":
      return "Primary regional art or history reference. Plan around it if in the region.";
    case "Detour":
      return "Specialized destination that plausibly alters your route.";
    case "Consider":
      return "Worth visiting when already in the area. Proximity-dependent.";
    case "Background":
      return "Limited travel gravity. Primarily serves local community.";
    default:
      return "Not yet classified.";
  }
}

// ── Reputation Level helpers ─────────────────────────────────────────────────

export function getReputationBadgeColor(level: ReputationLevel | string | null | undefined): string {
  switch (level) {
    case "International": return "bg-purple-100 text-purple-800";
    case "National":      return "bg-blue-100 text-blue-800";
    case "Regional":      return "bg-teal-100 text-teal-800";
    case "Supra-Local":   return "bg-amber-100 text-amber-800";
    case "Local":         return "bg-slate-100 text-slate-600";
    default:              return "bg-slate-100 text-slate-400";
  }
}

// ── Collection Level helpers ──────────────────────────────────────────────────

export function getCollectionLevelBadgeColor(level: CollectionLevel | string | null | undefined): string {
  switch (level) {
    case "Flagship": return "bg-emerald-100 text-emerald-800";
    case "Strong":   return "bg-blue-100 text-blue-800";
    case "Moderate": return "bg-amber-100 text-amber-800";
    case "Small":    return "bg-slate-100 text-slate-600";
    default:         return "bg-slate-100 text-slate-400";
  }
}

// ── Effective PAS / Collection-Based PAS helpers ──────────────────────────────

/** Compute Collection-Based PAS client-side when not pre-computed. */
export function computeCollectionBasedPas(museum: Museum): number | null {
  const values = [
    museum.collection_based_pas,
    museum.impressionist_strength,
    museum.modern_contemporary_strength,
    museum.hat_strength,
    museum.planner_collection_pas,
  ].filter((v): v is number => v != null);
  return values.length > 0 ? Math.max(...values) : null;
}

/** Compute Effective PAS client-side when not pre-computed. */
export function computeEffectivePas(museum: Museum): number | null {
  const cbp = museum.effective_pas ?? computeCollectionBasedPas(museum);
  const eca = museum.eca_score ?? museum.planner_exhibition_advantage ?? null;
  const values = [cbp, eca].filter((v): v is number => v != null);
  return values.length > 0 ? Math.max(...values) : null;
}

// ── Legacy TourPlanningScores helpers ─────────────────────────────────────────
// Kept for backwards compatibility with Phase 1.9 planner data

export type TourPlanningScores = {
  collection_quality?: number | null;
  collection_depth?: number | null;
  family_friendly_score?: number | null;
  educational_value_score?: number | null;
  contemporary_score?: number | null;
  modern_score?: number | null;
  impressionist_score?: number | null;
  expressionist_score?: number | null;
  classical_score?: number | null;
  american_art_score?: number | null;
  european_art_score?: number | null;
  asian_art_score?: number | null;
  african_art_score?: number | null;
  painting_score?: number | null;
  sculpture_score?: number | null;
  decorative_arts_score?: number | null;
  photography_score?: number | null;
};

export function getTopScores(
  scores: TourPlanningScores | null | undefined
): Array<{ label: string; score: number }> {
  if (!scores) return [];

  const allScores = [
    { label: "Contemporary", score: scores.contemporary_score },
    { label: "Modern", score: scores.modern_score },
    { label: "Impressionist", score: scores.impressionist_score },
    { label: "Expressionist", score: scores.expressionist_score },
    { label: "Classical", score: scores.classical_score },
    { label: "American Art", score: scores.american_art_score },
    { label: "European Art", score: scores.european_art_score },
    { label: "Asian Art", score: scores.asian_art_score },
    { label: "African Art", score: scores.african_art_score },
    { label: "Painting", score: scores.painting_score },
    { label: "Sculpture", score: scores.sculpture_score },
    { label: "Decorative Arts", score: scores.decorative_arts_score },
    { label: "Photography", score: scores.photography_score },
  ];

  return allScores
    .filter((s) => s.score && s.score >= 5)
    .sort((a, b) => (b.score || 0) - (a.score || 0))
    .slice(0, 5)
    .map((s) => ({ label: s.label, score: s.score || 0 }));
}

export function hasAnyScore(
  scores: TourPlanningScores | null | undefined
): boolean {
  if (!scores) return false;
  return !!(
    scores.collection_quality ||
    scores.collection_depth ||
    scores.family_friendly_score ||
    scores.educational_value_score
  );
}
