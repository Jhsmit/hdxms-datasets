import polars as pl
import altair as alt
import numpy as np
from cmap import Colormap


def unique_peptides(df: pl.DataFrame) -> bool:
    """
    Checks if all peptides in the DataFrame are unique.
    Needs to have columns 'start' and 'end' marking peptide intervals (inclusive).

    Args:
        df: DataFrame containing peptide information.

    Returns:
        `True` if all peptides are unique, otherwise `False`.

    """

    return len(df) == len(df.unique(subset=["start", "end"]))


def find_wrap(
    peptides: pl.DataFrame,
    margin: int = 4,
    step: int = 5,
    wrap_limit: int = 200,
) -> int:
    """
    Find the minimum wrap value for a given list of intervals.

    Args:
        peptides: Dataframe with columns 'start' and 'end' representing intervals.
        margin: The margin applied to the wrap value. Defaults to 4.
        step: The increment step for the wrap value. Defaults to 5.
        wrap_limit: The maximum allowed wrap value. Defaults to 200.

    Returns:
        The minimum wrap value that does not overlap with any intervals.
    """
    wrap = step

    while True:
        peptides_y = peptides.with_columns(
            (pl.int_range(pl.len(), dtype=pl.UInt32).alias("y") % wrap)
        )

        no_overlaps = True
        for name, df in peptides_y.group_by("y", maintain_order=True):
            overlaps = (np.array(df["end"]) + 1 + margin)[:-1] >= np.array(df["start"])[1:]
            if np.any(overlaps):
                no_overlaps = False
                break
                # return wrap

        wrap += step
        if wrap > wrap_limit:
            return wrap_limit  # Return the maximum wrap limit if no valid wrap found
        elif no_overlaps:
            return wrap


def peptide_rectangles(peptides: pl.DataFrame, wrap: int | None = None) -> pl.DataFrame:
    """
    Given a DataFrame with 'start' and 'end' columns, each describing a peptide range,
    this function computes the corresponding rectangle coordinates for visualization.

    Typicall used for Altair plotting. The rectangles will be stacked vertically based on the `wrap` parameter.
    Horizontally, each rectangle spans from `start - 0.5` to `end + 0.5`.

    Args:
        peptides: DataFrame containing peptide information with 'start' and 'end' columns.
        wrap: The number of peptides to stack vertically before wrapping to the next row.
              If `None`, the function will compute an optimal wrap value to avoid overlaps.

    Returns:
        A DataFrame with columns 'x', 'x2', 'y', and 'y2' representing the rectangle coordinates.

    """
    wrap = find_wrap(peptides, step=1) if wrap is None else wrap
    columns = [
        (pl.col("start") - 0.5).alias("x"),
        (pl.col("end") + 0.5).alias("x2"),
        (wrap - (pl.col("idx") % wrap)).alias("y"),
    ]

    rectangles = (
        peptides["start", "end"]
        .with_row_index("idx")
        .with_columns(columns)
        .with_columns((pl.col("y") - 1).alias("y2"))
    )

    return rectangles


def plot_peptides(
    peptides: pl.DataFrame,
    value: str = "value",
    value_sd: str | None = None,
    colormap: str | Colormap = "viridis",
    domain: tuple[float | None, float | None] | None = None,
    bad_color: str = "#8c8c8c",
    N: int = 256,
    label: str | None = None,
    width: str | int = "container",
    height: str | int = 350,
    wrap: int | None = None,
    fill_nan: bool = True,
) -> alt.Chart:
    """
    Create an altair chart visualizing peptides as colored rectangles.

    Args:
        peptides: DataFrame containing peptide information with 'start', 'end', and `value` columns.
        value: The column name in `peptides` to use for coloring the rectangles.
        value_sd: Optional column name for standard deviation of `value`, used in tooltips.
        colormap: Colormap to use for coloring the rectangles. Can be a string or a Colormap object.
        domain: Tuple specifying the (min, max) values for the colormap. If `None`, uses min and max of `value`.
        bad_color: Color to use for invalid or NaN values.
        N: Number of discrete colors to generate from the colormap.
        label: Label for the color legend. If `None`, uses a title-cased version of `value`.
        width: Width of the chart. Can be an integer or 'container' for responsive width.
        height: Height of the chart in pixels.
        wrap: Number of peptides to stack vertically before wrapping to the next row. If `None`, computes an optimal wrap value.
        fill_nan: Whether to fill NaN values in `peptides` with None to avoid serialization issues.

    Returns:
        An Altair Chart object visualizing the peptides.

    """

    if not unique_peptides(peptides):
        raise ValueError("Peptides must be unique by 'start' and 'end' columns.")

    if fill_nan:
        # nan values can cause problems in serialization
        peptides = peptides.fill_nan(None)

    value_sd = value_sd or f"{value}_sd"
    colormap = Colormap(colormap) if isinstance(colormap, str) else colormap
    if domain is None:
        domain = (None, None)
    vmin = domain[0] if domain[0] is not None else peptides[value].min()  # type: ignore
    vmax = domain[1] if domain[1] is not None else peptides[value].max()  # type: ignore

    scale = alt.Scale(domain=(vmin, vmax), range=colormap.to_altair(N=N))  # type: ignore
    label = label or value.replace("_", " ").title()

    if value_sd in peptides.columns:
        tooltip_value = []
        for v, v_sd in zip(peptides[value], peptides[value_sd]):
            if v is not None and v_sd is not None:
                tooltip_value.append(
                    f"{v:.2f} \u00b1 {v_sd:.2f}"  # type: ignore
                )
            else:
                tooltip_value.append("NaN")
    else:
        tooltip_value = [f"{value:.2f}" if value is not None else "" for value in peptides[value]]

    rectangles = peptide_rectangles(peptides, wrap=wrap)
    peptide_source = peptides.join(rectangles, on=["start", "end"], how="left").with_columns(
        pl.col(value), pl.Series(tooltip_value).alias("tooltip_value")
    )

    invalid = {"color": {"value": bad_color}}
    peptide_chart = (
        alt.Chart(peptide_source)
        .mark_rect(
            stroke="black",
        )
        .encode(
            x=alt.X("x:Q", title="Residue Number"),
            y=alt.Y("y:Q", title="", axis=alt.Axis(ticks=False, domain=False, labels=False)),
            x2=alt.X2("x2:Q"),
            y2=alt.Y2("y2:Q"),
            tooltip=[
                alt.Tooltip("idx:Q", title="Index"),
                alt.Tooltip("start:Q", title="Start"),
                alt.Tooltip("end:Q", title="End"),
                alt.Tooltip("sequence:N", title="Sequence"),
                alt.Tooltip("tooltip_value:N", title=label),
            ],
            color=alt.Color(f"{value}:Q", scale=scale, title=label),
        )
        .configure_scale(invalid=invalid)
    )

    return peptide_chart.properties(height=height, width=width)
