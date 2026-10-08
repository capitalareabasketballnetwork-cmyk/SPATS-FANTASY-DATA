import polars as pl
from src.build import score

def test_ppr():
    df = pl.DataFrame({"rushing_yards":[85], "rushing_tds":[1], "receptions":[4], "receiving_yards":[35]})
    row = score(df).row(0, named=True)
    assert row["fantasy_standard"] == 18.0
    assert row["fantasy_half_ppr"] == 20.0
    assert row["fantasy_ppr"] == 22.0
