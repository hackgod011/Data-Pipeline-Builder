import pytest
from app.services.schema_detector import detect_schema, SchemaResult

SMALL_CSV = b"name,age,salary\nAlice,30,50000\nBob,,60000\nCharlie,25,45000\n"
THRESHOLD_BYTES = 10 * 1024 * 1024  # 10 MB


def test_detect_csv_returns_schema_result(tmp_path):
    f = tmp_path / "test.csv"
    f.write_bytes(SMALL_CSV)
    result = detect_schema(f, file_size_bytes=len(SMALL_CSV))
    assert isinstance(result, SchemaResult)
    assert result.row_count == 3
    assert result.column_count == 3


def test_detect_csv_null_count(tmp_path):
    f = tmp_path / "test.csv"
    f.write_bytes(SMALL_CSV)
    result = detect_schema(f, file_size_bytes=len(SMALL_CSV))
    age_col = next(c for c in result.columns if c.name == "age")
    assert age_col.null_count == 1


def test_detect_csv_sample_values(tmp_path):
    f = tmp_path / "test.csv"
    f.write_bytes(SMALL_CSV)
    result = detect_schema(f, file_size_bytes=len(SMALL_CSV))
    name_col = next(c for c in result.columns if c.name == "name")
    assert "Alice" in name_col.sample_values
    assert len(name_col.sample_values) <= 5


def test_detect_json_file(tmp_path):
    f = tmp_path / "data.json"
    f.write_text('[{"city":"Paris","pop":2000000},{"city":"Lyon","pop":500000}]')
    result = detect_schema(f, file_size_bytes=f.stat().st_size)
    assert result.column_count == 2
    assert result.row_count == 2


def test_unsupported_file_type_raises(tmp_path):
    f = tmp_path / "data.txt"
    f.write_text("hello")
    with pytest.raises(ValueError, match="Unsupported"):
        detect_schema(f, file_size_bytes=f.stat().st_size)
