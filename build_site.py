# -*- coding: utf-8 -*-
"""Build interactive HTML site — sections 64–85, dark theme, interactive maps."""
import json
import re
import shutil
import sys
from pathlib import Path

import fitz

ROOT = Path(r"F:\2026spring2\出图\html制作")
sys.path.insert(0, str(ROOT))
SRC = ROOT / "源文件"
ANALYSIS = Path(r"F:\2026spring2\四功能分区分析图")
OUT = ROOT / "site"
IMG = OUT / "assets" / "images"
EXTRACTED = OUT / "assets" / "extracted"
MAP_DATA = OUT / "assets" / "map-data"

LOGIC_TABS = [
    ("cliff", "POI Cliff", "分区逻辑/分图/01_Function_POI_Cliff_文字说明.txt"),
    ("entropy", "POI Entropy", "分区逻辑/分图/02_Function_POI_Entropy_文字说明.txt"),
    ("transect", "POI 断崖剖面", "分区逻辑/分图/03_Function_POI断崖剖面_文字说明.txt"),
    ("ped", "步行可达性", "分区逻辑/分图/07_Flow_步行可达性热力图_文字说明.txt"),
    ("frag", "Edge Fragmentation", "分区逻辑/分图/09_Morphology_EdgeFragmentation_文字说明.txt"),
    ("iface", "Interface Type", "分区逻辑/分图/10_Interface_UrbanInterfaceType_文字说明.txt"),
    ("final", "空间逻辑分区", "分区逻辑/分图/06_Final空间逻辑分区_文字说明.txt"),
]

VERIFY_TABS = [
    ("cbd", "CBD 高端商务", "分图/02_图1_CBD枢纽商务/02_文字说明.txt"),
    ("living", "番瓜弄住宅区", "分图/03_图2_番瓜弄住宅更新/02_文字说明.txt"),
    ("cbd2", "CBD 枢纽论证", "分图/02_图1_CBD枢纽商务/02_文字说明.txt"),
    ("entertain", "休闲商业区", "分图/04_图3_休闲商业更新/02_文字说明.txt"),
    ("culture", "文创园区", "分图/05_图4_文创传承激活/02_文字说明.txt"),
]

POI_CLUSTER_LABELS = [
    "聚类态 01 · 交通设施",
    "聚类态 02 · 住宿服务",
    "聚类态 03 · 体育休闲",
    "聚类态 04 · 公共设施",
    "聚类态 05 · 公司企业",
    "聚类态 06 · 医疗保健",
    "聚类态 07 · 商务住宅",
    "聚类态 08 · 地名地址",
    "聚类态 09 · 室内设施",
    "聚类态 10 · 摩托车服务",
    "聚类态 11 · 政府机构",
    "聚类态 12 · 汽车服务",
]


def ensure_dirs():
    IMG.mkdir(parents=True, exist_ok=True)
    EXTRACTED.mkdir(parents=True, exist_ok=True)
    MAP_DATA.mkdir(parents=True, exist_ok=True)


def save_pdf_embedded_image(pdf_num: int, img_index: int, rel_name: str, max_width: int = 1400) -> str:
    pdf_path = SRC / f"{pdf_num}.pdf"
    if not pdf_path.exists():
        return ""
    doc = fitz.open(pdf_path)
    page = doc[0]
    imgs = page.get_images()
    if img_index >= len(imgs):
        doc.close()
        return ""
    xref = imgs[img_index][0]
    pix = fitz.Pixmap(doc, xref)
    if pix.n - pix.alpha > 3:
        pix = fitz.Pixmap(fitz.csRGB, pix)
    dest = IMG / rel_name
    dest.parent.mkdir(parents=True, exist_ok=True)
    pix.save(str(dest))
    doc.close()
    return f"assets/images/{rel_name.replace(chr(92), '/')}"


def copy_asset(src: Path, rel_name: str) -> str:
    if not src.exists():
        return ""
    dest = IMG / rel_name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return f"assets/images/{rel_name.replace(chr(92), '/')}"


def parse_summary(text: str) -> dict:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    title = lines[0] if lines else ""
    purpose, analysis_lines, conclusion_lines, formula_lines = [], [], [], []
    section = None
    for ln in lines[1:]:
        if ln.startswith("【一"):
            section = "purpose"
            continue
        if ln.startswith("【二"):
            section = "data"
            continue
        if ln.startswith("【三"):
            section = "formula"
            continue
        if ln.startswith("【四"):
            section = "analysis"
            continue
        if ln.startswith("【六"):
            section = "conclusion"
            continue
        if section == "purpose":
            purpose.append(ln)
        elif section == "analysis":
            analysis_lines.append(ln)
        elif section == "conclusion":
            conclusion_lines.append(ln)
        elif section == "formula":
            formula_lines.append(ln)

    metrics = []
    for ln in analysis_lines + formula_lines:
        s = ln.lstrip("·▸ ").strip()
        if s and (re.search(r"\d", s) or "ρ" in s or "=" in s or "%" in s or "×" in s):
            metrics.append(s)
    if not metrics:
        metrics = [ln.lstrip("· ").strip() for ln in analysis_lines[:6]]

    return {
        "title": title,
        "purpose": " ".join(purpose)[:500],
        "metrics": metrics[:8],
        "conclusions": [ln.lstrip("▸ ").strip() for ln in conclusion_lines][:6],
    }


def load_txt(rel: str) -> str:
    p = ANALYSIS / rel
    return p.read_text(encoding="utf-8") if p.exists() else ""


def build_poi_cluster():
    tabs = []
    for i in range(12):
        pdf_num = 64 if i < 6 else 65
        img_idx = i if i < 6 else i - 6
        url = save_pdf_embedded_image(pdf_num, img_idx, f"poi/cluster_{i+1:02d}.png")
        tabs.append(
            {
                "id": f"poi-{i+1}",
                "label": POI_CLUSTER_LABELS[i],
                "image": url,
            }
        )
    return {
        "id": "poi-cluster",
        "tag": "64–65",
        "title": "POI 聚类分析",
        "subtitle": "业态类型 × 空间聚类态",
        "layout": "tabs-left-image",
        "intro": "基于红线内 POI 与空间单元，识别 12 类业态—空间组合态；切换按钮查看各聚类态在基地内的分布。",
        "tabs": tabs,
        "stats": [
            {"label": "聚类态", "value": "12"},
            {"label": "范围", "value": "红线内"},
            {"label": "方法", "value": "GMM 聚类"},
            {"label": "底图", "value": "城市肌理"},
        ],
        "summary": {
            "purpose": "将红线内 POI 按业态与空间形态聚类，形成 12 类可识别的组合态，为后续功能分区提供微观结构依据。",
            "metrics": [
                "12 类聚类态覆盖红线内主要 POI 组合",
                "每类对应一种业态核与空间集聚特征",
                "聚类结果叠加城市肌理底图展示",
            ],
            "conclusions": [
                "不同聚类态在空间上呈分区集聚，而非均匀散布",
                "站前与南侧传统商业街聚类态类型更丰富",
                "北侧与铁路背侧以低密度、单一功能聚类为主",
            ],
        },
    }


def build_poi_three_types():
    img66 = save_pdf_embedded_image(66, 0, "poi/three_types_66.png")
    return {
        "id": "poi-three-types",
        "tag": "66–67",
        "title": "三种POI点分析",
        "subtitle": "商业服务 · 文化教育 · 公服消费",
        "layout": "single-left-image",
        "images": [img66],
        "stats": [
            {"label": "POI 大类", "value": "3"},
            {"label": "商业与服务", "value": "绿"},
            {"label": "文化与教育", "value": "蓝"},
            {"label": "公服与消费", "value": "橙"},
        ],
        "summary": {
            "purpose": "将红线内 POI 归纳为商业与服务、文化与教育、公服与消费三大类，对比三类点位在基地南北方向上的分布密度与结构差异。",
            "metrics": [
                "商业与服务：站前西侧及南侧传统商业街密度最高",
                "文化与教育：整体稀疏，零星分布于站南与中部",
                "公服与消费：南侧带状集聚，北侧明显衰减",
                "三类 POI 在铁路南北呈现不同集聚中心",
            ],
            "conclusions": [
                "三类 POI 并非均匀分布，南侧公服与消费最为密集",
                "北侧文化与教育类 POI 明显不足",
                "铁路廊道对三类 POI 的连续分布均构成切割",
            ],
        },
    }


USER_POI_SCATTER = Path(
    r"C:\Users\17862\.cursor\projects\f-2026spring2\assets\c__Users_17862_AppData_Roaming_Cursor_User_workspaceStorage_b82374c18f70e7480895c415ef0b9867_images______2026-06-16_025501-f1fdaafb-0220-44af-8746-2795c1bd14e7.png"
)
USER_POI_CLIFF = Path(
    r"C:\Users\17862\.cursor\projects\f-2026spring2\assets\c__Users_17862_AppData_Roaming_Cursor_User_workspaceStorage_b82374c18f70e7480895c415ef0b9867_images______2026-06-16_025517-3f2793b5-e9fb-45d5-9073-182674fb69b0.png"
)


def build_poi_density():
    scatter = copy_asset(USER_POI_SCATTER, "poi/density_scatter.png")
    cliff = copy_asset(USER_POI_CLIFF, "poi/density_cliff.png")
    tabs = [
        {
            "id": "density-scatter",
            "label": "纬度散点分布",
            "image": scatter,
            "summary": {
                "purpose": "沿纬度方向展示三类 POI 大类的空间散点分布，横轴为纬度（南→北），纵轴为密度层级，用于识别南北密度带。",
                "metrics": [
                    "绿色：商业与服务 — 南侧高密度带",
                    "蓝色：文化与教育 — 整体低密度、零星分布",
                    "橙色：公服与消费 — 南侧最宽密度带",
                    "铁路附近三类点位均出现明显稀疏区",
                ],
                "conclusions": [
                    "三类 POI 在纬度上呈分层而非连续均匀",
                    "南侧形成多类 POI 叠合的高强度带",
                    "北侧以低密度散点为主，功能结构单一",
                ],
            },
        },
        {
            "id": "density-cliff",
            "label": "断崖折线剖面",
            "image": cliff,
            "summary": {
                "purpose": "沿南→北距离剖面统计三类 POI 密度，量化「老静安—原闸北」交界处的断崖式下降（CLIFF）。",
                "metrics": [
                    "剖面距离约 0–8 km（南→北）",
                    "断崖位置约 4.5 km 处，密度骤降",
                    "南侧峰值：公服与消费 > 商业与服务 > 文化教育",
                    "北侧三类密度均降至低位平台",
                ],
                "conclusions": [
                    "由南向北推进时，活力并非平缓衰减，而在两区交界出现断崖式下降",
                    "南侧持续集聚高强度商业与公服功能",
                    "跨越界线后 POI 数量迅速减弱，空间功能趋于稀疏单一",
                ],
            },
        },
    ]
    return {
        "id": "poi-density",
        "tag": "68–71",
        "title": "POI 大类密度分析",
        "subtitle": "纬度散点 + 断崖折线剖面",
        "layout": "tabs-left-image",
        "tabs": tabs,
        "stats": [
            {"label": "大类", "value": "3"},
            {"label": "剖面", "value": "南→北"},
            {"label": "断崖", "value": "~4.5 km"},
            {"label": "方法", "value": "密度剖面"},
        ],
    }


def build_logic_panel():
    tabs = []
    for key, label, txt_rel in LOGIC_TABS:
        entry = {
            "id": key,
            "label": label,
            "summary": parse_summary(load_txt(txt_rel)),
        }
        if key == "transect":
            entry["chartLayer"] = "logic_transect"
        else:
            entry["mapLayer"] = f"logic_{key}"
        tabs.append(entry)
    return {
        "id": "zoning-logic",
        "tag": "72–78",
        "title": "功能分区逻辑",
        "subtitle": "Cliff → Entropy → Flow → Frag → Interface → Zoning",
        "layout": "tabs-left-image",
        "group": "design-zoning",
        "tabs": tabs,
        "stats": [
            {"label": "证据链", "value": "6 步"},
            {"label": "格网", "value": "80 m"},
            {"label": "界面", "value": "4 类"},
            {"label": "语境", "value": "1200 m"},
        ],
    }


def build_verify_panel():
    tabs = []
    for key, label, txt_rel in VERIFY_TABS:
        tabs.append(
            {
                "id": key,
                "label": label,
                "mapLayer": f"verify_{key}",
                "summary": parse_summary(load_txt(txt_rel)),
            }
        )
    return {
        "id": "zoning-verify",
        "tag": "79–83",
        "title": "功能分区印证",
        "subtitle": "分区后指标验证与排他性论证",
        "layout": "tabs-left-image",
        "group": "design-zoning",
        "tabs": tabs,
        "stats": [
            {"label": "分区", "value": "4"},
            {"label": "CBD 距站", "value": "346 m"},
            {"label": "文创距站", "value": "1181 m"},
            {"label": "方法", "value": "POI+空间"},
        ],
    }


def build_matrix_panel():
    txt = load_txt("分图/06_图6_功能适配矩阵/02_文字说明.txt")
    full = parse_summary(txt)
    return {
        "id": "zoning-matrix",
        "tag": "84–85",
        "title": "功能适配度矩阵",
        "subtitle": "四区 × 四功能列归一化得分",
        "layout": "tabs-left-image",
        "group": "design-zoning",
        "tabs": [
            {
                "id": "matrix-result",
                "label": "适配矩阵",
                "matrixLayer": "matrix",
                "summary": full,
            },
        ],
        "stats": [
            {"label": "矩阵", "value": "4×4"},
            {"label": "得分", "value": "0–100"},
            {"label": "归一化", "value": "列内"},
            {"label": "对角线", "value": "最优"},
        ],
    }


def export_map_layers():
    try:
        import export_map_data as md

        md.export_all(MAP_DATA)
    except Exception as exc:
        print(f"Map layer export failed: {exc}")


def embed_map_layers_js():
    layers = {}
    for f in sorted(MAP_DATA.glob("*.json")):
        if f.name == "base.json":
            continue
        layers[f.stem] = json.loads(f.read_text(encoding="utf-8"))
    base_path = MAP_DATA / "base.json"
    base = json.loads(base_path.read_text(encoding="utf-8")) if base_path.exists() else {}
    buildings_path = MAP_DATA / "buildings.geojson"
    buildings = (
        json.loads(buildings_path.read_text(encoding="utf-8")) if buildings_path.exists() else None
    )
    out = OUT / "js" / "map-layers-data.js"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "window.MAP_BASE=" + json.dumps(base, ensure_ascii=False) + ";\n"
        + "window.MAP_GEO=" + json.dumps({"buildings": buildings}, ensure_ascii=False) + ";\n"
        + "window.MAP_LAYERS=" + json.dumps(layers, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )


def generate_html():
    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Fill In the Blank — 上海站城市设计</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <link rel="stylesheet" href="css/style.css" />
</head>
<body>
  <header class="site-header">
    <div class="site-logo">上海站 · <span>Fill In the Blank</span></div>
    <nav class="header-nav" id="header-nav"></nav>
  </header>
  <nav class="side-nav" id="side-nav" aria-label="章节"></nav>
  <main id="main"></main>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script src="js/pages-data.js"></script>
  <script src="js/map-layers-data.js"></script>
  <script src="js/map-viewer.js"></script>
  <script src="js/leaflet-maps.js"></script>
  <script src="js/app.js"></script>
</body>
</html>"""
    (OUT / "index.html").write_text(html, encoding="utf-8")


def main():
    ensure_dirs()
    export_map_layers()
    embed_map_layers_js()
    pages = [
        {
            "id": "index",
            "type": "index",
            "title": "研究框架",
            "links": [
                {"id": "poi-cluster", "num": "64–65", "label": "POI 聚类分析"},
                {"id": "poi-three-types", "num": "66–67", "label": "三种POI点分析"},
                {"id": "poi-density", "num": "68–71", "label": "POI 大类密度分析"},
                {"id": "zoning-logic", "num": "72–78", "label": "功能分区逻辑"},
                {"id": "zoning-verify", "num": "79–83", "label": "功能分区印证"},
                {"id": "zoning-matrix", "num": "84–85", "label": "功能适配矩阵"},
            ],
        },
        build_poi_cluster(),
        build_poi_three_types(),
        build_poi_density(),
        build_logic_panel(),
        build_verify_panel(),
        build_matrix_panel(),
    ]
    pages_js = OUT / "js" / "pages-data.js"
    pages_js.parent.mkdir(parents=True, exist_ok=True)
    pages_js.write_text("window.PAGES_DATA = " + json.dumps(pages, ensure_ascii=False) + ";\n", encoding="utf-8")
    (OUT / "pages.json").write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")
    generate_html()
    print(f"Done -> {OUT / 'index.html'}")


if __name__ == "__main__":
    main()
