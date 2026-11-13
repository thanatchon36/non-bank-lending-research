import numpy as np
import pytest

from lendwatch.mse import chao_lower_bound, chapman, estimate_population, loglinear_mse


def test_chapman_known_value():
    # 100 on list A, 80 on list B, 40 on both -> Lincoln-Petersen 200, Chapman ~198.5
    assert chapman(100, 80, 40)["N"] == pytest.approx(198.54, abs=0.01)


def test_loglinear_recovers_independent_lists():
    rng = np.random.default_rng(1)
    capture = (rng.random((1000, 4)) < [0.35, 0.25, 0.30, 0.15]).astype(int)
    est = loglinear_mse(capture, ["a", "b", "c", "d"])
    lo, hi = est["ci95"]
    assert lo < 1000 < hi
    assert est["N"] == pytest.approx(1000, rel=0.08)


def test_loglinear_handles_dependent_lists():
    rng = np.random.default_rng(1)
    z = rng.random(1000) < 0.5                      # lists a and b share a hidden driver
    capture = np.column_stack([rng.random(1000) < np.where(z, 0.6, 0.15),
                               rng.random(1000) < np.where(z, 0.5, 0.10),
                               rng.random(1000) < 0.30, rng.random(1000) < 0.15]).astype(int)
    est = loglinear_mse(capture, ["a", "b", "c", "d"])
    assert "axb" in est["top_models"][0]["interactions"]
    assert est["N"] == pytest.approx(1000, rel=0.12)


def test_estimators_side_by_side():
    rng = np.random.default_rng(3)
    capture = (rng.random((400, 3)) < [0.4, 0.3, 0.2]).astype(int)
    out = estimate_population(capture, ["a", "b", "c"])
    assert out["n_observed"] == int((capture.sum(axis=1) > 0).sum())
    assert out["chao_lower_bound"]["N"] >= out["n_observed"]
    assert chao_lower_bound(capture[capture.sum(axis=1) > 0])["f1"] > 0
