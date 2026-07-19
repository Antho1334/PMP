(function () {
    "use strict";

    const state = {
        map: null,
        markers: null,
        items: [],
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

    function setItems(items) {
        state.items = Array.isArray(items) ? items : [];
        state.markers.clearLayers();

        state.items.forEach(function (item) {
            const marker = L.circleMarker(
                [item.latitude, item.longitude],
                {
                    radius: 9,
                    color: "#ffffff",
                    weight: 2,
                    fillColor: item.color || "#2563eb",
                    fillOpacity: 1
                }
            );
            marker.bindTooltip(createTooltip(item));
            marker.addTo(state.markers);
        });

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
