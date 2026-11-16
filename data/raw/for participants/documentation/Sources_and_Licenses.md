# Sources and Licenses

Competition dataset v1.0 · Source snapshot 13 November 2026

The competition files are adapted extracts. The package’s case assignments, geographic join codes, file structure and column names are competition preparation choices. Source providers retain their original attribution and terms.

## Uppsala Conflict Data Program

`conflict_events.csv` and `event_sources.csv` use UCDP Georeferenced Event Dataset (GED) v26.1 and UCDP Candidate Events Dataset v26.01.26.09 from Uppsala University. The data are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The extract selects dyads and event start dates, renames fields, adds case and geography codes, and splits the source metadata into one row per source reference. First-level administrative geography is retained. Outlet labels beginning with spreadsheet formula prefixes carry the literal prefix `Source: `. Original event descriptions and article text are outside the extract.

- Davies, S., Pettersson, T., & Öberg, M. (2026). *Organized violence 1989–2025, and violent political protests*. Journal of Peace Research. [DOI](https://doi.org/10.1093/jopres/xjag046)
- Sundberg, R., & Melander, E. (2013). *Introducing the UCDP Georeferenced Event Dataset*. Journal of Peace Research, 50(4), 523–532. [DOI](https://doi.org/10.1177/0022343313484347)
- Hegre, H., Croicu, M., Eck, K., & Högbladh, S. (2020). *Introducing the UCDP Candidate Events Dataset*. Research & Politics. [DOI](https://doi.org/10.1177/2053168020935257)
- UCDP is part of and funded by DEMSCORE, Swedish Research Council grant 2021-00162. [Download centre and licence](https://ucdp.uu.se/downloads/) · [GED codebook](https://ucdp.uu.se/downloads/ged/ged261.pdf) · [Candidate codebook](https://ucdp.uu.se/downloads/candidateged/ucdp-candidate-codebook1.5.pdf)

## UNHCR and contributing sources

`bilateral_displacement_stocks.csv` is adapted from the **UNHCR Refugee Population Statistics Database** population endpoint. `unhcr_demographics.csv` is adapted from the **UNHCR Refugee Data Portal**, official population statistics (`PopStatsOfficial`, UNHCR Population Statistics Reference). Both extracts retain eight origin codes for 2014–2025, with columns renamed and missing-value conventions documented. The demographics extract retains nationally reported disaggregations only, and the bilateral extract keeps rows with a positive count in at least one included stock category. The data are available under CC BY 4.0 subject to the relevant UNHCR terms. [Database terms](https://www.unhcr.org/terms-use-datasets) · [Portal terms](https://refugeedata.unhcr.org/en/terms-and-conditions-of-use/) · [Population metadata](https://refugeedata.unhcr.org/en/documentation/data-coverage/metadata-catalog/PopStatsOfficial/) · [Methodology](https://www.unhcr.org/refugee-statistics/methodology/data-content)

`displacement_reference_stocks.csv` combines two separately identified series. Attribute `IDMC_CONFLICT_IDP` to the **Internal Displacement Monitoring Centre (IDMC), Global Internal Displacement Database**, accessed via the UNHCR Refugee Population Statistics Database. Attribute `UNRWA_REGISTERED_REFUGEE` to the **United Nations Relief and Works Agency for Palestine Refugees in the Near East (UNRWA)**, accessed via the same UNHCR database. The competition extract selects reporting years and harmonises field names. See the database terms and applicable source notices. [UNHCR API](https://api.unhcr.org/docs/refugee-statistics.html) · [IDMC Global Internal Displacement Database](https://www.internal-displacement.org/database/) · [UNHCR population metadata and source details](https://refugeedata.unhcr.org/en/documentation/data-coverage/metadata-catalog/PopStatsOfficial/)

## The World Bank

`country_year_context.csv` is adapted from **The World Bank: World Development Indicators** and its data providers. The extract selects years and economy codes, reshapes three series, and preserves missing values. The indicators are available under CC BY 4.0 with the additional World Bank dataset terms. [Terms](https://data.worldbank.org/summary-terms-of-use)

| Indicator | Attribution to original providers | Metadata |
|---|---|---|
| SP.POP.TOTL | United Nations Population Division, national statistical offices and other providers listed in the indicator metadata | [Total population](https://data.worldbank.org/indicator/SP.POP.TOTL) |
| NY.GDP.MKTP.KD.ZG | National statistical organisations and central banks, OECD national accounts, and World Bank staff estimates | [Annual GDP growth](https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG) |
| FP.CPI.TOTL.ZG | International Monetary Fund, International Financial Statistics database | [Annual consumer price inflation](https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG) |

`source_manifest.csv` lists the exact downloads and SHA-256 checksums for the input snapshot. The source archive filenames in that manifest identify the inputs to the adaptation.
