import type { TourPlanningScores } from "./types";

export function getScoreColor(score: number | null | undefined): string {
  if (!score) return "text-slate-400";
  if (score >= 9) return "text-emerald-600 font-bold";
  if (score >= 7) return "text-blue-600 font-semibold";
  if (score >= 5) return "text-amber-600";
  return "text-slate-500";
}

export function getScoreBadgeColor(score: number | null | undefined): string {
  if (!score) return "bg-slate-100 text-slate-500";
  if (score >= 9) return "bg-emerald-100 text-emerald-800 ring-emerald-600/20";
  if (score >= 7) return "bg-blue-100 text-blue-800 ring-blue-600/20";
  if (score >= 5) return "bg-amber-100 text-amber-800 ring-amber-600/20";
  return "bg-slate-100 text-slate-600";
}

export function getScoreLabel(score: number | null | undefined): string {
  if (!score) return "Not Rated";
  if (score >= 9) return "World-Class";
  if (score >= 8) return "Outstanding";
  if (score >= 7) return "Excellent";
  if (score >= 6) return "Very Good";
  if (score >= 5) return "Good";
  return "Modest";
}

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
