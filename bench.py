#!/usr/bin/env python3
"""A local task queue and evidence ledger. Apprentice itself executes the tasks."""
import argparse
import csv
import hashlib
import json
import math
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOCAL = ROOT / ".local"
MOVIES = Path.home() / "Movies/Apprentice"
DEFAULT_AGENT = Path.home() / "Clicky-Apprenticeship/apprentice-agent"
DEFAULT_APP = Path.home() / "Clicky-Apprenticeship/apprentice-mac"
LABELS = ("Success", "Failure", "BadTask", "Blocked")


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    temp.replace(path)


def ask(prompt, default=""):
    value = input(f"{prompt}" + (f" [{default}]" if default else "") + ": ").strip()
    return value or default


def required(prompt):
    while True:
        value = ask(prompt)
        if value:
            return value


def command(args):
    return subprocess.check_output(args, stderr=subprocess.DEVNULL).decode().strip()


def fingerprint(path):
    head = command(["git", "-C", str(path), "rev-parse", "HEAD"])
    changed = command(["git", "-C", str(path), "status", "--porcelain"])
    tracked = subprocess.check_output(["git", "-C", str(path), "ls-files", "-z"])
    untracked = subprocess.check_output(["git", "-C", str(path), "ls-files", "--others", "--exclude-standard", "-z"])
    h = hashlib.sha256()
    for name in sorted(set((tracked + untracked).split(b"\0")) - {b""}):
        file = path / name.decode()
        h.update(name + b"\0")
        h.update(digest(file).encode() if file.is_file() else b"MISSING")
    return {"commit": head, "dirty": bool(changed), "working_tree_sha256": h.hexdigest()}


def tasks(phase):
    name = "pilot.csv" if phase == "pilot" else "tasks.csv"
    manifest = json.loads((ROOT / "data/manifest.json").read_text())
    path = ROOT / "data" / name
    if digest(path) != manifest["file_sha256"][name]:
        raise ValueError(f"{name} changed after selection; restore it before running.")
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def configure():
    path = LOCAL / "config.json"
    if path.exists():
        print("Configuration already saved. Keep it fixed for this campaign.")
        return
    print("First launch the evaluation app using START_HERE.md and select the model in Apprentice.")
    model = required("Exact model identifier shown in Apprentice")
    operator = required("Public operator name or handle")
    note = required("Confirm how you launched this build and prepared its evaluation data directory")
    agent = Path(ask("Agent source directory", str(DEFAULT_AGENT))).expanduser()
    app = Path(ask("Mac app source directory", str(DEFAULT_APP))).expanduser()
    config = {
        "model": model, "operator": operator, "launch_note": note, "configured_at": now(),
        "agent_build": fingerprint(agent), "app_build": fingerprint(app),
        "os": platform.platform(), "task_limit_seconds": 900,
        "profile": "Product UI; original single-site rule; pre-authenticated test accounts; no task-solving help",
        "memory_policy": "Fresh evaluation data directory at launch; fresh conversation per task; product memory may persist",
        "protocol_sha256": digest(ROOT / "PROTOCOL.md"),
        "task_manifest_sha256": digest(ROOT / "data/manifest.json"),
        "instructions_sha256": digest(ROOT / "RUN_INSTRUCTIONS.txt"),
        "helper_sha256": digest(ROOT / "bench.py"),
    }
    save(path, config)
    save(LOCAL / "source_paths.json", {"agent": str(agent), "app": str(app)})
    print("Saved locally. No browser task has started.")


def record_path(phase, task_id):
    return LOCAL / "runs" / phase / task_id / "record.json"


def read_records(phase):
    return [json.loads(p.read_text()) for p in sorted((LOCAL / "runs" / phase).glob("*/record.json"))]


def collect_evidence(path, record):
    print("Stop recording with Control–Command–R. Wait for Apprentice to reveal the saved movie.")
    started = datetime.fromisoformat(record["started_at"]).timestamp()
    candidates = sorted((p for p in MOVIES.glob("demo-*.mov") if p.stat().st_mtime >= started),
                        key=lambda p: p.stat().st_mtime, reverse=True)
    default = str(candidates[0]) if candidates else ""
    supplied = ask("Recording path (or type MISSING if recording failed)", default)
    if supplied == "MISSING":
        record["recording_error"] = required("Explain why recording is missing; this cannot be scored Success")
    else:
        video = Path(supplied.strip("'\"").replace("\\ ", " ")).expanduser()
        if not video.is_file() or not video.stat().st_size:
            raise ValueError("Movie missing or empty. Run the same command to resume evidence collection.")
        if shutil.which("ffprobe"):
            command(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(video)])
        record["video_sha256"] = digest(video)
        # Keep the original movie in Movies/Apprentice, avoiding a second large copy.
        save(path.parent / "private_video.json", {"path": str(video)})
    print("Paste the final answer (or observed outcome). End with END on a line of its own.")
    lines = []
    while (line := input()) != "END":
        lines.append(line)
    record["answer"] = "\n".join(lines)
    record["human_assistance"] = ask("Any human intervention after submission? Describe it", "none")
    record["duration_seconds"] = float(required("Task duration in seconds, from submission to completion/stop"))
    if not math.isfinite(record["duration_seconds"]) or record["duration_seconds"] < 0:
        raise ValueError("Duration must be a finite, nonnegative number.")
    record["evidence_collected_at"] = now()
    record["state"] = "finished"
    save(path, record)
    print("Evidence saved. Grade it using: python3 bench.py review " + record["phase"])


def run(phase):
    if not (LOCAL / "config.json").exists():
        configure()
    config = json.loads((LOCAL / "config.json").read_text())
    if config["protocol_sha256"] != digest(ROOT / "PROTOCOL.md") or config["task_manifest_sha256"] != digest(ROOT / "data/manifest.json"):
        raise ValueError("Protocol or task manifest changed after configuration.")
    if config["instructions_sha256"] != digest(ROOT / "RUN_INSTRUCTIONS.txt") or config["helper_sha256"] != digest(ROOT / "bench.py"):
        raise ValueError("Instructions or helper changed after configuration.")
    paths = json.loads((LOCAL / "source_paths.json").read_text())
    for key in ("agent", "app"):
        if fingerprint(Path(paths[key])) != config[key + "_build"]:
            raise ValueError(f"{key} source changed after configuration. Restore the pinned build before continuing.")
    for task in tasks(phase):
        path = record_path(phase, task["ID"])
        if path.exists():
            record = json.loads(path.read_text())
            if record["state"] == "finished":
                continue
            print(f"Resuming evidence collection for task {task['ID']}; do not rerun it.")
            collect_evidence(path, record)
            return
        prompt = "Starting URL: " + task["Starting URL"] + "\n\n" + task["Task"] + "\n\n" + (ROOT / "RUN_INSTRUCTIONS.txt").read_text()
        path.parent.mkdir(parents=True, exist_ok=True)
        (path.parent / "prompt.txt").write_text(prompt)
        print(f"\n{phase.upper()} — task {task['ID']} / {task['Category']}\n\n{prompt}")
        print("\nOpen a NEW Apprentice conversation. Prepare test login before recording.")
        print("Keep Apprentice and Chrome on the recorded display. Press Control–Command–R and verify recording started.")
        print("Set a 15-minute timer. The next step copies the prompt; paste it into Apprentice yourself.")
        action = ask("Type START when ready, BLOCKED for an unavailable setup, or Enter to leave")
        if action not in {"START", "BLOCKED"}:
            return
        record = {"task_id": task["ID"], "phase": phase, "category": task["Category"],
                  "attempt": 1, "started_at": now(), "state": "started", "config": config,
                  "dispatched": action == "START",
                  "label": "Ungraded", "reason": "", "reviewer": "", "video_url": ""}
        if action == "BLOCKED":
            record.update(state="finished", label="Blocked", reason=required("Why blocked?"),
                          reviewer=config["operator"], review_type="self", answer="", human_assistance="none")
            save(path, record)
            print("Recorded as Blocked. It stays in the 323-task denominator.")
            return
        save(path, record)  # Persist BEFORE dispatch so interruption never silently creates a retry.
        if shutil.which("pbcopy"):
            subprocess.run(["pbcopy"], input=prompt.encode(), check=True)
            print("Prompt copied. Paste it into Apprentice now. Do not provide task-solving help.")
        input("When Apprentice finishes (or you stop it at 15 minutes), stop recording, then press Enter here.")
        record["operator_finished_at"] = now()
        save(path, record)
        collect_evidence(path, record)
        return
    print(f"All {len(tasks(phase))} {phase} tasks have records. Review and export next.")


def validate_grade(record, label, reviewer):
    if label not in LABELS:
        raise ValueError("Choose Success, Failure, BadTask or Blocked.")
    if label == "BadTask" and reviewer == record["config"]["operator"]:
        raise ValueError("BadTask exclusion needs a second reviewer; use Failure/Blocked pending review.")
    if label == "Success":
        if not record.get("video_sha256") or not record.get("answer", "").strip():
            raise ValueError("Success requires a recording and an answer/outcome.")
        duration = record.get("duration_seconds", 901)
        if not math.isfinite(duration) or not 0 <= duration <= 900:
            raise ValueError("Task exceeded the declared 15-minute limit.")
        if record.get("human_assistance", "").strip().lower() != "none":
            raise ValueError("Task-solving assistance is outside the declared autonomous profile.")


def review(phase):
    reviewer = required("Public reviewer name/handle (a different person for independent review)")
    selected = {t["ID"]: t for t in tasks(phase)}
    for record in read_records(phase):
        if record["state"] != "finished":
            continue
        print(f"\nTask {record['task_id']} — currently {record['label']}\nAnswer: {record.get('answer', '')}")
        print("Task:", selected[record["task_id"]]["Task"])
        private = record_path(phase, record["task_id"]).parent / "private_video.json"
        if private.exists():
            print("Recording:", json.loads(private.read_text())["path"])
        print("Watch the recording, check the exact task and domain rule, then grade.")
        label = ask("Success / Failure / BadTask / Blocked (Enter skips)")
        if not label:
            continue
        validate_grade(record, label, reviewer)
        reason = required("Reason and supporting video timestamp(s); BadTask needs feasibility evidence")
        path = record_path(phase, record["task_id"])
        history = record.setdefault("review_history", [])
        history.append({k: record.get(k) for k in ("label", "reason", "reviewer", "reviewed_at")})
        record.update(label=label, reviewer=reviewer, reason=reason, reviewed_at=now(),
                      review_type="self" if reviewer == record["config"]["operator"] else "independent")
        record["video_url"] = ask("Public recording URL (can be added later)", record.get("video_url", ""))
        save(path, record)


def summarize(selected, records):
    ids = {t["ID"] for t in selected}
    mapping = {r["task_id"]: r for r in records}
    if len(mapping) != len(records) or not set(mapping) <= ids:
        raise ValueError("Duplicate or unexpected task IDs in records.")
    counts = {label: 0 for label in (*LABELS, "Ungraded", "NotRun")}
    for task_id in ids:
        r = mapping.get(task_id)
        label = "NotRun" if r is None else r["label"] if r["state"] == "finished" else "Ungraded"
        counts[label] += 1
    complete = counts["NotRun"] == counts["Ungraded"] == 0
    denominator = len(ids) - counts["BadTask"]
    return {"selected": len(ids), "counts": counts, "complete": complete,
            "started": sum(bool(r.get("dispatched")) for r in records),
            "success_rate_all_selected": counts["Success"] / len(ids) if complete else None,
            "success_rate_feasible": counts["Success"] / denominator if complete and denominator else None,
            "missing_public_recordings": sum(not r.get("video_url") for r in records if r.get("video_sha256")),
            "independently_reviewed": sum(r.get("review_type") == "independent" for r in records)}


def export():
    print("This writes a PUBLIC results bundle. Review answers, notes and videos for secrets before committing.")
    if ask("Type EXPORT after reviewing local records") != "EXPORT":
        return
    summaries, public_records = {}, []
    for phase in ("pilot", "formal"):
        records = read_records(phase)
        for r in records:
            if r["label"] in LABELS:
                validate_grade(r, r["label"], r["reviewer"])
        summaries[phase] = summarize(tasks(phase), records)
        public_records.extend(records)
    save(ROOT / "results/records.json", public_records)
    save(ROOT / "results/summary.json", summaries)
    report = ["# Run summary", "", "Independent, self-reported evaluation. See PROTOCOL.md for the exact profile.", "",
              "| Phase | Selected | Success | Failure | Blocked | BadTask | Ungraded | Not run | All-selected rate | Feasible rate |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |"]
    for phase, summary in summaries.items():
        c = summary["counts"]
        rate = lambda value: "Pending" if value is None else f"{value:.2%}"
        report.append(f"| {phase} | {summary['selected']} | {c['Success']} | {c['Failure']} | {c['Blocked']} | {c['BadTask']} | {c['Ungraded']} | {c['NotRun']} | {rate(summary['success_rate_all_selected'])} | {rate(summary['success_rate_feasible'])} |")
    report += ["", "Missing public recording links and independent review counts are recorded in [summary.json](summary.json).",
               "Local scores do not imply the public evidence package is complete or officially verified.", ""]
    (ROOT / "results/summary.md").write_text("\n".join(report))
    fields = ["phase", "task_id", "category", "state", "label", "reason", "reviewer", "review_type",
              "duration_seconds", "human_assistance", "video_url", "video_sha256"]
    with (ROOT / "results/results.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(public_records)
    print(json.dumps(summaries, indent=2))
    print("Exported locally to results/. No upload or git push was performed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["configure", "pilot", "formal", "review", "status", "export"])
    parser.add_argument("phase", nargs="?", choices=["pilot", "formal"], default="pilot")
    args = parser.parse_args()
    if args.action == "configure":
        configure()
    elif args.action in {"pilot", "formal"}:
        run(args.action)
    elif args.action == "review":
        review(args.phase)
    elif args.action == "export":
        export()
    else:
        for phase in ("pilot", "formal"):
            print(phase, json.dumps(summarize(tasks(phase), read_records(phase)), indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(str(exc))
    except (KeyboardInterrupt, EOFError):
        print("\nStopped. Any started attempt is retained; rerun the same command to collect its evidence.")
