# Filter & pivot recipes — `snowpack.csv`

Tidy long is the *storage* shape; these recipes recover the *analysis* (wide) shapes. Each is given in **pandas**, **tidyverse**, and **DuckDB** (DuckDB queries the CSV directly — paste it into Datasette's SQL editor or BigQuery/Postgres).

> **⚠️ Read first.** (1) For a single SWE series per place, pick **one** source: `nrcs_snotel` is the daily modern record; `nrcs_snowcourse` is the semimonthly deep history (pre-1980). They are nearby-not-identical sites — don't average them. (2) `precip_accum_in` is **water-year cumulative** — *difference* it within a water year, never sum it. (3) Missing is NA, not zero.

## 1. Wide matrix: one column per station, one row per date (SNOTEL SWE)

**pandas**
```python
import pandas as pd
df = pd.read_csv("data/processed/snowpack.csv", parse_dates=["datetime"])
swe = df[(df.source == "nrcs_snotel") & (df.variable == "swe_in")]
wide = swe.pivot_table(index="datetime", columns="site_name", values="value")
```
**tidyverse**
```r
library(tidyverse)
df <- readr::read_csv("data/processed/snowpack.csv")
wide <- df |>
  filter(source == "nrcs_snotel", variable == "swe_in") |>
  pivot_wider(id_cols = datetime, names_from = site_name, values_from = value)
```
**DuckDB**
```sql
PIVOT (FROM 'data/processed/snowpack.csv'
       WHERE source = 'nrcs_snotel' AND variable = 'swe_in')
ON site_name USING first(value) GROUP BY datetime;
```

## 2. One station's full SWE record (Park Cone SNOTEL, 680:CO:SNTL)

**pandas**
```python
pc = df[(df.source == "nrcs_snotel") & (df.site_id == "680:CO:SNTL")
        & (df.variable == "swe_in")].sort_values("datetime")[["datetime", "value", "qa_flag"]]
```
**DuckDB**
```sql
SELECT datetime, value, qa_flag FROM 'data/processed/snowpack.csv'
WHERE source = 'nrcs_snotel' AND site_id = '680:CO:SNTL' AND variable = 'swe_in'
ORDER BY datetime;
```

## 3. Peak (April 1) SWE per station per water year

April-1 SWE is the canonical runoff predictor.

**pandas**
```python
s = df[(df.source == "nrcs_snotel") & (df.variable == "swe_in")].copy()
apr1 = s[(s.datetime.dt.month == 4) & (s.datetime.dt.day == 1)]
apr1_wide = apr1.pivot_table(index=s.datetime.dt.year, columns="site_name", values="value")
```
**DuckDB**
```sql
SELECT year(datetime) AS wy, site_name, value AS apr1_swe_in
FROM 'data/processed/snowpack.csv'
WHERE source = 'nrcs_snotel' AND variable = 'swe_in'
  AND month(datetime) = 4 AND day(datetime) = 1
ORDER BY site_name, wy;
```

## 4. ⭐ Basin SWE as percent of normal (the headline metric)

Reproduces `audit.basin_percent_normal` for one date: `100 × Σ current SWE / Σ day-of-year-median SWE`, by basin. Join the station→basin lookup first.

**pandas**
```python
sites = pd.read_csv("data/lookups/sites.csv")[["site_id", "basin"]]
s = df[(df.source == "nrcs_snotel") & (df.variable == "swe_in")].merge(sites, on="site_id")
s["md"] = s.datetime.dt.strftime("%m-%d")

target = pd.Timestamp("2024-04-01")
current = (s[s.datetime == target].groupby(["basin", "site_id"])["value"].last())
normal = (s[(s.md == "04-01") & s.datetime.dt.year.between(1991, 2020)]
          .groupby(["basin", "site_id"])["value"].median())
pair = pd.concat({"cur": current, "norm": normal}, axis=1).dropna()
pct = pair.groupby("basin").apply(lambda g: 100 * g.cur.sum() / g.norm.sum())
print(pct.round(0))
```
**DuckDB**
```sql
WITH s AS (
  SELECT d.site_id, d.datetime, d.value, k.basin
  FROM 'data/processed/snowpack.csv' d
  JOIN 'data/lookups/sites.csv' k USING (site_id)
  WHERE d.source = 'nrcs_snotel' AND d.variable = 'swe_in'
),
cur AS (SELECT basin, site_id, value AS cur FROM s WHERE datetime = DATE '2024-04-01'),
norm AS (SELECT basin, site_id, median(value) AS norm FROM s
         WHERE strftime(datetime, '%m-%d') = '04-01'
           AND year(datetime) BETWEEN 1991 AND 2020
         GROUP BY basin, site_id)
SELECT basin, round(100 * sum(cur) / sum(norm)) AS pct_of_normal
FROM cur JOIN norm USING (basin, site_id) GROUP BY basin ORDER BY basin;
```

## 5. Daily precipitation from the cumulative gauge (difference within a water year)

`precip_accum_in` is a running water-year total — recover daily increments by differencing, resetting at the Oct-1 boundary.

**pandas**
```python
p = df[(df.source == "nrcs_snotel") & (df.variable == "precip_accum_in")].sort_values("datetime").copy()
p["wy"] = p.datetime.dt.year + (p.datetime.dt.month >= 10).astype(int)
p["precip_daily_in"] = p.groupby(["site_id", "wy"])["value"].diff().clip(lower=0)
```

## 6. Cross-source: a co-located SNOTEL vs its snow course (Park Cone)

The *intended* use of keeping both sources — the per-row form of `audit.reconcile_cross_source`. Expect them to track within a few inches, **not** to be identical.

**pandas**
```python
both = df[(df.variable == "swe_in") &
          (df.site_id.isin(["680:CO:SNTL", "06L02:CO:SNOW"]))]   # Park Cone pair
cmp = both.pivot_table(index="datetime", columns="source", values="value").dropna()
cmp["diff_in"] = (cmp["nrcs_snotel"] - cmp["nrcs_snowcourse"]).abs()
print(cmp["diff_in"].describe())     # a few inches, not ~0
```

## 7. Drop provisional / suspect readings

NA `value` already marks gaps; to also exclude provisional or suspect values:
**pandas** `clean = swe[swe.value.notna() & ~swe.qa_flag.fillna("").str.contains("P|S")]`
**DuckDB** `... WHERE value IS NOT NULL AND qa_flag NOT LIKE '%S%'`
