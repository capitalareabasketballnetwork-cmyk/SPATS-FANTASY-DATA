# SPATS Fantasy Data

Historical NFL player-week stats with **fantasy scores computed from underlying box-score statistics**, not downloaded fantasy totals.

## Data source
Uses [nflverse](https://github.com/nflverse/nflverse-data) via [nflreadpy](https://github.com/nflverse/nflreadpy). Availability and fields differ by year; the pipeline reports errors rather than silently claiming complete coverage. Player-week data begins in 1999 where published.

## Quick start
```bash
pip install -r requirements.txt
python -m src.build --start 2025 --end 2026
pytest -q
```
For full history: `python -m src.build --start 1999 --end 2026`.

Raw files are in `data/raw/`; derived fantasy scores in `data/processed/`. Both use Parquet. Full PPR, half PPR, and standard offense-only scores are generated. Team DST and kicking scoring are outside scope.

**Important:** Missing source columns are not evidence of zero production. Review the source schema and completeness before using older seasons. The scoring formula is conventional but platform-specific scoring (bonuses, return TDs, fumble types) may differ.

The workflow can be run from **Actions → Update NFL player data → Run workflow**. It is scheduled weekly. The first historical import may be large and GitHub is not ideal for very large binary datasets; migrate to object storage if needed.
