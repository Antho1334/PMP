(function () {
    "use strict";

    const state = {
        map: null,
        markers: null,
        markersByKey: new Map(),
        items: [],
        selectedKey: null,
        bridge: null,
        configuration: {
            defaultCenter: [43.3336, 3.1200],
            defaultZoom: 14,
            singleItemZoom: 17,
            fitMaxZoom: 17,
            tileLayer: {
                url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                attribution: "&copy; OpenStreetMap contributors",
                minZoom: 0,
                maxZoom: 19
            }
        }
    };

    function initialize() {
        state.map = L.map("map", {
            zoomControl: true,
            attributionControl: true
        });
        state.markers = L.featureGroup().addTo(state.map);
        applyConfiguration();
        fitToItems();
        initializeWebChannel();
    }

    function initializeWebChannel() {
        if (typeof qt === "undefined" || typeof QWebChannel === "undefined") {
            return;
        }

        new QWebChannel(qt.webChannelTransport, function (channel) {
            state.bridge = channel.objects.mapEvents;
        });
    }

    function applyConfiguration() {
        const tileLayer = state.configuration.tileLayer;

        state.map.eachLayer(function (layer) {
            if (layer instanceof L.TileLayer) {
                state.map.removeLayer(layer);
            }
        });

        L.tileLayer(tileLayer.url, {
            attribution: tileLayer.attribution,
            minZoom: tileLayer.minZoom,
            maxZoom: tileLayer.maxZoom
        }).addTo(state.map);
    }

    function configure(configuration) {
        state.configuration = Object.assign(
            {},
            state.configuration,
            configuration,
            {
                tileLayer: Object.assign(
                    {},
                    state.configuration.tileLayer,
                    configuration.tileLayer || {}
                )
            }
        );
        applyConfiguration();
        fitToItems();
    }

    function createTooltip(item) {
        const container = document.createElement("div");
        const title = document.createElement("div");
        title.className = "pmp-marker-tooltip__title";
        title.textContent = item.title;
        container.appendChild(title);

        if (item.subtitle) {
            const subtitle = document.createElement("div");
            subtitle.className = "pmp-marker-tooltip__subtitle";
            subtitle.textContent = item.subtitle;
            container.appendChild(subtitle);
        }

        return container;
    }

    function normalMarkerStyle(item) {
        return {
            radius: 9,
            color: "#ffffff",
            weight: 2,
            fillColor: item.color || "#2563eb",
            fillOpacity: 1
        };
    }

    function selectedMarkerStyle(item) {
        return {
            radius: 12,
            color: "#0f172a",
            weight: 4,
            fillColor: item.color || "#2563eb",
            fillOpacity: 1
        };
    }

    function selectMarker(key, notifyPython) {
        const previous = state.markersByKey.get(state.selectedKey);
        if (previous) {
            previous.marker.setStyle(normalMarkerStyle(previous.item));
            previous.marker.closeTooltip();
        }

        const selected = state.markersByKey.get(key);
        if (!selected) {
            state.selectedKey = null;
            return;
        }

        state.selectedKey = key;
        selected.marker.setStyle(selectedMarkerStyle(selected.item));
        selected.marker.openTooltip();

        if (notifyPython && state.bridge) {
            state.bridge.selectMarker(key);
        }
    }

    function setItems(items, selectedKey) {
        state.items = Array.isArray(items) ? items : [];
        state.markers.clearLayers();
        state.markersByKey.clear();
        state.selectedKey = null;

        state.items.forEach(function (item) {
            const marker = L.circleMarker(
                [item.latitude, item.longitude],
                normalMarkerStyle(item)
            );
            marker.bindTooltip(createTooltip(item));
            marker.on("click", function () {
                if (!state.bridge) {
                    return;
                }
                selectMarker(item.key, true);
            });
            marker.addTo(state.markers);
            state.markersByKey.set(item.key, {marker: marker, item: item});
        });

        if (selectedKey && state.markersByKey.has(selectedKey)) {
            selectMarker(selectedKey, false);
        }
        fitToItems();
    }

    function fitToItems() {
        const configuration = state.configuration;

        if (state.items.length === 0) {
            state.map.setView(
                configuration.defaultCenter,
                configuration.defaultZoom,
                {animate: false}
            );
            return;
        }

        if (state.items.length === 1) {
            const item = state.items[0];
            state.map.setView(
                [item.latitude, item.longitude],
                configuration.singleItemZoom,
                {animate: false}
            );
            return;
        }

        state.map.fitBounds(state.markers.getBounds(), {
            padding: [35, 35],
            maxZoom: configuration.fitMaxZoom,
            animate: false
        });
    }

    window.PMPOperationalMap = {
        configure: configure,
        setItems: setItems,
        fitToItems: fitToItems
    };

    initialize();
}());
