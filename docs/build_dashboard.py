from __future__ import annotations

import csv
import html
from pathlib import Path


DASHBOARD_DIR = Path(__file__).resolve().parent
CATALOG_PATH = DASHBOARD_DIR / "figure_catalog.csv"
OUTPUT_PATH = DASHBOARD_DIR / "index.html"


def read_catalog() -> list[dict[str, str]]:
    with CATALOG_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def order_value(row: dict[str, str]) -> float:
    try:
        return float(row.get("order", ""))
    except (TypeError, ValueError):
        return float("inf")


def image_card(row: dict[str, str]) -> str:
    title = html.escape(row.get("title", "Untitled figure"))
    description = html.escape(row.get("description", ""))
    image = html.escape(row.get("image", ""), quote=True)
    metric = html.escape(row.get("metric_type", ""))
    metric_badge = f'<span class="badge">{metric}</span>' if metric else ""

    return f"""
    <article class="figure-card">
      <div class="figure-title-row"><h3>{title}</h3>{metric_badge}</div>
      <p>{description}</p>
      <img src="{image}" alt="{title}" loading="lazy">
    </article>
    """


def static_gallery(rows: list[dict[str, str]]) -> str:
    if not rows:
        return '<p class="empty">No figures are available.</p>'
    return '<div class="gallery">' + "".join(image_card(row) for row in rows) + "</div>"


def selector_gallery(
    rows: list[dict[str, str]],
    selector_id: str,
    label: str,
) -> str:
    if not rows:
        return '<p class="empty">No figures are available.</p>'

    options = []
    figures = []
    for index, row in enumerate(rows):
        selector = row.get("selector", "") or row.get("title", f"Figure {index + 1}")
        options.append(
            f'<option value="{index}">{html.escape(str(selector))}</option>'
        )
        display = "block" if index == 0 else "none"
        figures.append(
            f'<div id="{selector_id}-figure-{index}" '
            f'class="selectable-figure {selector_id}-figure" style="display:{display}">'
            f'{image_card(row)}</div>'
        )

    return f"""
    <div class="selector-row">
      <label for="{selector_id}">{html.escape(label)}</label>
      <select id="{selector_id}" onchange="switchFigure('{selector_id}', this.value)">
        {''.join(options)}
      </select>
    </div>
    <div>{''.join(figures)}</div>
    """


def main() -> None:
    rows = read_catalog()
    rows.sort(key=order_value)

    overview = [row for row in rows if row.get("section") == "Overview"]

    subreddit_year = [
        row for row in rows
        if row.get("section") == "Subreddit" and row.get("subsection") == "Year"
    ]
    subreddit_category = [
        row for row in rows
        if row.get("section") == "Subreddit" and row.get("subsection") == "Category"
    ]
    subreddit_demographic = [
        row for row in rows
        if row.get("section") == "Subreddit" and row.get("subsection") == "Demographic"
    ]

    product_overview = [
        row for row in rows
        if row.get("section") == "AI Product"
        and row.get("subsection") == "Overview"
    ]
    products = [
        row for row in rows
        if row.get("section") == "AI Product"
        and row.get("subsection") == "Product"
    ]

    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Reddit AI Discussion Dashboard</title>
  <style>
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{ margin: 0; background: #f3f5f7; color: #263238; font-family: Arial, Helvetica, sans-serif; }}
    header {{ padding: 30px 5%; background: #263238; color: white; }}
    header h1 {{ margin: 0; font-size: 30px; }}
    header p {{ margin: 9px 0 0; color: #d5dde1; }}
    nav {{ position: sticky; top: 0; z-index: 10; padding: 14px 5%; background: white; box-shadow: 0 2px 9px rgba(0,0,0,.09); }}
    nav a {{ margin-right: 25px; color: #263238; text-decoration: none; font-weight: 700; }}
    main {{ width: min(1500px, 96%); margin: 30px auto 60px; }}
    .main-section {{ margin-bottom: 34px; padding: 26px; border-radius: 12px; background: white; box-shadow: 0 2px 12px rgba(0,0,0,.08); }}
    .main-section > h2 {{ margin: 0 0 22px; font-size: 25px; border-bottom: 3px solid #4c78a8; padding-bottom: 9px; }}
    .subsection {{ margin: 30px 0 10px; }}
    .subsection:first-of-type {{ margin-top: 5px; }}
    .subsection > h3 {{ margin: 0 0 16px; font-size: 20px; }}
    .gallery {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(min(560px, 100%), 1fr)); gap: 24px; }}
    .figure-card {{ padding: 17px; border: 1px solid #dce3e7; border-radius: 9px; background: #fff; }}
    .figure-title-row {{ display: flex; align-items: start; justify-content: space-between; gap: 12px; }}
    .figure-card h3 {{ margin: 0; font-size: 17px; }}
    .figure-card p {{ min-height: 2.5em; color: #607078; line-height: 1.45; }}
    .figure-card img {{ display: block; width: 100%; height: auto; border-radius: 4px; }}
    .badge {{ flex: 0 0 auto; padding: 4px 8px; border-radius: 12px; background: #e7eef5; color: #355c7d; font-size: 12px; }}
    .selector-row {{ display: flex; align-items: center; gap: 13px; margin: 0 0 20px; padding: 15px; background: #eef2f4; border-radius: 8px; }}
    .selector-row label {{ font-weight: 700; }}
    select {{ min-width: 280px; padding: 10px 12px; border: 1px solid #aab7bd; border-radius: 6px; background: white; font-size: 15px; }}
    .selectable-figure .figure-card {{ max-width: 1250px; margin: 0 auto; }}
    .empty {{ color: #718087; font-style: italic; }}
    footer {{ padding: 25px; text-align: center; color: #718087; }}
    @media (max-width: 700px) {{
      nav a {{ display: inline-block; margin-bottom: 7px; }}
      .selector-row {{ display: block; }}
      select {{ width: 100%; min-width: 0; margin-top: 8px; }}
      .main-section {{ padding: 18px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Reddit AI Discussion Dashboard</h1>
    <p>Discussion volume, sentiment, subreddit characteristics, and AI products</p>
  </header>

  <nav>
    <a href="#overview">1. Overview</a>
    <a href="#subreddit">2. Subreddit</a>
    <a href="#ai-product">3. AI Product</a>
  </nav>

  <main>
    <section id="overview" class="main-section">
      <h2>1. Overview</h2>
      {static_gallery(overview)}
    </section>

    <section id="subreddit" class="main-section">
      <h2>2. Subreddit</h2>

      <div class="subsection">
        <h3>2.1 Year</h3>
        {selector_gallery(subreddit_year, "year-selector", "Select year:")}
      </div>

      <div class="subsection">
        <h3>2.2 Category</h3>
        {static_gallery(subreddit_category)}
      </div>

      <div class="subsection">
        <h3>2.3 Demographic</h3>
        {static_gallery(subreddit_demographic)}
      </div>
    </section>

    <section id="ai-product" class="main-section">
      <h2>3. AI Product</h2>

      <div class="subsection">
        <h3>3.1 Overview</h3>
        {static_gallery(product_overview)}
      </div>

      <div class="subsection">
        <h3>3.2 Product</h3>
        {selector_gallery(products, "product-selector", "Select AI product:")}
      </div>
    </section>
  </main>

  <footer>Generated from figure_catalog.csv</footer>

  <script>
    function switchFigure(selectorId, selectedIndex) {{
      document.querySelectorAll('.' + selectorId + '-figure').forEach(function(element) {{
        element.style.display = 'none';
      }});
      const selected = document.getElementById(selectorId + '-figure-' + selectedIndex);
      if (selected) selected.style.display = 'block';
    }}
  </script>
</body>
</html>
"""

    OUTPUT_PATH.write_text(page, encoding="utf-8")
    print(f"Dashboard generated: {OUTPUT_PATH}")
    print(f"Catalog rows: {len(rows)}")


if __name__ == "__main__":
    main()
