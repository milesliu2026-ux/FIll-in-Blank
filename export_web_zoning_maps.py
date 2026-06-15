# -*- coding: utf-8 -*-
"""Export zoning analysis maps for web: light background + context buildings (世界底图)."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt

SCRIPTS = Path(r"F:\2026spring2\form-function-flow-main\form-function-flow-main\scripts")
sys.path.insert(0, str(SCRIPTS))

import generate_zone_rationale_dark_suite as gz  # noqa: E402
import zone_spatial_logic as zsl  # noqa: E402

WEB_BG = "#f4f4f2"
WEB_CONTEXT_M = 1200
WEB_DPI = 150
WEB_FIG_MAP = (9.0, 7.2)
WEB_FIG_CHART = (9.0, 5.5)


def apply_web_theme() -> None:
    gz.CONTEXT_BUFFER_M = WEB_CONTEXT_M
    gz.BG_TRANSPARENT = WEB_BG
    gz.BUILD_OUT_FILL = "#d4d4d4"
    gz.BUILD_OUT_EDGE = "#b0b0b0"
    gz.BUILD_IN_FILL = "#e6e6e6"
    gz.BUILD_IN_EDGE = "#888888"
    gz.TEXT_MAIN = "#222222"
    gz.TEXT_DIM = "#555555"
    gz.LEGEND_FC = "#f0f0ee"
    gz.LEGEND_EC = "#cccccc"
    gz.LEGEND_TEXT = "#333333"

    def style_map_ax(ax):
        ax.set_facecolor(WEB_BG)
        ax.patch.set_alpha(1.0)

    def style_chart_ax(ax):
        ax.set_facecolor(WEB_BG)
        ax.patch.set_alpha(1.0)
        for spine in ("top", "right"):
            if spine in ax.spines:
                ax.spines[spine].set_visible(False)
        for spine in ("bottom", "left"):
            if spine in ax.spines:
                ax.spines[spine].set_color("#aaaaaa")
        ax.tick_params(colors=gz.TEXT_DIM)
        if ax.title:
            ax.title.set_color(gz.TEXT_MAIN)
        ax.xaxis.label.set_color(gz.TEXT_DIM)
        ax.yaxis.label.set_color(gz.TEXT_DIM)

    gz.style_map_ax = style_map_ax
    gz.style_chart_ax = style_chart_ax

    plt.rcParams.update(
        {
            "font.sans-serif": ["SimHei", "Microsoft YaHei", "DejaVu Sans"],
            "axes.unicode_minus": False,
            "figure.facecolor": WEB_BG,
            "savefig.facecolor": WEB_BG,
            "savefig.transparent": False,
        }
    )


def save_web(fig, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.patch.set_facecolor(WEB_BG)
    fig.savefig(
        path,
        dpi=WEB_DPI,
        bbox_inches="tight",
        facecolor=WEB_BG,
        transparent=False,
        pad_inches=0.08,
    )
    plt.close(fig)
    return path


def export_logic_panels(ctx, logic: dict, out_dir: Path) -> list[Path]:
    specs = [
        ("logic_cliff", zsl._draw_panel_cliff, WEB_FIG_MAP, True),
        ("logic_entropy", zsl._draw_panel_entropy, WEB_FIG_MAP, True),
        ("logic_transect", zsl._draw_panel_transect, WEB_FIG_CHART, False),
        ("logic_ped", zsl._draw_panel_ped_access, WEB_FIG_MAP, True),
        ("logic_frag", zsl._draw_panel_edge_frag_site, WEB_FIG_MAP, True),
        ("logic_iface", zsl._draw_panel_interface_type_site, WEB_FIG_MAP, False),
        ("logic_final", zsl._draw_panel_final, WEB_FIG_MAP, False),
    ]
    saved = []
    for name, drawer, size, has_cbar in specs:
        fig, ax = plt.subplots(figsize=size)
        if drawer is zsl._draw_panel_final:
            drawer(ax, ctx, logic, gz, show_chain=True)
        elif has_cbar:
            drawer(ax, ctx, logic, gz, add_cbar=True, cbar_fig=fig)
        else:
            drawer(ax, ctx, logic, gz)
        saved.append(save_web(fig, out_dir / f"{name}.png"))
    return saved


def export_verify_maps(ctx, stats, out_dir: Path) -> list[Path]:
    exports = [
        ("verify_cbd", gz.map_01_cbd),
        ("verify_living", gz.map_02_living),
        ("verify_cbd2", gz.map_01_cbd),
        ("verify_entertain", gz.map_03_entertain),
        ("verify_culture", gz.map_04_culture),
    ]
    saved = []
    orig_save = gz._save
    for web_name, fn in exports:
        target = out_dir / f"{web_name}.png"

        def _save_hook(fig, path, meta=None, _target=target):
            save_web(fig, _target)

        gz._save = _save_hook
        fn(ctx, stats)
        saved.append(target)
    gz._save = orig_save
    return saved


def export_matrix(ctx, stats, out_dir: Path) -> Path:
    target = out_dir / "matrix.png"
    fit = gz.compute_suitability_matrix(stats)

    def _save_hook(fig, path, meta=None):
        save_web(fig, target)

    orig = gz._save
    gz._save = _save_hook
    gz.map_06_suitability_heatmap(ctx, stats, fit)
    gz._save = orig
    return target


def export_all(out_dir: Path) -> list[Path]:
    apply_web_theme()
    ctx = gz.load_context()
    stats = gz.zone_stats(ctx)
    logic = zsl.compute_spatial_logic(ctx)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    paths.extend(export_logic_panels(ctx, logic, out_dir))
    paths.extend(export_verify_maps(ctx, stats, out_dir))
    paths.append(export_matrix(ctx, stats, out_dir))
    print(f"Web maps exported -> {out_dir} ({len(paths)} files)")
    return paths


if __name__ == "__main__":
    export_all(Path(r"F:\2026spring2\出图\html制作\site\assets\images\zoning"))
