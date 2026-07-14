"""Command line interface for rice."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .core import (
    COUNT_PROFILES,
    DEFAULT_ENUM_MAX_RECORDS,
    SIMPLE_PRIMITIVE_BUNDLES,
    ComponentConstraints,
    CountQuery,
    SupportCensusResult,
    assignment_census,
    assigned_support_census,
    bundle_set_census,
    enum_assigned_supports,
    enum_assignments,
    enum_bundle_sets,
    enum_bundle_types,
    enum_networks,
    enum_supports,
    network_census,
    reduction_census,
    support_census,
)


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


class RiceArgumentParser(argparse.ArgumentParser):
    """ArgumentParser with repository-wide CLI parsing policy."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("allow_abbrev", False)
        super().__init__(*args, **kwargs)


PROFILE_HELP = "Profiles: golden (R<=2, L+C<=3); main (R<=3, L+C<=5); ladenheim-structural-region (R+L+C<=5, L+C<=2); ladenheim-108-region (R+L+C<=5, R<=3, L+C<=2)."
SCOPE_HELP = "Finite scope: commands over source objects need a finite support-edge range, supplied by a finite profile/component budget, --support-edges, or --max-support-edges. Network and reduction counts/enums also work for fixed finite support-edge ranges because each source edge has one of seven simple bundle types."
GROUP_HELP = "Grouping dimensions: support-edges, r, l, c, lc, rlc, or none (networks: r, l, c, lc, rlc, or none)."
OUTPUT_HELP = "Output: auto chooses table for an interactive terminal and JSON when redirected; table is human-readable; markdown and json are deterministic."
RELATION_HELP = "Network relation choices: local-sp (canonical local series/parallel reduced topology; not rational immittance equivalence)."

TOP_DESCRIPTION = """RICE — Resistor-Inductor-Capacitor Enumerator for small two-terminal RLC one-port topology classes.

Command language map:
  count supports           source unlabelled support shapes, terminal labellings, and terminal-relevant supports
  count bundle-types       the seven simple primitive edge bundle labels
  count bundle-sets        source bundle inventories before support placement
  count assignments        source component-labelled placements on relevant supports
  count assigned-supports  assignments modulo terminal-set-preserving support automorphisms
  count networks           reduced objects under the local-sp reduced-topology relation
  count reductions         provenance of assignments -> assigned-supports -> networks

  enum supports | bundle-types | bundle-sets | assignments | assigned-supports | networks

Pipeline: supports -> bundle-types -> bundle-sets -> assignments -> assigned-supports -> networks; reductions summarize the many-to-one transitions.
Leaf help: rice help count networks, rice count networks --help, or rice --help count networks.
Example finite scope: rice count networks --profile golden --format table
"""


def build_parser() -> argparse.ArgumentParser:
    parser = RiceArgumentParser(
        prog="rice",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=TOP_DESCRIPTION,
        epilog=f"{PROFILE_HELP}\n{SCOPE_HELP}\n{OUTPUT_HELP}",
    )
    subparsers = parser.add_subparsers(
        dest="verb", metavar="<verb>", parser_class=RiceArgumentParser, required=False
    )

    count_parser = subparsers.add_parser(
        "count", help="count RICE objects, including reductions", formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Count objects along the source-to-reduced RICE pipeline.\n\n" + PROFILE_HELP + "\n" + SCOPE_HELP,
    )
    count_subparsers = count_parser.add_subparsers(
        dest="object", metavar="<count-target>", parser_class=RiceArgumentParser, required=False
    )

    def add_count_scope_options(target_parser: argparse.ArgumentParser) -> None:
        profile_group = target_parser.add_mutually_exclusive_group()
        profile_group.add_argument("--profile", choices=tuple(COUNT_PROFILES), default=argparse.SUPPRESS, help=PROFILE_HELP + " Default: none.")
        profile_group.add_argument("--max-rlc", type=int, default=argparse.SUPPRESS, help="maximum total R+L+C components. Default: none")
        # argparse cannot put multiple explicit options in one mutual-exclusion slot;
        # cross-option profile conflicts are validated centrally after parsing.
        target_parser.add_argument("--max-r", type=int, default=argparse.SUPPRESS, help="maximum resistors. Default: none")
        target_parser.add_argument("--max-l", type=int, default=argparse.SUPPRESS, help="maximum inductors. Default: none")
        target_parser.add_argument("--max-c", type=int, default=argparse.SUPPRESS, help="maximum capacitors. Default: none")
        target_parser.add_argument("--max-lc", type=int, default=argparse.SUPPRESS, help="maximum L+C reactive components. Default: none")
        edge_group = target_parser.add_mutually_exclusive_group()
        edge_group.add_argument("--support-edges", type=int, default=argparse.SUPPRESS, help="exact source support-edge count; mutually exclusive with --min/--max-support-edges. Default: none")
        edge_group.add_argument("--min-support-edges", type=int, default=argparse.SUPPRESS, help="minimum source support-edge count; use with --max-support-edges for a finite range. Default: 1")
        target_parser.add_argument("--max-support-edges", type=int, default=argparse.SUPPRESS, help="maximum source support-edge count. Default: derived from finite component budget/profile when available")
        target_parser.add_argument("--format", choices=("auto", "table", "markdown", "json"), default="auto", help="output format. " + OUTPUT_HELP + " Default: auto")

    count_supports = count_subparsers.add_parser("supports", help="count source support shapes and terminal-relevant supports", description="Count source support objects: unlabelled simple shapes, unordered terminal labellings, and terminal-relevant two-terminal supports. These are not component-labelled networks.\n\n" + SCOPE_HELP, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_count_scope_options(count_supports)
    count_supports.add_argument("--support-kind", choices=("basic", "terminal", "relevant", "all"), default="all", help="which support columns to show. Default: all")
    count_supports.set_defaults(_parser=count_supports)

    count_bundle_types = count_subparsers.add_parser("bundle-types", help="count the seven source simple primitive bundle labels", description="Count/list the seven source edge bundle types: R, L, C, R||L, R||C, L||C, R||L||C. No reductions are applied.", formatter_class=argparse.RawDescriptionHelpFormatter)
    count_bundle_types.add_argument("--format", choices=("auto", "table", "markdown", "json"), default="auto", help="output format. " + OUTPUT_HELP + " Default: auto")
    count_bundle_types.set_defaults(_parser=count_bundle_types)

    count_bundle_sets = count_subparsers.add_parser("bundle-sets", help="count source bundle inventories", description="Count source bundle inventories before placement on a support. Facts are source objects, not reduced networks.\n\n" + GROUP_HELP, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_count_scope_options(count_bundle_sets)
    count_bundle_sets.add_argument("--group-by", default="support-edges", help="comma-separated dimensions: support-edges,r,l,c,lc,rlc or none. Default: support-edges")
    count_bundle_sets.set_defaults(_parser=count_bundle_sets)

    count_assignments = count_subparsers.add_parser("assignments", help="count source assignments on relevant supports", description="Count raw source placements of bundle labels on terminal-relevant supports. No support-symmetry quotient and no local network reduction are applied.\n\n" + GROUP_HELP, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_count_scope_options(count_assignments)
    count_assignments.add_argument("--group-by", default="support-edges", help="comma-separated dimensions: support-edges,r,l,c,lc,rlc or none. Default: support-edges")
    count_assignments.set_defaults(_parser=count_assignments)

    count_assigned = count_subparsers.add_parser("assigned-supports", help="count source assignments modulo support automorphisms", description="Count assigned-support classes: source assignments quotiented by terminal-set-preserving support automorphisms. These are not locally reduced networks.\n\n" + GROUP_HELP, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_count_scope_options(count_assigned)
    count_assigned.add_argument("--group-by", default="support-edges", help="comma-separated dimensions: support-edges,r,l,c,lc,rlc or none. Default: support-edges")
    count_assigned.set_defaults(_parser=count_assigned)

    count_networks = count_subparsers.add_parser("networks", help="count reduced networks under a named relation", description="Count final reduced objects reached from finite source assignments. The implemented relation is local-sp reduced topology, not rational immittance equivalence.\n\n" + GROUP_HELP + "\n" + RELATION_HELP, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_count_scope_options(count_networks)
    count_networks.add_argument("--relation", choices=("local-sp",), default="local-sp", help=RELATION_HELP + " Default: local-sp")
    count_networks.add_argument("--group-by", default="r,lc", help="comma-separated dimensions: r,l,c,lc,rlc or none. Default: r,lc")
    count_networks.set_defaults(_parser=count_networks)

    count_reductions = count_subparsers.add_parser("reductions", help="count provenance across source-to-reduced transitions", description="Summarize many-to-one reductions from source assignments to assigned-support classes to local-sp networks. The 10,000-record guard limits intermediate enumeration by default.\n\n" + RELATION_HELP, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_count_scope_options(count_reductions)
    count_reductions.add_argument("--relation", choices=("local-sp",), default="local-sp", help=RELATION_HELP + " Default: local-sp")
    count_reductions.add_argument("--max-records", type=_positive_int, default=DEFAULT_ENUM_MAX_RECORDS, help="maximum intermediate enumeration records before the guard stops output. Default: 10000")
    count_reductions.set_defaults(_parser=count_reductions)

    enum_parser = subparsers.add_parser("enum", help="enumerate provisional RICE objects", formatter_class=argparse.RawDescriptionHelpFormatter, description="Enumerate records from the RICE object pipeline. Wide records default to JSON when redirected; use --format table/markdown/json explicitly as needed.\n\n" + SCOPE_HELP)
    enum_subparsers = enum_parser.add_subparsers(dest="object", metavar="<enum-target>", parser_class=RiceArgumentParser, required=False)
    for name in ("supports", "bundle-types", "bundle-sets", "assignments", "assigned-supports", "networks"):
        ep = enum_subparsers.add_parser(name, help=f"enumerate {name}")
        if name != "bundle-types":
            add_count_scope_options(ep)
        else:
            ep.add_argument("--format", choices=("auto", "table", "markdown", "json"), default="auto", help="output format. " + OUTPUT_HELP + " Default: auto")
        if name in {"assignments", "assigned-supports", "networks"}:
            ep.add_argument("--max-records", type=_positive_int, default=DEFAULT_ENUM_MAX_RECORDS, help="maximum records to emit before the 10,000-record guard stops output. Default: 10000")
        ep.description = f"Enumerate {name}. Facts are " + ("reduced objects under local-sp." if name == "networks" else "source/provisional objects before final reduction.") + "\n\n" + SCOPE_HELP
        ep.formatter_class = argparse.RawDescriptionHelpFormatter
        if name == "networks":
            ep.add_argument("--relation", choices=("local-sp",), default="local-sp", help=RELATION_HELP + " Default: local-sp")
        ep.set_defaults(_parser=ep)

    return parser


def _query_from_count_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> CountQuery:
    explicit_names = ("max_rlc", "max_r", "max_l", "max_c", "max_lc")
    if hasattr(args, "profile") and any(hasattr(args, name) for name in explicit_names):
        parser.error("--profile is mutually exclusive with explicit component-limit options")
    try:
        constraints = ComponentConstraints(
            max_rlc=getattr(args, "max_rlc", None),
            max_r=getattr(args, "max_r", None),
            max_l=getattr(args, "max_l", None),
            max_c=getattr(args, "max_c", None),
            max_lc=getattr(args, "max_lc", None),
        )
        query = CountQuery(
            component_constraints=constraints,
            support_edges=getattr(args, "support_edges", None),
            min_support_edges=getattr(args, "min_support_edges", None),
            max_support_edges=getattr(args, "max_support_edges", None),
            profile=getattr(args, "profile", None),
        )
        query.effective_support_edge_range()
        return query
    except ValueError as exc:
        parser.error(str(exc))


def _support_count_json(result: SupportCensusResult, query: CountQuery, support_kind: str) -> dict[str, Any]:
    eff = query.effective_support_edge_range()
    records = []
    start = eff.minimum or 1
    stop = eff.maximum or 0
    for edge_count in range(start, stop + 1):
        row: dict[str, int] = {"support_edges": edge_count}
        if support_kind in {"basic", "all"}:
            row["basic"] = result.basic_by_edges.get(edge_count, 0)
        if support_kind in {"terminal", "all"}:
            row["terminal"] = result.terminal_labelings_by_edges.get(edge_count, 0)
        if support_kind in {"relevant", "all"}:
            row["relevant"] = result.relevant_by_edges.get(edge_count, 0)
        records.append(row)
    totals = {k: sum(r.get(k, 0) for r in records) for k in ("basic", "terminal", "relevant") if support_kind in {k, "all"}}
    return {"format_version": 1, "object": "supports", "support_kind": support_kind, "query": query.to_json(), "group_by": ["support-edges"], "records": records, "totals": totals}


def _bundle_types_json() -> dict[str, Any]:
    records = [{"label": b.label, "r": b.r_count, "l": b.l_count, "c": b.c_count, "lc": b.reactive_count, "rlc": b.r_count + b.reactive_count} for b in SIMPLE_PRIMITIVE_BUNDLES]
    return {"format_version": 1, "object": "bundle-types", "records": records, "totals": {"bundle_types": len(records)}}


def _markdown_cell(value: str) -> str:
    """Escape Markdown table separator characters in a cell."""
    return value.replace("|", "\\|")


def _print_table(headers: list[str], rows: list[list[object]], output_format: str) -> None:
    """Print rows as either aligned terminal text or a Markdown table."""
    text_rows = [[str(value) for value in row] for row in rows]
    if output_format == "markdown":
        markdown_headers = [_markdown_cell(header) for header in headers]
        print("| " + " | ".join(markdown_headers) + " |")
        print("|" + "---:|" * len(headers))
        for row in text_rows:
            markdown_row = [_markdown_cell(cell) for cell in row]
            print("| " + " | ".join(markdown_row) + " |")
        return

    widths = [len(header) for header in headers]
    for row in text_rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))
    print("  ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print("  ".join("-" * width for width in widths))
    for values, text_values in zip(rows, text_rows):
        cells = [
            text.rjust(widths[index]) if isinstance(value, int) else text.ljust(widths[index])
            for index, (value, text) in enumerate(zip(values, text_values))
        ]
        print("  ".join(cells))



def _enum_payload(object_name: str, query: CountQuery | None, records: list[dict[str, Any]], relation: str | None = None, definition: str | None = None) -> dict[str, Any]:
    return {"format_version": 1, "operation": "enum", "object": object_name, "query": query.to_json() if query else {}, "relation": relation, "definition": definition, "records": records, "totals": {"records": len(records)}, "diagnostics": {"provisional_formats": True}}

def _print_enum_table(title: str, payload: dict[str, Any], output_format: str) -> None:
    print(f"{title} (provisional enumeration format)")
    if payload.get("relation"):
        print(f"Relation: {payload['relation']} ({payload.get('definition')})")
        print("Not rational immittance equivalence; stable strings are provisional structural serializations.")
    print(f"Records shown: {payload['totals']['records']}")
    records = payload["records"]
    if not records:
        print("No records."); return
    keys = list(records[0].keys())
    _print_table(keys, [[row.get(key, "") for key in keys] for row in records], output_format)


def _normalize_help_argv(argv: list[str]) -> list[str]:
    if not argv or argv in (["-h"], ["--help"]):
        return ["--help"]
    if argv[0] == "help":
        return [*argv[1:], "--help"] if len(argv) > 1 else ["--help"]
    if argv[0] == "--help" and len(argv) > 1:
        return [*argv[1:], "--help"]
    return argv


def _resolve_output_format(value: str) -> str:
    if value == "auto":
        return "table" if sys.stdout.isatty() else "json"
    return value

def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    argv = _normalize_help_argv(argv)
    args = parser.parse_args(argv)
    if getattr(args, "verb", None) is None:
        parser.print_help()
        return 0
    if getattr(args, "object", None) is None:
        # Bare group commands are successful group-help requests.
        if args.verb in {"count", "enum"}:
            # Re-parse as an explicit help request so argparse prints the group parser.
            try:
                parser.parse_args([args.verb, "--help"])
            except SystemExit as exc:
                if exc.code == 0:
                    return 0
                raise
        parser.print_help()
        return 0

    active_parser = getattr(args, "_parser", parser)

    if args.verb == "enum":
        output_format = _resolve_output_format(getattr(args, "format", "auto"))
        try:
            query = None if args.object == "bundle-types" else _query_from_count_args(active_parser, args)
            rel = None; definition = None
            if args.object == "supports": recs=[r.to_json() for r in enum_supports(query)]
            elif args.object == "bundle-types": recs=[r.to_json() for r in enum_bundle_types()]
            elif args.object == "bundle-sets": recs=[r.to_json() for r in enum_bundle_sets(query)]
            elif args.object == "assignments": recs=[r.to_json() for r in enum_assignments(query, max_records=args.max_records)]
            elif args.object == "assigned-supports": recs=[r.to_json() for r in enum_assigned_supports(query, max_records=args.max_records)]
            elif args.object == "networks":
                nets=enum_networks(query, relation=args.relation, max_records=args.max_records); recs=[r.to_json() for r in nets]; rel=args.relation; definition=nets[0].definition if nets else "canonical-reduced-topology-local-series-parallel-v1"
            else: raise AssertionError(args.object)
        except ValueError as exc:
            active_parser.error(str(exc))
        payload=_enum_payload(args.object, query, recs, rel, definition)
        if output_format == "json": print(json.dumps(payload, indent=2, sort_keys=True))
        else: _print_enum_table(f"Enum {args.object}", payload, output_format)
        return 0

    if args.verb == "count":
        output_format = _resolve_output_format(getattr(args, "format", "auto"))
        if args.object == "bundle-types":
            payload = _bundle_types_json()
            if output_format == "json":
                print(json.dumps(payload, indent=2, sort_keys=True))
            else:
                print("Simple primitive bundle types")
                rows = [[row["label"], row["r"], row["l"], row["c"], row["lc"], row["rlc"]] for row in payload["records"]]
                rows.append(["Total", payload["totals"]["bundle_types"], "", "", "", ""])
                _print_table(["Label", "R count", "L count", "C count", "L+C count", "Total components"], rows, output_format)
            return 0
        query = _query_from_count_args(active_parser, args)
        if args.object == "supports":
            eff = query.effective_support_edge_range()
            max_edges = eff.maximum or 0
            if max_edges == 0 or (eff.minimum or 1) > max_edges:
                result = SupportCensusResult(max_edges=0, basic_by_edges={}, terminal_labelings_by_edges={}, relevant_by_edges={})
            else:
                result = support_census(max_edges=max_edges)
            if output_format == "json":
                print(json.dumps(_support_count_json(result, query, args.support_kind), indent=2, sort_keys=True))
            else:
                print("Support object census")
                print("Component constraints bound compatible bundle inventories only; supports are not component-labelled.")
                headers = ["Support edges"]
                if args.support_kind in {"basic", "all"}: headers.append("Basic supports")
                if args.support_kind in {"terminal", "all"}: headers.append("Terminal supports")
                if args.support_kind in {"relevant", "all"}: headers.append("Relevant supports")
                payload = _support_count_json(result, query, args.support_kind)
                rows = []
                for row in payload["records"]:
                    vals = [row.get("support_edges"), row.get("basic"), row.get("terminal"), row.get("relevant")]
                    vals = [v for v in vals if v is not None]
                    rows.append(vals)
                totals = payload["totals"]
                rows.append(["Total", *(totals[k] for k in ("basic", "terminal", "relevant") if k in totals)])
                _print_table(headers, rows, output_format)
            return 0
        if args.object == "bundle-sets":
            group_by = tuple(part.strip() for part in args.group_by.split(","))
            try:
                result = bundle_set_census(query, group_by=group_by)
            except ValueError as exc:
                active_parser.error(str(exc))
            if output_format == "json":
                print(json.dumps(result.to_json(), indent=2, sort_keys=True))
            else:
                print("Bundle-set census")
                dims = result.group_by
                if dims == ("support-edges",):
                    headers = ["Support edges / bundle count", "Distinct bundle sets", "Raw placements represented"]
                    rows = [[row["support-edges"], row["distinct_bundle_sets"], row["raw_placements"]] for row in result.records]
                else:
                    headers = list(dims) + ["Distinct bundle sets", "Raw placements represented"]
                    rows = [[*(row[dim] for dim in dims), row["distinct_bundle_sets"], row["raw_placements"]] for row in result.records]
                total_prefix = ["Total", *("" for _ in dims[1:])] if dims else []
                rows.append([*total_prefix, result.distinct_bundle_sets_total, result.raw_placements_total])
                _print_table(headers, rows, output_format)
            return 0
        if args.object == "assignments":
            group_by = tuple(part.strip() for part in args.group_by.split(","))
            try:
                result = assignment_census(query, group_by=group_by)
            except ValueError as exc:
                active_parser.error(str(exc))
            if output_format == "json":
                print(json.dumps(result.to_json(), indent=2, sort_keys=True))
            else:
                print("Assignment census")
                print("Assignments are raw placements on terminal-relevant source supports; no support-symmetry quotient or local reduction is applied.")
                if result.group_by == ("support-edges",):
                    headers = ["Support edges", "Relevant supports", "Distinct bundle sets", "Assignments per support", "Raw assignments"]
                    rows = [[row["support-edges"], row["relevant_supports"], row["distinct_bundle_sets"], row["assignments_per_support"], row["raw_assignments"]] for row in result.records]
                    rows.append(["Total", "—", result.distinct_bundle_sets_total, "—", result.raw_assignments_total])
                else:
                    headers = list(result.group_by) + ["Distinct bundle sets", "Raw assignments"]
                    rows = [[*(row[dim] for dim in result.group_by), row["distinct_bundle_sets"], row["raw_assignments"]] for row in result.records]
                    total_values = (["Total", *("—" for _ in result.group_by[1:])] if result.group_by else []) + [result.distinct_bundle_sets_total, result.raw_assignments_total]
                    rows.append(total_values)
                _print_table(headers, rows, output_format)
            return 0
        if args.object == "assigned-supports":
            group_by = tuple(part.strip() for part in args.group_by.split(","))
            try:
                result = assigned_support_census(query, group_by=group_by)
            except ValueError as exc:
                active_parser.error(str(exc))
            if output_format == "json":
                print(json.dumps(result.to_json(), indent=2, sort_keys=True))
            else:
                print("Assigned-support census")
                print("Assigned-support classes quotient assignments by terminal-set-preserving support automorphisms; no local network reduction is applied.")
                if result.group_by == ("support-edges",):
                    headers = ["Support edges", "Relevant supports", "Raw assignments", "Assigned-support classes"]
                    rows = [[row["support-edges"], row["relevant_supports"], row["raw_assignments"], row["assigned_support_classes"]] for row in result.records]
                    rows.append(["Total", "—", result.raw_assignments_total, result.assigned_support_classes_total])
                else:
                    headers=list(result.group_by)+["Raw assignments","Assigned-support classes"]
                    rows = [[*(row[dim] for dim in result.group_by), row["raw_assignments"], row["assigned_support_classes"]] for row in result.records]
                    total_values = (["Total", *("—" for _ in result.group_by[1:])] if result.group_by else []) + [result.raw_assignments_total, result.assigned_support_classes_total]
                    rows.append(total_values)
                _print_table(headers, rows, output_format)
            return 0
        if args.object == "reductions":
            try:
                result = reduction_census(query, relation=args.relation, max_records=args.max_records)
            except ValueError as exc:
                active_parser.error(str(exc))
            if output_format == "json":
                print(json.dumps(result.to_json(), indent=2, sort_keys=True))
            else:
                print("Reduction provenance census (provisional format)")
                print(f"Relation: {result.relation.name} ({result.relation.definition})")
                print("This analyses many-to-one source mappings; it is not rational immittance equivalence and not a new network relation.")
                print("Distinct networks reached in transition rows are provenance facts and are not additive across rows.")
                _print_table(["Stage", "Objects"], [[k, v] for k, v in result.pipeline_totals.items()], output_format)
            return 0
        if args.object == "networks":
            group_by = tuple(part.strip() for part in args.group_by.split(","))
            try:
                result = network_census(query, relation=args.relation, group_by=group_by)
            except ValueError as exc:
                active_parser.error(str(exc))
            if output_format == "json":
                print(json.dumps(result.to_json(), indent=2, sort_keys=True))
            else:
                print("Network census")
                print(f"Relation: {result.relation.name} ({result.relation.definition})")
                print("Query constraints select generating source assignments; component table entries are final reduced-signature counts.")
                print("This is not full rational-immittance equivalence.")
                print()
                if result.group_by == ("r", "lc"):
                    matrix = result.matrix()
                    headers = ["R \\ L+C", *(str(x) for x in range(len(matrix[0]) if matrix else 0)), "Row total"]
                    rows = [[r, *row, sum(row)] for r, row in enumerate(matrix)]
                    _print_table(headers, rows, output_format)
                else:
                    headers=list(result.group_by)+["Networks"]
                    rows = [[*(row[dim] for dim in result.group_by), row["networks"]] for row in result.records]
                    _print_table(headers, rows, output_format)
                print()
                print(f"Unique network total: {result.total}")
                print("Diagnostics: " + f"raw assignments={result.diagnostics['raw_assignments']}; assigned-support classes={result.diagnostics['assigned_support_classes']}; unique reduced networks={result.diagnostics['unique_reduced_networks']}")
            return 0

    raise AssertionError(f"unhandled subcommand {args.verb!r}")


if __name__ == "__main__":
    raise SystemExit(main())
