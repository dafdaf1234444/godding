#!/usr/bin/env python3
"""Compare fractional-OU vs mixture-of-OU on lesson-Sharpe series.

Is observed long-memory (H~0.77, ACF plateau 0.94) genuine or apparent
from superposition of OU processes with different time constants?

Outputs JSON to stdout.  Requires only numpy + scipy.
Usage: python3 tools/fOU_vs_mixture.py
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
import numpy as np
from scipy.optimize import minimize

REPO = Path(__file__).resolve().parent.parent
SHARPE_RE = re.compile(r"Sharpe\*{0,2}:\s*(\d+)")
TARGET_PLATEAU = 0.940

def extract_sharpe() -> np.ndarray:
    d = REPO / "memory" / "lessons"
    pairs = []
    for sub in [d, d / "archive"]:
        if not sub.exists(): continue
        for p in sub.glob("L-*.md"):
            m = re.search(r"(\d+)", p.stem)
            if not m: continue
            sm = SHARPE_RE.search(p.read_text(encoding="utf-8", errors="replace"))
            if sm: pairs.append((int(m.group(1)), int(sm.group(1))))
    pairs.sort()
    if not pairs:
        print(json.dumps({"error": "no Sharpe values found"})); sys.exit(1)
    return np.array([v for _, v in pairs], dtype=float)

def acf(x, L=10):
    xm = x - x.mean(); c0 = np.dot(xm, xm) / len(x)
    if c0 == 0: return np.zeros(L)
    return np.array([np.dot(xm[:len(x)-k], xm[k:]) / len(x) / c0 for k in range(1, L+1)])

def plateau_ratio(a):
    return float(np.mean(a[5:]) / a[0]) if len(a) > 5 and a[0] != 0 else 0.0

# ── Fractional OU: Whittle MLE on periodogram ───────────────────────
def _periodogram(x):
    xm = x - x.mean(); ft = np.fft.rfft(xm)[1:]
    w = np.fft.rfftfreq(len(x))[1:] * 2 * np.pi
    return w, np.abs(ft)**2 / len(x)

def _fou_spec(w, H, theta, s2):
    return s2 * np.abs(w)**(1 - 2*H) / (theta**2 + w**2)

def _whittle(p, w, I):
    H, lt, ls = p
    if not 0.5 < H < 1.0: return 1e12
    S = _fou_spec(w, H, np.exp(np.clip(lt, -10, 10)), np.exp(np.clip(ls, -20, 40)))
    S = np.maximum(S, 1e-30)
    return float(np.sum(np.log(S) + I / S))

def _fou_acf(H, theta, s2, n, L=10):
    nf = min(n, 2048); w = np.arange(1, nf//2+1) * 2*np.pi/nf
    S = _fou_spec(w, H, theta, s2)
    cov = [np.sum(S * np.cos(w * k)) for k in range(L+1)]
    return np.array(cov[1:]) / cov[0] if cov[0] != 0 else np.zeros(L)

def fit_fou(x):
    w, I = _periodogram(x)
    best = None
    for H0 in [0.6, 0.75, 0.85, 0.92]:
        for lt0 in [-2, 0, 2]:
            ls0 = np.log(np.var(x) + 1e-6)
            r = minimize(_whittle, [H0, lt0, ls0], args=(w, I), method="Nelder-Mead",
                         options={"maxiter": 8000, "xatol": 1e-8, "fatol": 1e-8})
            if best is None or r.fun < best.fun: best = r
    H = np.clip(best.x[0], 0.501, 0.999)
    theta, s2 = np.exp(best.x[1]), np.exp(best.x[2])
    k = 3; nll = best.fun
    pa = _fou_acf(H, theta, s2, len(x))
    return {"model": "fOU", "H": round(float(H), 4), "theta": round(float(theta), 4),
            "sigma2": round(float(s2), 4), "nll": round(nll, 2),
            "AIC": round(2*nll + 2*k, 2), "BIC": round(2*nll + k*np.log(len(x)), 2),
            "k": k, "pred_acf": [round(float(v), 4) for v in pa],
            "pred_plateau": round(plateau_ratio(pa), 4)}

# ── Mixture of OU: EM on transitions ────────────────────────────────
def _ou_logpdf(xn, xc, mu, phi, nv):
    return -0.5*np.log(2*np.pi*nv + 1e-30) - 0.5*(xn - mu - phi*(xc - mu))**2/(nv + 1e-30)

def fit_mix(x, K, iters=200):
    xc, xn = x[:-1], x[1:]; T = len(xc)
    best_ll, best_p = -np.inf, None
    for trial in range(6):
        rng = np.random.RandomState(42 + trial)
        w = np.ones(K)/K; mu = x.mean() + rng.randn(K)*x.std()*0.3
        phi = np.clip(np.array([0.1 + 0.3*i for i in range(K)]) + rng.rand(K)*0.1, 0.01, 0.99)
        nv = np.full(K, np.var(np.diff(x))*0.5) + rng.rand(K)*0.1; prev = -1e30
        for _ in range(iters):
            lr = np.array([np.log(w[j]+1e-30) + _ou_logpdf(xn, xc, mu[j], phi[j], nv[j]) for j in range(K)])
            mx = lr.max(0); ln = mx + np.log(np.exp(lr - mx).sum(0))
            resp = np.exp(lr - ln); ll = ln.sum()
            if abs(ll - prev) < 1e-6: break
            prev = ll
            Nj = resp.sum(1) + 1e-10; w = Nj / T
            for j in range(K):
                r = resp[j]; ws = r.sum() + 1e-30
                wx, wy = (r*xc).sum()/ws, (r*xn).sum()/ws
                wxx, wxy = (r*xc**2).sum()/ws, (r*xc*xn).sum()/ws
                b = np.clip((wxy - wx*wy) / (wxx - wx**2 + 1e-30), 0.01, 0.999)
                a = wy - b*wx; phi[j] = b; mu[j] = a/(1-b+1e-30)
                nv[j] = max((r*(xn - mu[j] - b*(xc - mu[j]))**2).sum()/ws, 1e-6)
        if ll > best_ll: best_ll, best_p = ll, (w.copy(), mu.copy(), phi.copy(), nv.copy())
    w, mu, phi, nv = best_p
    tau = -1.0 / np.log(np.clip(phi, 1e-6, 0.999))
    # Simulate ACF
    rng = np.random.RandomState(123); acfs = []
    for _ in range(60):
        s = np.zeros(len(x)); s[0] = np.sum(w*mu)
        for t in range(1, len(x)):
            j = rng.choice(K, p=w)
            s[t] = mu[j] + phi[j]*(s[t-1]-mu[j]) + rng.randn()*np.sqrt(nv[j])
        acfs.append(acf(s))
    pa = np.mean(acfs, axis=0)
    kp = K*4 - 1; nll = -best_ll
    comps = [{"w": round(float(w[j]),3), "mu": round(float(mu[j]),2),
              "tau": round(float(tau[j]),2), "phi": round(float(phi[j]),4),
              "nv": round(float(nv[j]),4)} for j in np.argsort(-w)]
    return {"model": f"mix-OU-{K}", "K": K, "components": comps,
            "nll": round(nll, 2), "AIC": round(2*nll + 2*kp, 2),
            "BIC": round(2*nll + kp*np.log(len(x)), 2), "k": kp,
            "pred_acf": [round(float(v), 4) for v in pa],
            "pred_plateau": round(plateau_ratio(pa), 4)}

# ── Main ─────────────────────────────────────────────────────────────
def main():
    x = extract_sharpe(); n = len(x)
    oa = acf(x); op = plateau_ratio(oa)
    models = [fit_fou(x), fit_mix(x, 2), fit_mix(x, 3)]
    best = min(models, key=lambda m: m["BIC"])
    diag = {m["model"]: {"plateau_err": round(abs(m["pred_plateau"] - op), 4),
            "acf_rmse": round(float(np.sqrt(np.mean((np.array(m["pred_acf"]) - oa)**2))), 4)}
            for m in models}
    # Note: fOU uses Whittle spectral NLL, mixtures use transition NLL —
    # AIC/BIC not directly comparable across families. Compare within-family
    # and use ACF diagnostics for cross-family comparison.
    best_acf = min(models, key=lambda m: diag[m["model"]]["acf_rmse"])
    print(json.dumps({"series": {"n": n, "mean": round(float(x.mean()), 3),
        "std": round(float(x.std()), 3)},
        "observed_acf": [round(float(v), 4) for v in oa],
        "observed_plateau": round(op, 4), "target_plateau": TARGET_PLATEAU,
        "models": {m["model"]: m for m in models},
        "best_BIC_within_family": {"spectral": "fOU",
            "transition": min([m for m in models if m["model"]!="fOU"],
                              key=lambda m: m["BIC"])["model"]},
        "best_acf_fit": best_acf["model"], "acf_diagnostic": diag,
        "conclusion": ("genuine_long_memory" if best_acf["model"] == "fOU"
                       else "apparent_long_memory_from_mixture")}, indent=2))

if __name__ == "__main__":
    main()
