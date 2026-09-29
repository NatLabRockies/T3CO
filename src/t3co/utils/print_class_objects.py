import json
from collections import OrderedDict
from pathlib import Path
from typing import Any, List, Union

import pandas as pd
import numpy as np

import t3co.constants.Global as gl


def obj_to_string(obj: Union[object, List[object]], indent: str = "    ") -> str:
    """
    Converts an object or list of objects to a formatted string representation
    using a flattened dictionary view for objects with nested dictionaries.

    Args:
        obj (Union[object, List[object]]): The object or list of objects to convert.
        indent (str, optional): Indentation string for nested objects. Defaults to "    ".

    Returns:
        str: Formatted string representation of the object.
    """
    if isinstance(obj, list):
        return (
            "[\n"
            + ",\n".join(indent + obj_to_string(item, indent + "    ") for item in obj)
            + "\n"
            + indent[:-4]
            + "]"
        )
    elif isinstance(obj, dict):
        # If already a dict, pretty-print it.
        return json.dumps(obj, indent=4)
    elif hasattr(obj, "__dict__"):
        return f"{obj.__class__.__name__}\n" + "\n".join(
            f"{indent}{attr} = {obj_to_string(value, indent + '    ')}"
            for attr, value in sorted(vars(obj).items())
        )
    return str(obj)


def handle_nan(
    obj: Union[float, dict, list, Any],
) -> Union[None, dict, list, float, Any]:
    """
    Replaces NaN values in an object with None.

    Args:
        obj (Union[float, dict, list, Any]): The object to process.

    Returns:
        Union[None, dict, list, float, Any]: The processed object with NaN values replaced by None.
    """
    if isinstance(obj, float) and pd.isna(obj):
        return None
    elif isinstance(obj, dict):
        return {k: handle_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [handle_nan(v) for v in obj]
    return obj


def custom_default(obj: Any) -> Union[None, dict, str]:
    """
    Custom default function for JSON serialization.

    Args:
        obj (Any): The object to serialize.

    Returns:
        Union[None, dict, str]: The serialized object.
    """
    if isinstance(obj, float) and pd.isna(obj):
        return None
    elif isinstance(obj, Path):
        return str(obj)
    elif isinstance(obj, pd.DataFrame):
        return None
    elif hasattr(obj, "__dict__"):
        return vars(obj)
    return str(obj)


def to_flat_dict(
    obj: object,
    include_prefix: bool = True,
    prefix: str = "",
    delimiter: str = "_",
    nested_attrs: List[str] = None,
    include_calcs: bool = True,
    exclude_list_fields: bool = False,
    json_lists: bool = True,
) -> dict:
    """
    Flattens a nested object into a dictionary while preserving the order of declared attributes.
    Nested dictionaries and list items that are dict-like (or objects with __dict__)
    are recursively flattened.

    Args:
        obj (object): The object to flatten.
        include_prefix (bool, optional): Whether to include the prefix in the keys. Defaults to True.
        prefix (str, optional): The prefix for the keys. Defaults to "".
        delimiter (str, optional): The delimiter for the keys. Defaults to "_".
        nested_attrs (List[str], optional): List of attribute names to include as nested dictionaries. Defaults to None.
        include_calcs (bool, optional): Whether to include calculations (e.g. tco_per_year). Defaults to True.
        exclude_list_fields (bool, optional): Whether to exclude list/array fields to reduce CSV size. Defaults to False.
        json_lists (bool, optional): Whether to convert lists to JSON strings for CSV compatibility. Defaults to True.

    Returns:
        dict: The flattened dictionary.
    """

    flat_dict = {}
    nested_attrs = nested_attrs or []

    def flatten(item, current_prefix):
        """Recursively flattens attributes."""
        if isinstance(item, dict):
            for key, value in item.items():
                new_key = f"{current_prefix}{delimiter}{key}" if current_prefix else key
                flatten(value, new_key if include_prefix else key)
        elif isinstance(item, list):
            # Skip lists if exclude_list_fields is True (reduces CSV file size significantly)
            # However, do not exclude if the field is explicitly in nested_attrs (e.g. tco_per_year)
            if exclude_list_fields and current_prefix not in nested_attrs:
                return
            # For lists, flatten each item if it is dict-like.
            flat_list = []
            for sub_item in item:
                if isinstance(sub_item, dict) or hasattr(sub_item, "__dict__"):
                    flat_list.append(
                        to_flat_dict(
                            sub_item,
                            include_prefix,
                            "",
                            delimiter,
                            nested_attrs,
                            include_calcs,
                            exclude_list_fields,
                            json_lists,
                        )
                    )
                else:
                    if isinstance(sub_item, (float, np.floating)) and (
                        "cost" in current_prefix.lower()
                        or "dol" in current_prefix.lower()
                    ):
                        flat_list.append(round(float(sub_item), 2))
                    else:
                        flat_list.append(sub_item)
            # Convert to JSON string for CSV compatibility if json_lists is True
            # Ensure no newlines or extra spaces in JSON string
            # Also handle NaN values to ensure valid JSON
            if json_lists:
                flat_list = handle_nan(flat_list)
                flat_dict[current_prefix] = json.dumps(flat_list, separators=(",", ":"))
            else:
                flat_dict[current_prefix] = flat_list
        elif hasattr(item, "__dict__"):
            # If the item is an object, flatten its __dict__.
            flatten(vars(item), current_prefix)
        else:
            if isinstance(item, (float, np.floating)) and (
                "cost" in current_prefix.lower() or "dol" in current_prefix.lower()
            ):
                flat_dict[current_prefix] = round(float(item), 2)
            else:
                flat_dict[current_prefix] = item

    if hasattr(obj, "__dict__"):
        # Extract attributes in the order they were declared.
        cls = obj.__class__
        declared_attributes = list(getattr(cls, "__annotations__", {}).keys())
        instance_attributes = list(vars(obj).keys())

        # Maintain order: declared first, then dynamically assigned attributes.
        ordered_fields = OrderedDict.fromkeys(declared_attributes + instance_attributes)

        # Create ordered dictionary of attributes.
        ordered_obj = OrderedDict(
            (field, getattr(obj, field, None)) for field in ordered_fields
        )

        if not include_calcs and "tco_per_year" in ordered_obj:
            del ordered_obj["tco_per_year"]

        # Flatten the ordered object.
        flatten(ordered_obj, prefix if include_prefix else "")
    else:
        flatten(obj, prefix if include_prefix else "")

    return flat_dict


def remove_df_attrs(obj: object) -> None:
    """
    Removes attributes from an object if they are DataFrame instances.

    Args:
        obj (object): The object to process.
    """
    for attr in list(vars(obj).keys()):  # Use `list()` to avoid modification issues.
        if isinstance(getattr(obj, attr), pd.DataFrame):
            delattr(obj, attr)


def get_path_object(filename: str, strict: bool = True) -> Path:
    """
    Resolves filename as an absolute path, or relative to the t3co resources folder.

    Args:
        filename (str): Absolute path, or path relative to the resources folder.
        strict (bool, optional): Whether an absolute path must already exist. Use
            False for output locations that may not have been created yet. Defaults to True.

    Returns:
        Path: The resolved path.
    """
    return (
        Path(filename).resolve(strict=strict)
        if Path(filename).is_absolute()
        else gl.RESOURCES_FOLDERPATH / filename
    )
