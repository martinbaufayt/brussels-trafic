const map = L.map("map").setView([50.85, 4.35], 13);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  maxZoom: 19,
}).addTo(map);

const statusEl = document.getElementById("status");
let layer = null;

function speedColor(speed) {
  if (speed === null || speed === undefined) return "#95a5a6";
  if (speed < 20) return "#e74c3c";
  if (speed < 50) return "#f39c12";
  return "#27ae60";
}

function formatValue(v, unit) {
  return v !== null && v !== undefined ? `${v} ${unit}` : "N/A";
}

async function refreshMap() {
  try {
    const res = await fetch("/api/devices");
    const geojson = await res.json();

    if (layer) map.removeLayer(layer);

    const active = geojson.features.filter(f => {
      const p = f.properties;
      return p.count !== null || p.speed !== null || p.occupancy !== null;
    });
    const filtered = { type: "FeatureCollection", features: active };

    layer = L.geoJSON(filtered, {
      pointToLayer(feature, latlng) {
        const speed = feature.properties.speed;
        return L.circleMarker(latlng, {
          radius: 7,
          fillColor: speedColor(speed),
          color: "#fff",
          weight: 1,
          fillOpacity: 0.9,
        });
      },
      onEachFeature(feature, featureLayer) {
        const p = feature.properties;
        const time = p.recorded_at
          ? new Date(p.recorded_at).toLocaleTimeString("fr-BE")
          : "—";
        featureLayer.bindPopup(`
          <strong>${p.descr_fr || p.traverse_name}</strong><br>
          Vitesse : ${formatValue(p.speed, "km/h")}<br>
          Comptage : ${formatValue(p.count, "véh/min")}<br>
          Occupation : ${formatValue(p.occupancy, "%")}<br>
          <small>Mis à jour : ${time}</small><br>
          <a href="/api/history/${p.traverse_name}" target="_blank">Historique JSON</a>
        `);
      },
    }).addTo(map);

    const total = geojson.features.length;
    const infoCount = document.getElementById("info-count");
    if (infoCount) infoCount.textContent = total;

    const time = new Date().toLocaleTimeString("fr-BE");
    statusEl.textContent = `${active.length} / ${total} capteurs actifs — actualisé à ${time}`;
  } catch {
    statusEl.textContent = "Erreur de chargement des données.";
  }
}

refreshMap();
setInterval(refreshMap, 60_000);
