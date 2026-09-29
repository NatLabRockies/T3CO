from pathlib import Path

import pandas as pd
import pytest

from t3co.utils.print_class_objects import (
    custom_default,
    get_path_object,
    handle_nan,
    obj_to_string,
    remove_df_attrs,
    to_flat_dict,
)

# Create some dummy classes to test object serialization and flattening.


class SimpleObject:
    a: int
    b: str

    def __init__(self, a, b):
        self.a = a
        self.b = b
        self.extra = "dynamic"


class NestedObject:
    x: int
    y: str

    def __init__(self, x, y):
        self.x = x
        self.y = y


class OuterObject:
    nested: NestedObject
    c: int

    def __init__(self, nested, c):
        self.nested = nested
        self.c = c
        self.dynamic = "extra"


# ============================
# Tests for obj_to_string
# ============================


def test_obj_to_string_single_object():
    obj = SimpleObject(1, "test")
    result = obj_to_string(obj)
    # Check that the output contains the class name and all attribute values.
    assert "SimpleObject" in result
    assert "a = 1" in result
    assert "b = test" in result
    assert "extra = dynamic" in result


def test_obj_to_string_list():
    obj1 = SimpleObject(1, "one")
    obj2 = SimpleObject(2, "two")
    result = obj_to_string([obj1, obj2])
    # Check that the result is a string representation of a list (starts with '[' and ends with ']')
    assert result.startswith("[")
    assert result.endswith("]")
    # Check that both objects' attributes appear in the string
    assert "a = 1" in result
    assert "a = 2" in result


# ============================
# Tests for handle_nan
# ============================


def test_handle_nan_float():
    nan_val = float("nan")
    result = handle_nan(nan_val)
    assert result is None


def test_handle_nan_dict():
    data = {"key1": 123, "key2": float("nan")}
    result = handle_nan(data)
    assert result["key1"] == 123
    assert result["key2"] is None


def test_handle_nan_list():
    data = [1, float("nan"), 3]
    result = handle_nan(data)
    assert result[0] == 1
    assert result[1] is None
    assert result[2] == 3


# ============================
# Tests for custom_default
# ============================


def test_custom_default_path(tmp_path: Path):
    # tmp_path is a built-in pytest fixture that gives a temporary directory as a Path object.
    test_file = tmp_path / "test.txt"
    result = custom_default(test_file)
    assert result == str(test_file)


def test_custom_default_dataframe():
    df = pd.DataFrame({"a": [1, 2, 3]})
    result = custom_default(df)
    # For DataFrames, custom_default should return None.
    assert result is None


def test_custom_default_object():
    obj = SimpleObject(42, "value")
    result = custom_default(obj)
    # custom_default should return a dict of the object's __dict__
    assert isinstance(result, dict)
    assert result.get("a") == 42
    assert result.get("b") == "value"
    assert result.get("extra") == "dynamic"


# ============================
# Tests for to_flat_dict
# ============================


def test_to_flat_dict_with_nested_object():
    nested = NestedObject(100, "hello")
    outer = OuterObject(nested, 42)
    flat = to_flat_dict(outer)
    # Expected keys:
    # - For the nested object: keys "nested_x" and "nested_y"
    # - For the outer object: keys "c" and "dynamic"
    expected = {
        "nested_x": 100,
        "nested_y": "hello",
        "c": 42,
        "dynamic": "extra",
    }
    # Check that every expected key/value pair is in the flattened dictionary.
    for key, value in expected.items():
        assert key in flat, f"Missing key: {key}"
        assert flat[key] == value, f"Value mismatch for key: {key}"


def test_to_flat_dict_without_prefix():
    # When include_prefix is False and prefix is empty, the behavior should be the same.
    nested = NestedObject(5, "test")
    outer = OuterObject(nested, 99)
    flat = to_flat_dict(outer, include_prefix=False)
    expected = {
        "x": 5,
        "y": "test",
        "c": 99,
        "dynamic": "extra",
    }
    for key, value in expected.items():
        assert key in flat
        assert flat[key] == value


# ============================
# Tests for remove_df_attrs
# ============================


def test_remove_df_attrs():
    class DataHolder:
        def __init__(self):
            self.df = pd.DataFrame({"a": [1, 2]})
            self.value = 10

    obj = DataHolder()
    # Ensure the attribute exists before removal.
    assert hasattr(obj, "df")
    remove_df_attrs(obj)
    # After removal, df should no longer exist while value should remain.
    assert not hasattr(obj, "df")
    assert hasattr(obj, "value")
    assert obj.value == 10


def test_get_path_object_strict(tmp_path):
    missing = tmp_path / "missing"
    with pytest.raises(FileNotFoundError):
        get_path_object(str(missing))
    assert get_path_object(str(missing), strict=False) == missing.resolve()
