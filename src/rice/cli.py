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


def build_parser() -> argparse.ArgumentParser:
    parser = RiceArgumentParser(
        prog="rice",
        description="RICE — Resistor-Inductor-Capacitor Enumerator for small two-terminal RLC one-port topology classes.",
        epilog="Subcommand options go after the subcommand.",
    )
    subparsers = parser.add_subparsers(
        dest="command", parser_class=RiceArgumentParser, required=True
    )

    count_parser = subparsers.add_parser(
        "count", help="count object-oriented RICE objects (supports, bundle-types, bundle-sets, assignments, assigned-supports, networks)"
    )
    count_subparsers = count_parser.add_subparsers(
        dest="count_object", parser_class=RiceArgumentParser, required=True
    )

    def add_count_scope_options(target_parser: argparse.ArgumentParser) -> None:
        profile_group = target_parser.add_mutually_exclusive_group()
        profile_group.add_argument("--profile", choices=tuple(COUNT_PROFILES), default=argparse.SUPPRESS)
        profile_group.add_argument("--max-rlc", type=int, default=argparse.SUPPRESS, help="maximum total R+L+C components")
        # argparse cannot put multiple explicit options in one mutual-exclusion slot;
        # cross-option profile conflicts are validated centrally after parsing.
        target_parser.add_argument("--max-r", type=int, default=argparse.SUPPRESS, help="maximum resistors")
        target_parser.add_argument("--max-l", type=int, default=argparse.SUPPRESS, help="maximum inductors")
        target_parser.add_argument("--max-c", type=int, default=argparse.SUPPRESS, help="maximum capacitors")
        target_parser.add_argument("--max-lc", type=int, default=argparse.SUPPRESS, help="maximum L+C reactive components")
        edge_group = target_parser.add_mutually_exclusive_group()
        edge_group.add_argument("--support-edges", type=int, default=argparse.SUPPRESS, help="exact source support-edge count")
        edge_group.add_argument("--min-support-edges", type=int, default=argparse.SUPPRESS, help="minimum source support-edge count")
        target_parser.add_argument("--max-support-edges", type=int, default=argparse.SUPPRESS, help="maximum source support-edge count")
        target_parser.add_argument("--format", choices=("markdown", "json"), default=argparse.SUPPRESS, help="output format, default: markdown")

    count_supports = count_subparsers.add_parser("supports", help="count basic, terminal, and relevant supports")
    add_count_scope_options(count_supports)
    count_supports.add_argument("--support-kind", choices=("basic", "terminal", "relevant", "all"), default="all")

    count_bundle_types = count_subparsers.add_parser("bundle-types", help="list and count the fixed simple primitive bundle types")
    count_bundle_types.add_argument("--format", choices=("markdown", "json"), default=argparse.SUPPRESS, help="output format, default: markdown")

    count_bundle_sets = count_subparsers.add_parser("bundle-sets", help="count simple primitive bundle multisets/inventories")
    add_count_scope_options(count_bundle_sets)
    count_bundle_sets.add_argument("--group-by", default="support-edges", help="comma-separated dimensions: support-edges,r,l,c,lc,rlc or none")

    count_assignments = count_subparsers.add_parser("assignments", help="count raw bundle assignments on terminal-relevant supports")
    add_count_scope_options(count_assignments)
    count_assignments.add_argument("--group-by", default="support-edges", help="comma-separated dimensions: support-edges,r,l,c,lc,rlc or none")

    count_assigned = count_subparsers.add_parser("assigned-supports", help="count assignments modulo terminal-set-preserving support automorphisms")
    add_count_scope_options(count_assigned)
    count_assigned.add_argument("--group-by", default="support-edges", help="comma-separated dimensions: support-edges,r,l,c,lc,rlc or none")

    count_networks = count_subparsers.add_parser("networks", help="count unique networks under a named relation")
    add_count_scope_options(count_networks)
    count_networks.add_argument("--relation", default="local-sp", help="network relation, default: local-sp")
    count_networks.add_argument("--group-by", default="r,lc", help="comma-separated dimensions: r,l,c,lc,rlc or none")

    count_reductions = count_subparsers.add_parser("reductions", help="analyse assignments to assigned-supports to networks reductions")
    add_count_scope_options(count_reductions)
    count_reductions.add_argument("--relation", default="local-sp", help="network relation, default: local-sp")
    count_reductions.add_argument("--max-records", type=_positive_int, default=DEFAULT_ENUM_MAX_RECORDS, help="maximum intermediate enumeration records, default: 10000")

    enum_parser = subparsers.add_parser("enum", help="enumerate provisional RICE objects")
    enum_subparsers = enum_parser.add_subparsers(dest="enum_object", parser_class=RiceArgumentParser, required=True)
    for name in ("supports", "bundle-types", "bundle-sets", "assignments", "assigned-supports", "networks"):
        ep = enum_subparsers.add_parser(name, help=f"enumerate {name}")
        if name != "bundle-types":
            add_count_scope_options(ep)
        else:
            ep.add_argument("--format", choices=("markdown", "json"), default=argparse.SUPPRESS)
        if name in {"assignments", "assigned-supports", "networks"}:
            ep.add_argument("--max-records", type=_positive_int, default=DEFAULT_ENUM_MAX_RECORDS, help="maximum records to emit, default: 10000")
        if name == "networks":
            ep.add_argument("--relation", default="local-sp", help="network relation, default: local-sp")

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



def _enum_payload(object_name: str, query: CountQuery | None, records: list[dict[str, Any]], relation: str | None = None, definition: str | None = None) -> dict[str, Any]:
    return {"format_version": 1, "operation": "enum", "object": object_name, "query": query.to_json() if query else {}, "relation": relation, "definition": definition, "records": records, "totals": {"records": len(records)}, "diagnostics": {"provisional_formats": True}}

def _print_enum_markdown(title: str, payload: dict[str, Any]) -> None:
    print(f"{title} (provisional enumeration format)")
    if payload.get("relation"):
        print(f"Relation: {payload['relation']} ({payload.get('definition')})")
        print("Not rational immittance equivalence; stable strings are provisional structural serializations.")
    print(f"Records shown: {payload['totals']['records']}")
    records = payload["records"]
    if not records:
        print("No records."); return
    keys = list(records[0].keys())
    print("| " + " | ".join(keys) + " |")
    print("|" + "---|" * len(keys))
    for row in records:
        print("| " + " | ".join(str(row.get(k, "")) for k in keys) + " |")

def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    args = parser.parse_args(argv)

    output_format = getattr(args, "format", "markdown")


    if args.command == "enum":
        output_format = getattr(args, "format", "markdown")
        try:
            query = None if args.enum_object == "bundle-types" else _query_from_count_args(parser, args)
            rel = None; definition = None
            if args.enum_object == "supports": recs=[r.to_json() for r in enum_supports(query)]
            elif args.enum_object == "bundle-types": recs=[r.to_json() for r in enum_bundle_types()]
            elif args.enum_object == "bundle-sets": recs=[r.to_json() for r in enum_bundle_sets(query)]
            elif args.enum_object == "assignments": recs=[r.to_json() for r in enum_assignments(query, max_records=args.max_records)]
            elif args.enum_object == "assigned-supports": recs=[r.to_json() for r in enum_assigned_supports(query, max_records=args.max_records)]
            elif args.enum_object == "networks":
                nets=enum_networks(query, relation=args.relation, max_records=args.max_records); recs=[r.to_json() for r in nets]; rel=args.relation; definition=nets[0].definition if nets else "canonical-reduced-topology-local-series-parallel-v1"
            else: raise AssertionError(args.enum_object)
        except ValueError as exc:
            parser.error(str(exc))
        payload=_enum_payload(args.enum_object, query, recs, rel, definition)
        if output_format == "json": print(json.dumps(payload, indent=2, sort_keys=True))
        else: _print_enum_markdown(f"Enum {args.enum_object}", payload)
        return 0

    if args.command == "count":
        output_format = getattr(args, "format", "markdown")
        if args.count_object == "bundle-types":
            payload = _bundle_types_json()
            if output_format == "json":
                print(json.dumps(payload, indent=2, sort_keys=True))
            else:
                print("Simple primitive bundle types")
                print("| Label | R count | L count | C count | L+C count | Total components |")
                print("|---|---:|---:|---:|---:|---:|")
                for row in payload["records"]:
                    print(f"| {row['label']} | {row['r']} | {row['l']} | {row['c']} | {row['lc']} | {row['rlc']} |")
                print(f"| Total | {payload['totals']['bundle_types']} |  |  |  |  |")
            return 0
        query = _query_from_count_args(parser, args)
        if args.count_object == "supports":
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
                print("| " + " | ".join(headers) + " |")
                print("|" + "---:|" * len(headers))
                payload = _support_count_json(result, query, args.support_kind)
                for row in payload["records"]:
                    vals = [row.get("support_edges"), row.get("basic"), row.get("terminal"), row.get("relevant")]
                    vals = [v for v in vals if v is not None]
                    print("| " + " | ".join(str(v) for v in vals) + " |")
                totals = payload["totals"]
                print("| Total | " + " | ".join(str(totals[k]) for k in ("basic", "terminal", "relevant") if k in totals) + " |")
            return 0
        if args.count_object == "bundle-sets":
            group_by = tuple(part.strip() for part in args.group_by.split(","))
            try:
                result = bundle_set_census(query, group_by=group_by)
            except ValueError as exc:
                parser.error(str(exc))
            if output_format == "json":
                print(json.dumps(result.to_json(), indent=2, sort_keys=True))
            else:
                print("Bundle-set census")
                dims = result.group_by
                if dims == ("support-edges",):
                    print("| Support edges / bundle count | Distinct bundle sets | Raw placements represented |")
                    print("|---:|---:|---:|")
                    for row in result.records:
                        print(f"| {row['support-edges']} | {row['distinct_bundle_sets']} | {row['raw_placements']} |")
                else:
                    headers = list(dims) + ["Distinct bundle sets", "Raw placements represented"]
                    print("| " + " | ".join(headers) + " |")
                    print("|" + "---:|" * len(headers))
                    for row in result.records:
                        values = [*(row[dim] for dim in dims), row["distinct_bundle_sets"], row["raw_placements"]]
                        print("| " + " | ".join(str(value) for value in values) + " |")
                print(f"| Total | {result.distinct_bundle_sets_total} | {result.raw_placements_total} |")
            return 0
        if args.count_object == "assignments":
            group_by = tuple(part.strip() for part in args.group_by.split(","))
            try:
                result = assignment_census(query, group_by=group_by)
            except ValueError as exc:
                parser.error(str(exc))
            if output_format == "json":
                print(json.dumps(result.to_json(), indent=2, sort_keys=True))
            else:
                print("Assignment census")
                print("Assignments are raw placements on terminal-relevant source supports; no support-symmetry quotient or local reduction is applied.")
                if result.group_by == ("support-edges",):
                    print("| Support edges | Relevant supports | Distinct bundle sets | Assignments per support | Raw assignments |")
                    print("|---:|---:|---:|---:|---:|")
                    for row in result.records:
                        print(f"| {row['support-edges']} | {row['relevant_supports']} | {row['distinct_bundle_sets']} | {row['assignments_per_support']} | {row['raw_assignments']} |")
                    print(f"| Total | — | {result.distinct_bundle_sets_total} | — | {result.raw_assignments_total} |")
                else:
                    headers = list(result.group_by) + ["Distinct bundle sets", "Raw assignments"]
                    print("| " + " | ".join(headers) + " |")
                    print("|" + "---:|" * len(headers))
                    for row in result.records:
                        values = [*(row[dim] for dim in result.group_by), row["distinct_bundle_sets"], row["raw_assignments"]]
                        print("| " + " | ".join(str(v) for v in values) + " |")
                    total_values = (["Total", *("—" for _ in result.group_by[1:])] if result.group_by else []) + [result.distinct_bundle_sets_total, result.raw_assignments_total]
                    print("| " + " | ".join(str(v) for v in total_values) + " |")
            return 0
        if args.count_object == "assigned-supports":
            group_by = tuple(part.strip() for part in args.group_by.split(","))
            try:
                result = assigned_support_census(query, group_by=group_by)
            except ValueError as exc:
                parser.error(str(exc))
            if output_format == "json":
                print(json.dumps(result.to_json(), indent=2, sort_keys=True))
            else:
                print("Assigned-support census")
                print("Assigned-support classes quotient assignments by terminal-set-preserving support automorphisms; no local network reduction is applied.")
                if result.group_by == ("support-edges",):
                    print("| Support edges | Relevant supports | Raw assignments | Assigned-support classes |")
                    print("|---:|---:|---:|---:|")
                    for row in result.records:
                        print(f"| {row['support-edges']} | {row['relevant_supports']} | {row['raw_assignments']} | {row['assigned_support_classes']} |")
                    print(f"| Total | — | {result.raw_assignments_total} | {result.assigned_support_classes_total} |")
                else:
                    headers=list(result.group_by)+["Raw assignments","Assigned-support classes"]
                    print("| "+" | ".join(headers)+" |")
                    print("|"+"---:|"*len(headers))
                    for row in result.records:
                        values=[*(row[dim] for dim in result.group_by), row["raw_assignments"], row["assigned_support_classes"]]
                        print("| "+" | ".join(str(v) for v in values)+" |")
                    total_values = (["Total", *("—" for _ in result.group_by[1:])] if result.group_by else []) + [result.raw_assignments_total, result.assigned_support_classes_total]
                    print("| " + " | ".join(str(v) for v in total_values) + " |")
            return 0
        if args.count_object == "reductions":
            try:
                result = reduction_census(query, relation=args.relation, max_records=args.max_records)
            except ValueError as exc:
                parser.error(str(exc))
            if output_format == "json":
                print(json.dumps(result.to_json(), indent=2, sort_keys=True))
            else:
                print("Reduction provenance census (provisional format)")
                print(f"Relation: {result.relation.name} ({result.relation.definition})")
                print("This analyses many-to-one source mappings; it is not rational immittance equivalence and not a new network relation.")
                print("Distinct networks reached in transition rows are provenance facts and are not additive across rows.")
                print("| Stage | Objects |")
                print("|---|---:|")
                for k,v in result.pipeline_totals.items(): print(f"| {k} | {v} |")
            return 0
        if args.count_object == "networks":
            group_by = tuple(part.strip() for part in args.group_by.split(","))
            try:
                result = network_census(query, relation=args.relation, group_by=group_by)
            except ValueError as exc:
                parser.error(str(exc))
            if output_format == "json":
                print(json.dumps(result.to_json(), indent=2, sort_keys=True))
            else:
                print("Network census")
                print(f"Relation: {result.relation.name} ({result.relation.definition})")
                print("Query constraints select generating source assignments; component table entries are final reduced-signature counts.")
                print("This is not full rational-immittance equivalence.")
                print()
                if result.group_by == ("r", "lc"):
                    print(result.as_markdown_table())
                else:
                    headers=list(result.group_by)+["Networks"]
                    print("| "+" | ".join(headers)+" |")
                    print("|"+"---:|"*len(headers))
                    for row in result.records:
                        values=[*(row[dim] for dim in result.group_by), row["networks"]]
                        print("| "+" | ".join(str(v) for v in values)+" |")
                print()
                print(f"Unique network total: {result.total}")
                print("Diagnostics: " + f"raw assignments={result.diagnostics['raw_assignments']}; assigned-support classes={result.diagnostics['assigned_support_classes']}; unique reduced networks={result.diagnostics['unique_reduced_networks']}")
            return 0

    raise AssertionError(f"unhandled subcommand {args.command!r}")


if __name__ == "__main__":
    raise SystemExit(main())
