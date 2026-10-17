# Wöchentliche Urologie-Berichte

Hier werden die angeforderten Studienberichte und Repository-Prüfungen archiviert. Die erste geplante Ausgabe ist am **16. Oktober 2026**. Studienbericht und Repository-Prüfung sind für Freitagmorgen in der Zeitzone **Europe/Berlin** geplant. Sie werden im selben Freitagslauf als getrennte Berichte erzeugt. Die Terminierung erfolgt über eine ChatGPT-Aufgabe; sie ist kein GitHub-Actions-Cronjob.

## Studien und Updates

Ablage: `weekly-reports/research/YYYY-MM-DD.md`.

Der Studienbericht wird vollständig in Spanisch, Englisch und Deutsch aus derselben recherchierten Evidenz in **Usubillaga/Urofragen** und **Usubillaga/Residency-Game-DE** veröffentlicht. Er enthält nur relevante neue Studien, Leitlinien- und Zulassungsänderungen seit der vorherigen Ausgabe, beim ersten Lauf aus den letzten sieben Tagen. Eine ruhige Woche wird ausdrücklich als solche dokumentiert.

Je Beitrag: Originalquelle und Veröffentlichungsdatum, Fragestellung und Studiendesign, Population, Vergleich, wichtigste Ergebnisse und Grenzen sowie konkrete Bedeutung für Fragen, Erklärungen, Klassifikationen oder Lernfälle. Neue Evidenz, geltende Leitlinien und Zulassungsstatus werden getrennt dargestellt. Auswirkungen auf die beiden Projekte werden anhand tatsächlich gelesener Inhalte beschrieben.

Die datierten Ausgaben bleiben erhalten. Ein Verzeichnis der erschienenen Berichte wird hier ergänzt. Vor der ersten Ausführung existiert noch kein Studienbericht.

## Repository-Prüfung und Verbesserungen

Ablage: `weekly-reports/maintenance/YYYY-MM-DD.md`.

Geprüft werden neue Commits und offene Pull Requests, Build und vorhandene Tests, Fragen-/Antwortkonsistenz, Quellenstand, Übersetzungen, Klassifikationen, lokale Verweise und die Funktionsfähigkeit der Lernoberfläche. Der erste Lauf schließt eine Ausgangsprüfung des aktuellen Stands ein.

Belegte Fehler und sinnvolle begrenzte Verbesserungen werden in nachvollziehbaren Branches und Pull Requests umgesetzt. Jeder Prüfbericht nennt Befund, betroffene Dateien oder Fragen-IDs, konkrete Maßnahme, PR-Link sowie tatsächlich ausgeführte Prüfungen und verbleibende Lücken. Eine Woche ohne Befund wird knapp dokumentiert. Doppelte PRs für dieselbe unveränderte Ursache werden vermieden.

Medizinische Änderungen erhalten eine überprüfbare Quelle. Eine technische Prüfung oder KI-Überarbeitung ersetzt keine vorhandene fachärztliche Freigabe; Reviewstatus und Provenienz müssen zur jeweiligen Inhaltsversion und Sprache passen. Persönliche Spielstände, Prüfernamen und private Gesprächsinhalte gehören nicht in diese öffentlichen Berichte.

## Besonderheiten von Residency-Game-DE

- Der aktuelle Fragenvertrag in `data/question-contract.json` hat Vorrang; derzeit genau 500 bewertete Fragen.
- Die 50 klinisch/operativ eingebetteten Anatomiefragen und die 30 TNM-/Traumafälle erhalten.
- Klinische und pathologische Klassifikation sowie TNM- und AAST-Editionen eindeutig unterscheiden.
- Cartoonstil, Humor, freiwillige Joker, Markierungen und deren Export sowie kompatible Spielstände erhalten.
- Keine Lernziele oder ungewollten Antwort-Hinweise vor der Entscheidung ausliefern.
- Sprachfassungen DE/EN/ES, Importprovenienz und die Korrekturschicht berücksichtigen.
- Quelldaten bearbeiten und Katalog sowie Offline-Ausgabe über `python scripts/manage.py build` erzeugen.

Die aktuellen Prüfungen stehen in `.github/workflows/check.yml`: `python scripts/manage.py validate`, `python -m unittest discover -s tests -v`, `node tests/tests-engine.cjs`, `node tests/tests-cartoon.cjs` sowie Build und Paketierung. Vor jeder Ausführung die aktuelle Workflowfassung lesen.

## Sprachfassungen und Relevanznoten

Studien- und Wartungsberichte erscheinen vollständig in **Spanisch, Englisch und Deutsch**, in dieser Reihenfolge. Die bestehende deutsche Datei `YYYY-MM-DD.md` bleibt gültig; Begleitfassungen heißen `YYYY-MM-DD-es.md` und `YYYY-MM-DD-en.md`. Jede Fassung enthält dieselben Befunde, Zahlen, Daten, Quellen, Projektbezüge, IDs, Entscheidungen und Grenzen, vollständig übersetzt, mit gegenseitigen Sprachlinks. Die Studienfassungen sind in beiden Repositories identisch; Wartungsberichte bleiben projektspezifisch.

Jeder ausgewählte Studien-/Updatebeitrag und jeder Wartungsbefund erhält eine **Relevanznote** mit kurzer Begründung:

| Note | Deutsch | English | Español |
|---|---|---|---|
| 1 | sehr relevant | very relevant | muy relevante |
| 2 | relevant | relevant | relevante |
| 3 | etwas relevant | somewhat relevant | algo relevante |
| 4 | wenig relevant | low relevance | poco relevante |

Die Note bewertet redaktionell die praktische Bedeutung für Lerninhalte, Erklärungen oder die verlässliche Projektfunktion. Sie wird in allen Sprachfassungen gleich vergeben und getrennt von **P1/P2/P3, klinischer Tragweite, Evidenzstärke, Zulassungsstatus, Konfidenz und Änderungsentscheidung** ausgewiesen. Eine hohe Relevanz ist keine medizinische Freigabe und keine neue Leitlinienempfehlung. Methoden, reine Testprotokolle und Stichprobenlisten zählen nicht als zusätzliche neue Befunde.

Der einzige Wartungscursor bleibt der JSON-Abschnitt `monitoring_state` in der deutschen Basisdatei `maintenance/YYYY-MM-DD.md`. Frühere Ausgaben für die Cursor-/Abdeckungswahl nur anhand dieses Basismusters auswählen, nicht anhand der Sprachsuffixe. Ergänze dort in jedem `reported_findings`-Eintrag `relevance_grade` (Ganzzahl 1–4) und `relevance_reason`; die Übersetzungen verlinken diesen gemeinsamen Zustand. Eine reine Sprach-/Notenergänzung schreibt weder Prüfcursor noch Freigaben fort und gilt nicht als erneute Recherche oder neue Ausgabe.

## Ausgaben

Noch keine Ausgabe; erster geplanter Termin: 16.10.2026.

- 17.10.2026: [Studien und Updates](research/2026-10-17.md)

- 17.10.2026: [Repository-Prüfung](maintenance/2026-10-17.md)

<!-- urology-report-languages:2026-10-17 -->
### Sprachfassungen der Ausgabe vom 17.10.2026

- Studien: [Español](research/2026-10-17-es.md) · [English](research/2026-10-17-en.md) · [Deutsch](research/2026-10-17.md)
- Wartung: [Español](maintenance/2026-10-17-es.md) · [English](maintenance/2026-10-17-en.md) · [Deutsch](maintenance/2026-10-17.md)

