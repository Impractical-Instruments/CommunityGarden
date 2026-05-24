#!/usr/bin/env python3
"""Merge contributor BodyCaptcha level JSONs into the master JSON.

Identity is (image, prompt). Exact duplicates are silently deduplicated.
Levels with the same identity but differing fields are reported as
conflicts; the first source wins (so the master always beats contributors
when it appears first on the command line).

Output is sorted by (image, prompt) so future merges produce clean diffs.

Examples:
    python merge_levels.py ../bodycaptcha-levels.json contrib/alice.json \\
        -o ../bodycaptcha-levels.json

    python merge_levels.py ../bodycaptcha-levels.json contrib/*.json \\
        --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _load(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text())
    except Exception as e:
        print(f"ERROR: failed to read {path}: {e}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(data, list):
        print(f"ERROR: {path} is not a JSON array", file=sys.stderr)
        sys.exit(2)
    return data


def _identity(level: dict) -> tuple[str, str]:
    return (level.get("image") or "", level.get("prompt") or "")


def _normalize(level: dict) -> dict:
    out = dict(level)
    if "valid_cells" in out:
        out["valid_cells"] = sorted(tuple(c) for c in out["valid_cells"])
    if "grid" in out:
        out["grid"] = tuple(out["grid"])
    return out


def _equiv(a: dict, b: dict) -> bool:
    return _normalize(a) == _normalize(b)


def merge(sources: list[tuple[str, list[dict]]]) -> tuple[list[dict], list[str]]:
    """Merge level lists in source order; first occurrence of each identity wins.

    Returns (merged_levels_sorted, conflict_messages).
    """
    seen: dict[tuple[str, str], tuple[str, dict]] = {}
    conflicts: list[str] = []
    for source_name, levels in sources:
        for lv in levels:
            key = _identity(lv)
            if key in seen:
                prev_source, prev_level = seen[key]
                if _equiv(prev_level, lv):
                    continue
                conflicts.append(
                    f"CONFLICT  image={key[0]!r}  prompt={key[1]!r}\n"
                    f"  kept from : {prev_source}  {json.dumps(_diff_fields(prev_level))}\n"
                    f"  ignored   : {source_name}  {json.dumps(_diff_fields(lv))}"
                )
            else:
                seen[key] = (source_name, lv)
    merged = sorted((lv for _, lv in seen.values()), key=_identity)
    return merged, conflicts


def _diff_fields(lv: dict) -> dict:
    """Subset of fields useful for conflict reporting (excludes the identity keys)."""
    return {k: v for k, v in lv.items() if k not in ("image", "prompt")}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Merge BodyCaptcha level JSONs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Exit code is non-zero if any conflicts were detected.",
    )
    ap.add_argument("master", help="Master levels JSON (read first; wins ties)")
    ap.add_argument("contributors", nargs="+", help="Contributor levels JSONs")
    ap.add_argument("-o", "--output",
                    help="Write merged JSON to this path (default: stdout)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Report only; do not write output")
    args = ap.parse_args(argv)

    sources: list[tuple[str, list[dict]]] = []
    for path_str in [args.master] + args.contributors:
        path = Path(path_str)
        sources.append((path.name, _load(path)))

    merged, conflicts = merge(sources)

    total_in = sum(len(lv) for _, lv in sources)
    print(
        f"Merged {total_in} input levels from {len(sources)} source(s) "
        f"-> {len(merged)} unique ({len(conflicts)} conflict(s)).",
        file=sys.stderr,
    )
    for c in conflicts:
        print(c, file=sys.stderr)

    if args.dry_run:
        return 1 if conflicts else 0

    text = json.dumps(merged, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(text)
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(text)

    return 1 if conflicts else 0


if __name__ == "__main__":
    raise SystemExit(main())
