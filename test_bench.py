"""Check denominator integrity, evidence requirements and interrupted attempts."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bench


class BenchmarkIntegrity(unittest.TestCase):
    def test_selection_is_fixed_and_pilot_is_separate(self):
        formal, pilot = bench.tasks("formal"), bench.tasks("pilot")
        self.assertEqual(len(formal), 323)
        self.assertEqual(len(pilot), 10)
        self.assertFalse({x["ID"] for x in formal} & {x["ID"] for x in pilot})
        self.assertTrue(all(x["Category"] == "READ" for x in pilot))
        self.assertIn("Register a new user account", next(x for x in formal if x["ID"] == "364")["Task"])

    def test_no_headline_score_for_partial_run(self):
        rows = [{"task_id": "1", "state": "finished", "label": "Success"}]
        result = bench.summarize([{"ID": "1"}, {"ID": "2"}], rows)
        self.assertIsNone(result["success_rate_all_selected"])
        self.assertIsNone(result["success_rate_feasible"])
        self.assertEqual(result["counts"]["NotRun"], 1)

    def test_blocked_retained_bad_task_disclosed(self):
        rows = [{"task_id": str(i), "state": "finished", "label": label}
                for i, label in enumerate(["Success", "Failure", "Blocked", "BadTask"])]
        result = bench.summarize([{"ID": str(i)} for i in range(4)], rows)
        self.assertEqual(result["success_rate_all_selected"], 1 / 4)
        self.assertEqual(result["success_rate_feasible"], 1 / 3)

    def test_interrupted_attempt_is_not_complete(self):
        result = bench.summarize([{"ID": "1"}], [{"task_id": "1", "state": "started", "label": "Success"}])
        self.assertFalse(result["complete"])
        self.assertEqual(result["counts"]["Ungraded"], 1)

    def test_duplicate_or_foreign_ids_rejected(self):
        for rows in [[{"task_id": "2"}], [{"task_id": "1"}, {"task_id": "1"}]]:
            with self.assertRaises(ValueError):
                bench.summarize([{"ID": "1"}], rows)

    def test_success_requires_evidence_budget_and_no_help(self):
        good = {"config": {"operator": "alice"}, "video_sha256": "hash", "answer": "observed result",
                "duration_seconds": 90, "human_assistance": "none"}
        bench.validate_grade(good, "Success", "alice")
        for update in [{"video_sha256": ""}, {"answer": ""}, {"duration_seconds": 901},
                       {"duration_seconds": float("nan")}, {"human_assistance": "helped navigate"}]:
            with self.assertRaises(ValueError):
                bench.validate_grade(good | update, "Success", "alice")

    def test_exclusion_requires_second_reviewer(self):
        record = {"config": {"operator": "alice"}}
        with self.assertRaises(ValueError):
            bench.validate_grade(record, "BadTask", "alice")
        bench.validate_grade(record, "BadTask", "bob")

    def test_started_attempt_resumes_without_dispatch(self):
        with tempfile.TemporaryDirectory() as temp:
            local = Path(temp)
            config = {"protocol_sha256": bench.digest(bench.ROOT / "PROTOCOL.md"),
                      "task_manifest_sha256": bench.digest(bench.ROOT / "data/manifest.json"),
                      "instructions_sha256": bench.digest(bench.ROOT / "RUN_INSTRUCTIONS.txt"),
                      "helper_sha256": bench.digest(bench.ROOT / "bench.py"),
                      "agent_build": {}, "app_build": {}}
            bench.save(local / "config.json", config)
            bench.save(local / "source_paths.json", {"agent": temp, "app": temp})
            task = bench.tasks("pilot")[0]
            record = {"task_id": task["ID"], "state": "started", "label": "Ungraded"}
            path = local / "runs/pilot" / task["ID"] / "record.json"
            bench.save(path, record)
            with patch.object(bench, "LOCAL", local), patch.object(bench, "fingerprint", return_value={}), \
                 patch.object(bench, "collect_evidence") as collect, patch.object(bench.subprocess, "run") as dispatch:
                bench.run("pilot")
                collect.assert_called_once_with(path, record)
                dispatch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
