"""Service transverse de géocodage d'adresses."""

import json
import math

from PySide6.QtCore import QObject, QTimer, QUrl, QUrlQuery, Signal
from PySide6.QtNetwork import (
    QNetworkAccessManager,
    QNetworkReply,
    QNetworkRequest,
)

from app.models.geocoding_result import GeocodingResult


GEOCODING_ENDPOINT = "https://data.geopf.fr/geocodage/search"
DEFAULT_RESULT_LIMIT = 7
DEFAULT_TIMEOUT_MS = 10_000


def _parse_geocoding_response(payload):
    """Convertit une réponse GeoJSON en résultats applicatifs valides."""
    if isinstance(payload, (bytes, bytearray)):
        payload = payload.decode("utf-8")
    if isinstance(payload, str):
        payload = json.loads(payload)
    if not isinstance(payload, dict):
        raise ValueError("La réponse de géocodage n'est pas un objet JSON.")

    features = payload.get("features")
    if not isinstance(features, list):
        raise ValueError("La réponse de géocodage ne contient pas de résultats.")

    results = []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        geometry = feature.get("geometry") or {}
        properties = feature.get("properties") or {}
        coordinates = geometry.get("coordinates")
        if (
            geometry.get("type") != "Point"
            or not isinstance(coordinates, (list, tuple))
            or len(coordinates) < 2
            or not isinstance(properties, dict)
        ):
            continue

        try:
            longitude = float(coordinates[0])
            latitude = float(coordinates[1])
        except (TypeError, ValueError):
            continue
        if (
            not math.isfinite(latitude)
            or not math.isfinite(longitude)
            or not -90 <= latitude <= 90
            or not -180 <= longitude <= 180
        ):
            continue

        label = str(
            properties.get("label")
            or properties.get("name")
            or ""
        ).strip()
        if not label:
            continue

        score = properties.get("score")
        try:
            score = float(score) if score is not None else None
        except (TypeError, ValueError):
            score = None

        results.append(
            GeocodingResult(
                label=label,
                latitude=latitude,
                longitude=longitude,
                score=score,
                postcode=str(properties.get("postcode") or ""),
                city=str(properties.get("city") or ""),
                result_type=str(properties.get("type") or ""),
                provider_id=str(
                    properties.get("id")
                    or feature.get("id")
                    or ""
                ),
                context=str(properties.get("context") or ""),
            )
        )

    return results


class GeocodingService(QObject):
    """Recherche des adresses sans connaître la carte ni le métier."""

    resultsReady = Signal(int, object)
    searchFailed = Signal(int, str)

    def __init__(
        self,
        network_manager=None,
        endpoint=GEOCODING_ENDPOINT,
        timeout_ms=DEFAULT_TIMEOUT_MS,
        parent=None,
    ):
        super().__init__(parent)
        self._network_manager = (
            network_manager or QNetworkAccessManager(self)
        )
        self._endpoint = endpoint
        self._timeout_ms = timeout_ms
        self._next_request_id = 1
        self._requests = {}

    def search(self, query, limit=DEFAULT_RESULT_LIMIT):
        """Démarre une recherche et retourne son identifiant."""
        normalized_query = " ".join(str(query or "").split())
        if len(normalized_query) < 3:
            raise ValueError(
                "Saisissez au moins trois caractères pour rechercher une adresse."
            )

        try:
            limit = int(limit)
        except (TypeError, ValueError) as error:
            raise ValueError("La limite de résultats est invalide.") from error
        limit = max(1, min(limit, 15))

        request_id = self._next_request_id
        self._next_request_id += 1

        url = QUrl(self._endpoint)
        parameters = QUrlQuery()
        parameters.addQueryItem("q", normalized_query)
        parameters.addQueryItem("limit", str(limit))
        parameters.addQueryItem("index", "address")
        url.setQuery(parameters)

        request = QNetworkRequest(url)
        request.setRawHeader(b"User-Agent", b"PMP-Geocoding/1.0")
        request.setRawHeader(
            b"Accept",
            b"application/geo+json, application/json",
        )

        reply = self._network_manager.get(request)
        timer = QTimer(reply)
        timer.setSingleShot(True)
        timer.timeout.connect(
            lambda current_reply=reply: self._abort_for_timeout(current_reply)
        )
        reply.finished.connect(
            lambda current_reply=reply: self._finish_request(current_reply)
        )
        self._requests[reply] = (request_id, timer)
        timer.start(self._timeout_ms)
        return request_id

    def _abort_for_timeout(self, reply):
        if reply not in self._requests:
            return
        reply.setProperty("pmp_geocoding_timed_out", True)
        reply.abort()

    def _finish_request(self, reply):
        request_data = self._requests.pop(reply, None)
        if request_data is None:
            reply.deleteLater()
            return

        request_id, timer = request_data
        timer.stop()
        status = reply.attribute(
            QNetworkRequest.Attribute.HttpStatusCodeAttribute
        )

        if reply.property("pmp_geocoding_timed_out"):
            self.searchFailed.emit(
                request_id,
                "Le service de géocodage n'a pas répondu dans le délai prévu.",
            )
        elif reply.error() != QNetworkReply.NetworkError.NoError:
            self.searchFailed.emit(
                request_id,
                self._network_error_message(status, reply.errorString()),
            )
        else:
            try:
                results = _parse_geocoding_response(bytes(reply.readAll()))
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
                self.searchFailed.emit(
                    request_id,
                    "La réponse du service de géocodage est invalide.",
                )
            else:
                self.resultsReady.emit(request_id, results)

        reply.deleteLater()

    @staticmethod
    def _network_error_message(status, detail):
        if status == 429:
            return (
                "Le service de géocodage est temporairement trop sollicité. "
                "Veuillez réessayer plus tard."
            )
        if status is not None and int(status) >= 500:
            return "Le service de géocodage est temporairement indisponible."
        if detail:
            return f"Recherche impossible : {detail}"
        return "La recherche est impossible en raison d'une erreur réseau."
