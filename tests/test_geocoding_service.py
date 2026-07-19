import json

import pytest

from app.services.geocoding_service import (
    GeocodingService,
    _parse_geocoding_response,
)


def _feature(
    label="1 place de la Mairie 34310 Montady",
    longitude=3.12,
    latitude=43.3336,
    **properties,
):
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [longitude, latitude],
        },
        "properties": {
            "label": label,
            "postcode": "34310",
            "city": "Montady",
            "score": 0.92,
            **properties,
        },
    }


def test_parser_reads_geojson_coordinates_in_longitude_latitude_order():
    results = _parse_geocoding_response(
        {"type": "FeatureCollection", "features": [_feature()]}
    )

    assert len(results) == 1
    assert results[0].longitude == 3.12
    assert results[0].latitude == 43.3336
    assert results[0].postcode == "34310"
    assert results[0].city == "Montady"


def test_parser_preserves_multiple_results_and_special_characters():
    payload = {
        "features": [
            _feature(label='1 rue de l’Église "Centre" <ancien>'),
            _feature(
                label="2 rue de l'Église",
                longitude=3.121,
                latitude=43.334,
            ),
        ]
    }

    restored = _parse_geocoding_response(
        json.dumps(payload, ensure_ascii=False)
    )

    assert [result.label for result in restored] == [
        '1 rue de l’Église "Centre" <ancien>',
        "2 rue de l'Église",
    ]


def test_parser_ignores_invalid_features():
    payload = {
        "features": [
            _feature(latitude=91),
            _feature(longitude=float("nan")),
            {"geometry": {"type": "LineString", "coordinates": []}},
            _feature(label=""),
        ]
    }

    assert _parse_geocoding_response(payload) == []


def test_parser_rejects_invalid_response_shape():
    with pytest.raises(ValueError):
        _parse_geocoding_response({"unexpected": []})


def test_network_errors_have_actionable_messages():
    assert "trop sollicité" in GeocodingService._network_error_message(
        429, "rate limited"
    )
    assert "indisponible" in GeocodingService._network_error_message(
        503, "server error"
    )
    assert "proxy" in GeocodingService._network_error_message(
        None, "proxy refusé"
    )
