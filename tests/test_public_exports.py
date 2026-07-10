"""Characterisation test for the current top-level ``rice`` export surface.

This pins which public names are legacy-only versus shared with (or exclusive
to) the reduced-topology model, so a later cleanup PR can see at a glance which
entries in ``LEGACY_ONLY_EXPORTS`` to delete from ``rice.__all__`` and which
entries in ``SURVIVING_EXPORTS`` must still resolve afterwards.
"""

import rice

LEGACY_ONLY_EXPORTS = {
    "CountResult",
    "count_networks",
}

SURVIVING_EXPORTS = {
    "BundleAssignmentCensusResult",
    "BundleLabelingCensusResult",
    "ReducedFactor",
    "ReducedSignature",
    "ReducedTopologyCensusResult",
    "SIMPLE_PRIMITIVE_BUNDLES",
    "SupportCensusResult",
    "canonical_reduced_signature",
    "iter_reduced_topology_signatures",
    "factor_from_simple_primitive_bundle",
    "normalise_parallel_factor",
    "normalise_series_factor",
    "primitive_factor",
    "reduced_signature_component_counts",
    "reduced_topology_census",
    "simple_bundle_assignment_census",
    "simple_bundle_labeling_census",
    "simple_bundle_labeling_orbit_count",
    "support_census",
}


def test_current_public_export_surface_matches_documented_legacy_split():
    assert set(rice.__all__) == LEGACY_ONLY_EXPORTS | SURVIVING_EXPORTS


def test_every_documented_export_name_is_importable_from_top_level_package():
    for name in LEGACY_ONLY_EXPORTS | SURVIVING_EXPORTS:
        assert hasattr(rice, name), f"rice.{name} is not importable"


def test_generic_mode_is_not_a_top_level_export():
    # "generic" reactive-element support is exposed only through count_networks'
    # mode argument and the CLI, not as its own top-level name.
    assert "Mode" not in rice.__all__
    assert "generic" not in rice.__all__
