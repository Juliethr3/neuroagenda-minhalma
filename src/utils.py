"""Utilidades estadísticas para el EDA de inasistencia a citas (no-show).

Todas las funciones son puras (no modifican sus entradas) y están
documentadas con su fórmula para facilitar la revisión metodológica.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def wilson_ci(k: np.ndarray | int, n: np.ndarray | int, alpha: float = 0.05):
    """Intervalo de Wilson para una proporción k/n.

    Preferible al intervalo de Wald cuando p es cercana a 0 o 1 o n es pequeño.
    Devuelve (p, li, ls).
    """
    k = np.asarray(k, dtype=float)
    n = np.asarray(n, dtype=float)
    z = stats.norm.ppf(1 - alpha / 2)
    p = np.divide(k, n, out=np.zeros_like(k), where=n > 0)
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return p, centre - half, centre + half


def rate_table(df: pd.DataFrame, col: str, target: str = "no_show") -> pd.DataFrame:
    """Tasa de no-show por categoría con IC de Wilson al 95 %."""
    g = df.groupby(col, observed=True)[target].agg(["sum", "count"])
    p, lo, hi = wilson_ci(g["sum"].values, g["count"].values)
    out = pd.DataFrame(
        {"n": g["count"], "no_show": g["sum"], "tasa": p, "ic95_inf": lo, "ic95_sup": hi},
        index=g.index,
    )
    return out


def cramers_v(x: pd.Series, y: pd.Series) -> tuple[float, float, float]:
    """Chi-cuadrado de independencia y V de Cramér con corrección de sesgo
    (Bergsma, 2013). Devuelve (chi2, p_valor, V)."""
    ct = pd.crosstab(x, y)
    chi2, p, _, _ = stats.chi2_contingency(ct, correction=False)
    n = ct.values.sum()
    r, k = ct.shape
    phi2 = chi2 / n
    phi2c = max(0.0, phi2 - (k - 1) * (r - 1) / (n - 1))
    rc = r - (r - 1) ** 2 / (n - 1)
    kc = k - (k - 1) ** 2 / (n - 1)
    v = np.sqrt(phi2c / max(1e-12, min(kc - 1, rc - 1)))
    return chi2, p, v


def mann_whitney_rb(a: np.ndarray, b: np.ndarray) -> tuple[float, float, float]:
    """U de Mann-Whitney y correlación rank-biserial r = 1 - 2U/(n1 n2).
    r > 0 indica valores mayores en `a`."""
    u, p = stats.mannwhitneyu(a, b, alternative="two-sided")
    r = 2 * u / (len(a) * len(b)) - 1
    return u, p, r


def mantel_haenszel_or(df: pd.DataFrame, exposure: str, outcome: str, strata: str):
    """OR de Mantel-Haenszel ajustado por estratos y su IC 95 %
    (varianza de Robins-Breslow-Greenland)."""
    num = den = 0.0
    P_R = P_S_Q_R = Q_S = 0.0
    for _, s in df.groupby(strata, observed=True):
        a = ((s[exposure] == 1) & (s[outcome] == 1)).sum()
        b = ((s[exposure] == 1) & (s[outcome] == 0)).sum()
        c = ((s[exposure] == 0) & (s[outcome] == 1)).sum()
        d = ((s[exposure] == 0) & (s[outcome] == 0)).sum()
        n = a + b + c + d
        if n == 0 or (a + b) == 0 or (c + d) == 0:
            continue
        R, S = a * d / n, b * c / n
        P, Q = (a + d) / n, (b + c) / n
        num += R
        den += S
        P_R += P * R
        P_S_Q_R += P * S + Q * R
        Q_S += Q * S
    or_mh = num / den
    var_log = P_R / (2 * num**2) + P_S_Q_R / (2 * num * den) + Q_S / (2 * den**2)
    se = np.sqrt(var_log)
    return or_mh, np.exp(np.log(or_mh) - 1.96 * se), np.exp(np.log(or_mh) + 1.96 * se)


def logit_or_table(X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
    """Regresión logística no penalizada (sklearn) con errores estándar
    obtenidos de la matriz de información de Fisher: Var(β) = (XᵀWX)⁻¹.
    Devuelve OR, IC 95 % y p-valor de Wald por predictor."""
    from sklearn.linear_model import LogisticRegression

    model = LogisticRegression(penalty=None, max_iter=5000)
    model.fit(X.values, y.values)
    Xd = np.column_stack([np.ones(len(X)), X.values])
    beta = np.concatenate([model.intercept_, model.coef_.ravel()])
    p = 1 / (1 + np.exp(-Xd @ beta))
    W = p * (1 - p)
    cov = np.linalg.inv(Xd.T @ (Xd * W[:, None]))
    se = np.sqrt(np.diag(cov))
    z = beta / se
    pval = 2 * stats.norm.sf(np.abs(z))
    names = ["intercepto"] + list(X.columns)
    out = pd.DataFrame(
        {
            "beta": beta,
            "OR": np.exp(beta),
            "ic95_inf": np.exp(beta - 1.96 * se),
            "ic95_sup": np.exp(beta + 1.96 * se),
            "p_valor": pval,
        },
        index=names,
    )
    return out.drop(index="intercepto")
