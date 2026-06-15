# Fill In the Blank — 上海站城市设计 · 交互汇报站点

组员可共同编辑的 HTML 汇报页（POI 分析 + 功能分区逻辑/印证/矩阵）。

## 本地预览

```bat
start_site.bat
```

浏览器打开 http://localhost:8765/

或直接打开 `site/index.html`（地图底图需联网）。

## 重新生成站点

更新配图或 `build_site.py` 后：

```bat
python build_site.py
```

## 组员协作流程（GitHub）

1. **克隆仓库**
   ```bash
   git clone https://github.com/<你的用户名>/<仓库名>.git
   cd <仓库名>
   ```

2. **改内容**
   - 页面文案/结构：编辑后运行 `python build_site.py`（会更新 `site/js/pages-data.js`）
   - 样式：`site/css/style.css`
   - 交互逻辑：`site/js/app.js`、`site/js/leaflet-maps.js`、`site/js/map-viewer.js`
   - 配图：`site/assets/images/` 下对应图片，或改 `build_site.py` 中的提取逻辑

3. **提交并推送**
   ```bash
   git add .
   git commit -m "说明本次修改"
   git push
   ```

4. **合并**：在 GitHub 上开 Pull Request，或由管理员合并到 `main`。

## 在线演示（GitHub Pages，可选）

仓库 Settings → Pages → Source 选 **Deploy from branch** → Branch `main`，Folder **`/site`** → Save。

几分钟后访问：`https://<用户名>.github.io/<仓库名>/`

## 仓库结构

| 路径 | 说明 |
|------|------|
| `site/` | 可直接部署的静态网站 |
| `build_site.py` | 从 PDF/配图生成 `pages-data.js` 等 |
| `export_map_data.py` | 导出交互地图 GeoJSON |
| `源文件/` | PDF 源稿（若已纳入仓库） |

## 组员名单

董梓霖 · 刘幸彤 · 张炜煜 · 刘优燕
