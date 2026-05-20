import pytest
from pathlib import Path
from app.services.profiler import profile_file


def _write_csv(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def test_profile_csv_row_and_column_count(tmp_path):
    f = _write_csv(tmp_path / "data.csv", "a,b,c\n1,2,3\n4,5,6\n7,8,9\n")
    result = profile_file(f)
    assert result.row_count == 3
    assert result.column_count == 3


def test_profile_csv_null_count(tmp_path):
    f = _write_csv(tmp_path / "data.csv", "a,b\n1,\n2,3\n,3\n")
    result = profile_file(f)
    col_a = next(c for c in result.columns if c.name == "a")
    col_b = next(c for c in result.columns if c.name == "b")
    assert col_a.null_count == 1
    assert col_b.null_count == 1


def test_profile_numeric_stats(tmp_path):
    f = _write_csv(tmp_path / "data.csv", "val\n10\n20\n30\n")
    result = profile_file(f)
    col = result.columns[0]
    assert col.mean == pytest.approx(20.0)
    assert col.min == 10.0
    assert col.max == 30.0


def test_quality_score_perfect_data(tmp_path):
    f = _write_csv(tmp_path / "data.csv", "a,b\n1,x\n2,y\n3,z\n")
    result = profile_file(f)
    assert result.quality_score == 100


def test_quality_score_penalises_nulls(tmp_path):
    # 50% nulls in column a → quality score should be less than 100
    f = _write_csv(tmp_path / "data.csv", "a,b\n1,x\n,y\n")
    result = profile_file(f)
    assert result.quality_score < 100


def test_profile_unsupported_type_raises(tmp_path):
    f = tmp_path / "data.txt"
    f.write_text("hello")
    with pytest.raises(ValueError, match="Cannot profile"):
        profile_file(f)


def test_sample_values_are_json_serializable(tmp_path):
    import json
    f = _write_csv(tmp_path / "data.csv", "val\n1\n2\n3\n")
    result = profile_file(f)
    # Should not raise — all values must be native Python types
    json.dumps([c.sample_values for c in result.columns])
