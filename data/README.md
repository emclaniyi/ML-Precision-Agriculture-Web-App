# Dataset notes

## `final_data.csv`

This is a legacy dataset. Its original source, collection date, geographic coverage,
measurement units, license, and collection method are currently unknown. It must be
treated as unverified research data until its provenance can be recovered or replaced.

The file currently contains 999 rows and these fields:

```text
pH, N, P, K, OC, Particles, Water_holding_content, Soil_type, crop_type
```

There are no coordinates, dates, seasons, farm identifiers, yield measurements, or
management records. Consequently, weather, rainfall, satellite, and soil-map data
cannot be joined to these rows reliably yet.

## Findings from the initial audit

- No missing values were found.
- No exact duplicate rows were found.
- There are 10 crop labels and 3 soil-type labels.
- Crop labels are strongly associated with soil type: `carrot`, `potatoes`, and
  `rice` occur only with `clay`; `coconut` and `melon` occur only with `Sandy`;
  the remaining labels occur only with `loamy`.
- The units and meaning of `OC`, `Particles`, and `Water_holding_content` have not
  been verified.
- The data should not be merged with an external dataset merely because column
  names overlap.

## Data policy for future additions

External data must first be kept in a separate raw file and documented with:

- source URL and download date;
- license and redistribution terms;
- country, region, and time period;
- measurement units and soil depth where applicable;
- target-label definitions;
- transformation and cleaning steps.

Only compatible data should be combined into a processed training table. Every
processed row should retain a `source` field, and ideally a `plot_id`, coordinates,
and season/date fields.

The current CSV remains the model baseline until a traceable replacement dataset is
available.
