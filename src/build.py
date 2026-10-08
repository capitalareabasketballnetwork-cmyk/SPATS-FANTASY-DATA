import argparse
from pathlib import Path
import polars as pl
import nflreadpy as nfl

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"

def score(df: pl.DataFrame) -> pl.DataFrame:
    """Conventional offensive fantasy scoring from source statistics."""
    def stat(name):
        return pl.col(name).cast(pl.Float64, strict=False).fill_null(0) if name in df.columns else pl.lit(0.0)

    base = (
        stat("passing_yards") * 0.04
        + stat("passing_tds") * 4
        - stat("interceptions") * 2
        + stat("rushing_yards") * 0.1
        + stat("rushing_tds") * 6
        + stat("receiving_yards") * 0.1
        + stat("receiving_tds") * 6
        + stat("passing_2pt_conversions") * 2
        + stat("rushing_2pt_conversions") * 2
        + stat("receiving_2pt_conversions") * 2
    )
    components = ("sack_fumbles_lost", "rushing_fumbles_lost", "receiving_fumbles_lost")
    if any(c in df.columns for c in components):
        base = base - sum((stat(c) for c in components), pl.lit(0.0)) * 2
    else:
        base = base - stat("fumbles_lost") * 2
    catches = stat("receptions")
    return df.with_columns(
        base.round(2).alias("fantasy_standard"),
        (base + catches * 0.5).round(2).alias("fantasy_half_ppr"),
        (base + catches).round(2).alias("fantasy_ppr"),
    )

def run(start, end):
    RAW.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    for year in range(start, end + 1):
        print(f"Loading {year}...", flush=True)
        df = nfl.load_player_stats(seasons=[year], summary_level="week")
        if df.is_empty():
            print(f"{year}: no records")
            continue
        df.write_parquet(RAW / f"player_week_{year}.parquet")
        score(df).write_parquet(OUT / f"player_week_{year}.parquet")
        print(f"{year}: {df.height} player-week rows, {len(df.columns)} source fields", flush=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1999)
    parser.add_argument("--end", type=int, default=2026)
    args = parser.parse_args()
    run(args.start, args.end)
