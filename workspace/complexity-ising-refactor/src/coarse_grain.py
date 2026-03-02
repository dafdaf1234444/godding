"""
Coarse-graining functions for spin configurations.

Implements block coarse-graining via majority vote:
each b×b block is reduced to a single spin based on the sign of the sum.
"""

import numpy as np


def block_coarsegrain(config, block_size):
    """
    Coarse-grain a single spin configuration using majority vote.

    Parameters
    ----------
    config : ndarray of shape (L, L) with values +1/-1
        The fine-grained spin configuration.
    block_size : int
        Side length of each block. L must be divisible by block_size.

    Returns
    -------
    coarse : ndarray of shape (L//b, L//b) with values +1/-1
        Coarse-grained configuration. Each cell is the majority vote
        (sign of sum) of the corresponding block. Ties go to +1.
    """
    L = config.shape[0]
    b = block_size
    assert L % b == 0, f"L={L} not divisible by block_size={b}"

    L_coarse = L // b
    coarse = np.empty((L_coarse, L_coarse), dtype=np.int8)

    for i in range(L_coarse):
        for j in range(L_coarse):
            block = config[i * b:(i + 1) * b, j * b:(j + 1) * b]
            s = block.sum()
            coarse[i, j] = 1 if s >= 0 else -1

    return coarse


def coarsegrain_timeseries(configs, block_size):
    """
    Coarse-grain a time series of spin configurations.

    Parameters
    ----------
    configs : ndarray of shape (N, L, L) with values +1/-1
        Time series of spin configurations.
    block_size : int
        Side length of each block.

    Returns
    -------
    coarse_configs : ndarray of shape (N, L//b, L//b) with values +1/-1
        Coarse-grained time series.
    """
    N = configs.shape[0]
    L = configs.shape[1]
    b = block_size
    L_coarse = L // b

    coarse_configs = np.empty((N, L_coarse, L_coarse), dtype=np.int8)
    for t in range(N):
        coarse_configs[t] = block_coarsegrain(configs[t], b)

    return coarse_configs


def test_coarse_grain():
    """Run sanity checks for coarse-graining."""
    print("=" * 60)
    print("COARSE-GRAINING SANITY CHECKS")
    print("=" * 60)

    all_pass = True

    # Check 1: All-up grid stays all-up
    print("\nCheck 1: All-up 8x8 grid → all-up 4x4 coarse grid (b=2)")
    config = np.ones((8, 8), dtype=np.int8)
    coarse = block_coarsegrain(config, 2)
    passed = np.all(coarse == 1)
    status = "PASS ✓" if passed else "FAIL ✗"
    print(f"  All coarse spins +1? {passed} → {status}")
    all_pass &= passed

    # Check 2: All-down grid stays all-down
    print("\nCheck 2: All-down 8x8 grid → all-down 4x4 coarse grid (b=2)")
    config = -np.ones((8, 8), dtype=np.int8)
    coarse = block_coarsegrain(config, 2)
    passed = np.all(coarse == -1)
    status = "PASS ✓" if passed else "FAIL ✗"
    print(f"  All coarse spins -1? {passed} → {status}")
    all_pass &= passed

    # Check 3: Random grid → roughly half up, half down
    print("\nCheck 3: Random 32x32 grid → 16x16 coarse grid (b=2)")
    rng = np.random.RandomState(42)
    config = rng.choice([-1, 1], size=(32, 32)).astype(np.int8)
    coarse = block_coarsegrain(config, 2)
    frac_up = (coarse == 1).mean()
    # With 2x2 blocks of random ±1, ties (sum=0) go to +1, so expect slightly above 0.5
    passed = 0.3 < frac_up < 0.8
    status = "PASS ✓" if passed else "FAIL ✗"
    print(f"  Fraction of +1 in coarse grid: {frac_up:.3f}, expected ~0.5-0.6 → {status}")
    all_pass &= passed

    # Check 4: Timeseries coarse-graining
    print("\nCheck 4: Timeseries of 5 all-up 8x8 grids → all-up coarse (b=4)")
    configs = np.ones((5, 8, 8), dtype=np.int8)
    coarse_ts = coarsegrain_timeseries(configs, 4)
    passed = coarse_ts.shape == (5, 2, 2) and np.all(coarse_ts == 1)
    status = "PASS ✓" if passed else "FAIL ✗"
    print(f"  Shape: {coarse_ts.shape}, all +1? {np.all(coarse_ts == 1)} → {status}")
    all_pass &= passed

    print(f"\n{'ALL COARSE-GRAINING CHECKS PASSED ✓' if all_pass else 'SOME COARSE-GRAINING CHECKS FAILED ✗'}")
    print("=" * 60)
    return all_pass


def config_to_patch_states(configs, patch_size):
    """Extract non-overlapping patches and encode as integers.

    Parameters
    ----------
    configs : ndarray of shape (N, L, L) with values +1/-1
        Time series of 2D spin configurations.
    patch_size : int
        Side length of each patch.

    Returns
    -------
    states : ndarray of shape (N, n_patches), dtype int32
        Integer-encoded patch states.
    n_states : int
        Number of possible states (2^(patch_size^2)).
    n_patches : int
        Number of patches per configuration.
    """
    N, L, _ = configs.shape
    p = patch_size
    n_patches_per_side = L // p
    n_patches = n_patches_per_side * n_patches_per_side
    n_bits = p * p
    n_states = 2 ** n_bits

    states = np.empty((N, n_patches), dtype=np.int32)
    for t in range(N):
        idx = 0
        for i in range(n_patches_per_side):
            for j in range(n_patches_per_side):
                patch = configs[t, i*p:(i+1)*p, j*p:(j+1)*p]
                bits = ((patch.ravel() + 1) // 2).astype(np.int32)
                state = 0
                for bit in bits:
                    state = (state << 1) | bit
                states[t, idx] = state
                idx += 1
    return states, n_states, n_patches


def config_to_patch_states_2d(configs, patch_size):
    """Extract non-overlapping 2D patches and encode as integers (vectorized).

    Functionally equivalent to config_to_patch_states but uses numpy
    broadcasting instead of loops. 10-50x faster on large grids.

    Parameters
    ----------
    configs : ndarray of shape (N, L, L) with values +1/-1
    patch_size : int

    Returns
    -------
    states, n_states, n_patches : same as config_to_patch_states
    """
    N, L, _ = configs.shape
    p = patch_size
    n_patches_per_side = L // p
    n_patches = n_patches_per_side * n_patches_per_side
    n_bits = p * p
    n_states = 2 ** n_bits

    binary = ((configs + 1) // 2).astype(np.int32)
    reshaped = binary.reshape(N, n_patches_per_side, p, n_patches_per_side, p)
    patches = reshaped.transpose(0, 1, 3, 2, 4)
    patches_flat = patches.reshape(N, n_patches, n_bits)

    powers = (2 ** np.arange(n_bits - 1, -1, -1)).astype(np.int32)
    states = (patches_flat * powers[np.newaxis, np.newaxis, :]).sum(axis=2)

    return states, n_states, n_patches


def config_to_patch_states_1d(configs, patch_size):
    """Extract non-overlapping 1D patches and encode as integers (vectorized).

    For 1D spin chains instead of 2D grids.

    Parameters
    ----------
    configs : ndarray of shape (N, chain_length) with values +1/-1
    patch_size : int

    Returns
    -------
    states : ndarray of shape (N, n_patches), dtype int32
    n_states : int
    n_patches : int
    """
    N, chain_len = configs.shape
    n_patches = chain_len // patch_size
    n_states = 2 ** patch_size

    binary = ((configs + 1) // 2).astype(np.int32)
    trimmed = binary[:, :n_patches * patch_size]
    patches = trimmed.reshape(N, n_patches, patch_size)

    powers = (2 ** np.arange(patch_size - 1, -1, -1)).astype(np.int32)
    states = (patches * powers[np.newaxis, np.newaxis, :]).sum(axis=2)

    return states, n_states, n_patches


if __name__ == "__main__":
    test_coarse_grain()
