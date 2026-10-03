# v0.1.0 — synthetic command diagnostic and reproducible technical note

Includes original synthetic command inputs, two independent grammar parsers, whole-state scoring, frozen main statistics, all 11,520 model outputs, full cell/family tables, and an English/Chinese guide with a technical-note PDF.

The release archive contains the full data and retained outputs. Run `python tools/fetch_artifacts.py` to retrieve and verify it, then replay the main analysis on CPU. No GPU or model weights are needed for reconstruction. The dataset has no real ASR, audio, human annotation or self-correction examples. The filler-steering hypothesis was unsupported; the negative/mixed results and measurement limitations are retained.

Code MIT; authored synthetic inputs CC BY 4.0. The source repository and data asset have separate hashes so frozen research outputs remain identifiable.
