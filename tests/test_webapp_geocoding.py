"""
Tests for the Nominatim reverse-geocoding client (network calls mocked -
these tests never hit the real service).
"""

import json
import socket
import urllib.error

import pytest

from photobook_as_code.webapp.geocoding import (
    GeocodingError,
    USER_AGENT,
    resolve_place_name,
    reverse_geocode,
)


class _FakeResponse:
    def __init__(self, body: bytes):
        self._body = body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class TestReverseGeocodeRequest:
    def test_successful_response_is_parsed(self, monkeypatch):
        captured = {}

        def fake_urlopen(req, timeout=None):
            captured["url"] = req.full_url
            captured["headers"] = req.headers
            captured["timeout"] = timeout
            return _FakeResponse(json.dumps({"name": "St. Michaelis Church"}).encode("utf-8"))

        monkeypatch.setattr(
            "photobook_as_code.webapp.geocoding.urllib.request.urlopen", fake_urlopen
        )

        result = reverse_geocode(53.5, 10.0, accept_language="de")

        assert result == {"name": "St. Michaelis Church"}
        assert "lat=53.5" in captured["url"]
        assert "lon=10.0" in captured["url"]
        assert "zoom=18" in captured["url"]
        assert "addressdetails=1" in captured["url"]
        assert "accept-language=de" in captured["url"]
        # urllib normalizes header casing to "User-agent"
        assert captured["headers"]["User-agent"] == USER_AGENT
        assert captured["timeout"] == 10

    def test_omits_accept_language_param_when_not_given(self, monkeypatch):
        captured = {}

        def fake_urlopen(req, timeout=None):
            captured["url"] = req.full_url
            return _FakeResponse(b"{}")

        monkeypatch.setattr(
            "photobook_as_code.webapp.geocoding.urllib.request.urlopen", fake_urlopen
        )

        reverse_geocode(53.5, 10.0)

        assert "accept-language" not in captured["url"]

    def test_network_error_raises_geocoding_error(self, monkeypatch):
        def fake_urlopen(req, timeout=None):
            raise urllib.error.URLError("no route to host")

        monkeypatch.setattr(
            "photobook_as_code.webapp.geocoding.urllib.request.urlopen", fake_urlopen
        )

        with pytest.raises(GeocodingError):
            reverse_geocode(53.5, 10.0)

    def test_http_error_raises_geocoding_error(self, monkeypatch):
        def fake_urlopen(req, timeout=None):
            raise urllib.error.HTTPError(req.full_url, 503, "Service Unavailable", {}, None)

        monkeypatch.setattr(
            "photobook_as_code.webapp.geocoding.urllib.request.urlopen", fake_urlopen
        )

        with pytest.raises(GeocodingError):
            reverse_geocode(53.5, 10.0)

    def test_timeout_raises_geocoding_error(self, monkeypatch):
        def fake_urlopen(req, timeout=None):
            raise socket.timeout("timed out")

        monkeypatch.setattr(
            "photobook_as_code.webapp.geocoding.urllib.request.urlopen", fake_urlopen
        )

        with pytest.raises(GeocodingError):
            reverse_geocode(53.5, 10.0)

    def test_unparsable_body_raises_geocoding_error(self, monkeypatch):
        def fake_urlopen(req, timeout=None):
            return _FakeResponse(b"not json")

        monkeypatch.setattr(
            "photobook_as_code.webapp.geocoding.urllib.request.urlopen", fake_urlopen
        )

        with pytest.raises(GeocodingError):
            reverse_geocode(53.5, 10.0)


class TestResolvePlaceName:
    def test_prefers_named_place(self):
        response = {
            "name": "St. Michaelis Church",
            "address": {"city": "Hamburg", "country": "Germany"},
        }

        assert resolve_place_name(response) == "St. Michaelis Church"

    def test_falls_back_to_city_and_country(self):
        response = {"address": {"city": "Hamburg", "country": "Germany"}}

        assert resolve_place_name(response) == "Hamburg, Germany"

    def test_falls_back_to_town_when_no_city_key(self):
        response = {"address": {"town": "Seewalchen", "country": "Austria"}}

        assert resolve_place_name(response) == "Seewalchen, Austria"

    def test_falls_back_to_village_when_no_city_or_town_key(self):
        response = {"address": {"village": "Hinterstoder", "country": "Austria"}}

        assert resolve_place_name(response) == "Hinterstoder, Austria"

    def test_falls_back_to_country_when_no_locality_present(self):
        response = {"address": {"state": "Tyrol", "country": "Austria"}}

        assert resolve_place_name(response) == "Austria"

    def test_empty_address_yields_no_result(self):
        assert resolve_place_name({"address": {}}) is None

    def test_empty_response_yields_no_result(self):
        assert resolve_place_name({}) is None
