import math
from pathlib import Path
from typing import Tuple, Optional

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
    gdf.plot(ax=ax, **kwargs)


def plot_and_save(
    roads: GeoDataFrame,
    water: GeoDataFrame,
    greens: GeoDataFrame,
    cscheme: ColorScheme,
    geometry: MapGeometry,
    path: Path,
    dpi: Optional[int] = 300,
    width: Optional[int] = None,
    figsize: Optional[Tuple[float, float]] = (8, 8),
) -> None:
    plt.clf()
    if width is not None:
        figsize = (width, width)
    fig, ax = plt.subplots(figsize=figsize, facecolor=cscheme.facecolor.rgb)
    if not isinstance(ax, Axes):
        return
    plot_dataframe(ax=ax, gdf=water, color=cscheme.water.rgb, lw=0.1)
    plot_dataframe(ax=ax, gdf=greens, color=cscheme.greens.rgb, lw=0.1)
    plot_dataframe(
        ax=ax,
        gdf=roads,
        color=cscheme.roads.rgb,
        linewidth=[road_width(d) for d in roads.speeds],
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
    ax.set_axis_off()
    fig.savefig(path, bbox_inches="tight", dpi=dpi)
