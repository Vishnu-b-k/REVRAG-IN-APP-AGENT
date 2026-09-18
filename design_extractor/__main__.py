"""
CLI entrypoint for the design_extractor module.

Usage:
    # Extract tokens for a single screen:
    python -m design_extractor --input fixtures/screen_login.json --output tokens.json

    # Extract tokens for all screens in a knowledge pack:
    python -m design_extractor --pack docs/sample_knowledge_pack.json --output enriched_pack.json

    # Aggregate mode — enrich a pack with per-screen tokens + global design system:
    python -m design_extractor --aggregate --pack docs/sample_knowledge_pack.json --output enriched_pack.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from design_extractor.extractor import extract_design_tokens, extract_from_file
from design_extractor.aggregator import aggregate_design_system, enrich_knowledge_pack


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="design_extractor",
        description="Extract visual design tokens from knowledge pack screen data.",
    )

    parser.add_argument(
        "--input",
        type=str,
        help="Path to a single screen fixture JSON file.",
    )
    parser.add_argument(
        "--pack",
        type=str,
        help="Path to a full knowledge pack JSON file.",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output path. Defaults to stdout.",
    )
    parser.add_argument(
        "--aggregate",
        action="store_true",
        help="Aggregate per-screen tokens into a global design system (requires --pack).",
    )
    parser.add_argument(
        "--screen-dir",
        type=str,
        default=None,
        help="Directory containing per-screen fixture JSON files (alternative to --pack).",
    )

    return parser.parse_args()


def _write_output(data: dict | list, output_path: str | None) -> None:
    """Write JSON output to file or stdout."""
    text = json.dumps(data, indent=2, ensure_ascii=False)
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(text)
        print(f"✓ Output written to {output_path}", file=sys.stderr)
    else:
        print(text)


def main() -> None:
    args = _parse_args()

    # --- Single screen mode ---
    if args.input:
        result = extract_from_file(args.input)
        _write_output(result["design_tokens"], args.output)
        return

    # --- Pack mode ---
    if args.pack:
        with open(args.pack, "r") as f:
            pack_data = json.load(f)

        screens = pack_data.get("screens", [])
        if not screens:
            print("⚠ No screens found in pack.", file=sys.stderr)
            sys.exit(1)

        # Extract tokens per screen
        all_tokens = []
        for screen in screens:
            tokens = extract_design_tokens(screen)
            all_tokens.append(tokens)
            print(f"  ✓ Extracted tokens for screen: {screen.get('name', screen.get('id', '?'))}", file=sys.stderr)

        if args.aggregate:
            # Enrich the pack with per-screen tokens + global design system
            result = enrich_knowledge_pack(pack_data, all_tokens)
            _write_output(result, args.output)
        else:
            # Output only the per-screen tokens
            _write_output(all_tokens, args.output)

        return

    # --- Screen directory mode ---
    if args.screen_dir:
        screen_dir = Path(args.screen_dir)
        if not screen_dir.is_dir():
            print(f"✗ Directory not found: {args.screen_dir}", file=sys.stderr)
            sys.exit(1)

        files = sorted(screen_dir.glob("screen_*.json"))
        if not files:
            print(f"⚠ No screen_*.json files found in {args.screen_dir}", file=sys.stderr)
            sys.exit(1)

        all_tokens = []
        for fp in files:
            result = extract_from_file(str(fp))
            all_tokens.append(result["design_tokens"])
            print(f"  ✓ Extracted tokens for: {fp.name}", file=sys.stderr)

        if args.aggregate:
            gds = aggregate_design_system(all_tokens)
            _write_output({"per_screen_tokens": all_tokens, "global_design_system": gds}, args.output)
        else:
            _write_output(all_tokens, args.output)

        return

    # No input specified
    print("✗ Provide --input, --pack, or --screen-dir. Use --help for usage.", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
