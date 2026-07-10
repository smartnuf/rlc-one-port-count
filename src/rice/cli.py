"""Command line interface for rice."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from typing import Any

from .core import (
    BundleAssignmentCensusResult,
    BundleLabelingCensusResult,
    ReducedTopologyCensusResult,
    SupportCensusResult,
    simple_bundle_assignment_census,
    reduced_topology_census,
    simple_bundle_labeling_census,
    support_census,
)


_REDUCED_DEFAULT_MAX_R = 2
_REDUCED_DEFAULT_MAX_REACTIVE = 3


class RiceArgumentParser(argparse.ArgumentParser):
    """ArgumentParser with repository-wide CLI parsing policy."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("allow_abbrev", False)
        super().__init__(*args, **kwargs)


def build_parser() -> argparse.ArgumentParser:
    parser = RiceArgumentParser(
        prog="rice",
        description="RICE — Resistor-Inductor-Capacitor Enumerator for small two-terminal RLC one-port topology classes.",
        epilog="Subcommand options go after the subcommand.",
    )
    subparsers = parser.add_subparsers(
        dest="command", parser_class=RiceArgumentParser, required=True
    )

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

    labelings_parser = subparsers.add_parser(
        "labelings",
        help="run the phase-3 canonical simple-bundle labeling-orbit census",
    )
    labelings_parser.add_argument(
        "--max-r",
        type=int,
        default=argparse.SUPPRESS,
        help="maximum number of resistors, default: 3",
    )
    labelings_parser.add_argument(
        "--max-reactive",
        type=int,
        default=argparse.SUPPRESS,
        help="maximum total number of reactive elements, default: 5",
    )
    labelings_parser.add_argument(
        "--max-edges",
        type=int,
        default=argparse.SUPPRESS,
        help="optional debugging/truncation support-edge count; default: max_r + max_reactive; cannot exceed that derived bound",
    )
    labelings_parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default=argparse.SUPPRESS,
        help="output format, default: markdown",
    )

    reduced_parser = subparsers.add_parser(
        "reduced",
        help="run the canonical reduced-topology census",
    )
    reduced_parser.add_argument(
        "--max-r",
        type=int,
        default=argparse.SUPPRESS,
        help=f"maximum number of resistors, default: {_REDUCED_DEFAULT_MAX_R}",
    )
    reduced_parser.add_argument(
        "--max-reactive",
        type=int,
        default=argparse.SUPPRESS,
        help=(
            "maximum total number of reactive elements, "
            f"default: {_REDUCED_DEFAULT_MAX_REACTIVE}"
        ),
    )
    reduced_parser.add_argument(
        "--max-edges",
        type=int,
        default=argparse.SUPPRESS,
        help="optional debugging/truncation support-edge count; default: max_r + max_reactive; cannot exceed that derived bound",
    )
    reduced_parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default=argparse.SUPPRESS,
        help="output format, default: markdown",
    )

    return parser


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


def _bundle_labeling_census_json(result: BundleLabelingCensusResult) -> dict[str, Any]:
    """Return phase-3 bundle-labeling census data including totals."""

    payload = asdict(result)
    payload.update(
        {
            "relevant_supports_total": result.relevant_supports_total,
            "raw_leaf_assignments_total": result.raw_leaf_assignments_total,
            "canonical_labeling_orbits_total": result.canonical_labeling_orbits_total,
        }
    )
    return payload


def _reduced_topology_census_json(
    result: ReducedTopologyCensusResult,
) -> dict[str, Any]:
    """Return reduced-topology census data using a stable documented shape."""

    regeneration_command = (
        ".venv/bin/python -m rice reduced "
        f"--max-r {result.max_r} --max-reactive {result.max_reactive} --format json"
    )
    return {
        "format_version": 1,
        "scope": {
            "max_r": result.max_r,
            "max_reactive": result.max_reactive,
            "max_edges": result.max_edges,
        },
        "definition": "canonical-reduced-topology-local-series-parallel-v1",
        "equivalence": (
            "internal node renaming, terminal reversal, local commutative series/parallel "
            "normalisation, and duplicate primitive singleton merging; not rational immittance equivalence"
        ),
        "exact_counts_by_r_x": [list(row) for row in result.exact_table],
        "total": result.total,
        "diagnostics": {
            "raw_phase2_assignments_total": result.raw_leaf_assignments_total,
            "phase3_assigned_support_labeling_orbits_total": result.canonical_labeling_orbits_total,
            "canonical_reduced_signatures_total": result.total,
        },
        "regeneration_command": (
            f".venv/bin/python -m rice reduced --max-r {result.max_r} "
            f"--max-reactive {result.max_reactive} --format json"
        ),
    }


def _validate_nonnegative(
    parser: argparse.ArgumentParser, command: str, option: str, value: int
) -> None:
    if value < 0:
        parser.error(f"{command} {option} must be nonnegative")


def _validate_positive(
    parser: argparse.ArgumentParser, command: str, option: str, value: int
) -> None:
    if value <= 0:
        parser.error(f"{command} {option} must be a positive integer")


def _resolve_component_census_limits(
    parser: argparse.ArgumentParser,
    command: str,
    args: argparse.Namespace,
    *,
    default_max_r: int,
    default_max_reactive: int,
) -> tuple[int, int, int | None]:
    max_r = getattr(args, "max_r", default_max_r)
    max_reactive = getattr(args, "max_reactive", default_max_reactive)
    max_edges = getattr(args, "max_edges", None)
    _validate_nonnegative(parser, command, "--max-r", max_r)
    _validate_nonnegative(parser, command, "--max-reactive", max_reactive)
    natural_max_edges = max_r + max_reactive
    if max_edges is not None:
        if natural_max_edges > 0:
            _validate_positive(parser, command, "--max-edges", max_edges)
        elif max_edges < 0:
            parser.error(
                f"{command} --max-edges must be nonnegative when component budgets are zero"
            )
        if max_edges > natural_max_edges:
            parser.error(f"{command} --max-edges cannot exceed --max-r + --max-reactive")
    return max_r, max_reactive, max_edges


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
        _validate_nonnegative(parser, "supports", "--max-r", args.max_r)
        _validate_nonnegative(parser, "supports", "--max-reactive", args.max_reactive)
        max_edges = args.max_r + args.max_reactive
        if max_edges <= 0:
            parser.error("supports --max-r + --max-reactive must be positive")
        return max_edges
    if has_max_edges:
        _validate_positive(parser, "supports", "--max-edges", args.max_edges)
        return args.max_edges
    return 8


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
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
        max_r, max_reactive, max_edges = _resolve_component_census_limits(
            parser, "bundles", args, default_max_r=3, default_max_reactive=5
        )
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

    if args.command == "labelings":
        max_r, max_reactive, max_edges = _resolve_component_census_limits(
            parser, "labelings", args, default_max_r=3, default_max_reactive=5
        )
        result = simple_bundle_labeling_census(
            max_r=max_r, max_reactive=max_reactive, max_edges=max_edges
        )
        if output_format == "json":
            print(
                json.dumps(
                    _bundle_labeling_census_json(result), indent=2, sort_keys=True
                )
            )
        else:
            print(
                "Canonical simple-bundle labeling census: "
                f"R <= {result.max_r}, L+C <= {result.max_reactive}, "
                f"max_edges <= {result.max_edges}"
            )
            print(
                "Raw leaves are phase-2 assignments; canonical labelings are "
                "orbits under terminal-set-preserving support automorphisms."
            )
            print(
                "| Support edges | Relevant supports | Raw assignment leaves | "
                "Canonical bundle-labeling orbits |"
            )
            print("|---:|---:|---:|---:|")
            for edge_count in range(1, result.max_edges + 1):
                print(
                    f"| {edge_count} | {result.relevant_supports_by_edges[edge_count]} | "
                    f"{result.raw_leaf_assignments_by_edges[edge_count]} | "
                    f"{result.canonical_labeling_orbits_by_edges[edge_count]} |"
                )
            print(
                f"| Total | {result.relevant_supports_total} | "
                f"{result.raw_leaf_assignments_total} | "
                f"{result.canonical_labeling_orbits_total} |"
            )
        return 0

    if args.command == "reduced":
        max_r = getattr(args, "max_r", _REDUCED_DEFAULT_MAX_R)
        max_reactive = getattr(
            args, "max_reactive", _REDUCED_DEFAULT_MAX_REACTIVE
        )
        max_edges = getattr(args, "max_edges", None)
        if max_edges is not None and max_edges > max_r + max_reactive:
            parser.error("reduced --max-edges cannot exceed --max-r + --max-reactive")
        result = reduced_topology_census(
            max_r=max_r, max_reactive=max_reactive, max_edges=max_edges
        )
        if output_format == "json":
            print(
                json.dumps(
                    _reduced_topology_census_json(result), indent=2, sort_keys=True
                )
            )
        else:
            print(
                "Canonical reduced-topology census: "
                f"R <= {result.max_r}, L+C <= {result.max_reactive}, "
                f"max_edges <= {result.max_edges}"
            )
            print(
                "Exact table entries are reduced primitive counts. "
                "L and C remain distinct topology labels, aggregated by L+C columns."
            )
            print(
                "Equivalence: internal node renaming, terminal reversal, "
                "local commutative series/parallel normalisation, and duplicate "
                "primitive singleton merging."
            )
            print("This is not full rational-immittance equivalence.")
            print()
            print(result.as_markdown_table())
            print()
            print(f"Cumulative reduced-topology total: {result.total}")
            print(
                "Diagnostics: "
                f"raw phase-2 assignments={result.raw_leaf_assignments_total}; "
                f"phase-3 labeling orbits={result.canonical_labeling_orbits_total}; "
                f"canonical reduced signatures={result.total}"
            )
        return 0

    raise AssertionError(f"unhandled subcommand {args.command!r}")


if __name__ == "__main__":
    raise SystemExit(main())
