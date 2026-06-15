(function (global) {
  "use strict";

  var DARK = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";
  var ATTR =
    "&copy; OpenStreetMap &copy; CARTO";
  var CMAPS = {
    inferno: ["#000004", "#420a68", "#932667", "#dd513a", "#fca50a", "#fcffa4"],
    viridis: ["#440154", "#31688e", "#35b779", "#fde725"],
    plasma: ["#0d0887", "#7e03a8", "#cc4778", "#f89441", "#f0f921"],
    magma: ["#000004", "#3b0f70", "#8c2981", "#de4964", "#fca636", "#fcfdbf"],
  };

  function colorFromCmap(cmap, t) {
    var pal = CMAPS[cmap] || CMAPS.inferno;
    t = Math.max(0, Math.min(1, t));
    var idx = t * (pal.length - 1);
    var i = Math.floor(idx);
    var f = idx - i;
    if (i >= pal.length - 1) return pal[pal.length - 1];
    function h(s) {
      return [parseInt(s.slice(1, 3), 16), parseInt(s.slice(3, 5), 16), parseInt(s.slice(5, 7), 16)];
    }
    var a = h(pal[i]), b = h(pal[i + 1]);
    var r = Math.round(a[0] + (b[0] - a[0]) * f);
    var g = Math.round(a[1] + (b[1] - a[1]) * f);
    var bl = Math.round(a[2] + (b[2] - a[2]) * f);
    return "rgb(" + r + "," + g + "," + bl + ")";
  }

  function darkMap(el) {
    var base = global.MAP_BASE || {};
    var center = base.center || [31.2492, 121.4595];
    var zoom = base.zoom || 15;
    var map = L.map(el, {
      center: center,
      zoom: zoom,
      zoomControl: false,
      attributionControl: false,
    });
    L.tileLayer(DARK, { maxZoom: 19, attribution: ATTR }).addTo(map);
    L.control.zoom({ position: "bottomright" }).addTo(map);
    return map;
  }

  function addBuildings(map) {
    var geo = global.MAP_GEO && global.MAP_GEO.buildings;
    if (!geo) return;
    L.geoJSON(geo, {
      style: {
        color: "#888888",
        weight: 0.4,
        fillColor: "#666666",
        fillOpacity: 0.45,
      },
    }).addTo(map);
  }

  function addRails(map, data) {
    if (!data.rails) return;
    L.geoJSON(data.rails, {
      style: { color: "#ffffff", weight: 2.5, opacity: 0.9 },
    }).addTo(map);
  }

  function addRedline(map, data) {
    if (!data.redline) return;
    L.geoJSON(data.redline, {
      style: { color: "#E53935", weight: 2, dashArray: "6 4", fill: false },
    }).addTo(map);
  }

  function addZones(map, data, highlight) {
    if (!data.zones) return;
    L.geoJSON(data.zones, {
      style: function (f) {
        var id = f.properties && f.properties.zone_id;
        var isHi = highlight && id === highlight;
        return {
          color: isHi ? "#ffffff" : f.properties.color || "#888",
          weight: isHi ? 2 : 1,
          fillColor: f.properties.color || "#888",
          fillOpacity: isHi ? 0.55 : 0.12,
        };
      },
    }).addTo(map);
  }

  function addAnalysisLayer(map, data) {
    if (!data.geojson || !data.layerStyle) return;
    var st = data.layerStyle;
    L.geoJSON(data.geojson, {
      style: function (f) {
        var p = f.properties || {};
        if (st.type === "grid") {
          var t = (p.v - st.vmin) / (st.vmax - st.vmin || 1);
          return {
            color: "transparent",
            weight: 0,
            fillColor: colorFromCmap(st.cmap, t),
            fillOpacity: 0.82,
          };
        }
        if (st.type === "categorical") {
          return {
            color: "transparent",
            weight: 0,
            fillColor: p.color || "#888",
            fillOpacity: 0.78,
          };
        }
        return { fillOpacity: 0.5 };
      },
    }).addTo(map);
  }

  function addPoints(map, data) {
    if (!data.points) return;
    L.geoJSON(data.points, {
      pointToLayer: function (f, latlng) {
        var c = (f.properties && f.properties.color) || "#FFB300";
        return L.circleMarker(latlng, {
          radius: (f.properties && f.properties.size) || 4,
          color: "#fff",
          weight: 0.3,
          fillColor: c,
          fillOpacity: 0.9,
        });
      },
    }).addTo(map);
  }

  function addLines(map, data) {
    if (!data.lines) return;
    L.geoJSON(data.lines, {
      style: function (f) {
        return {
          color: (f.properties && f.properties.color) || "#FFD54F",
          weight: (f.properties && f.properties.weight) || 1.2,
          dashArray: "6 4",
          opacity: 0.85,
        };
      },
    }).addTo(map);
  }

  function fitMap(map, data) {
    if (data.bounds) {
      map.fitBounds(data.bounds, { padding: [12, 12] });
    }
  }

  function createAnalysisMap(container, layerKey) {
    container.innerHTML = "";
    var wrap = document.createElement("div");
    wrap.className = "leaflet-wrap";
    wrap.style.width = "100%";
    wrap.style.height = "100%";
    container.appendChild(wrap);

    var data = (global.MAP_LAYERS && global.MAP_LAYERS[layerKey]) || null;
    if (!data) {
      wrap.innerHTML = "<p style='color:#888;padding:16px'>图层数据缺失</p>";
      return { reset: function () {}, zoomBy: function () {} };
    }

    var map = darkMap(wrap);
    addBuildings(map);
    addRails(map, data);

    var highlight = data.layerStyle && data.layerStyle.type === "highlight" ? data.layerStyle.highlight : null;
    if (highlight) {
      addZones(map, data, highlight);
      addPoints(map, data);
      addLines(map, data);
      addRedline(map, data);
    } else {
      addAnalysisLayer(map, data);
      addZones(map, data, null);
      addRedline(map, data);
    }

    fitMap(map, data);
    setTimeout(function () {
      map.invalidateSize();
      fitMap(map, data);
    }, 80);

    return {
      map: map,
      reset: function () {
        fitMap(map, data);
      },
      zoomBy: function (factor) {
        var z = map.getZoom();
        map.setZoom(Math.min(19, Math.max(12, z + (factor > 1 ? 1 : -1))));
      },
    };
  }

  global.LeafletAnalysisMap = { create: createAnalysisMap };
})(window);
