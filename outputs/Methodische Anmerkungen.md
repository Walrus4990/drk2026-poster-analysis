# Methodische Anmerkungen

## Modellspezifikation — Begründung des Ausgangsmodells

Das Ausgangsmodell wurde als lineares gemischtes Modell (Linear Mixed Effects Model) mit zufälligem Intercept pro Patient spezifiziert. Die Wahl dieses Modelltyps begründet sich darin, dass pro Patient zwei Messzeitpunkte vorliegen (vor und nach der Behandlung), wodurch die Beobachtungen nicht unabhängig sind. Ein Standard-Regressionsmodell würde die Annahme der Unabhängigkeit verletzen.

**Abhängige Variable:** Score-Wert (score_value) — kontinuierlich, eine Beobachtung pro Patient pro Zeitpunkt.

**Unabhängige Variablen (Fixed Effects):**
- Zeitpunkt (vorher/nachher) — Hauptvariable zur Erfassung des Behandlungseffekts
- Geschlecht — zeitinvariante Patientencharakteristik, deren Effekt auf Populationsebene von Interesse ist
- Zeitpunkt × Geschlecht — Interaktionsterm zur Prüfung geschlechtsspezifischer Behandlungsresponse
- Alter — kontinuierliche Kovariate, bekannter Confounder in rheumatologischen Funktionsoutcomes
- Diagnosegruppe — Fixed Effect, da die Gruppen (L40, M05, M06, M45, Sonstige) exhaustiv und spezifisch sind

**Zufälliger Effekt:** Zufälliger Intercept pro Patient (patnr) — berücksichtigt patientenindividuelle Ausgangsniveaus. Ein zufälliger Slope ist bei zwei Messzeitpunkten nicht schätzbar; die Random-Intercept-Spezifikation ist daher korrekt.

**Schätzmethode:** REML (Restricted Maximum Likelihood) — liefert unverzerrte Schätzungen der Varianzkomponenten bei dieser Stichprobengröße (N=251), während ML die Varianz unterschätzen würde.

**Aktivitätsscores und Diagnosegruppe:** Im Ausgangsmodell wurde die Diagnosegruppe nicht als Kovariate in das Norm-Modell (Aktivität) aufgenommen, da die normalisierten Aktivitätsscores (norm1/norm2) **diagnoseabhängig** berechnet werden: Jeder Patient erhält seinen Score auf Basis des diagnosespezifischen Tests (SDAI für RA, DAPSA für PsA, BASDAI für SpA). Dies begründet den Verdacht einer Zirkularität. Diese Entscheidung wurde empirisch überprüft (siehe unten).

---

## Methodische Einschränkungen

**Konfundierung zwischen Geschlecht und Diagnose:**
Die Gesamtverteilung (75 Männer, 176 Frauen) verdeckt diagnosespezifische Unterschiede. M05 und M06 sind zu 78% weiblich, M45 ist nahezu ausgeglichen (51% männlich). Geschlecht und Diagnosegruppe sind daher korreliert, was Standardfehler erhöhen und die Interpretation einzelner Koeffizienten erschweren kann. Das Modell kontrolliert jedoch simultan für beide Variablen.

**Vollständige Fallanalyse (Complete Case Analysis):**
Patienten ohne beide Messzeitpunkte werden über dropna() ausgeschlossen. Dies entspricht einer Complete-Case-Analyse, die unter der Annahme fehlender Daten vollständig zufällig (MCAR) valide ist.

**Aktivitätsscore und Diagnosegruppe — Zirkularität:**
Die Normalisierung erfolgt per Testscore, d.h. separat für SDAI, DAPSA, BASDAI etc. Die Zuordnung des Testscores folgt der Diagnose:
- DAPSA → überwiegend L40 (Psoriasis-Arthritis)
- BASDAI/BASFI → überwiegend M45 (Spondylitis ankylosans)
- SDAI/DAS28 → überwiegend M05/M06 (Rheumatoide Arthritis)

Auch nach Normalisierung trägt der norm-Score diagnostische Information. Die Aufnahme der Diagnosegruppe als Kovariate im Norm-Modell könnte daher redundant sein und Standardfehler aufblähen. Dies wurde empirisch geprüft (Test 2).

---

## Modelldiagnostik

### Test 1: Interaktionsterm Zeitpunkt × Geschlecht

Verglichen wurden ein vollständiges Modell (mit Interaktionsterm) und ein reduziertes Modell (ohne Interaktionsterm) anhand des Akaike-Informationskriteriums (AIC). Modelle wurden mit ML (nicht REML) geschätzt, da REML keinen validen AIC-Vergleich bei unterschiedlichen Fixed-Effects-Strukturen erlaubt. Eine AIC-Differenz von mehr als 2 Punkten gilt als bedeutsam.

| Score | AIC_Interaktion | AIC_Ohne_Interaktion | AIC_Differenz | Interaktion |
|-------|----------------|---------------------|---------------|-------------|
| vasa  | 1950.19        | 1953.01             | -2.82         | Ja          |
| vasp  | 1970.74        | 1972.37             | -1.63         | Nein        |
| ffbh  | 3436.67        | 3435.27             | 1.40          | Nein        |
| norm  | -284.24        | -282.90             | -1.34         | Nein        |

**Schlussfolgerung:** Der Interaktionsterm verbessert den Modellfit bei nur einem Score (VAS-A) um mehr als 2 AIC-Punkte, und dort nur um 2,8. Da die Verbesserung marginal und nicht konsistent über alle Scores ist, wird der Interaktionsterm aus dem finalen Modell ausgeschlossen.

### Test 2: Konfundierung im Norm-Modell durch Diagnosegruppe

Verglichen wurden die Koeffizienten und Standardfehler des Norm-Modells mit und ohne Diagnosegruppe als Kovariate. Eine Koeffizientenänderung von mehr als 10% bei stabilem Standardfehler gilt als Indikator für Konfundierung.

| Parameter   | Koeffizient_Ohne_Diagnose | Koeffizient_Mit_Diagnose | Änderung_Koeffizient_% | SE_Ohne_Diagnose | SE_Mit_Diagnose | Änderung_SE_% | Konfundierung |
|-------------|--------------------------|-------------------------|------------------------|-----------------|----------------|---------------|---------------|
| Zeitpunkt   | -0.1694                  | -0.1694                 | 0.0                    | 0.0100          | 0.0100         | 0.0           | Nein          |
| Geschlecht  | -0.0048                  | -0.0488                 | 924.5                  | 0.0310          | 0.0295         | 4.9           | Ja            |
| Alter       | 0.0002                   | 0.0019                  | 878.9                  | 0.0013          | 0.0013         | 3.6           | Ja            |

**Schlussfolgerung:** Der Behandlungseffektkoeffizient (Zeitpunkt) bleibt stabil. Geschlecht- und Alterkoeffizienten sind durch die Diagnosegruppe konfundiert — die Koeffizienten ändern sich um mehr als 10% bei stabilem Standardfehler. Die Diagnosezugehörigkeit kovariiert mit anderen Prädiktoren im Modell. Um Konfundierung zu vermeiden und die Effekte der einzelnen Prädiktoren isoliert schätzen zu können, wird die Diagnose in allen Modellen berücksichtigt.
