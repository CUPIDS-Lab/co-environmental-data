# Filter-pivot recipes — `reservoir-storage.csv`

Long is the *storage* shape; wide is the *analysis* shape. These recipes recover
the human-readable wide views from the tidy long CSV at
`data/processed/reservoir-storage.csv`. Three stacks, same result.

## 1. Latest storage per reservoir (wide: reservoir × variable)

**pandas**
```python
import pandas as pd
df = pd.read_csv("data/processed/reservoir-storage.csv", parse_dates=["datetime"])
latest = (df.sort_values("datetime")
            .groupby(["source", "reservoir_id", "variable"]).tail(1))
wide = latest.pivot_table(index=["source", "reservoir_name"],
                          columns="variable", values="value", aggfunc="last")
```

**R / tidyverse**
```r
library(tidyverse)
df <- read_csv("data/processed/reservoir-storage.csv")
df |>
  group_by(source, reservoir_id, variable) |>
  slice_max(datetime, n = 1) |>
  pivot_wider(names_from = variable, values_from = value)
```

**SQL / DuckDB**
```sql
PIVOT (
  SELECT source, reservoir_name, variable, value,
         row_number() OVER (PARTITION BY source, reservoir_id, variable
                            ORDER BY datetime DESC) AS rn
  FROM read_csv_auto('data/processed/reservoir-storage.csv')
) ON variable USING last(value) WHERE rn = 1 GROUP BY source, reservoir_name;
```

## 2. Storage time series for one reservoir

```python
gm = df.query("variable == 'storage_af' and reservoir_name == 'Green Mountain Reservoir'")
gm.set_index("datetime")["value"].plot()   # acre-feet over time
```

## 3. Rows per source × variable (the audit table, on demand)

```python
df.pivot_table(index="source", columns="variable", values="value", aggfunc="count")
```

## 4. Cross-source concept comparison (mind the caveats)

```python
# Compare elevation across sources ONLY after confirming vertical datums —
# see data/lookups/concepts.yaml (reservoir.elevation_ft caveat).
elev = df[df["concept"] == "reservoir.elevation_ft"]
elev.pivot_table(index="datetime", columns="source", values="value")
```
> ⚠️ A pivot that *looks* comparable can be misinformation if the datum/capacity
> caveats are ignored. Read the concept catalog before publishing a comparison.
