# Verification scope

The release preserves the completed main inputs, raw outputs, scored outputs, model revisions, schemas, selection and frozen scoring/statistical code. `provenance/COPIED_FILES.json` lists unchanged source hashes; `ARTIFACTS.json` pins distributed data. CPU replay independently checks identities and byte equality with the recorded outputs.

The manuscript's numbers and tables were reconstructed from raw journals, and citations were checked against primary records. Computational agreement validates the retained calculation, not general ASR behavior, human language semantics, causal attribution, novelty or publication-worthiness. The bounded technical note remains a negative/mixed result with explicit measurement limitations.

New tools in this repository provide artifact fetching, an illustrative demo, same-input prediction scoring and safe fixture regeneration. They are convenience interfaces and do not change the frozen main analysis. Demo predictions are explicitly constructed examples.

The local freeze is represented by a clearly labeled selected-field export in provenance/MAIN_FREEZE_PUBLIC.json. Its times and original commit IDs are author-held provenance, not independent external registration. The v0.1.1 report update changes author metadata and its administrative reproducibility/release paragraph. Scientific text, numerical results and citation passages are unchanged. The original v0.1.0 report remains in version history.
