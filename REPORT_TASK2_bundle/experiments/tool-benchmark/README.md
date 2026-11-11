# Coding-agent benchmark

The frozen dataset contains three independent Cartkit tasks, 29 acceptance checks,
and four pre-existing repository tests. Each task is run three times through
OpenCode 2.2.7, Pi 1.5.0 and Codex CLI 0.166.0-alpha.6.

The model is `gpt-6.1-sol` with reasoning `medium`. The scripts use native tool
integrations and existing ChatGPT sign-ins. Authentication material is prepared
under `/tmp/coding-benchmark` and is excluded from this package.

## Reproduce

Requirements are Linux x64, Python 3.12, Git, the specified Codex binary and active
OpenAI sign-ins in Codex and OpenCode. Install the earlier lab runtime first.

```bash
python3 ../opencode-v1-v2/scripts/setup.py
/tmp/opencode-lab/runtime/bun-linux-x64/bun install --frozen-lockfile
python3 scripts/prepare_auth.py
python3 scripts/run_benchmark.py --rounds 3
python3 scripts/analyze.py
python3 scripts/verify_results.py
python3 scripts/audit_saved_solutions.py
python3 scripts/plot_results.py
```

Install `requirements-plot.txt` in the Python environment used for plotting.
`BENCH_CODEX_BIN`, `BENCH_CODEX_AUTH` and `BENCH_OPENCODE_DB` override machine-specific
locations. Each native tool receives a new session and an independent copy of the
fixture. Runs already containing `metrics.json` are skipped. To produce a new
experiment, use a new copy with an empty `results` directory and a new
`/tmp/coding-benchmark/workspaces` directory.

## Inspect results

- `dataset.json` records baseline scores, test names and input hashes.
- `results/trials.csv` contains one normalized row per run.
- `results/summary.json` contains tool/task aggregates.
- `results/<tool>-<task>-r<n>/` contains logs, test scores, a Git diff and the saved solution.
- `results/artifact-sha256.json` records hashes for the captured artifacts.
- `results/exploratory-audit.json` records a post-run behavior probe separately from the primary score.

Regrade a saved solution without calling a model.

```bash
python3 scripts/grade.py T2 results/pi-T2-r1/solution
```

Timing includes process startup, model calls, tools and agent-run tests. Fixture
setup and external grading are excluded. The OpenCode server is warm. The token
normalizer counts each completed model response once and handles cached input and
reasoning according to each tool's native usage representation. Full methodology
and interpretation are in the repository's `REPORT_TASK2.md`.
