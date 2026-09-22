#!/usr/bin/env python3
"""Reproduce the task selection from an immutable upstream revision."""
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
SHA = "ea7a1628443321363989f354401f0653e0cba6f4"
BASE = f"https://raw.githubusercontent.com/Halluminate/WebBench/{SHA}/"
FIELDS = ["ID", "Starting URL", "Category", "Difficulty", "Task"]
SEED = "apprentice-webbench-pilot-v1:"


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    data = ROOT / "data"
    data.mkdir(exist_ok=True)
    sources = {}

    def fetch(name):
        raw = urlopen(BASE + name, timeout=30).read()
        sources[name] = {"url": BASE + name, "sha256": hashlib.sha256(raw).hexdigest()}
        return raw

    def read(name):
        return list(csv.DictReader(io.StringIO(fetch(name).decode("utf-8-sig"))))

    original = read("results/operatorhitlfinal.csv")
    tasks = [{k: row[k] for k in FIELDS} for row in original]
    ids = {t["ID"] for t in tasks}
    assert len(tasks) == len(ids) == 323
    write_csv(data / "tasks.csv", FIELDS, tasks)

    all_tasks = read("webbenchfinal.csv")
    small = read("webbench_hitl_final.csv")
    candidates = sorted(
        (t for t in all_tasks if t["Category"] == "READ" and t["ID"] not in ids),
        key=lambda t: hashlib.sha256((SEED + t["ID"]).encode()).hexdigest(),
    )
    pilot, domains = [], set()
    for t in candidates:
        domain = urlparse(t["Starting URL"]).hostname.removeprefix("www.")
        if domain not in domains:
            pilot.append(t)
            domains.add(domain)
        if len(pilot) == 10:
            break
    write_csv(data / "pilot.csv", FIELDS, pilot)

    baselines, mismatches = [], []
    originals = {t["ID"]: t for t in tasks}
    for name, label, rows in [
        ("operator_hitl_2025", "operator_hitl_eval", original),
        ("anthropic_cua_2025", "Anthropic_Eval", read("results/anthropicfinal.csv")),
        ("openai_cua_2025", "CUAEval", read("results/openaicuafinal.csv")),
        ("rtrvr_2025", "Human Label", read("results/rtrvrfinal.csv")),
    ]:
        for row in rows:
            if row["ID"] not in ids:
                continue
            matches = row["Task"] == originals[row["ID"]]["Task"]
            baselines.append({"agent": name, "task_id": row["ID"], "label": row[label],
                              "prompt_matches": str(matches).lower()})
            if not matches:
                mismatches.append({"agent": name, "task_id": row["ID"],
                                   "original": originals[row["ID"]]["Task"], "changed": row["Task"]})
    write_csv(data / "historical_labels.csv", ["agent", "task_id", "label", "prompt_matches"], baselines)
    (data / "upstream-LICENSE").write_bytes(fetch("LICENSE"))
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(data.iterdir())
              if p.name in {"tasks.csv", "pilot.csv", "historical_labels.csv", "upstream-LICENSE"}}
    manifest = {
        "upstream_repository": "https://github.com/Halluminate/WebBench", "upstream_commit": SHA,
        "selection": "All 323 rows of results/operatorhitlfinal.csv; original prompts unchanged.",
        "task_count": len(tasks), "categories": dict(Counter(t["Category"] for t in tasks)),
        "pilot_selection": "First 10 READ tasks outside the 323 IDs, one per hostname, sorted by SHA256(seed + ID).",
        "pilot_seed": SEED, "pilot_ids": [t["ID"] for t in pilot],
        "upstream_full_csv_rows": len(all_tasks), "upstream_hitl_csv_rows": len(small),
        "prompt_mismatches": mismatches, "sources": sources, "file_sha256": hashes,
    }
    (data / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Prepared {len(tasks)} formal tasks and {len(pilot)} separate pilot tasks.")


if __name__ == "__main__":
    main()
