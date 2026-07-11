"""Characterisation test for the supported top-level ``rice`` export surface.

Pins ``rice.__all__`` to the final supported set of names, after the legacy
multiset-bundle counter (``CountResult``, ``count_networks``) and its ``mode``
machinery were removed in ``docs/plan/02-cleanup/02-legacy.md``, and after
``SimplePrimitiveBundle`` and ``normalise_reduced_factor`` were added in
``docs/plan/02-cleanup/04-public-api.md``. See ``docs/python_api.md`` for the
documented role of every name here.
"""

import rice

PUBLIC_EXPORTS = {
    "assignment_census",
    "assigned_support_census",
    "network_census",
    "validate_network_relation",
    "AssignmentCensusResult",
    "AssignmentFact",
    "AssignedSupportCensusResult",
    "AssignedSupportFact",
    "NetworkCensusResult",
    "NetworkFact",
    "NetworkRelation",
    "LOCAL_SP_RELATION",
    "iter_bundle_sets",
    "bundle_set_census",
    "IntegerRange",
    "CountQuery",
    "ComponentConstraints",
    "COUNT_PROFILES",
    "BundleSetCensusResult",
    "BundleSet",
    "BundleAssignmentCensusResult",
    "BundleLabelingCensusResult",
    "ReducedFactor",
    "ReducedSignature",
    "ReducedTopologyCensusResult",
    "SIMPLE_PRIMITIVE_BUNDLES",
    "SimplePrimitiveBundle",
    "SupportCensusResult",
    "canonical_reduced_signature",
    "iter_reduced_topology_signatures",
    "factor_from_simple_primitive_bundle",
    "normalise_parallel_factor",
    "normalise_reduced_factor",
    "normalise_series_factor",
    "primitive_factor",
    "reduced_signature_component_counts",
    "reduced_topology_census",
    "simple_bundle_assignment_census",
    "simple_bundle_labeling_census",
    "simple_bundle_labeling_orbit_count",
    "support_census",
}

REMOVED_NAMES = {
    "CountResult",
    "count_networks",
    "Mode",
    "fixed_assignments_by_total",
}


def test_public_export_surface_matches_supported_api():
    assert set(rice.__all__) == PUBLIC_EXPORTS


def test_every_public_export_is_importable_from_top_level_package():
    for name in PUBLIC_EXPORTS:
        assert hasattr(rice, name), f"rice.{name} is not importable"


def test_removed_legacy_names_are_absent_from_exports_and_attributes():
    for name in REMOVED_NAMES:
        assert name not in rice.__all__
        assert not hasattr(rice, name), f"rice.{name} should no longer exist"
