import rice

PUBLIC_EXPORTS = {
# line-length: ignore-next-line -- legacy line pending wrap
    "LOCAL_SP_RELATION", "NetworkRelation", "NetworkFact", "NetworkCensusResult",
# line-length: ignore-next-line -- legacy line pending wrap
    "AssignedSupportFact", "AssignedSupportCensusResult", "AssignmentFact", "AssignmentCensusResult",
# line-length: ignore-next-line -- legacy line pending wrap
    "validate_network_relation", "network_census", "assigned_support_census", "assignment_census",
# line-length: ignore-next-line -- legacy line pending wrap
    "iter_bundle_sets", "bundle_set_census", "IntegerRange", "CountQuery", "ComponentConstraints",
# line-length: ignore-next-line -- legacy line pending wrap
    "COUNT_PROFILES", "BundleSetCensusResult", "BundleSet", "ReducedFactor", "ReducedSignature",
    "SIMPLE_PRIMITIVE_BUNDLES", "SimplePrimitiveBundle", "SupportCensusResult",
# line-length: ignore-next-line -- legacy line pending wrap
    "canonical_reduced_signature", "factor_from_simple_primitive_bundle", "normalise_parallel_factor",
    "normalise_reduced_factor", "normalise_series_factor", "primitive_factor",
    "reduced_signature_component_counts", "support_census",
    "SupportRecord", "BundleTypeRecord", "BundleSetRecord", "AssignmentRecord",
    "AssignedSupportRecord", "NetworkRecord", "ReductionCensusResult",
# line-length: ignore-next-line -- legacy line pending wrap
    "enum_supports", "enum_bundle_types", "enum_bundle_sets", "enum_assignments",
    "enum_assigned_supports", "enum_networks", "reduction_census",
}

REMOVED_NAMES = {
# line-length: ignore-next-line -- legacy line pending wrap
    "BundleAssignmentCensusResult", "BundleLabelingCensusResult", "ReducedTopologyCensusResult",
# line-length: ignore-next-line -- legacy line pending wrap
    "iter_reduced_topology_signatures", "reduced_topology_census", "simple_bundle_assignment_census",
# line-length: ignore-next-line -- legacy line pending wrap
    "simple_bundle_labeling_census", "simple_bundle_labeling_orbit_count", "CountResult", "count_networks",
}


def test_public_export_surface_matches_documented_provisional_api():
    assert set(rice.__all__) == PUBLIC_EXPORTS


def test_every_public_export_is_importable_from_top_level_package():
    for name in PUBLIC_EXPORTS:
        assert hasattr(rice, name), name


def test_removed_names_are_absent_from_exports_and_attributes():
    for name in REMOVED_NAMES:
        assert name not in rice.__all__
        assert not hasattr(rice, name)
