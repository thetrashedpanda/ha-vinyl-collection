"""Tests for Discogs metadata lookup."""
from __future__ import annotations

from unittest.mock import AsyncMock

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vinyl_collection import async_setup_entry
from custom_components.vinyl_collection.const import DOMAIN, SERVICE_LOOKUP_DISCOGS


class MockDiscogsResponse:
    """Mock Discogs API response context manager."""

    status = 200

    async def __aenter__(self) -> MockDiscogsResponse:
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None

    async def json(self) -> dict[str, list[dict[str, object]]]:
        return {
            "results": [
                {
                    "type": "release",
                    "id": 123,
                    "title": "Artist - Album One",
                    "genre": ["Rock"],
                    "style": ["Psychedelic Rock", "Prog Rock"],
                },
                {
                    "type": "release",
                    "id": 456,
                    "title": "Artist - Album Two",
                    "genre": ["Rock"],
                    "style": ["Hard Rock"],
                },
            ]
        }


class MockDiscogsSession:
    """Mock the HTTP session used for the Discogs search."""

    def get(self, *_args: object, **_kwargs: object) -> MockDiscogsResponse:
        return MockDiscogsResponse()


async def test_discogs_lookup_uses_result_styles_not_genres(hass, monkeypatch) -> None:
    """Each lookup result should carry only its own album styles."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"discogs_enabled": True},
    )
    entry.add_to_hass(hass)
    hass.data[f"{DOMAIN}_frontend"] = {"registered": True}
    monkeypatch.setattr(
        hass.config_entries,
        "async_forward_entry_setups",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "custom_components.vinyl_collection.async_get_clientsession",
        lambda _hass: MockDiscogsSession(),
    )

    await async_setup_entry(hass, entry)
    response = await hass.services.async_call(
        DOMAIN,
        SERVICE_LOOKUP_DISCOGS,
        {"query": "Artist Album"},
        blocking=True,
        return_response=True,
    )

    assert [result["genre"] for result in response["results"]] == [
        "Psychedelic Rock, Prog Rock",
        "Hard Rock",
    ]
