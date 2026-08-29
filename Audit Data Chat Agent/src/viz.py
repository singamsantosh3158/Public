"""Chart building for DAX query results.

Palette and form choices follow the project's data-viz guidelines: sequential
single-hue for plain magnitude comparisons, the fixed 8-hue categorical order
only when there are genuinely multiple series, never a rainbow, never dual-axis.
"""

from __future__ import annotations

import warnings

import pandas as pd
import plotly.graph_objects as go

# Fixed categorical hue order (validated for CVD-safety) - never cycle/generate hues.
CATEGORICAL_PALETTE = [
    "#2a78d6",  # blue
    "#eb6834",  # orange
    "#1baf7a",  # aqua
    "#eda100",  # yellow
    "#e87ba4",  # magenta
    "#008300",  # green
    "#4a3aa7",  # violet
    "#e34948",  # red
]
SEQUENTIAL_BLUE = "#2a78d6"
CHART_SURFACE = "#fcfcfb"
GRIDLINE = "#e1e0d9"
MUTED_INK = "#898781"
PRIMARY_INK = "#0b0b0b"
FONT_FAMILY = "system-ui, -apple-system, 'Segoe UI', sans-serif"


def _coerce_numeric(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str], list[str]]:
    df = df.copy()
    numeric_cols, other_cols = [], []
    for col in df.columns:
        converted = pd.to_numeric(df[col], errors="coerce")
        if converted.notna().all():
            df[col] = converted
            numeric_cols.append(col)
        else:
            other_cols.append(col)
    return df, numeric_cols, other_cols


def _coerce_date(df: pd.DataFrame, candidates: list[str]) -> tuple[pd.DataFrame, str | None]:
    df = df.copy()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        for col in candidates:
            converted = pd.to_datetime(df[col], errors="coerce")
            if converted.notna().all():
                df[col] = converted
                return df, col
    return df, None


def build_chart(rows: list[dict]) -> go.Figure | None:
    """Returns a Plotly figure for tabular DAX results, or None if the shape doesn't chart well."""
    if not rows or len(rows) < 2:
        return None

    df = pd.DataFrame(rows)
    if df.shape[1] < 2:
        return None

    df, numeric_cols, other_cols = _coerce_numeric(df)
    if not numeric_cols or not other_cols:
        return None

    df, date_col = _coerce_date(df, other_cols)
    category_col = date_col or other_cols[0]
    df = df.sort_values(category_col)

    if len(numeric_cols) == 1:
        measure = numeric_cols[0]
        if date_col:
            fig = go.Figure(
                go.Scatter(
                    x=df[category_col],
                    y=df[measure],
                    mode="lines+markers+text",
                    line=dict(color=SEQUENTIAL_BLUE, width=2),
                    marker=dict(size=8, color=SEQUENTIAL_BLUE),
                    text=df[measure],
                    texttemplate="%{text:,.2s}",
                    textposition="top center",
                    textfont=dict(color=PRIMARY_INK, size=11),
                    hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>",
                )
            )
        else:
            fig = go.Figure(
                go.Bar(
                    x=df[category_col],
                    y=df[measure],
                    marker_color=SEQUENTIAL_BLUE,
                    text=df[measure],
                    texttemplate="%{text:,.2s}",
                    textposition="outside",
                    textfont=dict(color=PRIMARY_INK, size=11),
                    cliponaxis=False,
                    hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>",
                )
            )
    else:
        measures = numeric_cols[:8]
        fig = go.Figure()
        for i, measure in enumerate(measures):
            fig.add_trace(
                go.Bar(
                    x=df[category_col],
                    y=df[measure],
                    name=str(measure),
                    marker_color=CATEGORICAL_PALETTE[i % len(CATEGORICAL_PALETTE)],
                    text=df[measure],
                    texttemplate="%{text:,.2s}",
                    textposition="outside",
                    textfont=dict(color=PRIMARY_INK, size=10),
                    cliponaxis=False,
                    hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>",
                )
            )
        fig.update_layout(barmode="group", legend=dict(orientation="h", yanchor="bottom", y=1.02))

    fig.update_layout(
        plot_bgcolor=CHART_SURFACE,
        paper_bgcolor=CHART_SURFACE,
        font=dict(color=PRIMARY_INK, family=FONT_FAMILY),
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(showgrid=False, color=MUTED_INK, title=None),
        yaxis=dict(showgrid=True, gridcolor=GRIDLINE, color=MUTED_INK, zeroline=False, title=None),
        height=360,
        bargap=0.25,
    )
    return fig


def render_single_row_metrics(row: dict) -> tuple[list[tuple[str, str]], dict]:
    """Splits a single-row result into (label, numeric-value) metric pairs plus leftover context fields."""
    metrics = []
    context = {}
    for key, value in row.items():
        try:
            num = float(value)
        except (TypeError, ValueError):
            context[key] = value
            continue
        display = f"{num:,.2f}" if not num.is_integer() else f"{num:,.0f}"
        metrics.append((key, display))
    return metrics, context
