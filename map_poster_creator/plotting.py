import math
from typing import Tuple, Optional

from geopandas import GeoDataFrame
from matplotlib import pyplot as plt
from matplotlib.axes import Axes

from map_poster_creator.colorscheme import Color, ColorScheme
from map_poster_creator.geojson import MapGeometry
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
        path: str,
        figsize: Optional[Tuple[float, float]] = (19, 19),
        dpi: Optional[int] = 300,
) -> None:
    plt.clf()
    fig, ax = plt.subplots(figsize=figsize, facecolor=cscheme.facecolor.rgb)
    plot_dataframe(ax=ax, gdf=water, color=cscheme.water.rgb, lw=0.1)
    plot_dataframe(ax=ax, gdf=greens, color=cscheme.greens.rgb, lw=0.1)
    plot_dataframe(
        ax=ax,
        gdf=roads,
        color=cscheme.roads.rgb,
        linewidth=[road_width(d) for d in roads.speeds],
    )
    ax.set_aspect(
        1 / math.cos(math.pi / 180 * geometry.center[0])
    )
    ax.set_ylim((geometry.bottom, geometry.top))
    ax.set_xlim((geometry.left, geometry.right))
    ax.set_axis_off()
    fig.savefig(path, bbox_inches='tight', dpi=dpi)

