# Dataset card

## Origin and intended use

All examples are authored by a deterministic Python generator before inference. They are English, closed-grammar commands with synthetic identifiers. Intended use: bounded command-state extraction diagnostics, evaluation-method inspection, and regression comparisons under explicitly documented new conditions. No borrowed benchmark examples, private speech or recordings are included.

## Inventory

Development: 36 A/R pairs, 72 items, 432 rendered texts. Test: 240 pairs, 480 items, 2,880 texts. The test uses three families × eight surface frames × ten generated pairs. Every item has six variants (two layouts × three filler conditions). IDs, items, templates and day assignments are split-specific; the grammar and quantity vocabulary are shared. This is no guarantee of general out-of-distribution validity.

`pivot/inputs/main.jsonl` contains the frozen selected test texts, whole-state reference (`gold`), exhaustive readings relative to the grammar (`readings`), and condition metadata. `test.jsonl` is the retained full pool; this main run selected all 240 pairs, with identical bytes. Development/calibration files are separate. Each pair contains an A-item (two readings after boundary removal) and an R-item (an additional opposite-command day makes both layouts uniquely recoverable). Updates/self-corrections are absent, even though historical parser productions also accept some update forms.

## Interpretation of labels

- `gold`: constructed pre-render reference, not a human judgment.
- `readings`: states licensed by the declared command grammar, not all possible natural-English readings.
- `L0_parse`, `L1_schema`: parse/schema failure.
- `L2_outside_readings`: outside every declared reading.
- `L3_licensed_alternate`: a licensed state differing from the constructed reference.
- `L4_latent`: agreement with the constructed reference.

On ambiguous inputs, reference agreement is not a correctness/error rate. Admissibility is not successful recovery of original intent. On unique-state inputs those measurements coincide.

## Known limits

No ASR/audio/human annotation/naturalness evaluation. Period and newline removal are joint. Filler count is one; case and content words are retained. Both experimental preambles instruct the models to ignore um/uh. Two small instruction models use fixed revisions, greedy generation and constrained JSON. Secondary development/family/direction diagnostics are descriptive and never pooled into primary test evidence.

## Distribution and license

The versioned GitHub Release archive contains complete synthetic inputs and retained model output journals, expected scored outputs and their manifests. The archive is fetched with a pinned SHA-256. Authored inputs are CC BY 4.0; see DATA_LICENSE.md. Code is MIT. Model-output journals are provided as an experiment record with their model/source attribution; the software license does not relicense third-party model weights. No weights are included.
