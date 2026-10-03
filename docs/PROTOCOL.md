# Measurement protocol and provenance

Completed main run: 20261002-182357. Original research source commit: 9e34d608c7a96a34c6ee7680878505fedc296bbc. The source hash identifies the private original execution snapshot; that history is not this public repository's commit graph. Public copied-file hashes are provided separately.

Main input SHA-256: e2d5f827d4d21728ac60aca3b4c9c833e4ea31e9d1bae1bf4aee86b4ef570bda. It matches the test pool frozen before calibration. Selection used clean/cued development capability and throughput only; all 240 pairs were selected. No item filtering by test outcomes. Calibration has 1,728 outputs. Complete main journals contain 5,760 outputs per model.

P1 is raw prompt_id 0; P2 is prompt_id 1. The frozen summary has legacy `cells_*depths`/`override_descriptive` keys whose nested 0/1 identify prompt IDs. The public CSV labels them explicitly. No renamed/re-scored frozen summary is substituted.

E1: paired R-cued minus R-uncued exact-state correctness, no filler. E2: paired unconditional right commitment before minus after filler, A-uncued. Invalid outputs count as zero commitments; every selected pair enters the denominator. Four primary model/endpoint tests use fixed Holm adjustment. P2 and family/direction diagnostics are secondary. A-uncued has no unique-state correctness measure.

Frozen statistics: 10,000 empirical hierarchical resamples, template then generated base (10 per frame), seed 20261002; percentile approximate 95% intervals; centered two-sided add-one p-values with tolerance 1e-12. E1 practical region ±5 pp. Degenerate bootstraps are descriptive and receive p=1 for the frozen family. Approximate p-values do not yield an exact family-error guarantee; intervals inside the region are not certified population equivalence. All 24 surface frames and all ten bases per frame remain in the analysis.

Generation: one pinned model per Tesla T4, fp16, greedy, context 2048, output cap 512, batch64, seed20261002, vLLM0.11.2/torch2.9.0/transformers4.57.6/xgrammar0.1.25. Both engine and request use fixed separators, fallback disabled and disable_any_whitespace=True. This allows a single space after commas/colons; it is not whitespace-free JSON. The retained raw receipt contains the engine initialization strings. No output is truncated or rewritten before frozen scoring.

The main record is complete. The filler-steering hypothesis is unsupported; E2 is floor-degenerate and confounded with the ignore-fillers instruction. Earlier v2/v3 failed calibration and v4 incomplete infrastructure attempts are described in the technical-note appendix, never pooled into this main result. This public package replays only the completed main analysis, not all historical attempts or cloud generation.
