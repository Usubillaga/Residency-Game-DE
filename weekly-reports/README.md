# Wöchentliche Urologie-Berichte

Hier werden die angeforderten Studienberichte und Repository-Prüfungen archiviert. Die erste geplante Ausgabe ist am **16. Oktober 2026**. Studienbericht und Repository-Prüfung sind für Freitagmorgen in der Zeitzone **Europe/Berlin** geplant. Sie werden im selben Freitagslauf als getrennte Berichte erzeugt. Die Terminierung erfolgt über eine ChatGPT-Aufgabe; sie ist kein GitHub-Actions-Cronjob.

## Studien und Updates

Ablage: `weekly-reports/research/YYYY-MM-DD.md`.

Der deutschsprachige Bericht wird aus derselben recherchierten Evidenz in **Usubillaga/Urofragen** und **Usubillaga/Residency-Game-DE** veröffentlicht. Er enthält nur relevante neue Studien, Leitlinien- und Zulassungsänderungen seit der vorherigen Ausgabe, beim ersten Lauf aus den letzten sieben Tagen. Eine ruhige Woche wird ausdrücklich als solche dokumentiert.

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

## Ausgaben

Noch keine Ausgabe; erster geplanter Termin: 16.10.2026.

- 17.10.2026: [Studien und Updates](research/2026-10-17.md)
