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
]
AREA_IDS = tuple(area["id"] for area in AREAS)
CASE_FILES = tuple(f"{area}.json" for area in AREA_IDS)
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
    for kind, names in (("stylesheet", ("styles.css",)), ("script", ("i18n.js", "catalog.js", "engine.js", "app.js"))):
        for name in names:
            require((root / "assets" / name).resolve() in by_kind[kind], f"index.html must reference assets/{name} exactly once")
    for kind, expected in (("stylesheet", ("styles.css", "cartoon.css")), ("script", ("i18n.js", "banter.js", "art.js", "catalog.js", "engine.js", "app.js"))):
        ordered_paths = [(root / "assets" / name).resolve() for name in expected]
        observed = [asset for asset in by_kind[kind] if asset in ordered_paths]
        require(observed == [asset for asset in ordered_paths if asset in observed], f"index.html {kind} dependency order must be {' → '.join(expected)}")


def tag_attributes(markup: str) -> dict:
    parser = AssetParser()
    parser.feed(markup)
    return parser.tags[0][1]


def retained_attributes(attributes: dict, excluded: set[str]) -> str:
    return "".join(f" {name}" if value is None else f' {name}="{escape(value, quote=True)}"' for name, value in attributes.items() if name not in excluded)


def load_and_validate(root: Path = ROOT, *, check_assets: bool = True):
    """Return all cases and deduplicated references, after validating source data."""
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
    for area, filename in zip(AREA_IDS, CASE_FILES):
        rows = read_json(root / "data" / filename)
        require(isinstance(rows, list) and bool(rows), f"{filename}: expected a nonempty array")
        for index, case in enumerate(rows):
            where = f"{filename}[{index}]"
            require(isinstance(case, dict), f"{where}: expected an object")
            nonempty(case.get("id"), f"{where}.id")
            require(case["id"] not in case_ids, f"{where}: duplicate case id {case['id']!r}")
            case_ids.add(case["id"])
            require(case.get("area") == area, f"{where}.area: expected {area!r}")
            require(type(case.get("level")) is int and case["level"] in (1, 2, 3), f"{where}.level: expected 1, 2 or 3")
            require(case.get("acuity") in ("routine", "urgent", "critical"), f"{where}.acuity: invalid acuity")
            patient = case.get("patient")
            require(isinstance(patient, dict), f"{where}.patient: expected an object")
            nonempty(patient.get("name"), f"{where}.patient.name")
            require("age" in patient, f"{where}.patient.age: expected an age or explicit null")
            if patient["age"] is not None:
                integer(patient["age"], f"{where}.patient.age")
                require(patient["age"] <= 120, f"{where}.patient.age: age must be <= 120")
            for key in ("title", "presenting", "takeaway"):
                localised(case.get(key), f"{where}.{key}")
            localised(case.get("objectives"), f"{where}.objectives", array=True)
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
            cases.append(case)
    if check_assets:
        validate_assets(root)
    return cases, [references[key] for key in sorted(references)]


def build(root: Path = ROOT) -> dict:
    """Generate the no-fetch browser catalog and a single-file offline edition."""
    root = Path(root)
    # catalog.js is an output of this command, so validate other assets first.
    cases, references = load_and_validate(root, check_assets=False)
    catalog = {"version": 2, "languages": list(LANGUAGES), "areas": AREAS, "cases": cases, "references": references}
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


def schedule(root: Path, chosen_date: str, seed: str, output: Path) -> dict:
    require(bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", chosen_date)), "--date must be YYYY-MM-DD")
    try:
        date.fromisoformat(chosen_date)
    except ValueError as exc:
        raise ValidationError("--date must be YYYY-MM-DD") from exc
    cases, _ = load_and_validate(root, check_assets=False)
    generator = random.Random(f"night-shift-academy:v2:{chosen_date}:{seed}")
    chosen = []
    for area in AREA_IDS:
        pool = sorted((case for case in cases if case["area"] == area), key=lambda case: case["id"])
        require(len(pool) >= 2, f"A balanced 10-case shift needs at least 2 cases in {area}")
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
    require(isinstance(data, dict) and data.get("version") == 2, "Export must have version 2")
    history = data.get("history")
    require(isinstance(history, list), "Export.history must be an array")
    cases, _ = load_and_validate(root, check_assets=False)
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
    shifting = subcommands.add_parser("schedule", help="Create a reproducible, balanced 10-case shift")
    shifting.add_argument("--date", default=date.today().isoformat())
    shifting.add_argument("--seed", default="academy")
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
            print(f"Valid: {len(cases)} cases, {len(references)} references, 3 languages, 5 areas.")
        elif args.command == "build":
            catalog = build()
            print(f"Built catalog.js and standalone.html with {len(catalog['cases'])} cases.")
        elif args.command == "schedule":
            result = schedule(ROOT, args.date, args.seed, args.output)
            print(f"Saved {len(result['caseIds'])} cases (2 per area) to {args.output}.")
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
