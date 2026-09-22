# Your first recorded run

## 1. Start a fresh evaluation copy of Apprentice

On the Mac where this was prepared, run:

```sh
bash /Users/akshitbansal/Clicky-Apprenticeship/apprentice-mac/scripts/dev.sh \
  --data-dir="/Users/akshitbansal/Clicky::Apprenticeship/apprentice-webbench/.local/apprentice-data"
```

This is Apprentice's existing development launcher. **It stops running Apprentice instances**, rebuilds the Mac app, and starts the Python agent from source. Run it when your other Apprentice work is finished. It uses a dedicated evaluation data directory and the app's existing shared Claude login. Do not clear that shared login.

If you cloned this repository elsewhere, substitute the local repository and Apprentice source paths. `bench.py configure` will ask for both source directories. The benchmark repo does not include Apprentice's private source.

Select the model you want to evaluate in Apprentice and note its exact identifier. Keep that model and build fixed through the pilot and formal campaign. The helper records source commits, whether the trees are modified, and a hash of their contents. This describes the working sources; the launch step above is needed to ensure those sources are actually running. If you improve Apprentice after the pilot, begin a separately named campaign with a new public configuration; do not mix builds.

## 2. Check Chrome and the recorder before starting the pilot

Open your normal Chrome profile and visit `chrome://inspect/#remote-debugging`. Confirm that **Allow remote debugging for this browser instance** is enabled. Apprentice's normal browser tools attach to this running profile using Chrome's Allow dialog. Do not add `--remote-debugging-port` flags or create a second debugging profile for this workflow.

In a separate Apprentice conversation, send: **“Connection check only: call browser_tabs once and report whether it succeeds. Do not navigate, restart Chrome, launch another profile, or change settings. If it fails, report the error and stop.”** Click **Allow** in Chrome when prompted. Proceed only after Apprentice confirms a successful connection. This is a setup check, not a pilot or scored task. A Chrome restart or a new agent connection can require approval again.

If Chrome is unreachable, stop the setup check and resolve that first; do not use a benchmark task as the connection test. If a pilot attempt has already started, retain its failed attempt and recording rather than silently restarting it.

Keep Apprentice and Chrome on the display being recorded. Turn off distracting notifications and keep unrelated private windows off that display.

Press **Control–Command–R**, wait a few seconds, then press it again. Apprentice should reveal a playable `.mov` in **Movies → Apprentice**. This shortcut is configurable in Apprentice's Shortcuts settings. On macOS 15 or later, its built-in recorder captures the screen and system audio. If macOS requests Screen Recording access, grant it to Apprentice in System Settings and retry this setup check.

Open the saved movie and verify that the prompt, browser and response are readable. This recording check is not a benchmark attempt.

## 3. Run one pilot task

Double-click **Start Pilot.command**, or run:

```sh
cd '/Users/akshitbansal/Clicky::Apprenticeship/apprentice-webbench'
python3 bench.py pilot
```

On the first invocation, enter the selected model, your public name/handle, a short launch note, and the two source directories (the local defaults are filled in).

For each task:

1. Open a **new Apprentice conversation**. Prepare any permitted test login before the attempt. The pilot contains only READ tasks.
2. Start recording with **Control–Command–R** and verify it started. Set a **15-minute timer**.
3. Type `START` in the terminal. The helper copies the full prompt. Paste it into Apprentice and start the timer when you submit it.
4. Let Apprentice work. Stop it at 15 minutes if it has not finished. Do not help it solve the task.
5. Stop the recorder with **Control–Command–R**. Wait for the saved-file notification, then return to the terminal.
6. Confirm the movie path, paste the final answer/outcome followed by `END` on a new line, and enter duration and any intervention.

The next invocation advances to the next task. An interrupted attempt resumes evidence collection; it does not grant a retry. A recording failure stays visible and cannot earn Success. The helper stores movie hashes and paths but does not duplicate large video files, so keep the originals.

## 4. Grade, then expand

```sh
python3 bench.py review pilot
```

Watch each recording, inspect the exact task in `data/pilot.csv`, and explain the grade with video timestamps. A public video URL can be added later by running the review command again. Have someone else review the formal recordings; use a distinct person's name, not another alias for the operator. The helper requires a second reviewer before excluding a task as infeasible.

When the pilot workflow works, use `python3 bench.py formal`. This starts at the beginning of the original 323-task selection. Some tasks need test accounts or designated test spaces. Read each task before dispatch; if its setup is unavailable, enter `BLOCKED` with a reason. It stays visible in the selected-task denominator. Never publish real messages, invitations or posts to uninvolved people merely to complete an eval task.

## 5. Make the evidence public

Upload reviewed recordings to the video host of your choice and add the URL when grading. Keep all attempts, including failures. Redact credentials or unrelated personal data if needed, describe the redaction, preserve the task actions/timing, and retain the private original whose hash was captured. Do not edit away failures.

```sh
python3 bench.py review formal
python3 bench.py export
```

The export writes `results/records.json`, `results/results.csv` and `results/summary.json`. It does **not** upload anything. Inspect these files before committing: answers and free-text notes are included. Update the README's status to identify the completed campaign, then commit and push only the reviewed public files. Until every formal task is resolved, the aggregate formal score is `null`; pilot success is never presented as the formal score.

No benchmark task, model request, recording, account creation or site mutation was executed during initial setup.
