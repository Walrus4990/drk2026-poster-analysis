## Multivariate Regressionsanalyse

| score_type                       | zeitpunkt   | geschlecht   | alter      | L40        | M05       | M06      | M45      | N     |
|:---------------------------------|:------------|:-------------|:-----------|:-----------|:----------|:---------|:---------|:------|
| vasa                             | -2.7888***  | -0.1008      | -0.0028    | 0.9856**   | 1.3731*** | 0.9362** | 0.3362   | 251.0 |
| vasp                             | -2.0239***  | -0.0359      | -0.004     | 0.5377     | 1.029**   | 0.4986   | 0.5527   | 251.0 |
| ffbh                             | 4.8586***   | 4.7167       | -0.6137*** | -14.2654** | -8.431    | -9.9059* | -8.5505  | 212.0 |
| norm                             | -0.1694***  | -0.0488      | 0.0019     | -0.0848    | -0.043    | -0.0764  | 0.1451** | 195.0 |
| * p<0.05, ** p<0.01, *** p<0.001 |             |              |            |            |           |          |          |       |

---

## Brauchen wir einen Interaktionsterm Zeitpunkt x Geschlecht?

| Score   |   AIC_Interaktion |   AIC_Ohne_Interaktion |   AIC_Differenz | Interaktion   |
|:--------|------------------:|-----------------------:|----------------:|:--------------|
| vasa    |           1950.19 |                1953.01 |           -2.82 | Ja            |
| vasp    |           1970.74 |                1972.37 |           -1.63 | Nein          |
| ffbh    |           3436.67 |                3435.27 |            1.4  | Nein          |
| norm    |           -312.8  |                -311.46 |           -1.34 | Nein          |

**Schlussfolgerung:** Der Interaktionsterm verbessert den Modellfit bei nur einem Score um mehr als 2 AIC-Punkte,und dort nur um 2,8. Der Interaktionsterm wird aus dem finalen Modell ausgeschlossen.


---

## Sind die Diagnosegruppen-Koeffizienten im Norm-Modell konfundiert?

| Parameter   |   Koeffizient_Ohne_Diagnose |   Koeffizient_Mit_Diagnose |   Änderung_Koeffizient_% |   SE_Ohne_Diagnose |   SE_Mit_Diagnose |   Änderung_SE_% | Konfundierung   |
|:------------|----------------------------:|---------------------------:|-------------------------:|-------------------:|------------------:|----------------:|:----------------|
| Zeitpunkt   |                     -0.1694 |                    -0.1694 |                      0   |             0.01   |            0.01   |             0   | Nein            |
| Geschlecht  |                     -0.0048 |                    -0.0488 |                    924.5 |             0.031  |            0.0295 |             4.9 | Ja              |
| Alter       |                      0.0002 |                     0.0019 |                    878.9 |             0.0013 |            0.0013 |             3.6 | Ja              |

**Schlussfolgerung:** Der Behandlungseffektkoeffizient (Zeitpunkt) bleibt stabil. Geschlecht- und Alterkoeffizienten ändern sich um mehr als 10% bei stabilem Standardfehler. Die Diagnosezugehörigkeit kovariiert mit anderen Prädiktoren im Modell. Um Konfundierung zu vermeiden und die Effekte der einzelnen Prädiktoren isoliert schätzen zu können, wird die Diagnose in allen Modellen berücksichtigt.
