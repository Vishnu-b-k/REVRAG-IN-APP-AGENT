"""
CLI entrypoint for the rebuild_test module.

Usage:
    # Rebuild all screens from a knowledge pack:
    python -m rebuild_test --input docs/sample_knowledge_pack.json --output-dir output/rebuild/

    # Rebuild specific screens:
    python -m rebuild_test --input docs/sample_knowledge_pack.json --output-dir output/rebuild/ --screens scr_login_01 scr_otp_02

    # Full comparison with demo artifacts:
    python -m rebuild_test --compare --input docs/sample_knowledge_pack.json --output-dir demo/rebuild/
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rebuild_test.rebuilder import rebuild_from_pack, rebuild_to_files
from rebuild_test.compare import compare_pack, generate_demo_artifacts


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="rebuild_test",
        description="Rebuild screens from knowledge pack data (no original screenshots).",
    )

    parser.add_argument(
        "--input", "-i",
        type=str,
        required=True,
        help="Path to a knowledge pack JSON file.",
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="output/rebuild",
        help="Output directory for rebuilt HTML files. Default: output/rebuild/",
    )
    parser.add_argument(
        "--screens",
        nargs="*",
        default=None,
        help="Specific screen IDs to rebuild. Default: all screens.",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Generate comparison metrics and demo artifacts.",
    )

    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    # Load knowledge pack
    pack_path = Path(args.input)
    if not pack_path.exists():
        print(f"✗ File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    with open(pack_path, "r") as f:
        pack_data = json.load(f)

    screens = pack_data.get("screens", [])
    if not screens:
        print("⚠ No screens found in pack.", file=sys.stderr)
        sys.exit(1)

    screen_ids = args.screens

    # Rebuild screens
    print(f"📦 Loaded pack with {len(screens)} screens", file=sys.stderr)

    rebuilt = rebuild_from_pack(pack_data, screen_ids)
    print(f"🏗️  Rebuilt {len(rebuilt)} screens:", file=sys.stderr)
    for sid in rebuilt:
        print(f"  ✓ {sid}", file=sys.stderr)

    # Write HTML files
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for sid, html_content in rebuilt.items():
        filepath = out_dir / f"{sid}_rebuilt.html"
        filepath.write_text(html_content, encoding="utf-8")
        print(f"  → {filepath}", file=sys.stderr)

    if args.compare:
        # Generate comparison report + demo artifacts
        print("\n📊 Generating comparison report...", file=sys.stderr)
        artifacts = generate_demo_artifacts(pack_data, rebuilt, str(out_dir))
        print(f"  Generated {len(artifacts)} artifacts:", file=sys.stderr)
        for a in artifacts:
            print(f"  → {a}", file=sys.stderr)

        # Print summary
        report = compare_pack(pack_data, rebuilt)
        summary = report.get("summary", {})
        print(f"\n{'='*50}", file=sys.stderr)
        print(f"  Screens rebuilt:     {summary.get('screens_rebuilt', 0)}/{summary.get('screens_in_pack', 0)}", file=sys.stderr)
        print(f"  Avg overall score:   {summary.get('average_overall_score', 0):.0%}", file=sys.stderr)
        print(f"  Avg element coverage:{summary.get('average_element_coverage', 0):.0%}", file=sys.stderr)
        print(f"  Avg text coverage:   {summary.get('average_text_coverage', 0):.0%}", file=sys.stderr)
        print(f"{'='*50}", file=sys.stderr)

    print(f"\n✅ Done. Open {out_dir}/comparison_summary.html to view results.", file=sys.stderr)


if __name__ == "__main__":
    main()
