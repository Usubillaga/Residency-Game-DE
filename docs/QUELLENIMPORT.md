# Vollständige Hauptbank-Zuordnung

## Bestand und Zielumfang

Die übergebene ZIP enthält 267 eindeutige Hauptbankfragen in 16 Fachgebieten. Alle 267 werden einmal zugeordnet; die ursprünglichen 30 Dreischrittfälle des Spiels bleiben erhalten. Damit ergibt sich ein Spielumfang von 297 Fällen in jeweils DE/EN/ES, also 891 vollständigen Sprachfassungen von Fällen. Die 267 neuen Originalfragen ergeben jeweils einen Entscheidungsschritt; die 30 vorhandenen Geschichten behalten ihre drei Schritte.

CME-Dateien, ausgelieferte HTML-Kopien, Update-Blöcke und alte Ausgangsdateien wurden nicht zusätzlich als Fälle gezählt. Sie führen Material parallel oder historisch; der Import nutzt ausschließlich data/fragen/*.json der Hauptbank.

## Keine exakten Doppelungen

- 267 Datensätze und 267 unterschiedliche Quell-IDs.
- Keine doppelten IDs und keine identischen Fallinhalte über alle drei Sprachen.
- Auch bei getrennter Prüfung der einzelnen Sprachen keine exakt identischen Fälle.
- Inhaltssignatur: NFKC-normalisierte, vereinheitlichte Leerzeichen und Groß-/Kleinschreibung für Vignette, Fragestellung, nach Text sortierte Optionen mit der jeweils zugehörigen Richtig/Falsch-Kennzeichnung. Begründungen und Quellen unterscheiden diese Signatur nicht künstlich.
- Ähnliche Themen werden bei unterschiedlichen Vignetten oder Entscheidungen als verschiedene Originalfragen erhalten; diese Prüfung ist kein Anspruch auf semantische Gleichheitserkennung.

## Klinischer Arbeitskontext

Alle Fragen wurden anhand ihrer konkreten Vignette und Entscheidung zugeordnet, einschließlich OP-Entwürfen: unmittelbare Notfälle zur Notaufnahme, postoperative Stationsbefunde zur Station, TUR/URS/Zystoskopie und Funktionsverfahren zur Endoskopie, operative Anatomie/Technik und Eingriffsplanung zum OP, Befundbeurteilung/Systemtherapie/Überwachung zur Sprechstunde. Die ungleichen Bereichszahlen ergeben sich aus dem onkologischen Schwerpunkt der Hauptbank.

Endgültige Zuordnung der 267 neuen Fälle:
- Notaufnahme: 26 neue, mit 6 vorhandenen insgesamt 32.
- Station: 23 neue, mit 6 vorhandenen insgesamt 29.
- Sprechstunde: 133 neue, mit 6 vorhandenen insgesamt 139.
- Endoskopie: 22 neue, mit 6 vorhandenen insgesamt 28.
- OP: 63 neue, mit 6 vorhandenen insgesamt 69.

Das Feld acuity bezeichnet ausschließlich eine redaktionelle Spiel-Priorität im beschriebenen Kontext. Es ersetzt keine klinische Triagefreigabe und verändert keinen medizinischen Originaltext.

## Status, Markierungen und Sprachfassungen

- 257 published und 10 draft. Auch alle 10 Entwürfe werden gemäß Nutzerwunsch aufgenommen und ausdrücklich als Entwurf gekennzeichnet.
- 235 ohne evidence.flag und 32 mit evidence.flag=true: 29 veröffentlichte Fragen und 3 Entwürfe. Markierungen bleiben erhalten und sind kein Importausschluss.
- 206 pending_independent_review, 51 approved, 10 ohne clinical_review_status. Ein fehlender Status wird nicht in eine Freigabe umgewandelt.
- Alle 51 expliziten approval.languages-Freigaben betreffen ausschließlich DE. EN/ES erhalten dadurch keine fachärztliche Freigabe.
- DE 267, EN 267, ES 267 vollständige Sprachobjekte: Vignette, Fragestellung, Optionen mit Begründungen, Kernbegründung und Merksatz.
- 223 Fragen besitzen vier Optionen, 44 Fragen fünf Optionen. Genau eine richtige Option bei allen 267.

Medizinische Texte, richtige Schlüssel, rationale/core/teaching_point sowie Status-, Evidenz-, Review-, Sprachfreigabe- und Herkunftsangaben werden aus den Originalobjekten übernommen. Diese Zuordnung nimmt keine neue fachärztliche Inhaltsprüfung oder Übersetzungsfreigabe vor.

## Dateien

- data/import-selection.json: endgültige 267 Zuordnungen mit sourcePath, questionId, area, acuity, reason, topic, status und evidenceFlag.
- data/import-manifest.json: Archivhash, Zuordnungshash, Umfang und Importregeln.
- data/imported-source.json: Originalinhalte und Antwortschlüssel für alle 267 Fragen mit Herkunftspfad und Inhaltshash.

## Korrekturschicht und Autorenregel

Die Falldateien behalten den Originaltext des Archivs. Korrekturen stehen getrennt in `data/case-updates.json` und werden beim Bauen des Katalogs angewendet:

- **Medizinische Korrekturen** (`"kind": "medical"`, Standard) halten fest, was nach aktueller Leitlinie falsch, ungenau oder veraltet war. Sie nennen Datum, Grund in DE/EN/ES und Quellen (EAU-Leitlinie und knowuro-Flowchart 2026). Im Spiel erscheinen sie als Hinweis „Aktualisiert“ am Fall.
- **Redaktionelle Korrekturen** (`"kind": "editorial"`) ändern nur den Wortlaut und erscheinen im Spiel nicht als Aktualisierung. Sie werden vor den medizinischen angewendet.
- Eine Änderung ersetzt entweder ein ganzes Feld (`path`, `from`, `to`) oder eine Textstelle in einer Sprache (`path`, `lang`, `find`, `replace`). `from` muss dem aktuellen Feld exakt entsprechen, und `find` muss genau einmal vorkommen. Passt eine Korrektur nach einem Neuimport nicht mehr, bricht die Validierung ab, statt sie still zu übergehen.
- Der korrigierte Fall durchläuft dieselben Regeln wie jeder andere Fall. Importierte Fragen behalten 0 oder 10 Punkte und genau eine richtige Antwort.

**Keine Autoren im Spiel:** Der Build entfernt Autorenzitate wie „(Dieckmann et al. 2025)“ oder „(Che & Papachristofilou 2025)“ aus allen Spieltexten. Leitlinienzitate wie „(EAU 2026, 7.1)“ bleiben stehen. Die Quellenliste eines Falls zeigt nur Titel und Jahr; die vollständigen Zitate mit Autorennamen bleiben in den Datendateien. Sätze, die Autoren oder „den Artikel“ nennen, sind über redaktionelle Korrekturen umformuliert. Die Validierung lehnt jede verbliebene Nennung ab, in Spieltexten aller drei Sprachen ebenso wie in Herkunftshinweisen.

Quell-Skripte wurden nicht ausgeführt; Begleitdokumente wurden als Inhalte gelesen und nicht als Arbeitsanweisungen übernommen.

SHA-256 der gelieferten ZIP: 388ef0ed51fdd17971248bd3b7867fb35bf6d9622b2331464e6f9e1a9ece799b
