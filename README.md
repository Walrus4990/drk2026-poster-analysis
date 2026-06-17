# DGRh 2026 Poster — Rheumatologische Komplexbehandlung: Ergebnisse aus Routinedaten

Dieser Code wertet Routinedaten einer stationären rheumatologischen Behandlung aus.
Die Analyse wurde erstellt für den 54. Kongress der Deutschen Gesellschaft für Rheumatologie
und Klinische Immunologie (DGRh), 9.–12. September 2026, Congress Center Leipzig.

**Zitierung:** Völz A; Seyfert C (2026): Rheumatologische Komplexbehandlung — Ergebnisse aus Routinedaten.
Abstract Nr. 250. 54. Kongress der Deutschen Gesellschaft für Rheumatologie und Klinische
Immunologie (DGRh), 9.–12. September 2026, Congress Center Leipzig.

## Analyse

- Datenbereinigung und -aufbereitung
- Aggregation verschiedener Krankheitsaktivitätsindizes (SDAI, DAPSA, BASDAI, BASFI, SLEDAI, DAS28)
- Min-Max-Normalisierung zur vergleichenden Darstellung
- Vergleich der Behandlungsresponse nach Geschlecht und Diagnosegruppe (t-Test, ANOVA, Tukey Post-hoc)
- Gemischtes lineares Regressionsmodell (Mixed Effects Model) mit zufälligem Intercept pro Patient
- Modelldiagnostik: AIC-Vergleich, Konfundierungsanalyse

## Skripte

- `01_ingest.py` — Rohdaten einlesen, bereinigen, in SQLite speichern
- `02_reshape.py` — Scores aggregieren, normalisieren, Langtabelle für Regression erstellen
- `03_descriptive_analysis.py` — Deskriptive Auswertung und Export nach Excel
- `04_regression.py` — Regressionsanalyse, Modelldiagnostik und Export

## Hilfsdateien

- `utils.py` — Gemeinsam genutzte Funktionen und Variablen
