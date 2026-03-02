"""
Kuramoto model of coupled oscillators.

N oscillators with natural frequencies drawn from a standard normal distribution,
coupled through sine interactions with coupling strength K.
Includes small additive noise (Euler-Maruyama integration).

The synchronization transition occurs at K_c = 2/(pi * g(0))
where g is the density of natural frequencies.
For standard normal: g(0) = 1/sqrt(2*pi) ≈ 0.399, so K_c ≈ 1.596.
"""

import numpy as np


def simulate_kuramoto(N, K, omega, dt, n_steps, n_equilib, seed=42, sigma=0.1):
    """
    Simulate the Kuramoto model with Euler-Maruyama integration.

    Parameters
    ----------
    N : int
        Number of oscillators.
    K : float
        Coupling strength.
    omega : ndarray of shape (N,)
        Natural frequencies of each oscillator.
    dt : float
        Timestep for integration.
    n_steps : int
        Number of timesteps to record AFTER equilibration.
    n_equilib : int
        Number of timesteps for equilibration.
    seed : int
        Random seed for noise.
    sigma : float
        Noise strength (standard deviation of Wiener increments).

    Returns
    -------
    phases : ndarray of shape (n_steps, N)
        Phase of each oscillator at each recorded timestep, in [0, 2*pi).
    order_param : ndarray of shape (n_steps,)
        Kuramoto order parameter r(t) = |mean(exp(i*theta))|.
    """
    rng = np.random.RandomState(seed)

    # Initialize phases uniformly in [0, 2*pi)
    theta = rng.uniform(0, 2 * np.pi, size=N)

    sqrt_dt = np.sqrt(dt)

    def step(theta):
        """One Euler-Maruyama step."""
        # Compute coupling: (K/N) * sum_j sin(theta_j - theta_i)
        # Using vectorized computation
        diff = theta[np.newaxis, :] - theta[:, np.newaxis]  # diff[i,j] = theta_j - theta_i
        coupling = (K / N) * np.sin(diff).sum(axis=1)

        # Deterministic drift + noise
        dtheta = (omega + coupling) * dt + sigma * sqrt_dt * rng.randn(N)
        theta_new = (theta + dtheta) % (2 * np.pi)
        return theta_new

    # Equilibration
    for _ in range(n_equilib):
        theta = step(theta)

    # Recording
    phases = np.empty((n_steps, N))
    order_param = np.empty(n_steps)

    for t in range(n_steps):
        theta = step(theta)
        phases[t] = theta

        # Order parameter: r = |<e^{i*theta}>|
        z = np.exp(1j * theta)
        order_param[t] = np.abs(z.mean())

    return phases, order_param


def test_kuramoto():
    """Run sanity checks for the Kuramoto model."""
    print("=" * 60)
    print("KURAMOTO MODEL SANITY CHECKS")
    print("=" * 60)

    all_pass = True
    N = 50
    rng = np.random.RandomState(42)
    omega = rng.randn(N)

    # Check 1: Weak coupling → incoherent (low r)
    print("\nCheck 1: K=0.5 (weak coupling) → low order parameter")
    _, r = simulate_kuramoto(N, K=0.5, omega=omega, dt=0.05,
                             n_steps=2000, n_equilib=5000, seed=42)
    mean_r = r.mean()
    passed = mean_r < 0.4
    status = "PASS ✓" if passed else "FAIL ✗"
    print(f"  Mean r = {mean_r:.4f}, expected < 0.4 → {status}")
    all_pass &= passed

    # Check 2: Strong coupling → coherent (high r)
    print("\nCheck 2: K=3.0 (strong coupling) → high order parameter")
    _, r = simulate_kuramoto(N, K=3.0, omega=omega, dt=0.05,
                             n_steps=2000, n_equilib=5000, seed=42)
    mean_r = r.mean()
    passed = mean_r > 0.6
    status = "PASS ✓" if passed else "FAIL ✗"
    print(f"  Mean r = {mean_r:.4f}, expected > 0.6 → {status}")
    all_pass &= passed

    # Check 3: Order parameter in [0, 1]
    print("\nCheck 3: Order parameter always in [0, 1]")
    passed = r.min() >= 0 and r.max() <= 1.0
    status = "PASS ✓" if passed else "FAIL ✗"
    print(f"  r_min = {r.min():.4f}, r_max = {r.max():.4f} → {status}")
    all_pass &= passed

    # Check 4: Phases in [0, 2*pi)
    print("\nCheck 4: Phases in [0, 2*pi)")
    phases, _ = simulate_kuramoto(N, K=1.5, omega=omega, dt=0.05,
                                   n_steps=100, n_equilib=1000, seed=42)
    passed = phases.min() >= 0 and phases.max() < 2 * np.pi
    status = "PASS ✓" if passed else "FAIL ✗"
    print(f"  phase_min = {phases.min():.4f}, phase_max = {phases.max():.4f} → {status}")
    all_pass &= passed

    print(f"\n{'ALL KURAMOTO CHECKS PASSED ✓' if all_pass else 'SOME KURAMOTO CHECKS FAILED ✗'}")
    print("=" * 60)
    return all_pass


if __name__ == "__main__":
    test_kuramoto()
