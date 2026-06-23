# Filter & pivot recipes

Long is the *storage* shape (one row per `source × site_id × datetime × variable`); wide is the *analysis* shape. Recover wide views with these recipes — don't store them.

```python
import pandas as pd
df = pd.read_csv("data/processed/climate-stations.csv", parse_dates=["datetime"],
                 dtype={"site_id": str})
stations = pd.read_csv("data/lookups/stations.csv", dtype={"site_id": str})
```

## One measure, wide over stations (a station × date matrix)

```python
swe = (df[df.variable == "swe_in"]
       .pivot_table(index="datetime", columns="site_id", values="value"))
```

## One station, all measures side by side (a daily climate record)

```python
one = (df[df.site_id == "1886"]
       .pivot_table(index="datetime", columns="variable", values="value"))
# e.g. columns: temp_max_f, temp_min_f, precip_in, solar_rad_mj_m2, vapor_pressure_kpa, wind_run_km
```

## Join the station dimension (network, location, period of record)

```python
enriched = df.merge(
    stations[["site_id", "network", "latitude", "longitude", "division"]],
    on="site_id", how="left")
```

## Filter by network (don't pool across networks blindly)

```python
coop_precip = enriched[(enriched.network == "NOAA") & (enriched.variable == "precip_in")]
mesonet = enriched[enriched.network == "CoAgMet"]   # has Solar/VP/Wind
```

## SWE only — the SNOTEL crosswalk to snowpack #11

```python
swe = df[df.variable == "swe_in"].merge(
    stations[["site_id", "site_id_network", "network"]], on="site_id", how="left")
# site_id_network (GHCN/NRCS id) crosswalks to the snowpack pipeline's SNOTEL series;
# de-duplicate — CDSS SWE re-serves NRCS, it is not an independent measurement.
```

## Derived quantities (mind the units)

```python
# mean wind SPEED (km/h) from wind RUN (km/day):
speed = df[df.variable == "wind_run_km"].assign(speed_kmh=lambda d: d.value / 24)
# open-water evaporation estimate from PAN evaporation (apply a pan coefficient ~0.7):
lake_evap = df[df.variable == "evap_in"].assign(est_open_water_in=lambda d: d.value * 0.7)
```
