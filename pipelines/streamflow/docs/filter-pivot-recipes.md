# Filter & pivot recipes — `streamflow.csv`

Tidy long is the *storage* shape; these recipes recover the *analysis* (wide) shapes. Each is given in **pandas**, **tidyverse**, and **DuckDB** (DuckDB queries the CSV directly — paste it into Datasette's SQL editor or BigQuery/Postgres).

> **⚠️ Read first — de-duplicate the source overlap.** DWR re-serves many USGS gages, so the same physical gage can appear twice (once per source). For single-series analysis, pick **one** source first — USGS is the system of record: `df[df.source == "usgs_nwis"]`. Keep both sources only when you *want* the cross-source comparison (last recipe).

## 1. Wide matrix: one column per gage, one row per date (USGS only)

**pandas**
```python
import pandas as pd
df = pd.read_csv("data/processed/streamflow.csv", parse_dates=["datetime"])
usgs = df[(df.source == "usgs_nwis") & (df.variable == "discharge_cfs")]
wide = usgs.pivot_table(index="datetime", columns="site_name", values="value")
```
**tidyverse**
```r
library(tidyverse)
df <- readr::read_csv("data/processed/streamflow.csv")
wide <- df |>
  filter(source == "usgs_nwis", variable == "discharge_cfs") |>
  pivot_wider(id_cols = datetime, names_from = site_name, values_from = value)
```
**DuckDB**
```sql
PIVOT (FROM 'data/processed/streamflow.csv'
       WHERE source = 'usgs_nwis' AND variable = 'discharge_cfs')
ON site_name USING first(value) GROUP BY datetime;
```

## 2. One gage's full hydrograph (Colorado R near Cameo, 09095500)

**pandas**
```python
cameo = df[(df.source == "usgs_nwis") & (df.site_id == "09095500")
           ].sort_values("datetime")[["datetime", "value", "qa_flag"]]
```
**tidyverse**
```r
cameo <- df |> filter(source == "usgs_nwis", site_id == "09095500") |> arrange(datetime)
```
**DuckDB**
```sql
SELECT datetime, value, qa_flag FROM 'data/processed/streamflow.csv'
WHERE source = 'usgs_nwis' AND site_id = '09095500' ORDER BY datetime;
```

## 3. Annual mean discharge per gage by **water year** (Oct 1–Sep 30)

Colorado hydrology is reported by water year (WY = the year the Sep 30 falls in).

**pandas**
```python
u = df[(df.source == "usgs_nwis") & (df.variable == "discharge_cfs")].copy()
u["wy"] = u.datetime.dt.year + (u.datetime.dt.month >= 10).astype(int)
annual = u.groupby(["site_name", "wy"])["value"].mean().reset_index()
```
**tidyverse**
```r
annual <- df |>
  filter(source == "usgs_nwis", variable == "discharge_cfs") |>
  mutate(wy = year(datetime) + (month(datetime) >= 10)) |>
  group_by(site_name, wy) |> summarise(mean_cfs = mean(value, na.rm = TRUE), .groups = "drop")
```
**DuckDB**
```sql
SELECT site_name,
       year(datetime) + (month(datetime) >= 10)::INT AS wy,
       avg(value) AS mean_cfs
FROM 'data/processed/streamflow.csv'
WHERE source = 'usgs_nwis' AND variable = 'discharge_cfs'
GROUP BY site_name, wy ORDER BY site_name, wy;
```

## 4. Annual **peak** daily mean per gage (drought/flood framing)

**pandas**
```python
peak = u.groupby(["site_name", "wy"])["value"].max().reset_index(name="peak_daily_mean_cfs")
```
**DuckDB**
```sql
SELECT site_name, year(datetime) + (month(datetime) >= 10)::INT AS wy,
       max(value) AS peak_daily_mean_cfs
FROM 'data/processed/streamflow.csv'
WHERE source = 'usgs_nwis' AND variable = 'discharge_cfs'
GROUP BY 1, 2 ORDER BY 1, 2;
```

## 5. Cross-source agreement for one gage (USGS vs DWR re-serve)

This is the *intended* use of keeping both sources — the per-row form of `audit.reconcile_cross_source`.

**pandas**
```python
both = df[(df.variable == "discharge_cfs") &
          (df.site_id.isin(["09095500", "COLCAMCO"]))]   # USGS + its DWR mirror
cmp = both.pivot_table(index="datetime", columns="source", values="value").dropna()
cmp["diff"] = (cmp["usgs_nwis"] - cmp["dwr_cdss"]).abs()
print(cmp["diff"].describe())                            # expect ~0
```
**DuckDB**
```sql
SELECT u.datetime, u.value AS usgs, d.value AS dwr, abs(u.value - d.value) AS diff
FROM 'data/processed/streamflow.csv' u
JOIN 'data/processed/streamflow.csv' d
  ON d.source = 'dwr_cdss' AND d.site_id = 'COLCAMCO' AND d.datetime = u.datetime
WHERE u.source = 'usgs_nwis' AND u.site_id = '09095500'
ORDER BY diff DESC LIMIT 20;   -- biggest disagreements first (provisional lags)
```

## 6. Drop ice/missing days explicitly

NA `value` already marks them; to also exclude provisional or estimated readings: **pandas** `clean = usgs[usgs.value.notna() & ~usgs.qa_flag.fillna("").str.contains("P|e")]` **DuckDB** `... WHERE value IS NOT NULL AND qa_flag NOT LIKE '%P%'`
