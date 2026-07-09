from rice import count_networks


def test_generic_reactive_counts_match_reference_table():
    result = count_networks(max_r=3, max_reactive=5, mode="generic")
    assert result.support_count == 383
    assert result.support_count_by_edges == {1: 1, 2: 1, 3: 2, 4: 4, 5: 10, 6: 27, 7: 80, 8: 258}
    assert result.table == (
        (0, 1, 2, 4, 11, 31),
        (1, 2, 7, 24, 97, 403),
        (2, 7, 36, 170, 875, 4536),
        (4, 24, 170, 1083, 6928, 43527),
    )
    assert result.exactly_r_total(3) == 51736
    assert result.total == 57945


def test_lc_counts_match_reference_table():
    result = count_networks(max_r=3, max_reactive=5, mode="lc")
    assert result.support_count == 383
    assert result.support_count_by_edges == {1: 1, 2: 1, 3: 2, 4: 4, 5: 10, 6: 27, 7: 80, 8: 258}
    assert result.table == (
        (0, 2, 6, 22, 106, 596),
        (1, 4, 24, 160, 1205, 9668),
        (2, 14, 128, 1186, 11582, 115808),
        (4, 48, 634, 7878, 96376, 1163342),
    )
    assert result.exactly_r_total(3) == 1268282
    assert result.total == 1408796
