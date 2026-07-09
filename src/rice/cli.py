"""Command line interface for rice."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from typing import Any

from .core import CountResult, SupportCensusResult, count_networks, support_census


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rice",
        description="RICE — Resistor-Inductor-Capacitor Enumerator for small two-terminal RLC one-port topology classes.",
    )
    subparsers = parser.add_subparsers(dest="command")

    count_parser = subparsers.add_parser(
        "count", help="run the legacy component-bundle count"
    )
    _add_count_arguments(count_parser, suppress_defaults=True)

    supports_parser = subparsers.add_parser(
        "supports", help="run the phase-1 support graph census"
    )
    supports_parser.add_argument(
        "--max-edges",
        type=int,
        default=argparse.SUPPRESS,
        help="maximum support-edge count, default: 8",
    )
    supports_parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default=argparse.SUPPRESS,
        help="output format, default: markdown",
    )

    # Preserve the original no-subcommand interface for the legacy count.
    _add_count_arguments(parser, suppress_defaults=True)
    return parser


def _add_count_arguments(
    parser: argparse.ArgumentParser, *, suppress_defaults: bool = False
) -> None:
    default = argparse.SUPPRESS if suppress_defaults else None
    parser.add_argument(
        "--max-r",
        type=int,
        default=default,
        help="maximum number of resistors, default: 3",
    )
    parser.add_argument(
        "--max-reactive",
        type=int,
        default=default,
        help="maximum total number of reactive elements, default: 5",
    )
    parser.add_argument(
        "--mode",
        choices=("lc", "generic"),
        default=default,
        help="'lc' distinguishes L and C; 'generic' treats reactive elements as X",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default=default,
        help="output format, default: markdown",
    )


def _support_census_json(result: SupportCensusResult) -> dict[str, Any]:
    """Return support-census data including computed totals for JSON output."""

    payload = asdict(result)
    payload.update(
        {
            "basic_total": result.basic_total,
            "terminal_labelings_total": result.terminal_labelings_total,
            "relevant_total": result.relevant_total,
        }
    )
    return payload


def _count_json(result: CountResult) -> dict[str, Any]:
    """Return legacy count data including computed totals for JSON output."""

    payload = asdict(result)
    payload["total"] = result.total
    return payload


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    output_format = getattr(args, "format", "markdown")

    if args.command == "supports":
        max_edges = getattr(args, "max_edges", 8)
        result = support_census(max_edges=max_edges)
        if output_format == "json":
            print(json.dumps(_support_census_json(result), indent=2, sort_keys=True))
        else:
            print(f"Support census: max_edges <= {result.max_edges}")
            print(
                "| Support edges | Basic connected unlabelled graphs | Unordered two-terminal labelings | Terminal-relevant two-terminal graphs |"
            )
            print("|---:|---:|---:|---:|")
            for edge_count in range(1, result.max_edges + 1):
                print(
                    f"| {edge_count} | {result.basic_by_edges[edge_count]} | "
                    f"{result.terminal_labelings_by_edges[edge_count]} | "
                    f"{result.relevant_by_edges[edge_count]} |"
                )
            print(
                f"| Total | {result.basic_total} | {result.terminal_labelings_total} | "
                f"{result.relevant_total} |"
            )
        return 0

    max_r = getattr(args, "max_r", 3)
    max_reactive = getattr(args, "max_reactive", 5)
    mode = getattr(args, "mode", "lc")
    result = count_networks(max_r=max_r, max_reactive=max_reactive, mode=mode)

    if output_format == "json":
        print(json.dumps(_count_json(result), indent=2, sort_keys=True))
    else:
        reactive_label = "L+C" if mode == "lc" else "X"
        print(f"Mode: {mode}  (reactive column is {reactive_label})")
        print(f"Limits: R <= {max_r}, reactive <= {max_reactive}")
        print(f"Terminal-relevant two-terminal support graphs: {result.support_count}")
        print(
            f"Terminal-relevant support graphs by support-edge count: {result.support_count_by_edges}"
        )
        print()
        print(result.as_markdown_table())
        print()
        print(f"Total: {result.total}")
        if max_r >= 3:
            print(
                f"Exactly R=3, reactive <= {max_reactive}: {result.exactly_r_total(3)}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
