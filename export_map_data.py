# -*- coding: utf-8 -*-
"""Export dark-theme base map + vector layers for interactive web maps."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SCRIPTS = Path(r"F:\2026spring2\form-function-flow-main\form-function-flow-main\scripts")
sys.path.insert(0, str(SCRIPTS))

import generate_zone_rationale_dark_suite as gz  # noqa: E402
import zone_spatial_logic as zsl  # noqa: E402

OUT_ROOT = Path(r"F:\2026spring2\出图\html制作\site\assets\map-data")
BG = "#0a0a0a"
BUILD_OUT = "#3a3a3a"
BUILD_IN = "#5a5a5a"
CONTEXT_M = 1200
SIMPLIFY_M = 6.0
IMG_W = 1200

INTERFACE_COLORS = {
    "Soft": "#81C784",
    "Transitional": "#FFB74D",
    "Hard": "#EF5350",
    "Residual": "#9E9E9E",
}
LOGIC_COLORS = {
    "Urban Core": "#FFB300",
    "Mixed Urban Core": "#FF6D00",
    "Weaving Opportunity": "#E8E4DC",
    "Barrier Edge": "#5C6BC0",
}


def apply_dark_theme() -> None:
    gz.CONTEXT_BUFFER_M = CONTEXT_M
    gz.BG_TRANSPARENT = BG
    gz.BUILD_OUT_FILL = BUILD_OUT
    gz.BUILD_OUT_EDGE = "#4a4a4a"
    gz.BUILD_IN_FILL = BUILD_IN
    gz.BUILD_IN_EDGE = "#777777"
    gz.TEXT_MAIN = "#f0f0f0"
    gz.TEXT_DIM = "#aaaaaa"

    def style_map_ax(ax):
        ax.set_facecolor(BG)
        ax.patch.set_alpha(1.0)

    gz.style_map_ax = style_map_ax
    plt.rcParams.update(
        {
            "font.sans-serif": ["SimHei", "Microsoft YaHei", "DejaVu Sans"],
            "axes.unicode_minus": False,
            "figure.facecolor": BG,
            "savefig.facecolor": BG,
        }
    )


def _bbox(ctx) -> tuple[float, float, float, float]:
    return tuple(ctx["context_poly"].bounds)


def _wgs84_bounds(ctx) -> list:
    g = gpd.GeoSeries([ctx["context_poly"]], crs=gz.bl.WM).to_crs(4326)
    minx, miny, maxx, maxy = g.total_bounds
    return [[miny, minx], [maxy, maxx]]


def _center_zoom(ctx) -> tuple[list[float], int]:
    g = gpd.GeoSeries([ctx["context_poly"]], crs=gz.bl.WM).to_crs(4326)
    minx, miny, maxx, maxy = g.total_bounds
    return [(miny + maxy) / 2, (minx + maxx) / 2], 15


def _gdf_to_geojson(gdf, columns: list[str] | None = None) -> dict:
    if gdf is None or gdf.empty:
        return {"type": "FeatureCollection", "features": []}
    g = gdf.to_crs(4326)
    if columns:
        cols = [c for c in columns if c in g.columns] + ["geometry"]
        g = g[cols]
    return json.loads(g.to_json())


def _rings(geom) -> list:
    if geom is None or geom.is_empty:
        return []
    if geom.geom_type == "Polygon":
        return [[list(c) for c in geom.exterior.coords]]
    if geom.geom_type == "MultiPolygon":
        return [[list(c) for c in p.exterior.coords] for p in geom.geoms]
    return []


def _simplify_geom(geom):
    try:
        return geom.simplify(SIMPLIFY_M, preserve_topology=True)
    except Exception:
        return geom


def export_base_map(ctx, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    minx, miny, maxx, maxy = _bbox(ctx)
    w_m = maxx - minx
    h_m = maxy - miny
    aspect = h_m / max(w_m, 1)
    img_h = max(int(IMG_W * aspect), 400)

    fig, ax = plt.subplots(figsize=(IMG_W / 100, img_h / 100), dpi=100)
    fig.patch.set_facecolor(BG)
    gz._plot_buildings(ax, ctx)
    gz._apply_limits(ax, ctx)
    ax.axis("off")
    path = out_dir / "base.png"
    fig.savefig(path, facecolor=BG, bbox_inches="tight", pad_inches=0)
    plt.close(fig)

    center, zoom = _center_zoom(ctx)
    bounds = _wgs84_bounds(ctx)
    meta = {
        "bbox": [minx, miny, maxx, maxy],
        "bounds": bounds,
        "center": center,
        "zoom": zoom,
        "image": "assets/map-data/base.png",
        "width": IMG_W,
        "height": img_h,
        "bg": BG,
    }
    (out_dir / "base.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    return meta


def export_buildings_geojson(ctx, out_dir: Path) -> dict:
    parts = []
    for gdf, fill in [(ctx["bld_outside"], "#444444"), (ctx["bld_inside"], "#666666")]:
        if gdf is None or gdf.empty:
            continue
        g = gdf.to_crs(4326).copy()
        g["fill"] = fill
        parts.append(g)
    if not parts:
        geo = {"type": "FeatureCollection", "features": []}
    else:
        combined = gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), crs="EPSG:4326")
        combined.geometry = combined.geometry.simplify(0.000008, preserve_topology=True)
        geo = json.loads(combined.to_json())
    (out_dir / "buildings.geojson").write_text(json.dumps(geo, ensure_ascii=False), encoding="utf-8")
    return geo


def _grid_layer(grid, column: str, cmap: str) -> tuple[list, float, float, str]:
    if grid.empty or column not in grid.columns:
        return [], 0.0, 1.0, cmap
    vals = grid[column].astype(float)
    vmin = float(np.nanmin(vals))
    vmax = float(np.nanmax(vals))
    if vmax <= vmin:
        vmax = vmin + 1.0
    feats = []
    for _, row in grid.iterrows():
        rings = _rings(_simplify_geom(row.geometry))
        if rings:
            feats.append({"rings": rings, "v": float(row[column])})
    return feats, vmin, vmax, cmap


def _cat_layer(grid, column: str, color_map: dict) -> list:
    feats = []
    for _, row in grid.iterrows():
        rings = _rings(_simplify_geom(row.geometry))
        if not rings:
            continue
        key = str(row[column])
        feats.append({"rings": rings, "v": key, "color": color_map.get(key, "#888888")})
    return feats


def _zone_features(ctx) -> list[dict]:
    items = []
    for _, z in ctx["zones"].iterrows():
        items.append(
            {
                "id": z["zone_id"],
                "label": z["zone_label"],
                "color": z["zone_color"],
                "rings": _rings(_simplify_geom(z.geometry)),
            }
        )
    return items


def _line_features(gdf, color: str, width: float = 2.0) -> list[dict]:
    if gdf is None or gdf.empty:
        return []
    lines = []
    for geom in gdf.geometry:
        if geom is None or geom.is_empty:
            continue
        if geom.geom_type == "LineString":
            lines.append({"coords": [list(c) for c in geom.coords], "color": color, "width": width})
        elif geom.geom_type == "MultiLineString":
            for ln in geom.geoms:
                lines.append({"coords": [list(c) for c in ln.coords], "color": color, "width": width})
    return lines


def _point_features(gdf, color: str, size: float = 4) -> list[dict]:
    if gdf is None or gdf.empty:
        return []
    return [{"xy": [g.x, g.y], "color": color, "size": size} for g in gdf.geometry if g is not None]


def _zone_geojson(ctx) -> dict:
    z = ctx["zones"].copy()
    z["color"] = z["zone_color"]
    return _gdf_to_geojson(z, ["zone_id", "zone_label", "color"])


def _redline_geojson(ctx) -> dict:
    return _gdf_to_geojson(gpd.GeoDataFrame(geometry=[ctx["site"]], crs=gz.bl.WM))


def _rails_geojson(rail_gdf) -> dict:
    if rail_gdf is None or rail_gdf.empty:
        return {"type": "FeatureCollection", "features": []}
    return _gdf_to_geojson(gpd.GeoDataFrame(geometry=rail_gdf.geometry, crs=gz.bl.WM))


def _grid_geojson(grid, column: str, cmap: str) -> tuple[dict, dict]:
    if grid.empty or column not in grid.columns:
        return {"type": "FeatureCollection", "features": []}, {
            "type": "grid",
            "cmap": cmap,
            "vmin": 0.0,
            "vmax": 1.0,
            "property": "v",
        }
    g = grid.copy()
    g.geometry = g.geometry.simplify(SIMPLIFY_M, preserve_topology=True)
    g["v"] = g[column].astype(float)
    vals = g["v"]
    vmin = float(np.nanmin(vals))
    vmax = float(np.nanmax(vals))
    if vmax <= vmin:
        vmax = vmin + 1.0
    geo = _gdf_to_geojson(g, ["v"])
    style = {"type": "grid", "cmap": cmap, "vmin": vmin, "vmax": vmax, "property": "v"}
    return geo, style


def _cat_geojson(grid, column: str, color_map: dict) -> tuple[dict, dict]:
    if grid.empty or column not in grid.columns:
        return {"type": "FeatureCollection", "features": []}, {"type": "categorical"}
    g = grid.copy()
    g.geometry = g.geometry.simplify(SIMPLIFY_M, preserve_topology=True)
    g["color"] = g[column].astype(str).map(lambda k: color_map.get(k, "#888888"))
    g["v"] = g[column].astype(str)
    geo = _gdf_to_geojson(g, ["v", "color"])
    return geo, {"type": "categorical"}


def _write_map_layer(out_dir: Path, name: str, ctx, meta: dict, payload: dict) -> None:
    bounds = meta.get("bounds") or _wgs84_bounds(ctx)
    center = meta.get("center")
    base = {
        "id": name,
        "bounds": bounds,
        "center": center,
        "zoom": meta.get("zoom", 15),
        "zones": _zone_geojson(ctx),
        "redline": _redline_geojson(ctx),
        "rails": payload.get("rails_geojson", {"type": "FeatureCollection", "features": []}),
        "title": payload.get("title", ""),
        "layerStyle": payload.get("layerStyle"),
        "geojson": payload.get("geojson"),
        "points": payload.get("points"),
        "lines": payload.get("lines"),
    }
    (out_dir / f"{name}.json").write_text(json.dumps(base, ensure_ascii=False), encoding="utf-8")


def export_logic_layers(ctx, logic: dict, meta: dict, out_dir: Path) -> list[str]:
    grid = logic["grid"]
    iface_grid = logic.get("interface_grid", grid)
    rail = logic.get("rail")
    rails_geo = _rails_geojson(rail)
    names = []

    heat_specs = [
        ("logic_cliff", grid, "poi_cliff", "inferno", "POI Cliff Index"),
        ("logic_entropy", grid, "poi_entropy", "viridis", "POI Entropy"),
        ("logic_ped", grid, "ped_integration", "plasma", "步行网络 Integration"),
        ("logic_frag", iface_grid, "edge_frag", "inferno", "Edge Fragmentation"),
    ]
    for name, gdf, col, cmap, title in heat_specs:
        geo, layer_style = _grid_geojson(gdf, col, cmap)
        _write_map_layer(
            out_dir,
            name,
            ctx,
            meta,
            {
                "rails_geojson": rails_geo,
                "title": title,
                "geojson": geo,
                "layerStyle": layer_style,
            },
        )
        names.append(name)

    geo, layer_style = _cat_geojson(iface_grid, "interface_type", INTERFACE_COLORS)
    _write_map_layer(
        out_dir,
        "logic_iface",
        ctx,
        meta,
        {
            "rails_geojson": rails_geo,
            "title": "Interface Type",
            "geojson": geo,
            "layerStyle": layer_style,
        },
    )
    names.append("logic_iface")

    zm = logic["zone_metrics"]
    final_rows = []
    for _, z in ctx["zones"].iterrows():
        row = zm.loc[zm["zone_id"] == z["zone_id"]].iloc[0]
        lt = row["logic_type"]
        final_rows.append(
            {
                "geometry": _simplify_geom(z.geometry),
                "v": lt,
                "color": LOGIC_COLORS.get(lt, "#888888"),
                "label": z["zone_label"],
            }
        )
    final_gdf = gpd.GeoDataFrame(final_rows, crs=gz.bl.WM)
    geo = _gdf_to_geojson(final_gdf, ["v", "color", "label"])
    _write_map_layer(
        out_dir,
        "logic_final",
        ctx,
        meta,
        {
            "rails_geojson": rails_geo,
            "title": "空间逻辑分区",
            "geojson": geo,
            "layerStyle": {"type": "categorical"},
        },
    )
    names.append("logic_final")

    transect = logic.get("transect")
    if transect is not None and not transect.empty:
        chart = {
            "id": "logic_transect",
            "type": "transect",
            "title": "POI 断崖剖面",
            "series": [
                {"key": "south_dens", "label": "南侧 ρ", "color": "#FF6D00"},
                {"key": "north_dens", "label": "北侧 ρ", "color": "#5C6BC0"},
                {"key": "cliff_ns", "label": "Cliff |Δρ|", "color": "#FF7043", "dash": True},
            ],
            "x": transect["transect_ix"].tolist(),
            "data": {
                "south_dens": transect["south_dens"].tolist(),
                "north_dens": transect["north_dens"].tolist(),
                "cliff_ns": transect["cliff_ns"].tolist(),
            },
            "xlabel": "东西向剖面列",
            "ylabel": "商业/公服密度 (处/km²)",
        }
        (out_dir / "logic_transect.json").write_text(json.dumps(chart, ensure_ascii=False), encoding="utf-8")
        names.append("logic_transect")

    return names


def export_verify_layers(ctx, logic: dict, meta: dict, out_dir: Path) -> list[str]:
    rails_geo = _rails_geojson(logic.get("rail"))
    names = []
    station_pt = gpd.GeoDataFrame(
        {"color": ["#FF5252"], "size": [10]},
        geometry=[ctx["station"]],
        crs=gz.bl.WM,
    )
    buf_geoms = gpd.GeoSeries(
        [ctx["station"].buffer(800), ctx["station"].buffer(500)],
        crs=gz.bl.WM,
    ).boundary
    buf_lines = gpd.GeoDataFrame(
        {"color": ["#FFD54F", "#FFD54F"], "weight": [1.2, 1.2]},
        geometry=buf_geoms,
        crs=gz.bl.WM,
    )

    def poi_points(gdf, color):
        if gdf is None or gdf.empty:
            return {"type": "FeatureCollection", "features": []}
        g = gdf.copy()
        g["color"] = color
        g["size"] = 5
        return _gdf_to_geojson(g, ["color", "size"])

    def save_verify(name, highlight, poi_gdf, poi_color, extra_lines=None, extra_pts=None):
        feats = list(poi_points(poi_gdf, poi_color).get("features", []))
        if extra_pts is not None and not extra_pts.empty:
            feats.extend(_gdf_to_geojson(extra_pts, ["color", "size"]).get("features", []))
        pts = {"type": "FeatureCollection", "features": feats}
        lines_geo = (
            _gdf_to_geojson(extra_lines, ["color", "weight"])
            if extra_lines is not None and not extra_lines.empty
            else None
        )
        _write_map_layer(
            out_dir,
            name,
            ctx,
            meta,
            {
                "rails_geojson": rails_geo,
                "title": name,
                "layerStyle": {"type": "highlight", "highlight": highlight},
                "points": pts,
                "lines": lines_geo,
            },
        )
        names.append(name)

    cbd_poly = ctx["zones"][ctx["zones"]["zone_id"] == "CBD"].geometry.iloc[0]
    save_verify(
        "verify_cbd",
        "CBD",
        ctx["poi"][ctx["poi"]["biz"] & ctx["poi"].intersects(cbd_poly.buffer(150))],
        "#FFB300",
        buf_lines,
        station_pt,
    )
    save_verify("verify_living", "living", ctx["poi"][ctx["poi"]["commercial"]], "#FF6D00")
    save_verify("verify_cbd2", "CBD", ctx["poi"][ctx["poi"]["biz"]], "#FFB300", None, station_pt)
    ent = ctx["zones"][ctx["zones"]["zone_id"] == "entertain"].geometry.iloc[0]
    save_verify("verify_entertain", "entertain", ctx["poi"][ctx["poi"].intersects(ent)], "#FF6D00")
    cult = ctx["zones"][ctx["zones"]["zone_id"] == "culture"].geometry.iloc[0]
    save_verify("verify_culture", "culture", ctx["poi"][ctx["poi"].intersects(cult)], "#5C6BC0")
    return names


def export_matrix_chart(stats) -> str:
    fit = gz.compute_suitability_matrix(stats)
    payload = {
        "id": "matrix",
        "type": "matrix",
        "title": "功能适配度矩阵",
        "rowLabels": ["高端商务", "品质住宅", "休闲商业", "文创文化"],
        "colLabels": ["高端商务", "品质住宅", "休闲商业", "文创文化"],
        "values": fit.values.tolist(),
    }
    return payload


def export_all(out_dir: Path | None = None) -> list[str]:
    apply_dark_theme()
    out_dir = out_dir or OUT_ROOT
    out_dir.mkdir(parents=True, exist_ok=True)
    ctx = gz.load_context()
    stats = gz.zone_stats(ctx)
    logic = zsl.compute_spatial_logic(ctx)

    meta = export_base_map(ctx, out_dir)
    export_buildings_geojson(ctx, out_dir)
    names = export_logic_layers(ctx, logic, meta, out_dir)
    names.extend(export_verify_layers(ctx, logic, meta, out_dir))
    matrix = export_matrix_chart(stats)
    (out_dir / "matrix.json").write_text(json.dumps(matrix, ensure_ascii=False), encoding="utf-8")
    names.append("matrix")
    print(f"Map data exported: {len(names)} layers -> {out_dir}")
    return names


if __name__ == "__main__":
    export_all()
