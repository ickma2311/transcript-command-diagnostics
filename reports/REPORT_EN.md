# A bounded test of transcript-style command inputs

This study asks whether removing sentence boundaries changes recoverable task-state extraction, and whether placing a single `uh` before versus after a temporal junction steers an ambiguous reading. The retained main run has 240 constructed pairs, three command families, 24 surface frames, two pinned small models and two prompt preambles. Its 11,520 outputs are complete.

## Results

Primary no-filler recoverable-item accuracy is 240/240 cued versus 239/240 uncued for Qwen, and 225/240 versus 216/240 for Phi. Cued-minus-uncued differences are 0.417 pp (approximate 95% interval [0,2.083]) and 3.750 pp ([0,7.917]). Qwen has only one discordant pair near ceiling; Phi's interval does not establish the prespecified ±5pp region. The four Holm-adjusted primary tests do not reject zero difference.

Primary ambiguous-item right commitments are zero in both filler arms for both models. Across both prompts and all filler conditions, 2,701 of 2,880 ambiguous-uncued outputs are admissible and all select the preceding command. The steering bootstrap is degenerate and descriptive; it cannot show invariance or lack of graded sensitivity.

Without a filler, Qwen has 119/240 constructed-reference matches but 235/240 admissible states; Phi has 111/240 and 224/240. Thus 116 and 113 outputs respectively are licensed alternatives, not states outside the grammar. Admissibility still does not establish original-intent recovery.

Secondary diagnostics expose capability limits: Phi's cued A-item P1 correctness is 111/120 for constructed left readings versus 66/120 for right readings. Its P1 A-uncued admissibility is 224/240 without filler, 208/240 before filler, and 192/240 after. The files-family after-filler count is 33/80, despite a passing pooled entry guard. These descriptions do not replace the failed primary steering hypothesis. Complete tables are included.

## Interpretation

The protocol distinguishes format failure, states outside all readings, licensed alternatives and constructed-reference matches. It supplies a reusable diagnostic and a reproducible negative/mixed record. It does not demonstrate general transcript robustness, a causal filler-processing mechanism or a useful ASR preprocessing strategy.

The explicit ignore-fillers instruction, greedy selection, constrained JSON, one construction and asymmetric model capability make the steering null uninformative about smaller preference changes. No audio, ASR, naturalness ratings or human ambiguity annotations were collected. Period and newline removal were joint. The bootstrap is an approximation over authored frames, without certified population coverage.

See main.pdf for methods, references, full cell counts and historical failed-attempt accounting. The release reproduces the completed main calculation from retained raw outputs; it does not claim a new GPU inference replication or peer-reviewed publication.
