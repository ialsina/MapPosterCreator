import math
from pathlib import Path

from geopandas import GeoDataFrame
from matplotlib import pyplot as plt
from matplotlib.axes import Axes

from map_poster_creator.colorscheme import ColorScheme
from map_poster_creator.geometry import MapGeometry
from map_poster_creator.logs import log_processing


def road_width(speed: int) -> float:
    if speed in range(0, 30):
        return 0.05
    if speed in range(30, 50):
        return 0.1
    if speed in range(50, 90):
        return 0.2
    if speed in range(90, 200):
        return 0.3
    return 0.4


@log_processing
def plot_dataframe(ax: Axes, gdf: GeoDataFrame, **kwargs) -> None:
    """Plot a GeoDataFrame on the given axes.

    If the GeoDataFrame is empty or has invalid bounds, skip plotting
    to avoid matplotlib errors.
    """
    # Skip empty dataframes
    if gdf.empty:
        return

    # Check if dataframe has valid bounds
    try:
        bounds = gdf.total_bounds
        if bounds is None or len(bounds) != 4:
            return
        if not all(math.isfinite(b) for b in bounds):
            return
        # Check if bounds have valid width/height
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        if (
            width <= 0
            or height <= 0
            or not math.isfinite(width)
            or not math.isfinite(height)
        ):
            return
    except (AttributeError, ValueError, TypeError, IndexError):
        # If we can't get bounds, skip plotting to avoid errors
        return

    # Plot the dataframe
    # Note: We don't pass aspect here because we've already set it on the axes
    # geopandas will respect the existing aspect ratio
    try:
        gdf.plot(ax=ax, **kwargs)
    except ValueError as e:
        # If we get an aspect error, it means geopandas tried to adjust it
        # Re-raise if it's not an aspect error, otherwise skip
        if "aspect" not in str(e).lower():
            raise
        # For aspect errors, just skip this layer
        pass


def plot_and_save(
    roads: GeoDataFrame,
    water: GeoDataFrame,
    greens: GeoDataFrame,
    cscheme: ColorScheme,
    geometry: MapGeometry,
    path: Path,
    dpi: int | None = 300,
    width: int | None = None,
    figsize: tuple[float, float] | None = (8, 8),
) -> None:
    plt.clf()
    if width is not None:
        figsize = (width, width)
    fig, ax = plt.subplots(figsize=figsize, facecolor=cscheme.facecolor.rgb)
    if not isinstance(ax, Axes):
        return

    # Set limits and aspect ratio BEFORE plotting to prevent matplotlib
    # from auto-calculating aspect from potentially invalid data
    # Validate bounds before setting limits
    if (
        math.isfinite(geometry.bottom)
        and math.isfinite(geometry.top)
        and geometry.top > geometry.bottom
    ):
        ax.set_ylim((geometry.bottom, geometry.top))
    else:
        raise ValueError(
            f"Invalid y-axis bounds: bottom={geometry.bottom}, top={geometry.top}"
        )

    if (
        math.isfinite(geometry.left)
        and math.isfinite(geometry.right)
        and geometry.right > geometry.left
    ):
        ax.set_xlim((geometry.left, geometry.right))
    else:
        raise ValueError(
            f"Invalid x-axis bounds: left={geometry.left}, right={geometry.right}"
        )

    # Set aspect ratio according to latitude
    # (not sure why this is needed)
    # Validate aspect ratio calculation to avoid matplotlib errors
    try:
        latitude = geometry.center[0]
        if not (math.isfinite(latitude) and -90 <= latitude <= 90):
            # Invalid latitude, use default aspect ratio
            aspect_ratio = 1.0
        else:
            cos_lat = math.cos(math.pi / 180 * latitude)
            if cos_lat > 0 and math.isfinite(cos_lat):
                aspect_ratio = 1 / cos_lat
            else:
                aspect_ratio = 1.0
        ax.set_aspect(aspect_ratio)
    except (ValueError, ZeroDivisionError, OverflowError):
        # Fallback to default aspect ratio if calculation fails
        ax.set_aspect(1.0)

    # Now plot the dataframes (limits and aspect are already set)
    # Use try-except to catch any aspect ratio errors during plotting
    try:
        plot_dataframe(ax=ax, gdf=water, color=cscheme.water.rgb, lw=0.1)
    except (ValueError, RuntimeError) as e:
        if "aspect" in str(e).lower():
            # If aspect error, try with aspect='auto' explicitly
            try:
                water.plot(ax=ax, color=cscheme.water.rgb, lw=0.1, aspect="auto")
            except Exception:
                pass  # Skip if still fails

    try:
        plot_dataframe(ax=ax, gdf=greens, color=cscheme.greens.rgb, lw=0.1)
    except (ValueError, RuntimeError) as e:
        if "aspect" in str(e).lower():
            try:
                greens.plot(ax=ax, color=cscheme.greens.rgb, lw=0.1, aspect="auto")
            except Exception:
                pass

    try:
        plot_dataframe(
            ax=ax,
            gdf=roads,
            color=cscheme.roads.rgb,
            linewidth=[road_width(d) for d in roads.speeds],
        )
    except (ValueError, RuntimeError) as e:
        if "aspect" in str(e).lower():
            try:
                roads.plot(
                    ax=ax,
                    color=cscheme.roads.rgb,
                    linewidth=[road_width(d) for d in roads.speeds],
                    aspect="auto",
                )
            except Exception:
                pass
    ax.set_axis_off()
    fig.savefig(path, bbox_inches="tight", dpi=dpi)
