# Fragenbank: 500 bewertete Fragen

Stand des Quellenabgleichs: **11. Oktober 2026**. Die aktive Bank enthält **500 Entscheidungen in 402 Fällen** und **1.927 Antwortoptionen**, vollständig in Deutsch, Englisch und Spanisch. Eine Entscheidung zählt als eine Frage. Wiederholungen im Chefquiz, Atlas-Tipps und Übersetzungen zählen nicht zusätzlich.

## Zusammensetzung

| Inhalt | Fälle | Bewertete Fragen |
| --- | ---: | ---: |
| Ursprüngliche Schichtgeschichten | 30 | 90 |
| Onkologische Geschichten | 20 | 58 |
| Importierte Hauptbank | 267 | 267 |
| Ausgewählte klinische Zusatzfragen | 35 | 35 |
| Neue urologische Anatomiefragen | 50 | 50 |
| **Aktive Bank** | **402** | **500** |

Vor dieser Überarbeitung waren 423 Fälle mit 521 Entscheidungen aktiv. Alle 30 ursprünglichen Geschichten, 20 Onkologie-Geschichten und 267 importierten Fragen bleiben erhalten. Von 106 klinischen Zusatzfragen bleiben 35 aktiv: 12 aktuelle Leitlinienthemen, 10 Systemtherapie-/Nebenwirkungsfragen, 10 Bestrahlungsfragen und 3 funktionelle Fragen. Die Auswahl ergänzt die vorhandenen Themen und hält jeden der sechs Dienste mit mindestens zehn Fällen spielbar.

**71 Zusatzfragen liegen im Archiv**, `data/archive/supplemental-questions.json`. Das ist eine redaktionelle Auswahl für die feste Bankgröße, keine pauschale Aussage, dass jede archivierte Frage medizinisch falsch sei. Das Archiv bewahrt Frage, Antworten, Erklärungen, Hinweise und Zeichnungszuordnung. Alte abgeschlossene Antworten und Lesezeichen bleiben prüfbar und im Logbuch sichtbar; auch die Python-Auswertung kennt sie. Archivfragen gelangen nicht in Bibliothek, Dienstpläne, Revanche oder Protokolltraining. Ein alter unvollendeter Dienst mit einer Archivfrage kann in dieser Version nicht fortgesetzt werden; abgeschlossene Einträge bleiben erhalten.

## Neue Anatomie

| Bereich | Fragen | Beispiele |
| --- | ---: | --- |
| Niere | 10 | Hilusreihenfolge, Hüllen, Segmentarterien, Kelchzugang, Pleura, Hufeisenniere |
| Ureter | 8 | Gefäßversorgung, Psoasverlauf, Beckeneingang, Uterusarterie, Samenleiter, Doppelanlage |
| Blase | 6 | Trigonum, Urachus, Retzius-Raum, Obturatorreflex, Muskelschichten, Peritoneum |
| Prostata | 7 | Zonen, Ejakulationsgänge, posteriorer Präparationsraum, Nerven, Rhabdosphinkter |
| Penis und Urethra | 7 | Schwellkörper, Glans, Tunica albuginea, Buck-Faszie, Verletzungsmuster, Cowper-Gänge |
| Hoden und Skrotum | 7 | Lymphabfluss, Gonadalvenen, Temperaturregulation, Bell-clapper, Nebenhoden |
| Nerven und Miktion | 5 | Parasympathikus, Pudendus, Hypogastrikus, Emission, sensibler Penisnerv |
| **Gesamt** | **50** | |

Alle **50 Anatomiefragen** haben ein konkretes klinisches Korrelat: **31 OP-Situationen und 19 klinische Fälle**, in der Akte und im Fragetext. Beispiele sind die Hilusorientierung vor Nephrektomie, der Kelchzugang für PCNL, Prostatazonen vor HoLEP oder Biopsie, Nerven und Kontinenz bei Prostatektomie, Lymphabfluss beim Hodentumor und die Hodentorsion bei der Notfallexploration. Auch zuvor reine Strukturfragen sind jetzt eingebettet, etwa Nierenkörperchen bei der Beurteilung einer Nierenbiopsie oder der Samenleiterursprung vor Vasektomie. Die klinischen Vignetten sind fiktive Lehrfälle; sie geben die anatomische Lösung nicht als Lernziel vor.

Jede Frage hat vier gemischte Antwortoptionen, genau eine richtige Antwort und eine eigene Begründung zu jeder Option in DE/EN/ES. Die primären Schlüssel sind auf a/b/c/d verteilt (13/12/12/13); die tatsächliche Reihenfolge wird bei jeder Sitzung neu gemischt. Die Fragen verwenden eigenständige Formulierungen, keine kopierten Abbildungen oder Lehrbuchpassagen. Anatomische Regelvarianten werden als typisch beschrieben, nicht als ausnahmslos. Ein Überkreuzen der Iliakalgefäße wird beispielsweise als Landmarke behandelt, nicht als stets nachgewiesene dritte anatomische Ureterenge.

Das neue Fachgebiet **Urologische Anatomie** ist filterbar und erhält eine eigene Fortschrittsgruppe. Die Patientenkennung lautet bei diesen Modellvisiten „Anatomievisite“; Alter, Geschlecht und Vitalwerte werden nicht erfunden. Neutrale Cartoon-Dialoge rahmen die Fachfrage ein. Achtzehn Fragen bekamen bei der redaktionellen Prüfung anatomisch näherliegende Ablenkungsantworten.

## Gezielte klinische Verbesserungen

Die Korrekturen stehen mit altem und neuem Wortlaut, Datum und Quellen in `data/case-updates.json`. Bestehende Antwort-IDs, Punktwerte und Zeitwerte bleiben erhalten, damit bisherige korrekte Logbucheinträge weiter validiert werden können.

| Frage | Präzisierung | Grundlage |
| --- | --- | --- |
| Verlängerte Erektion nach Schwellkörperinjektion | Frühe orale Terbutalin-Option mit begrenzter Evidenz; kein obligatorischer erster Schritt und kein Warten bei Ischämieverdacht. Dauer allein beweist keine Ischämie. | EAU Sexual and Reproductive Health, Kapitel 10.1.2–10.1.3, Tabelle 10.4 |
| Refraktärer Priapismus nach 40 Stunden | Frühe Prothese gemeinsam im spezialisierten Zentrum besprechen; Gewebevitalität und Nekrosehinweise sind entscheidend, keine automatische Implantationspflicht nach einer festen Stundenzahl. | EAU, Kapitel 10.1.3.b.2 |
| BRCA2-Träger, bestätigter PSA ≥3 ng/ml | Spezieller S3-Risikopfad: MRT und Biopsieangebot nach Aufklärung; eine unauffällige MRT hebt das PSA-Kriterium nicht automatisch auf. | S3 Prostatakarzinom 8.1, Empfehlungen 4.8–4.10; EAU Diagnostik |
| Sestamibi-positive kleine Nierenraumforderung | Traceraufnahme beweist keine Gutartigkeit; Biopsie, wenn das Ergebnis das Vorgehen verändert. „Onkozytär“ in einer Stanzbiopsie ist kein endgültiger Onkozytomnachweis. Überwachung nach Gesamtrisikoentscheidung. | EAU RCC, Kapitel 3.5.4–3.5.5, 5.2.3, 5.3, 7.2.4 |
| Basis-PSA 2,1 ng/ml | Die Frage nennt die deutsche S3-Version und Empfehlung ausdrücklich; das zweijährliche Intervall bleibt korrekt. | S3 Prostatakarzinom 8.1, Empfehlung 4.4 |

Die Belzutifan-Hypoxiefrage verlinkt zusätzlich direkt die aktuelle europäische Fachinformation. Die übrigen ausgewählten Zusatzfragen behalten die dokumentierten Quellen und bisherigen Korrekturen. Die vorliegenden Änderungen sind ein gezielter Quellenabgleich, keine neue unabhängige fachärztliche Freigabe aller 500 Fragen oder aller Übersetzungen.

## Quellen

`data/refs-anatomy.json` enthält 24 konkrete Quellen mit Abrufdatum und abgegrenztem Geltungsbereich. Anatomische Fakten wurden anhand der NCBI-Bookshelf-Referenzkapitel geprüft. Klinische Entscheidungen verwenden die einschlägigen EAU-Kapitel, die offizielle deutsche S3-Leitlinie und die EMA-Fachinformation:

- [EAU Priapismus](https://uroweb.org/guidelines/sexual-and-reproductive-health/chapter/priapism)
- [EAU Prostatakarzinom: Diagnostik](https://uroweb.org/guidelines/prostate-cancer/chapter/diagnostic-evaluation)
- [S3 Prostatakarzinom 8.1: offizielle Kurzfassung](https://www.leitlinienprogramm-onkologie.de/fileadmin/user_upload/Downloads/Leitlinien/Prostatatkarzinom/Version_8/22_05_2026_Prostatakarzinom_Kurzversion_8.1_final_KL.pdf)
- [EAU Nierenzellkarzinom: Diagnostik](https://uroweb.org/guidelines/renal-cell-carcinoma/chapter/diagnostic-evaluation), [Pathologie](https://uroweb.org/guidelines/renal-cell-carcinoma/chapter/epidemiology-aetiology-and-pathology) und [Therapie](https://uroweb.org/guidelines/renal-cell-carcinoma/chapter/disease-management)
- [EAU Kinderurologie: Ureterozele und ektopischer Ureter](https://uroweb.org/guidelines/paediatric-urology/chapter/ureterocele-and-ectopic-ureter)
- [EMA Welireg: europäische Fachinformation](https://www.ema.europa.eu/en/documents/product-information/welireg-epar-product-information_en.pdf)

Die S3-Version 8.1 stammt aus 2025; sie wurde über die aktuell angebotene offizielle Fassung geprüft. „Geprüft am 11. Oktober 2026“ bezeichnet den Abruf, nicht das Veröffentlichungsjahr der Leitlinie. Anatomiequellen sind keine klinischen Therapieempfehlungen.

## Antwortverratende Lernziele entfernt

- Die Patientenakte zeigt keine Lernziel-Liste und keinen generischen Lernziel-Hinweis mehr.
- Janas Joker ergänzt keine Lernziele. Er bleibt als ausdrücklich angeforderte spielerische Hilfe erhalten.
- Ohne geschriebenen Konsultationshinweis wird kein Lernziel als Ersatz verwendet.
- Beim Build werden alle `objectives` aus aktiven und historischen Browserdaten entfernt. Importierte Rohdaten bleiben für die Provenienz erhalten.
- Fallweite Korrekturbegründungen, Evidenznotizen und markierte Zeichnungen werden erst nach der letzten Antwort eingeblendet. Zwischenfragen einer Geschichte werden nicht durch die abschließende Erklärung vorweggenommen.

Cartoon-Artwork, Figuren, Dialogbibliothek, Konfetti, Spritzer, Kaffeepausen, Sticker und Chefquiz bleiben erhalten. Die klassischen HTML-Spiele sind unverändert.

## Technische Prüfung

Der Vertrag `data/question-contract.json` prüft genau 500 aktive Entscheidungen, mindestens 50 Anatomiefragen und normalisierte identische Fragen samt Antworttexten in jeder Sprache. Eine absichtlich ergänzte 501. Frage und ein duplizierter Fragetext werden in Regressionstests abgelehnt. Anatomiefragen benötigen zusätzlich einen dokumentierten OP- oder Fallbezug (`clinicalContext`); fehlende, ungültige oder unvollständig übersetzte Angaben werden zurückgewiesen.

Die historischen Fälle durchlaufen dieselbe Struktur-, Sprach-, Antwort- und Quellenvalidierung wie aktive Fälle. Zusätzliche Tests prüfen alte Logbücher, manipulierte Punktwerte, Export/Import, Ausschluss archivierter Fragen aus neuen Diensten und die Anzeige vor beziehungsweise nach der Antwort. Die Softwareprüfungen sind in [VALIDATION.md](VALIDATION.md) protokolliert.

Importierte Freigabe- und Entwurfsmarkierungen bleiben erhalten. Die neuen Anatomiefragen tragen keine erfundene fachärztliche Freigabe (`clinicalSignoffLanguages: []`).
