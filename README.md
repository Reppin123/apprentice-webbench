# Apprentice × Halluminate WebBench

A public evaluation of Apprentice's browser use through the actual Apprentice app.

**Status: setup only. No benchmark tasks have been run and no Apprentice score is claimed.**

There are **323 formal tasks** and **10 separate read-only pilot tasks**. Tasks run on live websites; recordings and human grading provide the evidence. This is an independent evaluation, not an official Halluminate leaderboard submission.

## Run it

Read [START_HERE.md](START_HERE.md), launch Apprentice, then run:

```sh
python3 bench.py pilot
```

The helper copies one task to the clipboard. You start Apprentice's existing recorder, paste the task into a fresh conversation, let it finish, and attach the saved movie and final answer. Repeat the command for the next task. No Python packages, Docker, cloud browsers, or new Apprentice integration are required.

```sh
python3 bench.py review pilot  # grade the pilot recordings
python3 bench.py formal        # one formal task per invocation
python3 bench.py review formal
python3 bench.py status
python3 bench.py export        # build a public bundle locally after content review
```

## What is published

- [Original task list](data/tasks.csv), [pilot](data/pilot.csv), and [source manifest](data/manifest.json).
- [Protocol](PROTOCOL.md): model/build disclosure, first attempts, site restriction, authentication, limits, exclusions, grading, and publication.
- [Historical labels](data/historical_labels.csv), with a flag for changed prompts. These are historical evidence, not a current leaderboard.
- [Results](results/README.md), initially empty. Completed runs will include per-task grades, reasons, answers, recording hashes and public video links.

Integrity checks: `python3 -m unittest -v` validates selection, denominators, exclusion review, evidence requirements and interrupted-attempt handling without running Apprentice or visiting benchmark websites.

Local working records and movie paths live under `.local/`, which is ignored by Git. Original movies stay in `~/Movies/Apprentice/`. Public videos can be hosted on YouTube/Loom or as GitHub Release assets; the results link to each recording. Credentials and unrelated personal information are never part of the public bundle.

## Dataset provenance

Upstream: [Halluminate/WebBench](https://github.com/Halluminate/WebBench) at commit `ea7a1628443321363989f354401f0653e0cba6f4`. The 323 task definitions come from `results/operatorhitlfinal.csv`, retaining the original wording and IDs. At that revision, the small standalone task CSV has 315 rows and the full CSV has 2,647. The README's headline count is 2,454. The manifest records the exact selection and SHA-256 hashes.

The pilot is selected deterministically from READ tasks outside the formal IDs, with one task per hostname. Run `python3 prepare_data.py` to reproduce the data files from the pinned sources. It downloads public upstream data only.

rtrvr's historical CSV contains 258 Success, 59 Failure and 6 Omit labels (258/317 = 81.4%). Its prompt for task 364 differs from the original. Its [methodology](https://rtrvr.ai/blog/web-bench-results) also permits Google detours and assumes logged-in accounts; [Halluminate's original protocol](https://www.halluminate.ai/blog/benchmark) penalizes leaving the specified website. Comparisons must disclose these differences and evaluation dates.

## Recognition and claims

Public, reviewable evidence supports a claim about this exact task set, configuration and date. It does not by itself establish current overall leadership over other agents or models. Halluminate's [maintainer guidance](https://github.com/Halluminate/WebBench/issues/1) directs prospective leaderboard entrants to contact the team. No submission or email has been sent as part of this setup.

The helper is MIT licensed. Upstream dataset attribution and its license are retained in [data/upstream-LICENSE](data/upstream-LICENSE).
