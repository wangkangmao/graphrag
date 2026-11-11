# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Tests for JsonCache tolerance of non-dict cached payloads."""

import pytest
from graphrag_cache.json_cache import JsonCache
from graphrag_storage.file_storage import FileStorage


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("payload", "description"),
    [
        ('[1, 2, 3]', "json array"),
        ('"a string"', "json string"),
        ("42", "json number"),
        ("true", "json boolean"),
        ('{"other": 1}', "dict without result key"),
    ],
)
async def test_json_cache_get_purges_non_result_payloads(
    tmp_path, payload, description
):
    """A valid-JSON payload that is not a {"result": ...} dict must not crash get()."""
    storage = FileStorage(base_dir=str(tmp_path))
    cache = JsonCache(storage=storage)

    # Seed the storage directly with a payload that bypasses JsonCache.set
    # (e.g. written by an external tool, an older schema, or corrupted state).
    await storage.set("key", payload)

    assert await cache.get("key") is None, f"get() should return None for {description}"
    # The invalid entry must be purged so it is not re-read on every call.
    assert not await cache.has("key"), f"invalid payload should be deleted: {description}"


@pytest.mark.asyncio
async def test_json_cache_get_returns_result_from_valid_payload(tmp_path):
    """The dict-shaped happy path keeps returning the wrapped result."""
    storage = FileStorage(base_dir=str(tmp_path))
    cache = JsonCache(storage=storage)

    await cache.set("key", {"text": "héllo"})

    assert await cache.get("key") == {"text": "héllo"}
    assert await cache.has("key")
