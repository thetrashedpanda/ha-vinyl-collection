"""Tests for the Vinyl Collection storage and setup behavior."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vinyl_collection import async_setup_entry
from custom_components.vinyl_collection.const import DOMAIN
from custom_components.vinyl_collection.store import VinylCollectionStore


@pytest.mark.asyncio
async def test_add_record_uses_utc_timestamp(hass) -> None:
    """New record timestamps should be timezone-aware UTC values."""
    store = VinylCollectionStore(hass)
    with patch.object(store, "async_save", new=AsyncMock()):
        record = await store.async_add_record({"artist": "Test", "album": "Record"})

    added = datetime.fromisoformat(record["date_added"])
    assert added.tzinfo is not None
    assert added.utcoffset() == timedelta(0)


@pytest.mark.asyncio
async def test_setup_fails_when_storage_cannot_load(hass, monkeypatch) -> None:
    """Do not expose an empty writable collection when loading persisted data fails."""
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    hass.data[f"{DOMAIN}_frontend"] = {"registered": True}
    monkeypatch.setattr(
        VinylCollectionStore,
        "async_load",
        AsyncMock(side_effect=HomeAssistantError("storage unavailable")),
    )

    with pytest.raises(HomeAssistantError, match="storage unavailable"):
        await async_setup_entry(hass, entry)

    assert entry.entry_id not in hass.data.get(DOMAIN, {})
