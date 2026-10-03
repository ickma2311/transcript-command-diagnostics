"""Frozen10k hierarchical bootstrap and fixed-four Holm; no method shopping."""
import numpy as np


def hierarchical(pairs, seed=20261002, resamples=10000):
    """pairs: (actual surface-template ID, pair ID, fixed depth, contrast).

    Balanced complete blocks yield equal counts per template. Resample surface
    templates, then base pairs within EACH fixed depth. Never change depth
    allocation or turn depth into extra surface-template clusters.
    """
    clusters = {}
    for template, pair, depth, value in pairs:
        group = clusters.setdefault(template, {}).setdefault(depth, {})
        if pair in group:
            raise ValueError('Repeated base pair in endpoint')
        group[pair] = value
    if len(clusters) < 2:
        raise ValueError('Insufficient actual surface-template clusters')
    depths = sorted(next(iter(clusters.values())))
    if any(sorted(group) != depths for group in clusters.values()):
        raise ValueError('Unequal fixed depth strata across templates')
    counts = {len(v) for group in clusters.values() for v in group.values()}
    if len(counts) != 1:
        raise ValueError('Endpoint not a balanced full-template block; do not silently reweight')
    data = np.array([[[clusters[t][depth][pair] for pair in sorted(clusters[t][depth])]
                     for depth in depths] for t in sorted(clusters)], dtype=float)
    k, d, m = data.shape
    observed = float(data.mean())
    rng = np.random.default_rng(seed)
    samples = []
    for start in range(0, resamples, 500):
        count = min(500, resamples-start)
        template_draw = rng.integers(k, size=(count, k, 1, 1))
        depth_axis = np.arange(d).reshape(1, 1, d, 1)
        pair_draw = rng.integers(m, size=(count, k, d, m))
        samples.extend(data[template_draw, depth_axis, pair_draw].mean(axis=(1, 2, 3)).tolist())
    samples = np.array(samples)
    low, high = (float(v) for v in np.quantile(samples, [.025, .975]))
    deviation = np.abs(samples-observed)
    p = float((1+np.count_nonzero(deviation >= abs(observed)-1e-12))/(resamples+1))
    degenerate = bool(np.ptp(samples) < 1e-12)
    return {'difference': observed, 'ci95': [low, high], 'p_raw_centered': p,
            'templates': k, 'pairs': k*d*m, 'pairs_per_template': d*m,
            'fixed_depths': depths, 'pairs_per_template_depth': m,
            'resamples': resamples, 'seed': seed, 'bootstrap_degenerate': degenerate,
            'uncertainty_scope': 'declared surface frames and generated base assignments with fixed depth allocation; empirical hierarchical approximation'}


def holm_four(pvalues):
    if len(pvalues) != 4:
        raise ValueError('Primary multiplicity family must remain4, including ineligible tests')
    if any(not 0 <= p <= 1 for p in pvalues):
        raise ValueError('Invalid p value')
    order = sorted(range(4), key=lambda index: pvalues[index])
    adjusted = [None]*4
    running = 0.
    for rank, index in enumerate(order):
        running = max(running, (4-rank)*pvalues[index])
        adjusted[index] = min(1., running)
    return adjusted
