# Apprentice WebBench protocol v1

Status: declared before the first attempt; independent, self-reported evaluation.

## Selection and campaign

Use every task in `data/tasks.csv`: 323 historical HITL IDs, original prompts, 224 READ and 99 non-READ tasks. Preserve the file order. The separate 10-task READ pilot in `data/pilot.csv` has no ID overlap and is reported independently. Hashes and immutable upstream revision are in `data/manifest.json`.

Freeze the model identifier, source/build fingerprints, launch procedure, operating system, browser version, authentication setup and instructions before the campaign. Record Chrome's version and account preparation details in the configuration launch note. Do not change code or model halfway through. Local source hashes are checked before each task, but operator attestation is still needed for the running app, model selection and browser state. Runtime behavior and tool access are not technically sandboxed by this helper.

## Execution profile

- Execute through the normal Apprentice UI, with a new conversation for each task.
- Start Apprentice with a fresh evaluation data directory. Product memory may persist between tasks; this is a disclosed product evaluation, not a guarantee of stateless episodes. Do not feed it earlier grades, benchmark answers or the results repository.
- Use the existing browser tools, including DOM, JavaScript and same-site network capabilities. Disclose any other tool use in the recording/notes. This is not a screenshot-only computer-use track.
- Use the provided starting URL and retain the original task text. `RUN_INSTRUCTIONS.txt` is a uniform appended instruction, visibly included in every saved prompt.
- Restrict task solving to the specified site. Google/search-engine detours, unrelated APIs, local answer files and benchmark solutions invalidate Success. Normal same-site redirects are allowed. Prepare third-party sign-in before submission; an external identity-provider detour during the scored task is not silently exempted.
- Use prepared test accounts and start authenticated where appropriate. If account creation/login is itself the task, start in the task-appropriate state. Document this pre-authenticated setup; it differs from the original credentials-in-prompt API runs.
- One attempt, at most 15 minutes from prompt submission. This limit is our declared budget, not a claim about Halluminate's undocumented historical budget. The operator enforces the timer; the helper does not terminate Apprentice.
- Human preparation is allowed before the attempt. After submission, no login/CAPTCHA/navigation/task-solving assistance. If intervention is necessary, record it and score Failure for this profile. Starting/stopping the recorder and the timeout stop are administrative actions, not task-solving help.
- Do not ask Apprentice to grade itself. Do not improve a prompt, retry a failed attempt, or choose a preferred take for the headline result. Record interruptions. A later diagnostic retry belongs to a separately reported campaign.

## Evidence

Record the visible prompt, browser actions and final response, including failures. Preserve the original movie and SHA-256 hash. The helper keeps the exact prompt, model/build configuration, task ID, start/finish metadata, operator-reported duration, output, assistance, grade and rationale. Task duration should be checked against video, since terminal return time includes administrative overhead. Recordings capture visible actions, not necessarily every DOM/network tool payload; include additional relevant tool evidence when the visible result does not establish completion.

The per-task public bundle includes outcome text, reviewer identity, reason with timestamps, recording URL, and original recording hash. If a public copy is redacted, disclose what changed and preserve the private original. No credentials, API keys, personal account exports or unrelated conversations are published. Videos are linked rather than committed to Git.

## Human grading

Apply the [Halluminate rubric](https://www.halluminate.ai/blog/benchmark) to the exact original task, with our declared profile above:

- **Success**: all task requirements completed, supporting evidence available, site restriction obeyed, within 15 minutes, no task-solving help.
- **Failure**: incomplete/incorrect execution, site-rule violation, timeout, bot/login failure, intervention, or missing execution evidence. Agent output saying “done” is not proof.
- **BadTask**: the underlying task is genuinely infeasible. A second person must document feasibility evidence before exclusion. A site's changed workflow can qualify; an agent's inability to find it does not. Halluminate's rubric also treats tasks requiring payment or file upload as bad tasks.
- **Blocked**: the operator cannot prepare an authorized test setup (e.g. no appropriate account/test space). Report it separately and retain it as unsuccessful in the all-selected and feasible denominators. This label is our reporting addition, not a Halluminate label.

Use a second human reviewer for a stronger published result. Grades by the operator remain marked self-review. Reviewer names are attestations, not verified identities. Resolve disagreements visibly; retain grade history. An independent human review is not an official Halluminate verification.

## Reporting

Always report selected, started, not run, ungraded, Success, Failure, BadTask and Blocked counts, plus missing public recordings and independently reviewed count. Keep READ/non-READ/category breakdowns available via the results CSV. Do not report an aggregate formal success rate until all 323 IDs are resolved.

Report both:

1. All-selected success rate = Success / 323, retaining all exclusions and blocks in the denominator.
2. Feasible-task success rate = Success / (323 − independently confirmed BadTask).

Both remain null while tasks are unrun or ungraded. Publish the actual numerator/denominator next to any percentage. Also report execution date range, model/build, protocol, attempts, authentication, human assistance and evidence coverage. Missing video links mean the evidence package is incomplete even when a local score can be calculated. Do not claim measured cost unless usage/cost was actually collected; the helper does not measure provider cost.

## Historical comparisons

The 2025 baselines are historical, with different dates and environments. Their full-set headline rates must not be relabeled as rates on these 323 tasks. `historical_labels.csv` preserves labels on the shared IDs and flags prompt differences. Task 364 must be excluded from any comparison requiring identical prompts with rtrvr, or reported separately. Historical BadTask/Omit labels need a common denominator for any paired comparison.

rtrvr's published run allowed Google detours and used logged-in accounts. Our profile preserves the original single-site restriction but also uses prepared accounts. State those differences. A present-day live-web run is not a controlled head-to-head rerun of every historical agent. Formal leaderboard recognition requires coordination with Halluminate; the repo itself is not that recognition.
