# DRK 2026 Poster Datenanalyse

Dieser Code wertet Routinedaten einer stationären rheumatologischen Behandlung aus. Die Analyse umfasst:

* Datenbereinigung und -aufbereitung
* Aggregation verschiedener Krankheitsaktivitätsindizes (SDAI, DAPSA, BASDAI, BASFI, SLEDAI, DAS28)
* Min-Max-Normalisierung zur vergleichenden Darstellung
* Vergleich der Behandlungsresponse nach Geschlecht und Diagnosegruppe (t-Test, ANOVA, Tukey Post-hoc)
* Gemischtes lineares Regressionsmodell (Mixed Effects Model) 

Skripte:

01_ingest.py — Rohdaten einlesen, bereinigen, in SQLite speichern
02_reshape.py — Scores aggregieren, normalisieren, Langtabelle für Regression erstellen
03_analysis.py — Statistische Auswertung und Export nach Excel
