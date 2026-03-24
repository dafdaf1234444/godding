import json
from pathlib import Path

import tools.market_predict as market_predict


def _write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def test_score_uses_latest_interim_artifact_when_no_resolved(tmp_path, monkeypatch, capsys):
    registry = tmp_path / "registry.json"
    forecast_dir = tmp_path / "forecasting"
    _write_json(registry, {
        "predictions": [
            {"id": "PRED-0001", "status": "OPEN", "confidence": 0.4},
            {"id": "PRED-0002", "status": "OPEN", "confidence": 0.6},
            {"id": "PRED-0003", "status": "OPEN", "confidence": 0.5},
            {"id": "PRED-0004", "status": "OPEN", "confidence": 0.7},
        ],
        "next_id": 5,
        "metadata": {},
    })
    _write_json(forecast_dir / "f-fore1-scoring-s520.json", {
        "session": "S520",
        "data_date": "2026-03-23",
        "actual": {
            "predictions_scored": {
                "PRED-0001_SPY_BEAR": {"status": "AGAINST", "conf": 0.4},
                "PRED-0002_XLE_BULL": {"status": "EARLY", "conf": 0.6},
                "PRED-0003_TLT_BULL": {"status": "ON_TRACK", "conf": 0.5},
                "PRED-0004_GLD_BULL": {"status": "NO_DATA", "conf": 0.7},
            }
        },
    })

    monkeypatch.setattr(market_predict, "REGISTRY", registry)
    monkeypatch.setattr(market_predict, "FORECAST_DIR", forecast_dir)

    market_predict.score(None)
    out = capsys.readouterr().out

    assert "SWARM INVESTOR SCORECARD (INTERIM)" in out
    assert "Interim fallback:" in out
    assert "Scored open predictions: 3/4" in out
    assert "Direction accuracy: 66.7% (2/3)" in out
    assert "AGAINST: 1" in out
    assert "EARLY: 1" in out
    assert "ON_TRACK: 1" in out


def test_score_stays_empty_without_resolved_or_interim_artifact(tmp_path, monkeypatch, capsys):
    registry = tmp_path / "registry.json"
    _write_json(registry, {
        "predictions": [{"id": "PRED-0001", "status": "OPEN", "confidence": 0.4}],
        "next_id": 2,
        "metadata": {},
    })

    monkeypatch.setattr(market_predict, "REGISTRY", registry)
    monkeypatch.setattr(market_predict, "FORECAST_DIR", tmp_path / "missing")

    market_predict.score(None)
    out = capsys.readouterr().out

    assert "No resolved predictions yet." in out
    assert "Open predictions: 1" in out
    assert "INTERIM" not in out
