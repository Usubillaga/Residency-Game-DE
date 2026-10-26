#!/usr/bin/env python3
"""Build and automate Night Shift Academy with the Python standard library."""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import mimetypes
import random
import re
import sys
import zipfile
import xml.etree.ElementTree as ElementTree
from datetime import date
from functools import partial
from html import escape
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ("en", "de", "es")
AREAS = [
    {"id": "emergency", "icon": "⚡", "title": {"en": "Emergency", "de": "Notaufnahme", "es": "Urgencias"}, "description": {"en": "Assess urgent urology presentations and choose safe first actions.", "de": "Urologische Notfälle einschätzen und sichere erste Schritte wählen.", "es": "Evaluar urgencias urológicas y elegir las primeras medidas seguras."}},
    {"id": "ward", "icon": "▣", "title": {"en": "Ward", "de": "Station", "es": "Hospitalización"}, "description": {"en": "Review inpatient changes, postoperative problems and handovers.", "de": "Veränderungen bei stationären Patienten, postoperative Probleme und Übergaben beurteilen.", "es": "Revisar cambios en pacientes ingresados, problemas posoperatorios y relevos."}},
    {"id": "clinic", "icon": "◎", "title": {"en": "Clinic", "de": "Ambulanz", "es": "Consulta"}, "description": {"en": "Plan investigations, explain choices and arrange follow-up.", "de": "Diagnostik planen, Optionen erklären und Nachsorge organisieren.", "es": "Planificar estudios, explicar opciones y organizar el seguimiento."}},
    {"id": "endoscopy", "icon": "◉", "title": {"en": "Endoscopy", "de": "Endoskopie", "es": "Endoscopia"}, "description": {"en": "Prepare procedures, recognise complications and communicate findings.", "de": "Eingriffe vorbereiten, Komplikationen erkennen und Befunde mitteilen.", "es": "Preparar procedimientos, reconocer complicaciones y comunicar hallazgos."}},
    {"id": "theatre", "icon": "✚", "title": {"en": "Operating theatre", "de": "Operationssaal", "es": "Quirófano"}, "description": {"en": "Practise preparation, teamwork and decisions around surgery.", "de": "Vorbereitung, Teamarbeit und Entscheidungen rund um Operationen üben.", "es": "Practicar la preparación, el trabajo en equipo y las decisiones quirúrgicas."}},
    {"id": "urodynamics", "icon": "〰", "title": {"en": "Urodynamics lab", "de": "Urodynamik-Labor", "es": "Laboratorio de urodinámica"}, "description": {"en": "Read urodynamic tracings, from normal studies to overactivity, obstruction and artefacts.", "de": "Urodynamische Messkurven lesen: vom Normalbefund über Überaktivität und Obstruktion bis zu Artefakten.", "es": "Leer trazados urodinámicos: del estudio normal a la hiperactividad, la obstrucción y los artefactos."}},
]
AREA_IDS = tuple(area["id"] for area in AREAS)
CASE_FILES = tuple(f"{area}.json" for area in AREA_IDS)
DUTIES = ("night", "board", "clinic", "elective", "dayclinic", "radiotherapy", "urodynamics")
# Who answers the phone hint for a case: the attending by default, the radiation oncologist for radiotherapy questions.
CONSULTANTS = ("attending", "radiotherapist")
AGE_BANDS = {"newborn", "infant", "child", "teen", "young", "adult", "senior", "elderly", "unknown"}
IGNORED_DIRS = {".git", "__pycache__", ".pytest_cache", ".cache", "cache", ".venv", "venv", "node_modules", "work", "tmp", "temp"}


class ValidationError(ValueError):
    """A source file or exported session does not match the public format."""


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"Cannot read {path}: {exc}") from exc


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def nonempty(value, where: str) -> None:
    require(isinstance(value, str) and bool(value.strip()), f"{where}: expected a nonempty string")


def integer(value, where: str, minimum: int = 0) -> None:
    require(type(value) is int and value >= minimum, f"{where}: expected an integer >= {minimum}")


def localised(value, where: str, *, array: bool = False) -> None:
    require(isinstance(value, dict), f"{where}: expected translations for en/de/es")
    require(set(value) == set(LANGUAGES), f"{where}: translations must contain exactly en/de/es")
    lengths = []
    for language in LANGUAGES:
        text = value[language]
        if array:
            require(isinstance(text, list) and bool(text), f"{where}.{language}: expected a nonempty text list")
            for index, item in enumerate(text):
                nonempty(item, f"{where}.{language}[{index}]")
            lengths.append(len(text))
        else:
            nonempty(text, f"{where}.{language}")
    if array:
        require(len(set(lengths)) == 1, f"{where}: each language must have the same number of items")


def find_extra_translations(value, where: str) -> None:
    """Validate any optional translated field, including nested additions."""
    if isinstance(value, dict):
        if set(value) & set(LANGUAGES):
            is_array = isinstance(next(iter(value.values()), None), list)
            localised(value, where, array=is_array)
        else:
            for key, child in value.items():
                find_extra_translations(child, f"{where}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            find_extra_translations(child, f"{where}[{index}]")


def validate_source(source, where: str) -> None:
    """Check provenance shape; the importer verifies it against source content."""
    require(isinstance(source, dict), f"{where}: expected a provenance object")
    for key in ("questionId", "archivePath", "domain", "reviewStatus"):
        nonempty(source.get(key), f"{where}.{key}")
    integer(source.get("version"), f"{where}.version", 1)
    digest = source.get("contentSha256")
    require(isinstance(digest, str) and bool(re.fullmatch(r"[0-9a-fA-F]{64}", digest)), f"{where}.contentSha256: expected a SHA-256 hexadecimal digest")
    signoff = source.get("clinicalSignoffLanguages")
    require(isinstance(signoff, list) and all(isinstance(language, str) and language in LANGUAGES for language in signoff), f"{where}.clinicalSignoffLanguages: expected a language-code list")
    require(len(signoff) == len(set(signoff)), f"{where}.clinicalSignoffLanguages: duplicate language code")
    if "status" in source:
        nonempty(source["status"], f"{where}.status")
    if "evidenceFlag" in source:
        require(type(source["evidenceFlag"]) is bool, f"{where}.evidenceFlag: expected true or false")


class AssetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.assets = []
        self.stylesheets = []
        self.scripts = []
        self.tags = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        self.tags.append((tag, values))
        if tag == "link" and "stylesheet" in (values.get("rel") or "").lower().split():
            self.stylesheets.append(values.get("href"))
        if tag == "script" and "src" in values:
            self.scripts.append(values.get("src"))
        for attribute in ("src", "href", "poster"):
            value = values.get(attribute)
            if value:
                self.assets.append(value)


def local_asset(root: Path, value: str) -> Path | None:
    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    target = (root / unquote(parsed.path)).resolve()
    require(target.is_relative_to(root.resolve()), f"index.html asset escapes repository: {value}")
    require(target.is_file(), f"index.html references a missing local file: {value}")
    return target


def validate_assets(root: Path, *, required: bool = True) -> None:
    path = root / "index.html"
    if not path.is_file() and not required:
        return
    require(path.is_file(), "index.html is missing; frontend assets have not been created yet")
    parser = AssetParser()
    parser.feed(path.read_text(encoding="utf-8"))
    for value in parser.assets:
        local_asset(root, value)
    by_kind = {}
    for kind, sources in (("stylesheet", parser.stylesheets), ("script", parser.scripts)):
        paths = []
        for value in sources:
            nonempty(value, f"index.html {kind} reference")
            asset = local_asset(root, value)
            if asset:
                require(asset not in paths, f"index.html contains a duplicate {kind} reference: {value}")
                paths.append(asset)
            else:
                parsed = urlparse(value)
                require(parsed.scheme in ("https", "http", "data") or bool(parsed.netloc), f"index.html contains an invalid {kind} reference: {value}")
        by_kind[kind] = paths
    # The tracing renderer is needed only once the bank has urodynamic tracings to draw.
    scripts = ("i18n.js", "catalog.js", "engine.js") + (("urodynamics.js",) if (root / "data" / "urodynamic-tracings.json").exists() else ()) + ("app.js",)
    for kind, names in (("stylesheet", ("styles.css",)), ("script", scripts)):
        for name in names:
            require((root / "assets" / name).resolve() in by_kind[kind], f"index.html must reference assets/{name} exactly once")
    for kind, expected in (("stylesheet", ("styles.css", "cartoon.css")), ("script", ("i18n.js", "banter.js", "art.js", "catalog.js", "engine.js", "urodynamics.js", "app.js"))):
        ordered_paths = [(root / "assets" / name).resolve() for name in expected]
        observed = [asset for asset in by_kind[kind] if asset in ordered_paths]
        require(observed == [asset for asset in ordered_paths if asset in observed], f"index.html {kind} dependency order must be {' → '.join(expected)}")


def tag_attributes(markup: str) -> dict:
    parser = AssetParser()
    parser.feed(markup)
    return parser.tags[0][1]


def retained_attributes(attributes: dict, excluded: set[str]) -> str:
    return "".join(f" {name}" if value is None else f' {name}="{escape(value, quote=True)}"' for name, value in attributes.items() if name not in excluded)


UPDATE_PATH = re.compile(r"(?P<field>title|presenting|takeaway)|steps\.(?P<step>\d+)\.(?P<step_field>prompt|best)"
                         r"|steps\.(?P<ostep>\d+)\.options\.(?P<option>[a-z0-9-]+)\.(?P<option_field>text|feedback|score)")
UPDATE_KINDS = ("editorial", "medical")

# No authors in the game. Article citations such as "(Dieckmann et al. 2025)" or "(Che & Papachristofilou 2025)" are
# removed when the catalog is built; guideline citations such as "(EAU 2026, 7.1)" stay. Prose that names authors or
# "the article" has to be rewritten through an editorial update, and validation rejects whatever is left.
AUTHOR_NAME = r"[A-ZÄÖÜ][a-zäöüßéèáíóúñ'’-]+"
AUTHOR_CITATION = re.compile(rf"{AUTHOR_NAME}(?: et al\.| (?:&|and|und|y) {AUTHOR_NAME})?,? (?:19|20)\d{{2}}[a-z]?")
CITATION_GROUP = re.compile(r"([ \t]*)\(([^()]*)\)")
AUTHOR_WORDS = (rf"\bet al\b|\b{AUTHOR_NAME} (?:&|and|und|y) {AUTHOR_NAME},? (?:19|20)\d{{2}}\b|\({AUTHOR_NAME},? (?:19|20)\d{{2}}[a-z]?\)"
                r"|\b(?:Erst|Letzt|Ko-?)?[Aa]utor(?:en|in|innen)?(?:gruppe)?\b|\b(?:first |senior |co-?)?[Aa]uthors?\b|\b[Aa]utor(?:es|as?)?\b")
AUTHOR_MENTION = re.compile(AUTHOR_WORDS + r"|\bArtikels?\b|\b[Aa]rticles?\b|\b[Aa]rtículos?\b")
# Provenance notes may say that a source article differs from the guideline, but they name no authors either.
NOTE_AUTHOR_MENTION = re.compile(AUTHOR_WORDS)
NOTE_PATH = re.compile(r"source\.evidenceNotes\.(?P<note>\d+)\.text")


def strip_author_citations(text: str) -> str:
    """Drop author-year items from parenthesised citations; keep any guideline items in the same parentheses."""
    def group(match):
        items = [item.strip() for item in match[2].split(";")]
        kept = [item for item in items if not all(AUTHOR_CITATION.fullmatch(part.strip()) for part in item.split(" / "))]
        if len(kept) == len(items):
            return match[0]
        return match[1] + "(" + "; ".join(kept) + ")" if kept else ""
    return CITATION_GROUP.sub(group, text)


def case_texts(case: dict):
    """Yield (path, holder, key) for every localised text a player reads in a case."""
    for key in ("title", "presenting", "takeaway", "objectives", "topic"):
        if isinstance(case.get(key), dict):
            yield key, case, key
    patient = case.get("patient")
    if isinstance(patient, dict) and isinstance(patient.get("label"), dict):
        yield "patient.label", patient, "label"
    for step_index, step in enumerate(case.get("steps") if isinstance(case.get("steps"), list) else []):
        if not isinstance(step, dict):
            continue
        if isinstance(step.get("prompt"), dict):
            yield f"steps.{step_index}.prompt", step, "prompt"
        for option in step.get("options") if isinstance(step.get("options"), list) else []:
            for key in ("text", "feedback"):
                if isinstance(option, dict) and isinstance(option.get(key), dict):
                    yield f"steps.{step_index}.options.{option.get('id')}.{key}", option, key


def remove_authors(case: dict, where: str) -> None:
    """Strip article citations from the texts a player reads, then reject any author or article mention left over."""
    for path, holder, key in case_texts(case):
        value = holder[key]
        for language, text in value.items():
            if isinstance(text, str):
                value[language] = strip_author_citations(text)
            elif isinstance(text, list):
                value[language] = [strip_author_citations(item) if isinstance(item, str) else item for item in text]
            for item in value[language] if isinstance(value[language], list) else [value[language]]:
                hit = AUTHOR_MENTION.search(item) if isinstance(item, str) else None
                require(hit is None, f"{where}.{path}.{language}: no authors in the game; rewrite {hit[0]!r} through an editorial update" if hit else "")
    source = case.get("source")
    for index, note in enumerate(source.get("evidenceNotes", []) if isinstance(source, dict) and isinstance(source.get("evidenceNotes"), list) else []):
        if isinstance(note, dict) and isinstance(note.get("text"), str):
            note["text"] = strip_author_citations(note["text"])
            hit = NOTE_AUTHOR_MENTION.search(note["text"])
            require(hit is None, f"{where}.source.evidenceNotes[{index}]: no authors in the game; rewrite {hit[0]!r} through an editorial update" if hit else "")


def load_updates(root: Path) -> dict:
    """Reviewed corrections in data/case-updates.json, keyed by case id. The case files keep the original text.

    A case may have one editorial update (wording only, not shown as an update in the game) and one medical update."""
    path = Path(root) / "data" / "case-updates.json"
    if not path.exists():
        return {}
    data = read_json(path)
    require(isinstance(data, dict) and isinstance(data.get("updates"), list), "case-updates.json: expected {\"updates\": [...]}")
    updates = {}
    for index, update in enumerate(data["updates"]):
        where = f"case-updates.json[{index}]"
        require(isinstance(update, dict), f"{where}: expected an object")
        nonempty(update.get("case"), f"{where}.case")
        kind = update.get("kind", "medical")
        require(kind in UPDATE_KINDS, f"{where}.kind: expected editorial or medical")
        require(kind not in updates.get(update["case"], {}), f"{where}: more than one {kind} update for {update['case']!r}")
        require(bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(update.get("date", "")))), f"{where}.date: expected YYYY-MM-DD")
        localised(update.get("reason"), f"{where}.reason")
        refs = update.get("references", [] if kind == "editorial" else None)
        require(isinstance(refs, list) and (bool(refs) or kind == "editorial") and all(isinstance(ref, str) for ref in refs), f"{where}.references: expected reference ids")
        changes = update.get("changes")
        require(isinstance(changes, list) and bool(changes), f"{where}.changes: expected a nonempty list")
        updates.setdefault(update["case"], {})[kind] = (update, where)
    return updates


def apply_update(case: dict, update: dict, where: str, references: dict) -> None:
    """Replace reviewed fields of one case. Each change must still find the exact text it was written against.

    A change either replaces a whole field ({"path", "from", "to"}) or edits one passage of one language
    ({"path", "lang", "find", "replace"}); the passage must occur exactly once."""
    whole, passages = [], set()
    for index, change in enumerate(update["changes"]):
        change_where = f"{where}.changes[{index}]"
        require(isinstance(change, dict), f"{change_where}: expected an object")
        note_match = NOTE_PATH.fullmatch(str(change.get("path", "")))
        if note_match:
            # Provenance notes are single-language entries; only passage edits in the note's own language are allowed.
            notes = case.get("source", {}).get("evidenceNotes") if isinstance(case.get("source"), dict) else None
            note_index = int(note_match["note"])
            require(isinstance(notes, list) and note_index < len(notes) and isinstance(notes[note_index], dict), f"{change_where}.path: no such evidence note")
            note = notes[note_index]
            require("find" in change and set(change) == {"path", "lang", "find", "replace"} and change["lang"] == note.get("language"), f"{change_where}: evidence notes take passage edits in the note's language")
            require(isinstance(change["find"], str) and bool(change["find"]) and isinstance(change["replace"], str) and change["replace"] != change["find"], f"{change_where}: find must be nonempty text and replace changed text")
            require(isinstance(note.get("text"), str) and note["text"].count(change["find"]) == 1, f"{change_where}.find: must occur exactly once in the current text; review the update against the case")
            note["text"] = note["text"].replace(change["find"], change["replace"])
            passages.add(change["path"])
            continue
        match = UPDATE_PATH.fullmatch(str(change.get("path", "")))
        require(match is not None, f"{change_where}.path: unsupported path {change.get('path')!r}")
        container, key = case, None
        if match["field"]:
            key = match["field"]
        else:
            steps = case.get("steps") if isinstance(case.get("steps"), list) else []
            step_index = int(match["step"] or match["ostep"])
            require(step_index < len(steps) and isinstance(steps[step_index], dict), f"{change_where}.path: no such step")
            container = steps[step_index]
            key = match["step_field"]
            if match["option"]:
                options = [option for option in container.get("options", []) if isinstance(option, dict) and option.get("id") == match["option"]]
                require(len(options) == 1, f"{change_where}.path: no such option")
                container, key = options[0], match["option_field"]
        require(key in container, f"{change_where}.path: field not present in the case")
        if "find" in change:
            require(set(change) == {"path", "lang", "find", "replace"}, f"{change_where}: a passage edit needs exactly path, lang, find and replace")
            require(change["path"] not in whole, f"{change_where}.path: already replaced as a whole field")
            require(change["lang"] in LANGUAGES and isinstance(container[key], dict) and isinstance(container[key].get(change["lang"]), str), f"{change_where}.lang: expected a language of a localised text")
            require(isinstance(change["find"], str) and bool(change["find"]) and isinstance(change["replace"], str), f"{change_where}: find must be nonempty text and replace text")
            text = container[key][change["lang"]]
            require(text.count(change["find"]) == 1, f"{change_where}.find: must occur exactly once in the current text; review the update against the case")
            require(change["replace"] != change["find"], f"{change_where}.replace: expected a changed passage")
            container[key] = {**container[key], change["lang"]: text.replace(change["find"], change["replace"])}
            passages.add(change["path"])
            continue
        require("from" in change and container[key] == change["from"], f"{change_where}.from: no longer matches the case; review the update against the current text")
        require("to" in change and change["to"] != change["from"], f"{change_where}.to: expected a changed value")
        require(change["path"] not in whole and change["path"] not in passages, f"{change_where}.path: changed twice")
        container[key] = change["to"]
        whole.append(change["path"])
    refs = update.get("references", [])
    require(all(ref in references for ref in refs), f"{where}.references: unknown reference id")
    case["references"] = list(dict.fromkeys(list(case.get("references", [])) + refs))
    if update.get("kind", "medical") == "medical":
        case["update"] = {"date": update["date"], "reason": update["reason"], "references": refs, "fields": list(dict.fromkeys(whole + sorted(passages)))}


def load_and_validate(root: Path = ROOT, *, check_assets: bool = True, include_archive: bool = False):
    """Validate active and historical cases; return only playable cases by default."""
    root = Path(root)
    references = {}
    for path in sorted((root / "data").glob("refs-*.json")):
        rows = read_json(path)
        require(isinstance(rows, list), f"{path.name}: expected an array")
        for index, reference in enumerate(rows):
            where = f"{path.name}[{index}]"
            require(isinstance(reference, dict), f"{where}: expected an object")
            for key in ("id", "title", "url", "checked", "scope"):
                nonempty(reference.get(key), f"{where}.{key}")
            parsed = urlparse(reference["url"])
            require(parsed.scheme == "https" and bool(parsed.netloc), f"{where}.url: expected an HTTPS source link")
            require(bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", reference["checked"])), f"{where}.checked: expected YYYY-MM-DD")
            try:
                date.fromisoformat(reference["checked"])
            except ValueError as exc:
                raise ValidationError(f"{where}.checked: expected YYYY-MM-DD") from exc
            existing = references.get(reference["id"])
            require(existing is None or existing == reference, f"{where}: conflicting duplicate reference id {reference['id']!r}")
            references[reference["id"]] = reference
    require(bool(references), "No references found in data/refs-*.json")

    cases = []
    case_ids = set()
    updates = load_updates(root)
    sources = []
    for area, filename in zip(AREA_IDS, CASE_FILES):
        rows = read_json(root / "data" / filename)
        require(isinstance(rows, list) and bool(rows), f"{filename}: expected a nonempty array")
        sources.append((area, filename, rows, False))
    archive_path = root / "data" / "archive" / "supplemental-questions.json"
    if archive_path.exists():
        archive = read_json(archive_path)
        require(isinstance(archive, dict) and isinstance(archive.get("cases"), list), "supplemental-questions.json: expected archived cases")
        require(not archive.get("updates"), "supplemental-questions.json: archive corrected snapshots, not pending updates")
        require(all(isinstance(case, dict) and case.get("area") in AREA_IDS for case in archive["cases"]),
                "supplemental-questions.json: expected case objects with a known area")
        for area in AREA_IDS:
            sources.append((area, f"archive/supplemental-questions.json/{area}",
                            [case for case in archive["cases"] if case["area"] == area], True))
    for area, filename, rows, archived in sources:
        for index, case in enumerate(rows):
            where = f"{filename}[{index}]"
            require(isinstance(case, dict), f"{where}: expected an object")
            nonempty(case.get("id"), f"{where}.id")
            require(case["id"] not in case_ids, f"{where}: duplicate case id {case['id']!r}")
            case_ids.add(case["id"])
            # Editorial wording first, then medical corrections; the corrected case passes the same rules as every other case.
            for kind in UPDATE_KINDS:
                if kind in updates.get(case["id"], {}):
                    update, update_where = updates[case["id"]].pop(kind)
                    apply_update(case, update, update_where, references)
            updates.pop(case["id"], None)
            remove_authors(case, where)
            require(case.get("area") == area, f"{where}.area: expected {area!r}")
            require(type(case.get("level")) is int and case["level"] in (1, 2, 3), f"{where}.level: expected 1, 2 or 3")
            require(case.get("acuity") in ("routine", "urgent", "critical"), f"{where}.acuity: invalid acuity")
            if "duty" in case:
                require(case["duty"] in DUTIES, f"{where}.duty: expected one of {', '.join(DUTIES)}")
            if "consultant" in case:
                require(case["consultant"] in CONSULTANTS, f"{where}.consultant: expected one of {', '.join(CONSULTANTS)}")
            patient = case.get("patient")
            require(isinstance(patient, dict), f"{where}.patient: expected an object")
            nonempty(patient.get("name"), f"{where}.patient.name")
            require("age" in patient, f"{where}.patient.age: expected an age or explicit null")
            if patient["age"] is not None:
                integer(patient["age"], f"{where}.patient.age")
                require(patient["age"] <= 120, f"{where}.patient.age: age must be <= 120")
            require(patient.get("sex") in (None, "female", "male"), f"{where}.patient.sex: expected female, male or null")
            require(patient.get("ageBand", "unknown") in AGE_BANDS, f"{where}.patient.ageBand: unsupported age band")
            if "label" in patient:
                localised(patient["label"], f"{where}.patient.label")
            for key in ("title", "presenting", "takeaway"):
                localised(case.get(key), f"{where}.{key}")
            # Older source snapshots retain their objectives for provenance only.
            # New questions need no objectives; none are published in the game.
            if "objectives" in case:
                localised(case["objectives"], f"{where}.objectives", array=True)
            require("vitals" in case, f"{where}.vitals: expected vital signs or explicit null")
            vitals = case.get("vitals")
            if vitals is not None:
                require(isinstance(vitals, dict), f"{where}.vitals: expected an object or null")
                nonempty(vitals.get("bp"), f"{where}.vitals.bp")
                require(bool(re.fullmatch(r"\d{2,3}/\d{2,3}", vitals["bp"])), f"{where}.vitals.bp: expected systolic/diastolic")
                for key in ("hr", "temp", "spo2", "rr"):
                    require(type(vitals.get(key)) in (int, float), f"{where}.vitals.{key}: expected a number")
                    require(0 <= vitals[key] <= 300, f"{where}.vitals.{key}: outside supported display range")
                require(vitals["spo2"] <= 100, f"{where}.vitals.spo2: expected 0..100")
            if "source" in case:
                validate_source(case["source"], f"{where}.source")
            if "topic" in case:
                localised(case["topic"], f"{where}.topic")
            if case.get("subject") == "anatomy":
                context = case.get("clinicalContext")
                require(isinstance(context, dict), f"{where}.clinicalContext: anatomy requires an operation or clinical case")
                require(context.get("kind") in ("operation", "case"), f"{where}.clinicalContext.kind: expected operation or case")
                localised(context.get("label"), f"{where}.clinicalContext.label")
            steps = case.get("steps")
            require(isinstance(steps, list) and 1 <= len(steps) <= 8, f"{where}.steps: expected 1..8 steps")
            step_ids = set()
            for step_index, step in enumerate(steps):
                step_where = f"{where}.steps[{step_index}]"
                require(isinstance(step, dict), f"{step_where}: expected an object")
                nonempty(step.get("id"), f"{step_where}.id")
                require(step["id"] not in step_ids, f"{step_where}: duplicate step id")
                step_ids.add(step["id"])
                require(step.get("kind") in ("assessment", "action", "decision", "handover"), f"{step_where}.kind: invalid step kind")
                localised(step.get("prompt"), f"{step_where}.prompt")
                options = step.get("options")
                require(isinstance(options, list) and 2 <= len(options) <= 6, f"{step_where}.options: expected 2..6 options")
                option_ids = set()
                for option_index, option in enumerate(options):
                    option_where = f"{step_where}.options[{option_index}]"
                    require(isinstance(option, dict), f"{option_where}: expected an object")
                    nonempty(option.get("id"), f"{option_where}.id")
                    require(option["id"] not in option_ids, f"{option_where}: duplicate option id")
                    option_ids.add(option["id"])
                    for key in ("text", "feedback"):
                        localised(option.get(key), f"{option_where}.{key}")
                    require(type(option.get("score")) is int and option["score"] in (0, 3, 10), f"{option_where}.score: expected 0, 3 or 10")
                    integer(option.get("minutes"), f"{option_where}.minutes", 2)
                    require(option["minutes"] <= 20, f"{option_where}.minutes: expected 2..20 simulated minutes")
                    require(type(option.get("critical")) is bool, f"{option_where}.critical: expected true or false")
                    if "source" in case:
                        require(option["score"] in (0, 10), f"{option_where}.score: imported knowledge answers must score 0 or 10")
                        require(not option["critical"], f"{option_where}.critical: imported knowledge questions cannot assign clinical safety errors")
                require(step.get("best") in option_ids, f"{step_where}.best: must identify an available option")
                best = next(option for option in options if option["id"] == step["best"])
                require(best["score"] == 10 and not best["critical"], f"{step_where}.best: best option must score 10 and be noncritical")
                require(sum(option["score"] == 10 for option in options) == 1, f"{step_where}: exactly one option must score 10")
            source_ids = case.get("references")
            require(isinstance(source_ids, list) and bool(source_ids), f"{where}.references: expected a nonempty list")
            require(all(isinstance(item, str) and item in references for item in source_ids), f"{where}.references: unknown reference id")
            require(len(source_ids) == len(set(source_ids)), f"{where}.references: duplicate reference id")
            find_extra_translations(case, where)
            require("archived" not in case, f"{where}.archived: controlled by archive location")
            if archived:
                case["archived"] = True
            cases.append(case)
    require(not updates, f"case-updates.json: unknown case ids {sorted(updates)}")
    active_cases = [case for case in cases if not case.get("archived")]
    validate_question_contract(root, active_cases)
    if check_assets:
        validate_assets(root)
    return (cases if include_archive else active_cases), [references[key] for key in sorted(references)]


def validate_question_contract(root: Path, cases: list) -> None:
    """Count scored decisions, rather than cases, bonus quizzes or atlas taps.

    The contract is optional for small test fixtures and other installations.
    In the shipped bank it prevents a later import silently changing the target.
    """
    path = Path(root) / "data" / "question-contract.json"
    if not path.exists():
        return
    contract = read_json(path)
    require(isinstance(contract, dict), "question-contract.json: expected an object")
    target = contract.get("questions")
    integer(target, "question-contract.json.questions", 1)
    count = sum(len(case["steps"]) for case in cases)
    require(count == target, f"question-contract.json: expected {target} playable questions, found {count}")
    minimum = contract.get("minimumAnatomy", 0)
    integer(minimum, "question-contract.json.minimumAnatomy")
    anatomy = sum(len(case["steps"]) for case in cases if case.get("subject") == "anatomy")
    require(anatomy >= minimum, f"question-contract.json: expected at least {minimum} anatomy questions, found {anatomy}")
    if "stagingTraumaQuestions" in contract:
        expected = contract["stagingTraumaQuestions"]
        integer(expected, "question-contract.json.stagingTraumaQuestions", 1)
        found = sum(len(case["steps"]) for case in cases if case.get("classification"))
        require(found == expected, f"question-contract.json: expected {expected} TNM/trauma questions, found {found}")
    if "urodynamicsQuestions" in contract:
        expected = contract["urodynamicsQuestions"]
        integer(expected, "question-contract.json.urodynamicsQuestions", 1)
        found = sum(len(case["steps"]) for case in cases if case.get("subject") == "urodynamics")
        require(found == expected, f"question-contract.json: expected {expected} urodynamics questions, found {found}")
    # Same lead-in with a different clinical presentation is not a duplicate.
    for language in LANGUAGES:
        seen = set()
        normalise = lambda value: " ".join(value.casefold().split())
        for case in cases:
            for step in case["steps"]:
                signature = (normalise(case["presenting"][language]), normalise(step["prompt"][language]),
                             tuple(sorted(normalise(option["text"][language]) for option in step["options"])))
                require(signature not in seen, f"question-contract.json: duplicate question in {language}: {case['id']}/{step['id']}")
                seen.add(signature)


SCHEMA_ELEMENTS = {"g", "path", "rect", "circle", "ellipse", "line", "polyline", "polygon", "defs", "linearGradient", "radialGradient", "stop", "text", "tspan"}
SCHEMA_ATTRIBUTES = {"d", "x", "y", "width", "height", "rx", "ry", "cx", "cy", "r", "x1", "y1", "x2", "y2", "points", "fill", "stroke",
                     "stroke-width", "stroke-dasharray", "stroke-linecap", "stroke-linejoin", "opacity", "fill-opacity", "stroke-opacity",
                     "transform", "data-part", "data-label", "id", "offset", "stop-color", "stop-opacity", "gradientUnits", "gradientTransform", "fx", "fy",
                     "font-size", "font-family", "font-weight", "text-anchor", "dominant-baseline", "dx", "dy"}
MEDIA_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
MEDIA_MAX_BYTES = 400_000


def svg_tree(svg: str, where: str):
    """Parse the inner SVG strictly. The browser's HTML parser builds the same tree from well-formed markup
    without comments, processing instructions or angle brackets inside attribute values."""
    require("<!" not in svg and "<?" not in svg, f"{where}.svg: comments, CDATA and declarations are not allowed")
    try:
        root = ElementTree.fromstring("<svg>" + svg + "</svg>")
    except ElementTree.ParseError as error:
        raise ValidationError(f"{where}.svg: not well-formed ({error})") from None
    paint_ids = set()
    for element in root.iter():
        if "id" in element.attrib:
            id = element.get("id")
            require(element.tag in ("linearGradient", "radialGradient") and bool(re.fullmatch(r"[a-z][a-z0-9-]*", id)), f"{where}.svg: only inert gradients may have ids")
            require(id not in paint_ids, f"{where}.svg: duplicate gradient id")
            paint_ids.add(id)
    for element in root.iter():
        if element is not root:
            require(element.tag in SCHEMA_ELEMENTS, f"{where}.svg: element <{element.tag}> is not allowed")
        require((element.tag in ("text", "tspan") or not (element.text or "").strip()) and not (element.tail or "").strip(), f"{where}.svg: text belongs in a text element")
        for name, value in element.attrib.items():
            require(name in SCHEMA_ATTRIBUTES, f"{where}.svg: attribute {name} is not allowed")
            require(not re.search(r"[<>]|javascript:", value, re.I), f"{where}.svg: attribute {name} has an unsafe value")
            if re.search(r"url\(", value, re.I):
                match = re.fullmatch(r"url\(#([a-z][a-z0-9-]*)\)", value)
                require(name in ("fill", "stroke") and match is not None and match[1] in paint_ids, f"{where}.svg: unsafe value: only existing local gradients are allowed")
    return root


def validate_schema(schema, where: str) -> None:
    """Teaching schemas are inline SVG, so only inert drawing elements and attributes are accepted."""
    require(isinstance(schema, dict), f"{where}: expected an object")
    require(bool(re.fullmatch(r"[a-z0-9-]+", str(schema.get("id", "")))), f"{where}.id: expected a kebab-case id")
    for key in ("title", "caption"):
        localised(schema.get(key), f"{where}.{key}")
    require(schema.get("viewBox") == "0 0 600 420", f"{where}.viewBox: expected 0 0 600 420")
    svg = schema.get("svg")
    nonempty(svg, f"{where}.svg")
    require(len(svg) <= 40000, f"{where}.svg: too long")
    tree = svg_tree(svg, where)
    groups = [element for element in tree.iter() if "data-part" in element.attrib]
    drawn = {element.get("data-part") for element in groups}
    for group in groups:
        require(group.tag == "g", f"{where}.svg: data-part belongs on a <g> group")
        nested = [element for element in group.iter() if element is not group and "data-part" in element.attrib]
        require(not nested, f"{where}.svg: data-part groups must not be nested")
    parts = schema.get("parts")
    require(isinstance(parts, list) and 4 <= len(parts) <= 16, f"{where}.parts: expected 4..16 parts")
    for index, part in enumerate(parts):
        require(isinstance(part, dict), f"{where}.parts[{index}]: expected an object")
        require(bool(re.fullmatch(r"[a-z0-9-]+", str(part.get("id", "")))), f"{where}.parts[{index}].id: expected a kebab-case id")
        localised(part.get("label"), f"{where}.parts[{index}].label")
        localised(part.get("note"), f"{where}.parts[{index}].note")
        require(part["id"] in drawn, f"{where}.parts[{index}]: {part['id']!r} is not drawn")
    ids = [part["id"] for part in parts]
    require(len(set(ids)) == len(ids), f"{where}.parts: duplicate part ids")
    require(drawn <= set(ids), f"{where}.svg: drawn parts without a label: {sorted(drawn - set(ids))}")
    require(isinstance(schema.get("domains"), list), f"{where}.domains: expected a list")


def attach_hints(root: Path, cases: list) -> int:
    """The attending's hint per decision (data/attending-hints.json): a nudge towards the rule that decides, never the answer."""
    path = Path(root) / "data" / "attending-hints.json"
    if not path.exists():
        return 0
    data = read_json(path)
    require(isinstance(data, dict), "attending-hints.json: expected {case id: {step id: {en, de, es}}}")
    by_id = {case["id"]: case for case in cases}
    attached = 0
    for case_id, steps in data.items():
        where = f"attending-hints.json[{case_id!r}]"
        require(case_id in by_id, f"{where}: unknown case id")
        require(isinstance(steps, dict) and bool(steps), f"{where}: expected {{step id: hint}}")
        case_steps = {step["id"]: step for step in by_id[case_id]["steps"]}
        for step_id, hint in steps.items():
            step_where = f"{where}[{step_id!r}]"
            require(step_id in case_steps, f"{step_where}: unknown step id")
            localised(hint, step_where)
            step = case_steps[step_id]
            best = next(option for option in step["options"] if option["id"] == step["best"])
            for language in LANGUAGES:
                text = hint[language]
                require(len(text) <= 360, f"{step_where}.{language}: a hint is one or two sentences (at most 360 characters)")
                hit = AUTHOR_MENTION.search(text)
                require(hit is None, f"{step_where}.{language}: no authors in the game (found {hit[0]!r})" if hit else "")
                answer = best["text"][language].strip().lower()
                require(len(answer) < 12 or answer not in text.lower(), f"{step_where}.{language}: the hint must not quote the correct answer")
            step["hint"] = hint
            attached += 1
    return attached


PROTOCOL_ROUTES = ("i.v.", "p.o.", "s.c.", "i.m.", "intravesical")
# The drug table shows the dose and the days; explanations belong in support or cautions.
PROTOCOL_ROLES = ("standard", "alternative")
PROTOCOL_CELL_LIMITS = {"name": 48, "dose": 48, "schedule": 80}


def load_protocols(root: Path, cases: list) -> list:
    """Therapy protocols for the protocol page (data/protocols.json): a learning overview with cycles, doses and sources."""
    path = Path(root) / "data" / "protocols.json"
    if not path.exists():
        return []
    data = read_json(path)
    require(isinstance(data, dict) and isinstance(data.get("entities"), list) and bool(data["entities"]), "protocols.json: expected {\"entities\": [...]}")
    case_ids = {case["id"] for case in cases}
    entity_ids, regimen_ids = set(), set()
    for index, entity in enumerate(data["entities"]):
        where = f"protocols.json.entities[{index}]"
        require(isinstance(entity, dict), f"{where}: expected an object")
        nonempty(entity.get("id"), f"{where}.id")
        require(entity["id"] not in entity_ids, f"{where}: duplicate entity id")
        entity_ids.add(entity["id"])
        localised(entity.get("title"), f"{where}.title")
        regimens = entity.get("regimens")
        require(isinstance(regimens, list) and bool(regimens), f"{where}.regimens: expected a nonempty list")
        # The page shows the standards by default and the alternatives on request, so every tumour group needs a standard.
        require(any(isinstance(r, dict) and r.get("role") == "standard" for r in regimens), f"{where}: at least one regimen must be the standard")
        for r_index, regimen in enumerate(regimens):
            r_where = f"{where}.regimens[{r_index}]"
            require(isinstance(regimen, dict), f"{r_where}: expected an object")
            require(isinstance(regimen.get("id"), str) and bool(re.fullmatch(r"[a-z0-9][a-z0-9-]*", regimen["id"])), f"{r_where}.id: expected a kebab-case id")
            require(regimen["id"] not in regimen_ids, f"{r_where}: duplicate regimen id {regimen['id']!r}")
            regimen_ids.add(regimen["id"])
            require(regimen.get("role") in PROTOCOL_ROLES, f"{r_where}.role: expected one of {', '.join(PROTOCOL_ROLES)}")
            for key in ("name", "setting", "cycles", "support", "cautions", "evidence"):
                localised(regimen.get(key), f"{r_where}.{key}")
            cycle = regimen.get("cycleDays")
            require(cycle is None or (type(cycle) is int and 1 <= cycle <= 365), f"{r_where}.cycleDays: expected days or null")
            drugs = regimen.get("drugs")
            require(isinstance(drugs, list) and bool(drugs), f"{r_where}.drugs: expected a nonempty list")
            for d_index, drug in enumerate(drugs):
                d_where = f"{r_where}.drugs[{d_index}]"
                require(isinstance(drug, dict), f"{d_where}: expected an object")
                for key in ("name", "dose", "schedule"):
                    localised(drug.get(key), f"{d_where}.{key}")
                require(drug.get("route") in PROTOCOL_ROUTES, f"{d_where}.route: expected one of {', '.join(PROTOCOL_ROUTES)}")
                require(all(re.search(r"\d", drug["dose"][language]) for language in LANGUAGES), f"{d_where}.dose: expected a number with a unit")
                for key, limit in PROTOCOL_CELL_LIMITS.items():
                    for language in LANGUAGES:
                        require(len(drug[key][language]) <= limit, f"{d_where}.{key}.{language}: at most {limit} characters in the table; move details to support or cautions")
            texts = [entity["title"], *(regimen[key] for key in ("name", "setting", "cycles", "support", "cautions", "evidence")),
                     *(drug[key] for drug in drugs for key in ("name", "dose", "schedule"))]
            check_regimen_links(regimen, r_where, case_ids, texts)
    return data["entities"]


def check_regimen_links(regimen: dict, where: str, case_ids: set, texts: list) -> None:
    """Shared by therapy protocols and radiotherapy schemes: sources, linked questions and no authors."""
    sources = regimen.get("sources")
    require(isinstance(sources, list) and bool(sources), f"{where}.sources: expected at least one source")
    for s_index, source in enumerate(sources):
        s_where = f"{where}.sources[{s_index}]"
        require(isinstance(source, dict), f"{s_where}: expected an object")
        nonempty(source.get("label"), f"{s_where}.label")
        parsed = urlparse(str(source.get("url", "")))
        require(parsed.scheme == "https" and bool(parsed.netloc), f"{s_where}.url: expected an HTTPS link")
        hit = NOTE_AUTHOR_MENTION.search(source["label"])
        require(hit is None, f"{where}.sources: no authors in the game (found {hit[0]!r})" if hit else "")
    questions = regimen.get("questions", [])
    require(isinstance(questions, list) and all(isinstance(q, str) and q in case_ids for q in questions), f"{where}.questions: unknown case id")
    require(len(set(questions)) == len(questions), f"{where}.questions: duplicate case id")
    for text in [item[language] for item in texts for language in LANGUAGES]:
        hit = AUTHOR_MENTION.search(text)
        require(hit is None, f"{where}: no authors in the game (found {hit[0]!r})" if hit else "")


# A radiotherapy phase: target volume, total dose, dose per fraction and number of fractions. Continuous low-dose-rate
# brachytherapy (permanent seeds or a temporary LDR/PDR implant) has a total dose only. Otherwise the total must equal dose per fraction times fractions.
RT_CELL_LIMITS = {"target": 60, "schedule": 80}


def load_radiotherapy(root: Path, cases: list) -> list:
    """Radiotherapy schemes for the protocol page (data/radiotherapy.json): total dose, fractionation, target and sources."""
    path = Path(root) / "data" / "radiotherapy.json"
    if not path.exists():
        return []
    data = read_json(path)
    require(isinstance(data, dict) and isinstance(data.get("entities"), list) and bool(data["entities"]), "radiotherapy.json: expected {\"entities\": [...]}")
    case_ids = {case["id"] for case in cases}
    entity_ids, scheme_ids = set(), set()
    number = lambda value: type(value) in (int, float) and value == value
    for index, entity in enumerate(data["entities"]):
        where = f"radiotherapy.json.entities[{index}]"
        require(isinstance(entity, dict), f"{where}: expected an object")
        nonempty(entity.get("id"), f"{where}.id")
        require(entity["id"] not in entity_ids, f"{where}: duplicate entity id")
        entity_ids.add(entity["id"])
        localised(entity.get("title"), f"{where}.title")
        schemes = entity.get("regimens")
        require(isinstance(schemes, list) and bool(schemes), f"{where}.regimens: expected a nonempty list")
        for r_index, scheme in enumerate(schemes):
            r_where = f"{where}.regimens[{r_index}]"
            require(isinstance(scheme, dict), f"{r_where}: expected an object")
            require(isinstance(scheme.get("id"), str) and bool(re.fullmatch(r"[a-z0-9][a-z0-9-]*", scheme["id"])), f"{r_where}.id: expected a kebab-case id")
            require(scheme["id"] not in scheme_ids, f"{r_where}: duplicate scheme id {scheme['id']!r}")
            scheme_ids.add(scheme["id"])
            for key in ("name", "setting", "technique", "combined", "support", "cautions", "evidence"):
                localised(scheme.get(key), f"{r_where}.{key}")
            phases = scheme.get("phases")
            require(isinstance(phases, list) and bool(phases), f"{r_where}.phases: expected a nonempty list")
            for p_index, phase in enumerate(phases):
                p_where = f"{r_where}.phases[{p_index}]"
                require(isinstance(phase, dict), f"{p_where}: expected an object")
                for key, limit in RT_CELL_LIMITS.items():
                    localised(phase.get(key), f"{p_where}.{key}")
                    for language in LANGUAGES:
                        require(len(phase[key][language]) <= limit, f"{p_where}.{key}.{language}: at most {limit} characters in the table; move details to support or cautions")
                total, per, count = phase.get("totalGy"), phase.get("fractionGy"), phase.get("fractions")
                require(number(total) and 0 < total <= 200, f"{p_where}.totalGy: expected the total dose in Gy")
                require((per is None) == (count is None), f"{p_where}: give both fractionGy and fractions, or neither for continuous low-dose-rate brachytherapy")
                if per is not None:
                    require(number(per) and 0 < per <= 30, f"{p_where}.fractionGy: expected the dose per fraction in Gy")
                    require(type(count) is int and 1 <= count <= 60, f"{p_where}.fractions: expected 1 to 60 fractions")
                    require(abs(per * count - total) <= 0.05, f"{p_where}: {per} Gy x {count} fractions is {per * count:g} Gy, not {total} Gy")
            texts = [entity["title"], *(scheme[key] for key in ("name", "setting", "technique", "combined", "support", "cautions", "evidence")),
                     *(phase[key] for phase in phases for key in RT_CELL_LIMITS)]
            check_regimen_links(scheme, r_where, case_ids, texts)
    return data["entities"]


def load_regimens(root: Path, cases: list) -> tuple[list, list]:
    """Both halves of the protocol page; a regimen id names one table on the page, so it is unique across both files."""
    protocols, radiotherapy = load_protocols(root, cases), load_radiotherapy(root, cases)
    ids = [regimen["id"] for entities in (protocols, radiotherapy) for entity in entities for regimen in entity["regimens"]]
    shared = sorted({item for item in ids if ids.count(item) > 1})
    require(not shared, f"radiotherapy.json: regimen id {', '.join(shared)} is also used in protocols.json")
    return protocols, radiotherapy


def load_visuals(root: Path, cases: list) -> tuple[list, dict, dict]:
    """Schemas, case-to-schema highlights and licensed case images; all three files are optional."""
    root = Path(root)
    by_id = {case["id"]: case for case in cases}
    schemas = read_json(root / "data" / "schemas.json") if (root / "data" / "schemas.json").exists() else []
    require(isinstance(schemas, list), "schemas.json: expected an array")
    for index, schema in enumerate(schemas):
        validate_schema(schema, f"schemas.json[{index}]")
    schema_ids = [schema["id"] for schema in schemas]
    require(len(set(schema_ids)) == len(schema_ids), "schemas.json: duplicate schema ids")
    parts = {schema["id"]: {part["id"] for part in schema["parts"]} for schema in schemas}
    links = read_json(root / "data" / "case-schemas.json") if (root / "data" / "case-schemas.json").exists() else {}
    require(isinstance(links, dict), "case-schemas.json: expected an object keyed by case id")
    for case_id, link in links.items():
        where = f"case-schemas.json[{case_id!r}]"
        require(case_id in by_id, f"{where}: unknown case")
        require(isinstance(link, dict) and isinstance(link.get("schema"), str) and link["schema"] in parts, f"{where}.schema: unknown schema")
        highlight = link.get("parts", [])
        require(isinstance(highlight, list) and len(highlight) <= 4 and all(isinstance(part, str) for part in highlight),
                f"{where}.parts: expected up to 4 part ids")
        require(set(highlight) <= parts[link["schema"]], f"{where}.parts: unknown part of {link['schema']}")
    media_rows = read_json(root / "data" / "case-media.json") if (root / "data" / "case-media.json").exists() else []
    require(isinstance(media_rows, list), "case-media.json: expected an array")
    media: dict[str, list] = {}
    for index, row in enumerate(media_rows):
        where = f"case-media.json[{index}]"
        require(isinstance(row, dict) and row.get("case") in by_id, f"{where}.case: unknown case")
        file = str(row.get("file", ""))
        path = (root / file).resolve()
        require(file.startswith("media/") and root.resolve() / "media" in path.parents and path.is_file(), f"{where}.file: expected an existing file in media/")
        require(path.suffix.lower() in MEDIA_TYPES, f"{where}.file: only PNG, JPEG or WebP images are embedded")
        require(path.stat().st_size <= MEDIA_MAX_BYTES, f"{where}.file: larger than {MEDIA_MAX_BYTES // 1000} kB")
        localised(row.get("alt"), f"{where}.alt")
        localised(row.get("caption"), f"{where}.caption")
        nonempty(row.get("credit"), f"{where}.credit")
        nonempty(row.get("license"), f"{where}.license")
        media.setdefault(row["case"], []).append({
            "src": f"data:{MEDIA_TYPES[path.suffix.lower()]};base64," + base64.b64encode(path.read_bytes()).decode("ascii"),
            "alt": row["alt"], "caption": row["caption"], "credit": row["credit"], "license": row["license"],
        })
    return schemas, links, media


TRACING_CHANNELS = {"pves", "pabd", "pdet", "flow", "vol", "vvoid", "emg"}
TRACING_EVENTS = {"cough", "valsalva", "fs", "fd", "sd", "urgency", "leak", "void", "qmax", "reduction", "provocation", "drain",
                  "recatheterise", "bloodPressure", "stop"}
TRACING_KINDS = {"pressure-flow", "video-pressure-flow", "cystometry", "video-cystometry", "uroflow", "uroflow-emg"}
TRACING_LIMITS = {"pves": (-5, 250), "pabd": (-5, 250), "flow": (0, 60), "vinf": (0, 1500), "vvoid": (0, 1500), "emg": (0, 150)}


def load_tracings(root: Path, cases: list) -> dict:
    """Synthetic urodynamic tracings (data/urodynamic-tracings.json), keyed by case id.

    The curves come from scripts/urodynamic_traces.py. Each reading that a question relies on is
    recomputed from the curves, so the drawing and the text cannot drift apart unnoticed.
    """
    path = Path(root) / "data" / "urodynamic-tracings.json"
    if not path.exists():
        return {}
    data = read_json(path)
    require(isinstance(data, dict) and data.get("version") == 1 and isinstance(data.get("tracings"), dict), "urodynamic-tracings.json: expected version 1 with tracings")
    nonempty(data.get("note"), "urodynamic-tracings.json.note")
    by_id = {case["id"]: case for case in cases}
    for case_id, tracing in data["tracings"].items():
        where = f"urodynamic-tracings.json[{case_id!r}]"
        require(case_id in by_id, f"{where}: unknown case")
        case = by_id[case_id]
        require(isinstance(tracing, dict) and tracing.get("kind") in TRACING_KINDS, f"{where}.kind: expected one of {', '.join(sorted(TRACING_KINDS))}")
        t = tracing.get("t")
        require(isinstance(t, list) and len(t) >= 10 and all(type(x) in (int, float) for x in t), f"{where}.t: expected sample times")
        require(all(b > a for a, b in zip(t, t[1:])), f"{where}.t: sample times must increase")
        stored = [name for name in TRACING_LIMITS if name in tracing]
        for name in stored:
            values = tracing[name]
            low, high = TRACING_LIMITS[name]
            require(isinstance(values, list) and len(values) == len(t), f"{where}.{name}: expected one value per sample")
            require(all(type(v) in (int, float) and low <= v <= high for v in values), f"{where}.{name}: values outside {low}..{high}")
        channels = tracing.get("channels")
        require(isinstance(channels, list) and channels and set(channels) <= TRACING_CHANNELS and len(set(channels)) == len(channels), f"{where}.channels: unknown or duplicate channel")
        needs = {"pves": {"pves"}, "pabd": {"pabd"}, "pdet": {"pves", "pabd"}, "flow": {"flow"}, "vol": {"vinf", "vvoid"}, "vvoid": {"vvoid"}, "emg": {"emg"}}
        for channel in channels:
            require(needs[channel] <= set(stored), f"{where}.channels: {channel} needs {', '.join(sorted(needs[channel]))}")
        start, end = t[0], t[-1]
        events = tracing.get("events", [])
        require(isinstance(events, list), f"{where}.events: expected a list")
        for index, event in enumerate(events):
            require(isinstance(event, dict) and event.get("type") in TRACING_EVENTS, f"{where}.events[{index}].type: unknown marker")
            require(type(event.get("t")) in (int, float) and start <= event["t"] <= end, f"{where}.events[{index}].t: outside the tracing")
            require(set(event) <= {"t", "type", "value"}, f"{where}.events[{index}]: unexpected field")
        views = tracing.get("views")
        require(isinstance(views, list) and views, f"{where}.views: expected at least one view")
        view_ids = set()
        for index, view in enumerate(views):
            view_where = f"{where}.views[{index}]"
            nonempty(view.get("id"), f"{view_where}.id")
            require(view["id"] not in view_ids, f"{view_where}: duplicate view id")
            view_ids.add(view["id"])
            localised(view.get("label"), f"{view_where}.label")
            if "t" in view:
                window = view["t"]
                require(isinstance(window, list) and len(window) == 2 and start <= window[0] < window[1] <= end + 1e-6, f"{view_where}.t: expected a window inside the tracing")
        step_ids = [step["id"] for step in case["steps"]]
        steps = tracing.get("steps")
        require(isinstance(steps, dict) and steps, f"{where}.steps: expected step id → view id")
        for step_id, view_id in steps.items():
            require(step_id in step_ids, f"{where}.steps: unknown step {step_id!r}")
            require(view_id in view_ids, f"{where}.steps[{step_id!r}]: unknown view {view_id!r}")
        for index, note in enumerate(tracing.get("annotations", [])):
            note_where = f"{where}.annotations[{index}]"
            require(note.get("step") in steps, f"{note_where}.step: findings belong to a step that shows the tracing")
            require(note.get("kind") in ("span", "point") and note.get("tone", "key") in ("key", "good", "neutral"), f"{note_where}: expected a span or point with a known tone")
            localised(note.get("label"), f"{note_where}.label")
            if "channel" in note or note["kind"] == "point":
                require(note.get("channel") in channels, f"{note_where}.channel: not drawn in this tracing")
            times = (note["t0"], note["t1"]) if note["kind"] == "span" else (note["t"],)
            require(all(type(x) in (int, float) and start <= x <= end for x in times), f"{note_where}: outside the tracing")
            for language in LANGUAGES:
                hit = AUTHOR_MENTION.search(note["label"][language])
                require(hit is None, f"{note_where}.label.{language}: no authors in the game (found {hit[0]!r})" if hit else "")
        check_tracing_readings(tracing, where)
    return data["tracings"]


READING_RULES = (
    "capacity", "qmax", "pdetQmax", "pvesQmax", "pabdQmax", "voided", "leaked", "residual", "firstSensation", "firstDesire",
    "strongDesire", "leakPointPves", "qmax1", "qmax2", "voided1", "voided2", "flowTime", "pdetStart", "pdetEnd", "compliance",
    "leakPdet", "leakVolume", "volumeAtPdet40", "secondFillRate", "maxPdet", "overactivityFrom", "overactivityMax",
    "contractionOnsets", "contractionPeaks", "waveSeconds", "overactivityLeak", "coughLeakFrom", "baselinePves", "baselinePabd",
    "coughPves", "coughPabd", "rectalWaves", "rectalFrom", "rectalRise", "pvesVoidMax", "pdetVoidBelow", "pvesBeforeLossAbove",
)
GRID = 0.25  # seconds; the stored samples reproduce the model on this grid within the generator's tolerance


def _resample(t: list, values: list) -> list:
    """Linear interpolation of a stored channel on a regular grid from the first sample."""
    out, j = [], 0
    for k in range(int(round((t[-1] - t[0]) / GRID)) + 1):
        x = t[0] + k * GRID
        while j + 2 < len(t) and t[j + 1] <= x:
            j += 1
        span = t[j + 1] - t[j]
        f = min(1.0, max(0.0, (x - t[j]) / span))
        out.append(values[j] + (values[j + 1] - values[j]) * f)
    return out


def _running_median(values: list, half: int = 6) -> list:
    """Median over ±1.5 s: removes cough spikes but keeps detrusor and rectal waves."""
    out = []
    for k in range(len(values)):
        window = sorted(values[max(0, k - half):k + half + 1])
        out.append(window[len(window) // 2])
    return out


def _waves(raw: list, smooth: list, rise: float, start: int, stop: int) -> list:
    """Waves between grid indices start and stop: the smoothed signal more than `rise` above the lowest level of
    the preceding 40 s for at least 4 s. Onset is where it left that level (within 1 cmH2O); the wave lasts while
    it stays more than 2 cmH2O above it; top is the highest raw sample."""
    back, waves, k = int(40 / GRID), [], start
    while k < stop:
        level = min(smooth[max(start, k - back):k + 1])
        if smooth[k] - level <= rise:
            k += 1
            continue
        j = k
        while j < stop and smooth[j] - level > rise:
            j += 1
        if (j - k) * GRID < 4:
            k = j
            continue
        onset = k
        while onset > start and smooth[onset - 1] - level > 1.0:
            onset -= 1
        end = j
        while end < stop and smooth[end] - level > 2.0:
            end += 1
        above = [m for m in range(onset, end) if smooth[m] - level > 2.0]
        top = max(range(onset, end), key=lambda m: raw[m])
        waves.append({"onset": onset, "top": top, "end": end, "level": level, "seconds": (above[-1] - above[0]) * GRID})
        k = end + 1
    return waves


def check_tracing_readings(tracing: dict, where: str) -> None:
    """The values a question asks the player to read must be what the curves show.

    Every reading is recomputed from the stored curves by its rule below, and a reading without a rule fails,
    so a value quoted in a case cannot drift away from the drawing unnoticed."""
    readings = tracing.get("readings")
    require(isinstance(readings, dict) and readings, f"{where}.readings: expected the values the questions rely on")
    unknown = sorted(set(readings) - set(READING_RULES))
    require(not unknown, f"{where}.readings: no rule recomputes {', '.join(unknown)}")
    events = tracing.get("events", [])
    t = tracing["t"]
    has = lambda *names: all(name in tracing for name in names)  # noqa: E731

    def at(time: float) -> int:
        return min(range(len(t)), key=lambda k: abs(t[k] - time))

    def times(*kinds: str) -> list:
        return [e["t"] for e in events if e["type"] in kinds]

    def close(key: str, value: float, tolerance: float, unit: str = "") -> None:
        require(abs(value - readings[key]) <= tolerance, f"{where}.readings.{key}: the curves show {value:.1f}{unit}")

    pdet = [v - a for v, a in zip(tracing["pves"], tracing["pabd"])] if has("pves", "pabd") else []
    marks = [at(x) for x in times("qmax")]
    voids, leaks, coughs = times("void"), times("leak"), times("cough")
    restarts = times("drain", "recatheterise")

    # Uroflow and pressure-flow values.
    if "qmax" in readings:
        require(abs(max(tracing["flow"]) - readings["qmax"]) < 0.05, f"{where}.readings.qmax: the flow curve peaks at {max(tracing['flow'])}")
        if marks:
            require(any(abs(tracing["flow"][k] - readings["qmax"]) < 0.05 for k in marks), f"{where}: the Qmax marker is not at the maximum flow")
    for key, values, tolerance in (("pdetQmax", pdet, 0.5), ("pvesQmax", tracing.get("pves"), 1.0), ("pabdQmax", tracing.get("pabd"), 1.0)):
        if key in readings:
            require(marks and values, f"{where}.readings.{key}: needs a Qmax marker and pressures")
            if key == "pdetQmax":
                require(abs(values[marks[-1]] - readings[key]) < tolerance, f"{where}.readings.pdetQmax: Pdet at the Qmax marker is {values[marks[-1]]:.1f}")
            else:
                close(key, values[marks[-1]], tolerance, " cmH2O at the Qmax marker")
    if "capacity" in readings and "vinf" in tracing:
        require(abs(max(tracing["vinf"]) - readings["capacity"]) <= 1, f"{where}.readings.capacity: the infusion reaches {max(tracing['vinf'])} ml")
    if "voided" in readings:
        after = [k for k in range(len(t)) if not voids or t[k] >= voids[-1]]
        voided = max(tracing["vvoid"][k] for k in after)
        require(abs(voided - readings["voided"]) <= 1, f"{where}.readings.voided: the last void collects {voided} ml")
    # Leakage during filling reaches the flowmeter too; the voided volume starts again at permission to void.
    leaked = readings.get("leaked", 0)
    if "leaked" in readings:
        require(voids, f"{where}.readings.leaked: needs a void after the leakage")
        before = [tracing["vvoid"][k] for k in range(len(t)) if t[k] < voids[-1]]
        require(abs(max(before) - leaked) <= 1, f"{where}.readings.leaked: the flowmeter collects {max(before)} ml before voiding")
    if {"capacity", "voided", "residual"} <= set(readings):
        require(readings["capacity"] - leaked - readings["voided"] == readings["residual"],
                f"{where}.readings.residual: capacity minus leakage minus voided volume")
    # Voids: runs of flow that collect at least 20 ml (leakage collects less), in order.
    runs, k = [], 0
    flow = tracing.get("flow", [])
    while k < len(flow):
        if flow[k] > 0:
            j = k
            while j + 1 < len(flow) and flow[j + 1] > 0:
                j += 1
            before = tracing["vvoid"][k - 1] if k else 0
            volume = max(tracing["vvoid"][k:j + 2]) - before
            if volume >= 20:
                runs.append({"qmax": max(flow[k:j + 1]), "volume": volume, "seconds": t[j] - t[k]})
            k = j + 1
        else:
            k += 1
    for number in (1, 2):
        for key, field, tolerance in ((f"qmax{number}", "qmax", 0.05), (f"voided{number}", "volume", 1)):
            if key in readings:
                require(len(runs) >= number, f"{where}.readings.{key}: the tracing has {len(runs)} voids")
                close(key, runs[number - 1][field], tolerance)
    if "flowTime" in readings:
        require(runs, f"{where}.readings.flowTime: no void")
        close("flowTime", runs[-1]["seconds"], 1.0, " s")
    for key, kind in (("firstSensation", "fs"), ("firstDesire", "fd"), ("strongDesire", "sd")):
        if key in readings:
            found = [tracing["vinf"][at(x)] for x in times(kind)]
            require(any(abs(v - readings[key]) <= 1 for v in found), f"{where}.readings.{key}: no {kind} marker at {readings[key]} ml")
    if "leakPointPves" in readings:
        found = [tracing["pves"][at(x)] for x in leaks]
        require(any(abs(v - readings["leakPointPves"]) < 0.5 for v in found), f"{where}.readings.leakPointPves: no leakage marker at that Pves")
    if not pdet:
        return

    # Storage: pressures and volumes on a regular grid; waves are found on the smoothed curves.
    t0 = t[0]
    grid_pves, grid_pabd = _resample(t, tracing["pves"]), _resample(t, tracing["pabd"])
    grid_pdet = [v - a for v, a in zip(grid_pves, grid_pabd)]
    grid_vinf = _resample(t, tracing["vinf"])
    smooth_pdet, smooth_pabd = _running_median(grid_pdet), _running_median(grid_pabd)
    g = lambda time: max(0, min(len(grid_pdet) - 1, int(round((time - t0) / GRID))))  # noqa: E731
    first_end = min(voids + restarts) if voids + restarts else t[-1]
    start_pdet = sorted(grid_pdet[:g(t0 + 30) + 1])[len(grid_pdet[:g(t0 + 30) + 1]) // 2]
    if "pdetStart" in readings:
        close("pdetStart", start_pdet, 0.5, " cmH2O")
    if "pdetEnd" in readings:
        require(voids, f"{where}.readings.pdetEnd: needs a void marker")
        close("pdetEnd", pdet[at(voids[0])], 0.5, " cmH2O")
    if "compliance" in readings:
        end_point = leaks[0] if leaks and leaks[0] < first_end else first_end
        delta_v = tracing["vinf"][at(end_point)] - grid_vinf[0]
        computed = delta_v / (pdet[at(end_point)] - start_pdet)
        require(abs(computed - readings["compliance"]) <= 0.04 * computed, f"{where}.readings.compliance: ΔV/ΔPdet is {computed:.2f} ml/cmH2O")
    if "leakPdet" in readings:
        found = [pdet[at(x)] for x in leaks]
        require(any(abs(v - readings["leakPdet"]) <= 1 for v in found), f"{where}.readings.leakPdet: no leakage marker at Pdet {readings['leakPdet']}")
    if "leakVolume" in readings:
        require(leaks, f"{where}.readings.leakVolume: no leakage marker")
        close("leakVolume", tracing["vinf"][at(leaks[0])], 2, " ml")
    if "maxPdet" in readings:
        close("maxPdet", max(pdet), 1, " cmH2O")
    if {"volumeAtPdet40", "secondFillRate"} & set(readings):
        require(restarts, f"{where}.readings: a second filling needs a drain or recatheterisation marker")
        begin = g(restarts[-1])
        if "volumeAtPdet40" in readings:
            reached = next((k for k in range(begin, len(smooth_pdet)) if smooth_pdet[k] >= 39.5), None)
            require(reached is not None, f"{where}.readings.volumeAtPdet40: Pdet never reaches 40 cmH2O")
            close("volumeAtPdet40", grid_vinf[reached], 5, " ml")
        if "secondFillRate" in readings:
            after = [k for k in range(len(t)) if t[k] >= restarts[-1]]
            empty = max(k for k in after if tracing["vinf"][k] == 0)
            full = min(k for k in after if tracing["vinf"][k] == max(tracing["vinf"][m] for m in after))
            close("secondFillRate", tracing["vinf"][full] / (t[full] - t[empty]) * 60, 0.5, " ml/min")

    # Detrusor overactivity during the first filling.
    waves = _waves(grid_pdet, smooth_pdet, 6.0, 0, g(first_end))
    if "overactivityFrom" in readings:
        require(waves, f"{where}.readings.overactivityFrom: no detrusor wave")
        close("overactivityFrom", grid_vinf[waves[0]["onset"]], 8, " ml")
    if "overactivityMax" in readings:
        require(waves, f"{where}.readings.overactivityMax: no detrusor wave")
        close("overactivityMax", max(grid_pdet[w["top"]] for w in waves), 1.5, " cmH2O")
    for key, values, tolerance in (("contractionOnsets", [grid_vinf[w["onset"]] for w in waves], 8),
                                   ("contractionPeaks", [grid_pdet[w["top"]] for w in waves], 1.5)):
        if key in readings:
            stated = readings[key]
            require(isinstance(stated, list) and len(stated) == len(values), f"{where}.readings.{key}: the curves show {len(values)} detrusor waves")
            for index, (value, expected) in enumerate(zip(values, stated)):
                require(abs(value - expected) <= tolerance, f"{where}.readings.{key}[{index}]: the curves show {value:.1f}")
    if "waveSeconds" in readings:
        require(waves, f"{where}.readings.waveSeconds: no detrusor wave")
        close("waveSeconds", waves[0]["seconds"], 4, " s")
    if "overactivityLeak" in readings:
        inside = [x for x in leaks if any(t0 + w["onset"] * GRID <= x <= t0 + w["end"] * GRID for w in waves)]
        require(inside, f"{where}.readings.overactivityLeak: no leakage marker during a detrusor wave")
        close("overactivityLeak", tracing["vinf"][at(inside[0])], 6, " ml")
    if "coughLeakFrom" in readings:
        with_cough = [x for x in leaks if any(0 <= x - c <= 2 for c in coughs)]
        require(with_cough, f"{where}.readings.coughLeakFrom: no leakage marker with a cough")
        close("coughLeakFrom", tracing["vinf"][at(with_cough[0])], 2, " ml")

    # Quality control: resting values, cough transmission and rectal contractions.
    for key, values in (("baselinePves", grid_pves), ("baselinePabd", grid_pabd)):
        if key in readings:
            close(key, sorted(values[:g(t0 + 5) + 1])[len(values[:g(t0 + 5) + 1]) // 2], 1, " cmH2O")
    for key, name in (("coughPves", "pves"), ("coughPabd", "pabd")):
        if key in readings:
            require(coughs, f"{where}.readings.{key}: no cough marker")
            last = coughs[-1]
            peak = max(tracing[name][k] for k in range(len(t)) if last - 0.5 <= t[k] <= last + 3)
            close(key, peak - tracing[name][at(last - 0.75)], 1, " cmH2O rise with the last cough")
    if {"rectalWaves", "rectalFrom", "rectalRise"} & set(readings):
        # Pabd alone rises (Pdet falls by about as much); straining and coughs raise both lines.
        rectal = [w for w in _waves(grid_pabd, smooth_pabd, 5.0, 0, len(grid_pabd))
                  if smooth_pdet[w["top"]] - smooth_pdet[w["onset"]] < -0.7 * (smooth_pabd[w["top"]] - w["level"])]
        if "rectalWaves" in readings:
            require(len(rectal) == readings["rectalWaves"], f"{where}.readings.rectalWaves: the curves show {len(rectal)} rectal contractions")
        if "rectalFrom" in readings:
            require(rectal, f"{where}.readings.rectalFrom: no rectal contraction")
            close("rectalFrom", grid_vinf[rectal[0]["onset"]], 8, " ml")
        if "rectalRise" in readings:
            for w in rectal:
                close("rectalRise", smooth_pabd[w["top"]] - w["level"], 1.5, " cmH2O")

    # Voiding without the detrusor, and an expelled catheter.
    if {"pvesVoidMax", "pdetVoidBelow"} & set(readings):
        require(voids and flow, f"{where}.readings: needs a void with flow")
        last_flow = max(k for k in range(len(t)) if flow[k] > 0)
        phase = [k for k in range(len(t)) if voids[-1] <= t[k] <= t[last_flow]]
        if "pvesVoidMax" in readings:
            close("pvesVoidMax", max(tracing["pves"][k] for k in phase), 1, " cmH2O")
        if "pdetVoidBelow" in readings:
            highest = max(pdet[k] for k in phase)
            require(highest < readings["pdetVoidBelow"], f"{where}.readings.pdetVoidBelow: Pdet reaches {highest:.1f} cmH2O while voiding")
    if "pvesBeforeLossAbove" in readings:
        lost = next((k for k in range(len(t)) if tracing["pves"][k] < 0), None)
        require(lost is not None, f"{where}.readings.pvesBeforeLossAbove: Pves never falls below zero")
        highest = max(tracing["pves"][k] for k in range(len(t)) if t[lost] - 6 <= t[k] < t[lost])
        require(highest > readings["pvesBeforeLossAbove"], f"{where}.readings.pvesBeforeLossAbove: Pves reaches only {highest:.1f} before it falls")


def load_classifications(root: Path, cases: list, references: list, schemas: list) -> list:
    """Edition-labelled tables are sourced content, validated like the question bank."""
    path = Path(root) / "data/classifications.json"
    if not path.exists():
        return []
    data = read_json(path)
    require(isinstance(data, dict) and data.get("version") == 1, "classifications.json: expected version 1")
    guides = data.get("guides")
    require(isinstance(guides, list) and bool(guides), "classifications.json: expected nonempty guides")
    ids, linked = set(), set()
    by_case = {case["id"]: case for case in cases}
    ref_ids = {ref["id"] for ref in references}
    schema_ids = {schema["id"] for schema in schemas}
    for index, guide in enumerate(guides):
        where = f"classifications.json.guides[{index}]"
        require(isinstance(guide, dict), f"{where}: expected object")
        nonempty(guide.get("id"), f"{where}.id")
        require(guide["id"] not in ids, f"{where}: duplicate guide id")
        ids.add(guide["id"])
        require(guide.get("kind") in ("tumour", "trauma"), f"{where}.kind: invalid classification kind")
        localised(guide.get("title"), f"{where}.title")
        localised(guide.get("cautions"), f"{where}.cautions")
        nonempty(guide.get("edition"), f"{where}.edition")
        require(guide.get("schema") in schema_ids, f"{where}.schema: unknown schema")
        require(isinstance(guide.get("references"), list) and bool(guide["references"]) and
                all(ref in ref_ids for ref in guide["references"]), f"{where}.references: unknown or missing source")
        signoff = guide.get("clinicalSignoffLanguages")
        require(isinstance(signoff, list) and all(language in LANGUAGES for language in signoff) and len(signoff) == len(set(signoff)),
                f"{where}.clinicalSignoffLanguages: expected distinct known languages")
        sections = guide.get("sections")
        require(isinstance(sections, list) and bool(sections), f"{where}.sections: expected rows")
        for si, section in enumerate(sections):
            require(isinstance(section, dict), f"{where}.sections[{si}]: expected object")
            localised(section.get("title"), f"{where}.sections[{si}].title")
            require(isinstance(section.get("rows"), list) and bool(section["rows"]), f"{where}: empty table")
            codes = set()
            for row in section["rows"]:
                require(isinstance(row, dict), f"{where}.row: expected object")
                nonempty(row.get("code"), f"{where}.row.code")
                require(row["code"] not in codes, f"{where}: duplicate row code")
                codes.add(row["code"])
                localised(row.get("description"), f"{where}.row.description")
        require(isinstance(guide.get("cases"), list), f"{where}.cases: expected list")
        for case_id in guide["cases"]:
            require(case_id in by_case and by_case[case_id].get("classification") == guide["id"], f"{where}.cases: unknown or mismatched case")
            require(case_id not in linked, f"{where}.cases: duplicate case link")
            linked.add(case_id)
        if "visual" in guide:
            validate_classification_visual(guide["visual"], guide["cases"], where + ".visual")
        find_extra_translations(guide, where)
    require(linked == {case["id"] for case in cases if case.get("classification")}, "classifications.json: unlinked classification case")
    return guides


def validate_classification_visual(visual, cases, where):
    require(isinstance(visual, dict), f"{where}: expected visual object")
    require(visual.get("viewBox") == "0 0 960 640", f"{where}.viewBox: unexpected drawing size")
    localised(visual.get("orientation"), f"{where}.orientation")
    def drawing(svg, labels, drawing_where, minimum=0):
        nonempty(svg, drawing_where + ".svg")
        require(len(svg) <= 60000, f"{drawing_where}.svg: too long")
        tree = svg_tree(svg, drawing_where)
        require(isinstance(labels, list) and len(labels) >= minimum, f"{drawing_where}.labels: missing anatomy legend")
        ids = set()
        for label in labels:
            require(isinstance(label, dict), f"{drawing_where}.labels: expected object")
            id = label.get("id")
            require(isinstance(id, str) and bool(re.fullmatch(r"[a-z0-9-]+", id)) and id not in ids, f"{drawing_where}.labels: invalid or repeated id")
            ids.add(id)
            localised(label.get("text"), drawing_where + ".label.text")
            require(type(label.get("number")) is int and 1 <= label["number"] <= 16, f"{drawing_where}.label.number: invalid legend number")
        require({e.get("data-label") for e in tree.iter() if e.get("data-label")} <= ids, f"{drawing_where}.labels: unexplained drawing labels")
    drawing(visual.get("anatomy"), visual.get("labels"), where + ".anatomy", 4)
    stages = visual.get("stages")
    require(isinstance(stages, list) and len(stages) >= 4, f"{where}.stages: expected at least four lessons")
    ids = set()
    for stage in stages:
        require(isinstance(stage, dict), f"{where}.stage: expected object")
        id = stage.get("id")
        require(isinstance(id, str) and bool(re.fullmatch(r"[a-z0-9-]+", id)) and id not in ids, f"{where}.stage.id: invalid or repeated id")
        ids.add(id)
        nonempty(stage.get("code"), where + ".stage.code")
        require(stage.get("dimension") in ("T", "cT", "pT", "N", "cN", "pN", "M", "S", "UC", "injury"), f"{where}.stage.dimension: invalid category")
        for key in ("title", "explanation", "boundary", "orientation"):localised(stage.get(key), where + ".stage." + key)
        require(stage.get("svg") != visual["anatomy"], f"{where}.stage.svg: missing actual finding")
        drawing(stage.get("svg"), stage.get("labels"), where + ".stage[" + id + "]")
        require(isinstance(stage.get("cases"), list) and set(stage["cases"]) <= set(cases), f"{where}.stage.cases: unknown practice case")


def build(root: Path = ROOT) -> dict:
    """Generate the no-fetch browser catalog and a single-file offline edition."""
    root = Path(root)
    # catalog.js is an output of this command, so validate other assets first.
    all_cases, references = load_and_validate(root, check_assets=False, include_archive=True)
    cases = [case for case in all_cases if not case.get("archived")]
    history_cases = [case for case in all_cases if case.get("archived")]
    schemas, links, media = load_visuals(root, cases)
    attach_hints(root, cases)
    tracings = load_tracings(root, cases)
    protocols, radiotherapy = load_regimens(root, cases)
    classifications = load_classifications(root, cases, references, schemas)
    for case in all_cases:
        # Do not ship answer-revealing learning objectives in the browser payload.
        case.pop("objectives", None)
        if case["id"] in links:
            case["schema"] = {"id": links[case["id"]]["schema"], "parts": links[case["id"]].get("parts", [])}
        # The game lists source titles only; the full citations with author names stay in the data files.
        if isinstance(case.get("source"), dict) and isinstance(case["source"].get("originalSources"), list):
            case["source"]["originalSources"] = [{key: value for key, value in item.items() if key != "citation"} if isinstance(item, dict) else item
                                                 for item in case["source"]["originalSources"]]
        if case["id"] in media:
            case["media"] = media[case["id"]]
        if case["id"] in tracings:
            case["tracing"] = tracings[case["id"]]
    # Historical answers remain reviewable when a supplementary question leaves
    # the active bank. History cases never enter schedules, the library or quizzes.
    archive_path = root / "data" / "archive" / "supplemental-questions.json"
    if archive_path.exists():
        archive = read_json(archive_path)
        by_schema = {schema["id"]: schema for schema in schemas}
        for case in history_cases:
            link = archive.get("schemas", {}).get(case["id"])
            if link:
                require(link.get("schema") in by_schema, "supplemental-questions.json: unknown archived schema")
                part_ids = {part["id"] for part in by_schema[link["schema"]]["parts"]}
                require(set(link.get("parts", [])) <= part_ids, "supplemental-questions.json: unknown archived schema parts")
                case["schema"] = {"id": link["schema"], "parts": link.get("parts", [])}
    catalog = {"version": 2, "languages": list(LANGUAGES), "areas": AREAS, "cases": cases, "historyCases": history_cases,
               "questionCount": sum(len(case["steps"]) for case in cases), "references": references, "schemas": schemas,
               "protocols": protocols, "radiotherapy": radiotherapy, "classifications": classifications}
    assets = root / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "catalog.js").write_text("/* Generated by scripts/manage.py build. Edit data/*.json, then rebuild. */\nwindow.NSA_CATALOG = " + json.dumps(catalog, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    validate_assets(root)
    html = (root / "index.html").read_text(encoding="utf-8")
    def inline_link(match):
        attributes = tag_attributes(match[0])
        relations = (attributes.get("rel") or "").lower().split()
        if not attributes.get("href") or not set(relations) & {"stylesheet", "icon"}:
            return match[0]
        asset = local_asset(root, attributes["href"])
        if asset is None:
            return match[0]
        if "stylesheet" in relations:
            stylesheet = re.sub(r"</style", lambda closing: "\\3c /" + closing[0][2:], asset.read_text(encoding="utf-8"), flags=re.IGNORECASE)
            kept = retained_attributes(attributes, {"rel", "href", "integrity", "crossorigin"})
            return f"<style{kept}>\n{stylesheet}\n</style>"
        content_type = mimetypes.guess_type(asset.name)[0] or "application/octet-stream"
        encoded = base64.b64encode(asset.read_bytes()).decode("ascii")
        attributes["href"] = f"data:{content_type};base64,{encoded}"
        return "<link" + retained_attributes(attributes, set()) + ">"

    def inline_script(match):
        attributes = tag_attributes(match[0])
        if not attributes.get("src"):
            return match[0]
        asset = local_asset(root, attributes["src"])
        if asset is None:
            return match[0]
        javascript = re.sub(r"</script", lambda closing: "<\\/" + closing[0][2:], asset.read_text(encoding="utf-8"), flags=re.IGNORECASE)
        kept = retained_attributes(attributes, {"src", "integrity", "crossorigin", "async", "defer"})
        return f"<script{kept}>\n{javascript}\n</script>"

    html = re.sub(r"<link\b[^>]*>", inline_link, html, flags=re.IGNORECASE)
    html = re.sub(r"<script\b[^>]*>.*?</script\s*>", inline_script, html, flags=re.IGNORECASE | re.DOTALL)
    html = html.replace("<!-- STANDALONE_NOTE -->", "<!-- Standalone edition generated from the same source files. -->")
    (root / "standalone.html").write_text(html, encoding="utf-8")
    return catalog


def schedule(root: Path, chosen_date: str, seed: str, output: Path, duty: str | None = None) -> dict:
    require(bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", chosen_date)), "--date must be YYYY-MM-DD")
    try:
        date.fromisoformat(chosen_date)
    except ValueError as exc:
        raise ValidationError("--date must be YYYY-MM-DD") from exc
    cases, _ = load_and_validate(root, check_assets=False)
    generator = random.Random(f"night-shift-academy:v2:{chosen_date}:{seed}")
    if duty is not None:
        return duty_schedule(cases, generator, chosen_date, seed, duty, output)
    chosen = []
    for area in AREA_IDS:
        pool = sorted((case for case in cases if case["area"] == area), key=lambda case: case["id"])
        require(len(pool) >= 2, f"A balanced shift needs at least 2 cases in {area}")
        # Pick two distinct cases while favouring different difficulty levels.
        generator.shuffle(pool)
        first = pool.pop()
        other_levels = [case for case in pool if case["level"] != first["level"]]
        second = generator.choice(other_levels or pool)
        chosen.extend((first["id"], second["id"]))
    generator.shuffle(chosen)
    result = {"version": 2, "date": chosen_date, "seed": seed, "caseIds": chosen}
    write_json(output, result)
    return result


def duty_schedule(cases, generator, chosen_date: str, seed: str, duty: str, output: Path) -> dict:
    """Ten cases of one duty, rotating through topics so a shift does not repeat one subject."""
    require(duty in DUTIES, f"--duty must be one of {', '.join(DUTIES)}")
    groups: dict[str, list[str]] = {}
    for case in sorted((case for case in cases if case.get("duty") == duty), key=lambda case: case["id"]):
        key = case["source"]["domain"] if case.get("source") else "story-" + case["area"]
        groups.setdefault(key, []).append(case["id"])
    require(groups, f"No cases are assigned to the {duty} duty")
    queues = list(groups.values())
    for queue in queues:
        generator.shuffle(queue)
    generator.shuffle(queues)
    chosen: list[str] = []
    while len(chosen) < 10 and any(queues):
        for queue in queues:
            if queue and len(chosen) < 10:
                chosen.append(queue.pop())
    result = {"version": 2, "date": chosen_date, "seed": seed, "duty": duty, "caseIds": chosen}
    write_json(output, result)
    return result


def included_files(root: Path):
    for path in sorted(root.rglob("*"), key=lambda path: path.relative_to(root).as_posix()):
        relative = path.relative_to(root)
        if not path.is_file() or set(relative.parts) & IGNORED_DIRS:
            continue
        if path.suffix.lower() in (".pyc", ".pyo", ".zip", ".tmp", ".temp") or path.name == "SHA256.json" or path.name.startswith(".DS_Store"):
            continue
        yield path, relative.as_posix()


def package(root: Path, output: Path, *, rebuild: bool = True) -> dict:
    root = Path(root).resolve()
    output = Path(output).resolve()
    if rebuild:
        build(root)
    files = list(included_files(root))
    manifest = {relative: hashlib.sha256(path.read_bytes()).hexdigest() for path, relative in files}
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path, relative in files:
            info = zipfile.ZipInfo(f"night-shift-academy/{relative}", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
        info = zipfile.ZipInfo("night-shift-academy/SHA256.json", date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        archive.writestr(info, (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    return manifest


def analyse(source: Path, output: Path, root: Path = ROOT) -> int:
    data = read_json(source)
    # The game file (version 3) carries the logbook next to rank, stickers and the open shift; older exports held the logbook only.
    require(isinstance(data, dict) and (data.get("version") == 2 or (data.get("format") == "night-shift-academy-save" and data.get("version") == 3)),
            "Export must be a game file (version 3) or a logbook export (version 2)")
    history = data.get("history")
    require(isinstance(history, list), "Export.history must be an array")
    cases, _ = load_and_validate(root, check_assets=False, include_archive=True)
    by_id = {case["id"]: case for case in cases}
    fields = ("attempt", "case_id", "case_title_en", "area", "level", "score", "max_score", "score_percent", "elapsed_minutes", "critical_errors", "completed_at", "step_id", "option_id", "step_score", "step_minutes")
    rows = []
    for attempt, record in enumerate(history, 1):
        where = f"history[{attempt - 1}]"
        require(isinstance(record, dict), f"{where}: expected an object")
        case = by_id.get(record.get("caseId"))
        require(case is not None, f"{where}: unknown case id")
        require(record.get("area") == case["area"], f"{where}.area: does not match case")
        for key in ("score", "maxScore", "elapsed", "criticalErrors"):
            integer(record.get(key), f"{where}.{key}")
        require(record["maxScore"] > 0 and record["score"] <= record["maxScore"], f"{where}: invalid score range")
        nonempty(record.get("completedAt"), f"{where}.completedAt")
        answers = record.get("answers")
        require(isinstance(answers, list), f"{where}.answers: expected an array")
        step_by_id = {step["id"]: step for step in case["steps"]}
        seen_steps = set()
        for answer_index, answer in enumerate(answers):
            answer_where = f"{where}.answers[{answer_index}]"
            require(isinstance(answer, dict), f"{answer_where}: expected an object")
            step = step_by_id.get(answer.get("stepId"))
            require(step is not None and step["id"] not in seen_steps, f"{answer_where}: unknown or duplicate step id")
            seen_steps.add(step["id"])
            option = next((option for option in step["options"] if option["id"] == answer.get("optionId")), None)
            require(option is not None, f"{answer_where}: unknown option id")
            for key in ("score", "minutes"):
                integer(answer.get(key), f"{answer_where}.{key}")
            require(answer["score"] == option["score"] and answer["minutes"] == option["minutes"], f"{answer_where}: score/minutes do not match source case")
        expected_answers = len(case["steps"])
        require(len(answers) == expected_answers, f"{where}: completed attempt must have {expected_answers} answers")
        require(record["score"] == sum(answer["score"] for answer in answers), f"{where}.score: differs from answer total")
        require(record["elapsed"] == sum(answer["minutes"] for answer in answers), f"{where}.elapsed: differs from answer total")
        require(record["maxScore"] == sum(max(option["score"] for option in step["options"]) for step in case["steps"]), f"{where}.maxScore: differs from case maximum")
        critical_count = sum(next(option for option in step_by_id[answer["stepId"]]["options"] if option["id"] == answer["optionId"])["critical"] for answer in answers)
        require(record["criticalErrors"] == critical_count, f"{where}.criticalErrors: differs from selected options")
        common = {"attempt": attempt, "case_id": case["id"], "case_title_en": case["title"]["en"], "area": case["area"], "level": case["level"], "score": record["score"], "max_score": record["maxScore"], "score_percent": round(100 * record["score"] / record["maxScore"], 2), "elapsed_minutes": record["elapsed"], "critical_errors": record["criticalErrors"], "completed_at": record["completedAt"]}
        for answer in answers:
            rows.append({**common, "step_id": answer["stepId"], "option_id": answer["optionId"], "step_score": answer["score"], "step_minutes": answer["minutes"]})
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        # Prefix formula-like text so exported CSV is safe to open in Excel.
        for row in rows:
            writer.writerow({key: "'" + value if isinstance(value, str) and value.startswith(("=", "+", "-", "@")) else value for key, value in row.items()})
    return len(rows)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("validate", help="Check cases, translations, references and local assets")
    subcommands.add_parser("build", help="Generate catalog.js and standalone.html")
    serving = subcommands.add_parser("serve", help="Serve the repository on localhost")
    serving.add_argument("--port", type=int, default=8000)
    shifting = subcommands.add_parser("schedule", help="Create a reproducible shift: 10 cases of one duty, or two per department")
    shifting.add_argument("--date", default=date.today().isoformat())
    shifting.add_argument("--seed", default="academy")
    shifting.add_argument("--duty", choices=DUTIES, help="Draw only this duty's cases (night, board, clinic, elective, dayclinic, radiotherapy or urodynamics)")
    shifting.add_argument("--output", type=Path, default=ROOT / "outputs" / "daily-shift.json")
    packing = subcommands.add_parser("package", help="Build a reproducible ZIP with SHA256 manifest")
    packing.add_argument("--output", type=Path, default=ROOT.parent / "night-shift-academy.zip")
    analysis = subcommands.add_parser("analyse", help="Convert exported completed attempts into per-step CSV rows")
    analysis.add_argument("export", type=Path)
    analysis.add_argument("--output", type=Path, default=ROOT / "outputs" / "progress.csv")
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            cases, references = load_and_validate()
            schemas, links, media = load_visuals(ROOT, cases)
            hints, (protocols, radiotherapy) = attach_hints(ROOT, cases), load_regimens(ROOT, cases)
            classifications = load_classifications(ROOT, cases, references, schemas)
            tracings = load_tracings(ROOT, cases)
            steps = sum(len(case["steps"]) for case in cases)
            updated = sum("update" in case for case in cases)
            print(f"Valid: {len(cases)} cases ({updated} updated), {len(references)} references, {len(schemas)} schemas ({len(links)} linked cases), {sum(map(len, media.values()))} images, attending hints for {hints} of {steps} decisions, {sum(len(e['regimens']) for e in protocols)} protocols, {sum(len(e['regimens']) for e in radiotherapy)} radiotherapy schemes, {len(classifications)} classification guides, {len(tracings)} urodynamic tracings, 3 languages, {len(AREAS)} areas.")
        elif args.command == "build":
            catalog = build()
            print(f"Built catalog.js and standalone.html with {catalog['questionCount']} questions in {len(catalog['cases'])} cases; {len(catalog['historyCases'])} cases are history-only.")
        elif args.command == "schedule":
            result = schedule(ROOT, args.date, args.seed, args.output, args.duty)
            print(f"Saved {len(result['caseIds'])} cases ({'duty ' + args.duty if args.duty else '2 per area'}) to {args.output}.")
        elif args.command == "package":
            manifest = package(ROOT, args.output)
            print(f"Packaged {len(manifest)} files plus SHA256.json in {args.output}.")
        elif args.command == "analyse":
            count = analyse(args.export, args.output)
            print(f"Saved {count} decision rows to {args.output}.")
        elif args.command == "serve":
            require(1 <= args.port <= 65535, "--port must be between 1 and 65535")
            build()
            server = ThreadingHTTPServer(("127.0.0.1", args.port), partial(SimpleHTTPRequestHandler, directory=str(ROOT)))
            print(f"Open http://127.0.0.1:{args.port}/ — press Ctrl+C to stop.")
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                server.server_close()
    except (ValidationError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
