"""Discover-level regression guards for full-history retrieval.

These lock in the fixes for the "only the past year" bug: DWR needs *both* date
bounds (startDate alone → 404; no dates → last ~365 days), and RISE must paginate
(its page cap is 10,000 rows, well under a full reservoir history).
"""
from reservoir.sources import DwrCdss, ReclamationRise


def test_dwr_discover_requests_full_history():
    arts = list(DwrCdss().discover())
    assert arts, "DWR seed should yield artifacts"
    url = arts[0].url
    assert "startDate=" in url and "endDate=" in url   # both bounds = full history


def test_rise_discover_paginates_full_history():
    arts = list(ReclamationRise().discover())
    assert arts, "RISE seed should yield artifacts for resolved reservoirs"
    a = arts[0]
    assert "itemsPerPage=10000" in a.url               # RISE's page param (not page[size])
    assert a.metadata.get("paginate") == "jsonapi"      # fetcher follows links.next


def test_rise_discover_skips_unresolved():
    # reservoirs whose rise_item_ids are still null must not produce artifacts
    arts = list(ReclamationRise().discover())
    assert all("item_None" not in a.local_path.name for a in arts)
