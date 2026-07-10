"""Command line interface for rice."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from typing import Any

from .core import (
    BundleAssignmentCensusResult,
    CountResult,
    SupportCensusResult,
    count_networks,
    simple_bundle_assignment_census,
    support_census,
)


_COUNT_OPTION_NAMES = ("--max-r", "--max-reactive", "--mode")
_LEGACY_GLOBAL_OPTION_NAMES = (*_COUNT_OPTION_NAMES, "--format")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rice",
        description="RICE — Resistor-Inductor-Capacitor Enumerator for small two-terminal RLC one-port topology classes.",
        epilog=(
            "Subcommand options go after the subcommand. The no-subcommand "
            "legacy count form is retained for compatibility."
        ),
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
        "--max-r",
        type=int,
        default=argparse.SUPPRESS,
        help="component-budget resistor limit; with --max-reactive derives max_edges=max_r+max_reactive",
    )
    supports_parser.add_argument(
        "--max-reactive",
        type=int,
        default=argparse.SUPPRESS,
        help="component-budget reactive limit; with --max-r derives max_edges=max_r+max_reactive",
    )
    supports_parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default=argparse.SUPPRESS,
        help="output format, default: markdown",
    )

    bundles_parser = subparsers.add_parser(
        "bundles", help="run the phase-2 raw simple-bundle assignment census"
    )
    bundles_parser.add_argument(
        "--max-r",
        type=int,
        default=argparse.SUPPRESS,
        help="maximum number of resistors, default: 3",
    )
    bundles_parser.add_argument(
        "--max-reactive",
        type=int,
        default=argparse.SUPPRESS,
        help="maximum total number of reactive elements, default: 5",
    )
    bundles_parser.add_argument(
        "--max-edges",
        type=int,
        default=argparse.SUPPRESS,
        help="optional debugging/truncation support-edge count; default: max_r + max_reactive; cannot exceed that derived bound",
    )
    bundles_parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default=argparse.SUPPRESS,
        help="output format, default: markdown",
    )

    # Preserve the original no-subcommand interface for the legacy count, but
    # hide these compatibility options from top-level help so they are not
    # mistaken for options that apply to every subcommand.
    _add_count_arguments(parser, suppress_defaults=True, hide_help=True)
    return parser


def _add_count_arguments(
    parser: argparse.ArgumentParser,
    *,
    suppress_defaults: bool = False,
    hide_help: bool = False,
) -> None:
    default = argparse.SUPPRESS if suppress_defaults else None
    help_text = argparse.SUPPRESS if hide_help else None
    parser.add_argument(
        "--max-r",
        type=int,
        default=default,
        help=help_text or "maximum number of resistors, default: 3",
    )
    parser.add_argument(
        "--max-reactive",
        type=int,
        default=default,
        help=help_text or "maximum total number of reactive elements, default: 5",
    )
    parser.add_argument(
        "--mode",
        choices=("lc", "generic"),
        default=default,
        help=help_text
        or "'lc' distinguishes L and C; 'generic' treats reactive elements as X",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default=default,
        help=help_text or "output format, default: markdown",
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


def _bundle_assignment_census_json(
    result: BundleAssignmentCensusResult,
) -> dict[str, Any]:
    """Return phase-2 bundle-census data including computed totals."""

    payload = asdict(result)
    payload.update(
        {
            "relevant_supports_total": result.relevant_supports_total,
            "leaf_assignments_total": result.leaf_assignments_total,
        }
    )
    return payload


def _count_json(result: CountResult) -> dict[str, Any]:
    """Return legacy count data including computed totals for JSON output."""

    payload = asdict(result)
    payload["total"] = result.total
    return payload


def _option_name(token: str) -> str:
    return token.split("=", 1)[0]


def _reject_legacy_globals_before_supports(
    parser: argparse.ArgumentParser, argv: list[str]
) -> None:
    """Reject compatibility global options that would otherwise be ignored."""

    subcommands = {"supports", "bundles"}
    command_indexes = [i for i, token in enumerate(argv) if token in subcommands]
    if not command_indexes:
        return
    command_index = min(command_indexes)
    legacy_options = {
        _option_name(token)
        for token in argv[:command_index]
        if token.startswith("--") and _option_name(token) in _LEGACY_GLOBAL_OPTION_NAMES
    }
    if legacy_options:
        options = ", ".join(sorted(legacy_options))
        parser.error(
            f"options {options} must be placed after the subcommand "
            "when used with support or bundle census"
        )


def _resolve_support_max_edges(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    has_max_edges = hasattr(args, "max_edges")
    has_max_r = hasattr(args, "max_r")
    has_max_reactive = hasattr(args, "max_reactive")

    if has_max_edges and (has_max_r or has_max_reactive):
        parser.error(
            "supports --max-edges is mutually exclusive with supports "
            "--max-r/--max-reactive component budgets"
        )
    if has_max_r != has_max_reactive:
        parser.error("supports --max-r and --max-reactive must be provided together")
    if has_max_r and has_max_reactive:
        return args.max_r + args.max_reactive
    if has_max_edges:
        return args.max_edges
    return 8


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    _reject_legacy_globals_before_supports(parser, argv)
    args = parser.parse_args(argv)

    output_format = getattr(args, "format", "markdown")

    if args.command == "supports":
        max_edges = _resolve_support_max_edges(parser, args)
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

    if args.command == "bundles":
        max_r = getattr(args, "max_r", 3)
        max_reactive = getattr(args, "max_reactive", 5)
        max_edges = getattr(args, "max_edges", None)
        if max_edges is not None and max_edges > max_r + max_reactive:
            parser.error("bundles --max-edges cannot exceed --max-r + --max-reactive")
        result = simple_bundle_assignment_census(
            max_r=max_r, max_reactive=max_reactive, max_edges=max_edges
        )
        if output_format == "json":
            print(
                json.dumps(
                    _bundle_assignment_census_json(result), indent=2, sort_keys=True
                )
            )
        else:
            print(
                "Simple-bundle assignment census: "
                f"R <= {result.max_r}, L+C <= {result.max_reactive}, "
                f"max_edges <= {result.max_edges}"
            )
            print(
                "Raw assignment leaves before automorphism quotienting or "
                "reduced signatures."
            )
            print(
                "| Support edges | Relevant supports | "
                "Valid bundle assignments per support | Leaf assignments |"
            )
            print("|---:|---:|---:|---:|")
            for edge_count in range(1, result.max_edges + 1):
                print(
                    f"| {edge_count} | {result.relevant_supports_by_edges[edge_count]} | "
                    f"{result.assignments_per_support_by_edges[edge_count]} | "
                    f"{result.leaf_assignments_by_edges[edge_count]} |"
                )
            print(
                f"| Total | {result.relevant_supports_total} | — | "
                f"{result.leaf_assignments_total} |"
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
