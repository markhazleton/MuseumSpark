#!/usr/bin/env python3
"""Phase 2.5: Museum Content Generation.

Generates engaging human-readable content for online presentation:
- summary: 50-100 word overview for trip planning lists
- description: 200-300 word detailed narrative
- highlights: 5-8 key features/collections

Uses premium models for art museums (heart of trip planning), 
standard models for other museums.

Usage:
    # Process single state
    python scripts/phases/phase2_5_content.py --state CO

    # Process multiple states
    python scripts/phases/phase2_5_content.py --states CO,UT,WY

    # Process all states
    python scripts/phases/phase2_5_content.py --all-states

    # Force regeneration even if content exists
    python scripts/phases/phase2_5_content.py --state CO --force

    # Dry run (show what would be generated)
    python scripts/phases/phase2_5_content.py --state CO --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not required if env vars are set directly

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATES_DIR = PROJECT_ROOT / "data" / "states"
RUNS_DIR = PROJECT_ROOT / "data" / "runs"

# LLM Provider configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # openai or anthropic

# Model selection based on museum type
PREMIUM_MODEL = "gpt-5.2"  # For art museums - higher quality, more expensive
STANDARD_MODEL = "gpt-5.2"  # Temporarily using gpt-5.2 until gpt-5-mini is available


@dataclass
class ContentResult:
    """Result of content generation for a single museum."""
    museum_id: str
    success: bool = False
    summary: Optional[str] = None
    description: Optional[str] = None
    highlights: Optional[list[str]] = None
    model_used: Optional[str] = None
    error: Optional[str] = None
    skipped: bool = False
    skip_reason: Optional[str] = None
    
    def to_patch(self) -> dict[str, Any]:
        """Convert to museum record patch."""
        if not self.success:
            return {}
        
        patch = {
            "content_summary": self.summary,
            "content_description": self.description,
            "content_highlights": self.highlights,
            "content_generated_at": now_utc_iso(),
            "content_model": self.model_used,
            "content_source": LLM_PROVIDER,
        }
        return patch


@dataclass
class Phase25Stats:
    """Statistics for Phase 2.5 run."""
    total_processed: int = 0
    generated: int = 0
    skipped_has_content: int = 0
    skipped_no_data: int = 0
    errors: int = 0
    premium_model_used: int = 0
    standard_model_used: int = 0


def load_json(path: Path) -> Any:
    """Load JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    """Save JSON file with pretty formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now_utc_iso() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def is_art_museum(museum: dict[str, Any]) -> bool:
    """Determine if museum is an art museum (deserves premium model)."""
    museum_type = museum.get("museum_type") or ""
    museum_type = museum_type.lower()
    
    # Art museum indicators
    art_keywords = ["art", "arte", "kunst", "gallery", "contemporary"]
    
    return any(keyword in museum_type for keyword in art_keywords)


def load_museum_cache(museum_id: str, state_code: str, cache_type: str) -> Optional[dict]:
    """Load cached data for a museum."""
    # Find museum cache directory
    state_dir = STATES_DIR.parent / "states" / state_code
    if not state_dir.exists():
        return None
    
    # Find museum directory (hash-based)
    museum_hash = museum_id.replace("usa-", "").replace(f"-{state_code.lower()}-", "-").replace("-", "_")
    
    for museum_dir in state_dir.iterdir():
        if not museum_dir.is_dir() or museum_dir.name.startswith("_"):
            continue
        
        cache_file = museum_dir / "cache" / f"{cache_type}.json"
        if cache_file.exists():
            try:
                return load_json(cache_file)
            except Exception:
                continue
    
    return None


def build_context(museum: dict[str, Any], state_code: str) -> str:
    """Build rich context from all available metadata."""
    context_parts = []
    
    museum_id = museum.get("museum_id", "")
    
    # Try to load cached website content
    website_cache = load_museum_cache(museum_id, state_code, "website_content")
    if website_cache:
        if website_cache.get("meta_description"):
            context_parts.append(f"Website Description: {website_cache['meta_description']}")
        if website_cache.get("about_text"):
            about = website_cache["about_text"][:500]  # Limit length
            context_parts.append(f"About: {about}")
    
    # Website content from record
    if "website_content" in museum:
        content = museum["website_content"]
        if content.get("meta_description"):
            context_parts.append(f"Website Description: {content['meta_description']}")
        if content.get("about_text"):
            about = content["about_text"][:500]  # Limit length
            context_parts.append(f"About: {about}")
    
    # Wikipedia extract
    if museum.get("wikipedia_extract"):
        extract = museum["wikipedia_extract"][:600]
        context_parts.append(f"Wikipedia: {extract}")
    
    # Wikidata description
    if museum.get("wikidata_description"):
        context_parts.append(f"Wikidata: {museum['wikidata_description']}")
    
    # Visitor information
    visitor_info = []
    if museum.get("hours"):
        visitor_info.append("Hours available")
    if museum.get("admission"):
        admission = museum["admission"]
        if isinstance(admission, dict) and admission.get("adult"):
            visitor_info.append(f"Admission: {admission['adult']}")
    if museum.get("accessibility"):
        visitor_info.append("Accessibility features documented")
    
    if visitor_info:
        context_parts.append("Visitor Info: " + ", ".join(visitor_info))
    
    # Museum characteristics
    chars = []
    if museum.get("museum_type"):
        chars.append(f"Type: {museum['museum_type']}")
    if museum.get("reputation") is not None:
        rep_labels = {0: "International", 1: "National", 2: "Regional", 3: "Local"}
        chars.append(f"Reputation: {rep_labels.get(museum['reputation'], 'Unknown')}")
    if museum.get("collection_tier") is not None:
        tier_labels = {0: "Flagship", 1: "Strong", 2: "Moderate", 3: "Small"}
        chars.append(f"Collection: {tier_labels.get(museum['collection_tier'], 'Unknown')}")
    
    if chars:
        context_parts.append(" | ".join(chars))
    
    return "\n\n".join(context_parts) if context_parts else "Limited information available"


def generate_content_openai(museum: dict[str, Any], model: str, state_code: str) -> ContentResult:
    """Generate content using OpenAI API (GPT-5.2 for premium, GPT-5-mini for standard)."""
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        museum_id = museum.get("museum_id", "unknown")
        museum_name = museum.get("museum_name", "Unknown Museum")
        city = museum.get("city", "")
        state = museum.get("state", "")
        museum_type = museum.get("museum_type", "Museum")
        
        context = build_context(museum, state_code)
        
        # Craft premium prompt for art museums
        if model == PREMIUM_MODEL:
            tone_guidance = """You are an expert art historian and travel writer crafting content for art enthusiasts planning museum visits. 
Emphasize artistic significance, collection strengths, architectural merit, and the visitor experience for art lovers.
Be specific about notable artists, movements, or pieces when known."""
        else:
            tone_guidance = """You are a knowledgeable travel writer creating engaging museum descriptions for trip planning.
Focus on what makes this museum unique and worth visiting."""
        
        prompt = f"""{tone_guidance}

Museum: {museum_name}
Location: {city}, {state}
Type: {museum_type}

Available Information:
{context}

Generate engaging content in JSON format with markdown formatting:
{{
  "summary": "50-100 word compelling overview highlighting what makes this museum special and worth visiting. Plain text, no markdown.",
  "description": "200-300 word detailed narrative in **markdown format**. Use **bold** for emphasis, *italics* for artistic terms, and proper paragraphs. Cover history, collections, architecture, and visitor experience. Write in an engaging, informative tone for travelers.",
  "highlights": ["Key feature or collection 1", "Key feature or collection 2", "Key feature or collection 3", "Key feature or collection 4", "Key feature or collection 5"]
}}

Important:
- Summary: Concise but compelling, plain text only - make readers want to visit
- Description: Use markdown formatting (**bold** for museum names, architectural features, *italics* for artistic movements/terms), write in 2-3 paragraphs with blank lines between them
- Highlights: Array of strings, plain text (will be formatted as bullets in UI)
- Be specific and concrete (e.g., "World's largest collection of Navajo textiles" not just "Native American art")
- Focus on visitor perspective - what will they experience?
- If information is limited, focus on what makes this TYPE of museum interesting
"""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert museum content writer."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=2000,
        )
        
        content = json.loads(response.choices[0].message.content)
        
        return ContentResult(
            museum_id=museum_id,
            success=True,
            summary=content.get("summary"),
            description=content.get("description"),
            highlights=content.get("highlights", []),
            model_used=model,
        )
    
    except Exception as e:
        return ContentResult(
            museum_id=museum.get("museum_id", "unknown"),
            success=False,
            error=str(e),
        )


def generate_content_anthropic(museum: dict[str, Any], model: str, state_code: str) -> ContentResult:
    """Generate content using Anthropic API."""
    try:
        from anthropic import Anthropic
        
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        museum_id = museum.get("museum_id", "unknown")
        museum_name = museum.get("museum_name", "Unknown Museum")
        city = museum.get("city", "")
        state = museum.get("state", "")
        museum_type = museum.get("museum_type", "Museum")
        
        context = build_context(museum, state_code)
        
        # Map to Anthropic model names
        anthropic_model = "claude-3-5-sonnet-20241022" if model == PREMIUM_MODEL else "claude-3-5-haiku-20241022"
        
        prompt = f"""Generate engaging museum content for a trip planning application.

Museum: {museum_name}
Location: {city}, {state}
Type: {museum_type}

{context}

Generate JSON with these fields in markdown format:
- summary: 50-100 word compelling overview (plain text, no markdown)
- description: 200-300 word detailed narrative in **markdown format** (use **bold** for emphasis, *italics* for artistic terms, proper paragraphs separated by blank lines)
- highlights: array of 5-8 key features (plain text strings)

Focus on visitor experience and what makes this museum worth visiting."""

        response = client.messages.create(
            model=anthropic_model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = json.loads(response.content[0].text)
        
        return ContentResult(
            museum_id=museum_id,
            success=True,
            summary=content.get("summary"),
            description=content.get("description"),
            highlights=content.get("highlights", []),
            model_used=anthropic_model,
        )
    
    except Exception as e:
        return ContentResult(
            museum_id=museum.get("museum_id", "unknown"),
            success=False,
            error=str(e),
        )


def generate_content(museum: dict[str, Any], state_code: str) -> ContentResult:
    """Generate content using configured LLM provider."""
    museum_id = museum.get("museum_id", "unknown")
    
    # Select model based on museum type
    is_art = is_art_museum(museum)
    model = PREMIUM_MODEL if is_art else STANDARD_MODEL
    
    # Route to appropriate provider
    if LLM_PROVIDER == "anthropic":
        return generate_content_anthropic(museum, model, state_code)
    else:
        return generate_content_openai(museum, model, state_code)


def process_museum(
    museum: dict[str, Any],
    state_code: str,
    *,
    force: bool = False,
) -> ContentResult:
    """Generate content for a single museum.
    
    Args:
        museum: Museum record
        force: Force regeneration even if content exists
        
    Returns:
        ContentResult with generated content
    """
    museum_id = museum.get("museum_id", "unknown")
    
    # Check if museum already has content
    has_content = (
        museum.get("content_summary") and 
        museum.get("content_description") and 
        museum.get("content_highlights")
    )
    
    if not force and has_content:
        return ContentResult(
            museum_id=museum_id,
            skipped=True,
            skip_reason="Already has content",
        )
    
    # Check if we have enough data to generate content
    has_data = museum.get("museum_name") is not None
    
    # Even with minimal data, we can generate basic content using LLM knowledge
    # The LLM can write about what makes this TYPE of museum interesting
    
    if not has_data:
        return ContentResult(
            museum_id=museum_id,
            skipped=True,
            skip_reason="Missing museum name",
        )
    
    # Generate content
    return generate_content(museum, state_code)


def process_state(
    state_code: str,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> Phase25Stats:
    """Process all museums in a state.
    
    Args:
        state_code: Two-letter state code
        force: Force regeneration even if content exists
        dry_run: Don't write changes
        
    Returns:
        Phase25Stats with processing statistics
    """
    stats = Phase25Stats()
    
    state_path = STATES_DIR / f"{state_code}.json"
    if not state_path.exists():
        print(f"⚠️  State file not found: {state_path}")
        return stats
    
    # Load state data
    state_data = load_json(state_path)
    museums = state_data.get("museums", [])
    
    print(f"[STATE: {state_code}] Processing {len(museums)} museums")
    
    updated_museums = []
    
    for i, museum in enumerate(museums, 1):
        stats.total_processed += 1
        museum_id = museum.get("museum_id", "unknown")
        museum_name = museum.get("museum_name", "Unknown")
        
        # Process museum
        result = process_museum(museum, state_code, force=force)
        
        if result.skipped:
            if result.skip_reason == "Already has content":
                stats.skipped_has_content += 1
            else:
                stats.skipped_no_data += 1
            updated_museums.append(museum)
            continue
        
        if not result.success:
            stats.errors += 1
            print(f"  [{i}/{len(museums)}] {museum_name}")
            print(f"           ERROR: {result.error}")
            updated_museums.append(museum)
            continue
        
        # Track model usage
        if result.model_used == PREMIUM_MODEL or "sonnet" in result.model_used.lower():
            stats.premium_model_used += 1
        else:
            stats.standard_model_used += 1
        
        # Apply patch
        patch = result.to_patch()
        updated_museum = {**museum, **patch}
        updated_museum["updated_at"] = now_utc_iso()
        
        stats.generated += 1
        
        # Print progress
        model_label = "🎨 Premium" if stats.premium_model_used > stats.generated - 1 else "Standard"
        summary_preview = result.summary[:60] + "..." if result.summary and len(result.summary) > 60 else result.summary
        print(f"  [{i}/{len(museums)}] {museum_name}")
        print(f"           ✓ {model_label} | {summary_preview}")
        
        updated_museums.append(updated_museum)
    
    # Write updated state file
    if not dry_run and stats.generated > 0:
        state_data["museums"] = updated_museums
        state_data["updated_at"] = now_utc_iso()
        save_json(state_path, state_data)
        print(f"  Saved changes to {state_path}")
    
    return stats


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Phase 2.5: Museum Content Generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    
    # Scope selection (required)
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--state", help="Two-letter state code (e.g., CO)")
    scope.add_argument("--states", help="Comma-separated state codes (e.g., CO,UT,WY)")
    scope.add_argument("--all-states", action="store_true", help="Process all states")
    
    # Options
    parser.add_argument("--force", action="store_true", help="Force regeneration even if content exists")
    parser.add_argument("--dry-run", action="store_true", help="Don't write changes")
    parser.add_argument("--provider", choices=["openai", "anthropic"], help="Override LLM provider")
    
    args = parser.parse_args()
    
    # Override provider if specified
    if args.provider:
        global LLM_PROVIDER
        LLM_PROVIDER = args.provider
    
    # Determine state codes to process
    states: list[str] = []
    
    if args.all_states:
        states = sorted([
            p.stem.upper() for p in STATES_DIR.glob("*.json")
            if len(p.stem) == 2 and p.stem.isalpha()
        ])
    elif args.states:
        states = [s.strip().upper() for s in args.states.split(",")]
    elif args.state:
        states = [args.state.upper()]
    
    # Create run directory
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_dir = RUNS_DIR / f"phase2_5-{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Print header
    print("=" * 60)
    print("Phase 2.5: Museum Content Generation")
    print("=" * 60)
    print(f"States: {', '.join(states)}")
    print(f"Provider: {LLM_PROVIDER}")
    print(f"Premium model (art museums): {PREMIUM_MODEL}")
    print(f"Standard model (other museums): {STANDARD_MODEL}")
    print(f"Force: {args.force}")
    print(f"Dry run: {args.dry_run}")
    print(f"Run ID: {run_id}")
    print("=" * 60)
    print()
    
    # Process each state
    total_stats = Phase25Stats()
    
    for state_code in states:
        stats = process_state(state_code, force=args.force, dry_run=args.dry_run)
        
        # Aggregate statistics
        total_stats.total_processed += stats.total_processed
        total_stats.generated += stats.generated
        total_stats.skipped_has_content += stats.skipped_has_content
        total_stats.skipped_no_data += stats.skipped_no_data
        total_stats.errors += stats.errors
        total_stats.premium_model_used += stats.premium_model_used
        total_stats.standard_model_used += stats.standard_model_used
    
    # Print summary
    print()
    print("=" * 60)
    print("Phase 2.5 Complete")
    print("=" * 60)
    print(f"  Total processed:         {total_stats.total_processed}")
    print(f"  Content generated:       {total_stats.generated}")
    print(f"  🎨 Premium model used:   {total_stats.premium_model_used} (art museums)")
    print(f"  📝 Standard model used:  {total_stats.standard_model_used} (other museums)")
    print(f"  Skipped (has content):   {total_stats.skipped_has_content}")
    print(f"  Skipped (no data):       {total_stats.skipped_no_data}")
    print(f"  Errors:                  {total_stats.errors}")
    print()
    print(f"  Run directory: {run_dir}")
    print("=" * 60)
    
    # Save summary
    summary = {
        "run_id": run_id,
        "states": states,
        "provider": LLM_PROVIDER,
        "premium_model": PREMIUM_MODEL,
        "standard_model": STANDARD_MODEL,
        "force": args.force,
        "dry_run": args.dry_run,
        "total_processed": total_stats.total_processed,
        "generated": total_stats.generated,
        "premium_model_used": total_stats.premium_model_used,
        "standard_model_used": total_stats.standard_model_used,
        "skipped_has_content": total_stats.skipped_has_content,
        "skipped_no_data": total_stats.skipped_no_data,
        "errors": total_stats.errors,
        "completed_at": now_utc_iso(),
    }
    save_json(run_dir / "summary.json", summary)
    
    return 0 if total_stats.errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
