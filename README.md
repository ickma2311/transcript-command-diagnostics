# Transcript Command Diagnostics

[Technical note (PDF)](reports/main.pdf) · [Dataset card](DATASET_CARD.md) · [v0.1.0 data and outputs](https://github.com/ickma2311/transcript-command-diagnostics/releases/tag/v0.1.0)

A small, reproducible diagnostic for extracting structured task states from **synthetic English commands** with missing sentence boundaries and a single filled pause (`uh`). It distinguishes a licensed alternative interpretation from an output outside every interpretation allowed by the command grammar.

Use it to inspect command-extraction failures, compare prompts or models on a fixed fixture, and check whether an evaluation mistakes ambiguity for a model error. The completed experiment is a bounded negative/mixed result; this project makes no general robustness or real-ASR claim.

## What was measured

Each item contains two positive actions and one prohibition. The task families are shopping orders, task assignment and file copying. A day phrase can modify one of two neighboring actions under the declared grammar.

| Item | With periods | Without periods and line breaks |
|---|---|---|
| A: ambiguous after removing boundaries | One licensed state | Two licensed states |
| R: recoverable after removing boundaries | One licensed state | One licensed state, because an additional day phrase fixes the attachment |

Each item has six variants: boundaries retained/removed × no filler/`uh` before the junction day phrase/`uh` after it. The test set has **240 A/R pairs, 480 items, 2,880 texts and 24 surface frames**. Two pinned models and two prompt preambles produced **11,520 retained outputs**. Development data are provided separately and were not pooled with test outcomes.

For example, the cued input is:

```text
order two trays from quinn on saturday.
order six staples from ravi.
you must not buy cushions.
```

After removing both periods and line breaks, the grammar permits Saturday to modify either order. Matching the constructed reference, emitting another licensed state, and emitting an invalid state are separate outcomes. This grammar does not enumerate every interpretation of natural English.

## Main observations

Primary prompt P1, recoverable R-items, without a filler:

| Model | Cued correct /240 | Uncued correct /240 | Cued minus uncued | Approx. 95% interval |
|---|---:|---:|---:|---|
| Qwen3-4B-Instruct-2507 | 240 | 239 | +0.417 pp | [0, 2.083] pp |
| Phi-4-mini-instruct | 225 | 216 | +3.750 pp | [0, 7.917] pp |

Qwen's empirical interval lies inside the prespecified ±5 pp region, with only one discordant pair and a ceiling limitation. Phi's result is inconclusive for that region. None of the four Holm-adjusted primary tests rejects zero difference. The intervals are empirical approximations over authored frames, not a general-language guarantee.

The hypothesized filler-placement steering effect was **not supported**: no right/following-command commitment occurred in either primary arm (0/240 for both models). Across both preambles and all filler conditions, all 2,701 admissible outputs among 2,880 ambiguous uncued outputs selected the preceding-command reading. The resulting bootstrap is degenerate; it cannot establish that filler placement has no effect.

An evaluation example: Qwen's no-filler, ambiguous-uncued P1 cell has **119/240 reference matches but 235/240 grammar-admissible outputs**. The remaining 116 admissible states are licensed alternatives. Admissibility does not establish recovery of the speaker's original intent.

## Quick start: CPU only

Use Python 3.12; the reference reconstruction used 3.12.14. No model weights or GPU are needed.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-cpu.txt
.venv/bin/python tools/fetch_artifacts.py
.venv/bin/python tools/validate_dataset.py
.venv/bin/python tools/demo.py
```

Reconstruct the frozen main scores and statistics into a **new directory outside this checkout**:

```sh
REPRO_OUTPUT="$(mktemp -d)/main"
.venv/bin/python tools/reproduce_main.py --output "$REPRO_OUTPUT"
.venv/bin/python tools/verify_reproduction.py --output "$REPRO_OUTPUT"
```

The downloader checks the archive SHA-256 and every artifact hash before extracting allowlisted regular files. The replay preserves the historical journal order; the original scoring and statistics code is unchanged. Verification checks all 11,520 identities and byte equality of `summary.json` and `scored.jsonl`. This reconstructs analysis from recorded outputs; it does not replicate GPU generation or replay the entire earlier research pipeline.

Evaluate your own outputs for these same input row IDs:

```sh
.venv/bin/python tools/score_predictions.py \
  --predictions examples/predictions.jsonl --output /tmp/diagnostic-scores.json
```

The prediction format is one JSON object per line with `row_id` and `text` (the model's JSON response as a string). Optional `model_id` and `prompt_id` identify a group. The convenience scorer reports coverage, categories, grammar admissibility, reference agreement, and correctness restricted to unique-state inputs. It does not enforce the historical fixed-separator generation contract; the frozen reproduction above does. Example predictions are constructed demonstrations, not additional model results.

To regenerate the authored fixture safely in a new external directory:

```sh
.venv/bin/python tools/build_fixture.py --output /tmp/new-command-fixture
```

Do not run `pivot/build.py` inside the checkout after fetching artifacts: its historical entry point writes inputs. The wrapper runs a copied builder outside the retained dataset.

## Scope and limitations

- English, one temporal-attachment construction, three task families and synthetic identifiers. The 24 frames are surface templates, not 24 distinct phenomena.
- Periods and newlines were removed jointly, so their separate effects are unidentified. One `uh` is not a model of arbitrary spoken disfluency.
- No speech audio, ASR system, recognition errors, human naturalness/ambiguity annotations or self-correction experiment in this dataset.
- The experimental prompts explicitly say to ignore `um` and `uh`; generation is greedy and JSON-schema constrained. This design does not isolate instruction-following, schema constraints or graded preferences.
- Both parsers are independently implemented against the same authored contract. Their agreement is not independent human validation.
- Phi has marked direction/family capability differences. Secondary tables retain those failures and do not replace the frozen primary endpoint.

See the [technical note](reports/main.pdf), [English report](reports/REPORT_EN.md), [protocol](docs/PROTOCOL.md) and [complete cell counts](reports/all_main_cells.csv).

## Licenses and attribution

Original project code: [MIT](LICENSE). Authored synthetic inputs: [CC BY 4.0](DATA_LICENSE.md), attributed to the Transcript Command Diagnostics / speech-repair-llm contributors. No borrowed benchmark examples or model weights are distributed. Model identifiers, immutable revisions and their licenses are recorded in `pivot/configs/models.json`; see [NOTICE.md](NOTICE.md).

Use `CITATION.cff` to cite this diagnostic and technical report. There is no peer-reviewed publication associated with this release.
