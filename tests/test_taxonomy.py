from redteam.taxonomy import CATEGORY_INFO, Category, load_seeds


def test_all_categories_have_info():
    for cat in Category:
        assert cat in CATEGORY_INFO
        info = CATEGORY_INFO[cat]
        assert info["severity"] in {"critical", "high", "medium", "low"}


def test_load_seeds_counts():
    seeds = load_seeds()
    assert len(seeds) == 60  # 6 categories x 10 seeds
    for cat in Category:
        assert sum(1 for s in seeds if s.category == cat) == 10


def test_seed_ids_unique():
    ids = [s.id for s in load_seeds()]
    assert len(ids) == len(set(ids))
