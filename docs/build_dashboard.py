from __future__ import annotations

import csv
import html
from pathlib import Path


DASHBOARD_DIR = Path(__file__).resolve().parent
CATALOG_PATH = DASHBOARD_DIR / "figure_catalog.csv"
OUTPUT_PATH = DASHBOARD_DIR / "index.html"


def read_catalog() -> list[dict[str, str]]:
    with CATALOG_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [row for row in rows if row.get("title", "").strip()]


def resolve_replacements(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Apply catalog change states without mutating the catalog itself.

    remain: keep the existing row unchanged.
    replaced: omit it when a same-title replacing row exists.
    replacing: display it in place of the same-title replaced row.
    add: append it as a new figure.
    """
    allowed_states = {"remain", "replaced", "replacing", "add"}
    replacement_rows: dict[str, dict[str, str]] = {}
    replaced_titles = {
        row.get("title", "").strip()
        for row in rows
        if row.get("replace", "").strip().lower() == "replaced"
    }

    for row in rows:
        state = row.get("replace", "").strip().lower()
        title = row.get("title", "").strip()
        if state not in allowed_states:
            raise ValueError(f"Unknown replace state {state!r} for {title!r}")
        if state == "replacing":
            if title in replacement_rows:
                raise ValueError(f"Multiple replacing rows found for {title!r}")
            if title not in replaced_titles:
                raise ValueError(
                    f"Replacing row {title!r} has no same-title replaced row"
                )
            replacement_rows[title] = row

    missing_replacements = replaced_titles.difference(replacement_rows)
    if missing_replacements:
        raise ValueError(
            "Replaced rows without same-title replacements: "
            + ", ".join(sorted(missing_replacements))
        )

    resolved = []
    for row in rows:
        state = row.get("replace", "").strip().lower()
        title = row.get("title", "").strip()
        if state == "replaced":
            resolved.append(replacement_rows[title])
        elif state in {"remain", "add"}:
            resolved.append(row)
        # A replacing row was already inserted at its replaced row's position.

    missing_images = [
        row.get("image", "")
        for row in resolved
        if not (DASHBOARD_DIR / row.get("image", "")).is_file()
    ]
    if missing_images:
        raise FileNotFoundError(
            "Catalog images not found: " + ", ".join(missing_images)
        )
    return resolved


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
    catalog_rows = read_catalog()
    rows = resolve_replacements(catalog_rows)
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
    subreddit_demographic_all = [
        row for row in rows
        if row.get("section") == "Subreddit" and row.get("subsection") == "Demographic"
    ]
    subreddit_yearly_effects = [
        row for row in subreddit_demographic_all
        if row.get("title", "").startswith("Year-specific regression effect of ")
    ]
    subreddit_demographic = [
        row for row in subreddit_demographic_all
        if row not in subreddit_yearly_effects
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
    version_regression = [
        row for row in rows
        if row.get("section") == "Version_Decomposition"
        and row.get("subsection") == "Regression"
    ]
    version_regression_standalone = version_regression[:2]
    version_level_differences = version_regression[2:7]
    version_specific_trends = version_regression[7:11]
    version_mean_score = [
        row for row in rows
        if row.get("section") == "Version_Decomposition"
        and row.get("subsection") == "Mean Score"
    ]
    version_trend = [
        row for row in rows
        if row.get("section") == "Version_Decomposition"
        and row.get("subsection") == "Trend"
    ]
    version_release_period_trend = [
        row for row in rows
        if row.get("section") == "Version_Decomposition"
        and row.get("subsection") == "Release Period Trend"
    ]
    version_release_period_regression = [
        row for row in rows
        if row.get("section") == "Version_Decomposition"
        and row.get("subsection") == "Release Period Regression"
    ]

    mechanism_user = [
        row for row in rows
        if row.get("section") == "Mechanism"
        and row.get("subsection") == "User_Cohort"
    ]
    mechanism_community = [
        row for row in rows
        if row.get("section") == "Mechanism"
        and row.get("subsection") == "Community_Cohort"
    ]
    control_general_overview = [
        row for row in rows
        if row.get("section") == "Control_General"
        and row.get("subsection") == "Overview"
    ]
    control_general_community = [
        row for row in rows
        if row.get("section") == "Control_General"
        and row.get("subsection") == "Community"
    ]
    control_general_lifecycle = [
        row for row in rows
        if row.get("section") == "Control_General"
        and row.get("subsection") == "Lifecycle"
    ]
    control_individual_overview = [
        row for row in rows
        if row.get("section") == "Control_Individual"
        and row.get("subsection") == "Overview"
    ]
    control_individual_monthly_count = [
        row for row in rows
        if row.get("section") == "Control_Individual"
        and row.get("subsection") == "Monthly Count"
    ]
    control_individual_monthly_sentiment = [
        row for row in rows
        if row.get("section") == "Control_Individual"
        and row.get("subsection") == "Monthly Sentiment"
    ]
    control_individual_monthly_share = [
        row for row in rows
        if row.get("section") == "Control_Individual"
        and row.get("subsection") == "Monthly Sentiment Share"
    ]
    control_individual_annual = [
        row for row in rows
        if row.get("section") == "Control_Individual"
        and row.get("subsection") == "Annual"
    ]
    control_other_products_benchmark = [
        row for row in rows
        if row.get("section") == "Control_Other_Products"
        and row.get("subsection") == "Benchmark"
    ]
    control_other_products_count = [
        row for row in rows
        if row.get("section") == "Control_Other_Products"
        and row.get("subsection") == "Monthly Count"
    ]
    control_other_products_sentiment = [
        row for row in rows
        if row.get("section") == "Control_Other_Products"
        and row.get("subsection") == "Monthly Sentiment"
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
    .nested-heading {{ margin-top: 30px !important; padding-top: 20px; border-top: 1px solid #dce3e7; }}
    .gallery {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(min(560px, 100%), 1fr)); gap: 24px; }}
    .figure-card {{ padding: 17px; border: 1px solid #dce3e7; border-radius: 9px; background: #fff; }}
    .figure-title-row {{ display: flex; align-items: start; justify-content: space-between; gap: 12px; }}
    .figure-card h3 {{ margin: 0; font-size: 17px; }}
    .figure-card p {{ min-height: 2.5em; color: #607078; line-height: 1.45; white-space: pre-line; }}
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
    <p>Discussion volume, sentiment, subreddit characteristics, AI products, and mechanisms</p>
  </header>

  <nav>
    <a href="#overview">1. Overview</a>
    <a href="#subreddit">2. Subreddit</a>
    <a href="#ai-product">3. AI Product</a>
    <a href="#mechanism">4. Mechanism</a>
    <a href="#version-decomposition">5. Version Decomposition</a>
    <a href="#control-general">6. Control General</a>
    <a href="#control-individual">7. Control Individual</a>
    <a href="#control-other-products">8. Other Tech Products</a>
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

        <h3 class="nested-heading">Year-specific Regression Effects</h3>
        {selector_gallery(
            subreddit_yearly_effects,
            "yearly-effect-selector",
            "Select predictor:",
        )}
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

    <section id="mechanism" class="main-section">
      <h2>4. Mechanism</h2>

      <div class="subsection">
        <h3>4.1 User Cohort</h3>
        {static_gallery(mechanism_user)}
      </div>

      <div class="subsection">
        <h3>4.2 Community Cohort</h3>
        {static_gallery(mechanism_community)}
      </div>
    </section>

    <section id="version-decomposition" class="main-section">
      <h2>5. Version Decomposition</h2>

      <div class="subsection">
        <h3>5.1 Mean Score</h3>
        {selector_gallery(
            version_mean_score,
            "version-mean-score-selector",
            "Select AI product:",
        )}
      </div>

      <div class="subsection">
        <h3>5.2 Trend</h3>
        {selector_gallery(
            version_trend,
            "version-trend-selector",
            "Select AI product:",
        )}
      </div>

      <div class="subsection">
        <h3>5.3 Regression</h3>
        {static_gallery(version_regression_standalone)}

        <h3 class="nested-heading">Model-version Sentiment Differences</h3>
        {selector_gallery(
            version_level_differences,
            "version-level-difference-selector",
            "Select AI product:",
        )}

        <h3 class="nested-heading">Model-specific Sentiment Trends</h3>
        {selector_gallery(
            version_specific_trends,
            "version-specific-trend-selector",
            "Select AI product:",
        )}
      </div>

      <div class="subsection">
        <h3>5.4 Release-period Decomposition</h3>

        <h3 class="nested-heading">Weekly Trends by Release Period</h3>
        {selector_gallery(
            version_release_period_trend,
            "release-period-trend-selector",
            "Select AI product:",
        )}

        <h3 class="nested-heading">Release-period Regression Effects</h3>
        {static_gallery(version_release_period_regression)}
      </div>
    </section>

    <section id="control-general" class="main-section">
      <h2>6. Control General</h2>

      <div class="subsection">
        <h3>6.1 Overall Monthly Trends</h3>
        {static_gallery(control_general_overview)}
      </div>

      <div class="subsection">
        <h3>6.2 Community Characteristics</h3>
        {static_gallery(control_general_community)}
      </div>

      <div class="subsection">
        <h3>6.3 User Lifecycle</h3>
        {static_gallery(control_general_lifecycle)}
      </div>
    </section>

    <section id="control-individual" class="main-section">
      <h2>7. Control Individual</h2>

      <div class="subsection">
        <h3>7.1 Overview</h3>
        {static_gallery(control_individual_overview)}
      </div>

      <div class="subsection">
        <h3>7.2 Monthly Matched-sentence Count</h3>
        {selector_gallery(
            control_individual_monthly_count,
            "control-individual-count-selector",
            "Select page:",
        )}
      </div>

      <div class="subsection">
        <h3>7.3 Monthly Mean Sentiment</h3>
        {selector_gallery(
            control_individual_monthly_sentiment,
            "control-individual-sentiment-selector",
            "Select page:",
        )}
      </div>

      <div class="subsection">
        <h3>7.4 Monthly Sentiment-label Shares</h3>
        {selector_gallery(
            control_individual_monthly_share,
            "control-individual-share-selector",
            "Select page:",
        )}
      </div>

      <div class="subsection">
        <h3>7.5 Annual Overview</h3>
        {static_gallery(control_individual_annual)}
      </div>
    </section>

    <section id="control-other-products" class="main-section">
      <h2>8. Other Tech Products</h2>

      <div class="subsection">
        <h3>8.1 Comparisons with AI Benchmarks</h3>
        {static_gallery(control_other_products_benchmark)}
      </div>

      <div class="subsection">
        <h3>8.2 Monthly Product Volume</h3>
        {selector_gallery(
            control_other_products_count,
            "control-other-products-count-selector",
            "Select page:",
        )}
      </div>

      <div class="subsection">
        <h3>8.3 Monthly Product Sentiment</h3>
        {selector_gallery(
            control_other_products_sentiment,
            "control-other-products-sentiment-selector",
            "Select page:",
        )}
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
    print(f"Raw catalog rows: {len(catalog_rows)}")
    print(f"Displayed figures after replacement rules: {len(rows)}")


if __name__ == "__main__":
    main()
