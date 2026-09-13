from argparse import ArgumentParser, Namespace
import logging
from pandas import DataFrame
from pathlib import Path
from tabulate import tabulate
from typing import Callable, Tuple, Mapping, Sequence
import sys
import webbrowser

from map_poster_creator.config import paths, config
from map_poster_creator.core import (
    create_poster,
)
from map_poster_creator.colorscheme import (
    ColorScheme,
    get_colorscheme,
    get_colorschemes,
    add_colorscheme,
)
from map_poster_creator.data import (
    download_shp_interactive,
    find_download_shp,
    get_geojson_path_from_geoboundaries,
    create_geojson_from_points,
    read_coordinates_from_file,
    polygon_from_coordinates,
)
from map_poster_creator import __version__

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def _to_fwf(df, tablefmt="plain"):
    content = [[tup[0]] + tup[1] for tup in zip(df.index.tolist(), df.values.tolist())]
    content = tabulate(content, [""] + list(df.columns), tablefmt=tablefmt)
    return content


def _add_poster_subparsers(subparser_group) -> None:
    poster_parser = subparser_group.add_parser(
        "poster",
        description="Create Map Poster",
        help="Poster creation",
    )
    poster_parser.add_argument(
        action="store",
        help=(
            "City to draw. Required if shp_path is not passed and --coordinates-file is not used. "
            "When using --coordinates-file, city is optional but recommended to automatically find the correct SHP region."
        ),
        metavar="CITY",
        dest="city",
        nargs="?",
        default=None,
    )
    poster_parser.add_argument(
        "-c",
        "--country-code",
        default=None,
        action="store",
        required=False,
        help=(
            "Two-letter country code (e.g., 'JP', 'US'). "
            "If multiple cities match, the one with highest population is selected."
        ),
        metavar="COUNTRY_CODE",
    )
    poster_parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        required=False,
        help=(
            "If multiple cities match, prompt user to select one interactively. "
            "By default, selects the city with highest population."
        ),
    )
    poster_parser.add_argument(
        "-w",
        "--width",
        default=config.default_width,
        required=False,
        action="store",
        help=(
            "Width of the figure, with units (cm, in, px). "
            "If units are not passed, it defaults to cm."
        ),
        type=str,
        metavar="WIDTH",
    )
    poster_parser.add_argument(
        "-d",
        "--dpi",
        default=config.default_dpi,
        required=False,
        action="store",
        help=("Dots per inch (dpi) of the figure."),
        type=int,
        metavar="DPI",
    )
    poster_parser.add_argument(
        "--shp-path",
        default=None,
        action="store",
        required=False,
        help='Path to shp folder. Type "mapoc browse shp" to download.',
        metavar="SHP_PATH",
    )
    poster_parser.add_argument(
        "--geojson-path",
        default=None,
        action="store",
        required=False,
        help=(
            "Path to geojson file with boundary polygon. "
            'Type "mapoc browse geojson" to create and download.'
        ),
        metavar="GEOJSON_PATH",
    )
    poster_parser.add_argument(
        "--coordinates-file",
        default=None,
        action="store",
        required=False,
        help=(
            "Path to file containing polygon coordinates. "
            "Supports JSON array format ([[lon,lat],...]), "
            "CSV format (lon,lat per line), or space-separated (lon lat per line). "
            "Coordinates should be in [longitude, latitude] format."
        ),
        metavar="COORDINATES_FILE",
    )
    poster_parser.add_argument(
        "--colors",
        help=(
            "Provide one or several color schemes."
            'Default: "white". '
            'Type "mapoc color list" to see a list of available colors.'
        ),
        default=["white"],
        nargs="+",
    )
    poster_parser.add_argument(
        "--output-prefix",
        help=("Output filename prefix."),
        required=False,
        type=str,
        default=None,
    )


def _add_browse_subparsers(subparser_group) -> None:
    browse_parser = subparser_group.add_parser(
        "browse",
        description="browse services",
        help="browse services",
    )
    browse_parser_commands = browse_parser.add_subparsers(
        title="browse management commands",
        description="browse",
        help="Additional help for available commands",
        dest="browse_commands",
    )
    browse_parser_commands.add_parser(
        "shp",
        description="Shp download",
    )
    browse_parser_commands.add_parser(
        "geojson",
        description="Create geoJSON",
    )


def _add_color_subparsers(main_parser) -> None:
    def command_add() -> None:
        color_add_parser = color_parser_commands.add_parser(
            "add", description="List available colors"
        )
        color_add_parser.add_argument(
            "name",
            help='Name of color scheme. eq. "blue"',
            metavar="NAME",
        )
        color_add_parser.add_argument(
            "-f",
            "--facecolor",
            help="Face color, as a hex color or Matplotlib named color.",
            required=True,
            metavar="FACECOLOR",
        )
        color_add_parser.add_argument(
            "-w",
            "--water",
            help="Water color, as a hex color or Matplotlib named color.",
            required=True,
            metavar="WATER",
        )
        color_add_parser.add_argument(
            "-g",
            "--greens",
            help="Greens color, as a hex color or Matplotlib named color.",
            required=True,
            metavar="GREENS",
        )
        color_add_parser.add_argument(
            "-r",
            "--roads",
            help="Roads color, as a hex color or Matplotlib named color.",
            required=True,
            metavar="ROADS",
        )

    def command_show() -> None:
        parser = color_parser_commands.add_parser(
            "show", description="Show palette of available color"
        )
        parser.add_argument(
            "name",
            help="Name of the color scheme",
        )

    def command_list() -> None:
        color_parser_commands.add_parser(
            "list",
            description="List available colors",
        )

    color_parser = main_parser.add_parser(
        "color",
        description="Color services",
        help="Color services",
    )
    color_parser_commands = color_parser.add_subparsers(
        title="color management commands",
        description="Color management",
        help="Additional help for available commands",
        dest="color_commands",
    )
    command_add()
    command_show()
    command_list()


def _color_service(
    args: Namespace,
    print_help: Callable,
) -> None:
    command = args.color_commands
    if command == "list":
        print(
            _to_fwf(
                DataFrame.from_dict(
                    {
                        name: scheme.to_json()
                        for name, scheme in get_colorschemes().items()
                    },
                    orient="index",
                ).sort_index(inplace=False),
                tablefmt="fancy_grid",
            )
        )
    elif command == "add":
        add_colorscheme(
            args.name,
            ColorScheme(
                facecolor=args.facecolor,
                water=args.water,
                greens=args.greens,
                roads=args.roads,
            ),
        )
    elif command == "show":
        get_colorscheme(args.name).show()
    else:
        print_help()


def _browse_service(args: Namespace, print_help: Callable) -> None:
    command = args.browse_commands
    if command == "shp":
        webbrowser.open_new_tab("https://download.geofabrik.de/")
    elif command == "geojson":
        webbrowser.open_new_tab("https://geojson.io/")
    else:
        print_help()


def _size_to_inches(size_units: str) -> float:
    if size_units.isnumeric():
        return float(size_units) * 0.3937008
    if size_units.endswith("cm"):
        size = size_units.strip("cm").strip()
        return float(size) * 0.3937008
    if size_units.endswith("in"):
        size = size_units.strip("in").strip()
        return float(size)
    if size_units.endswith("px"):
        raise NotImplementedError(
            "px unit not yet implemented. "
            "Please, pass size in cm or in, and pass argument dpi."
        )
    else:
        raise ValueError(
            f"Unknown unit type in {size_units}. "
            "The supported units are 'cm', 'in', and 'px'."
        )


def _split_city_country(city_country_str: str | None) -> Tuple[str | None, str | None]:
    if city_country_str is None:
        return (None, None)
    city_country = [el.strip() for el in city_country_str.split(",", 2)]
    if len(city_country) == 1:
        return (city_country[0], None)
    return (city_country[0], city_country[1])


def _poster_service(args: Namespace, print_help: Callable) -> None:
    city_name, country_name = _split_city_country(args.city)
    shp_path: str | Path | None = args.shp_path
    geojson_path: str | Path | None = args.geojson_path
    coordinates_file: str | Path | None = getattr(args, "coordinates_file", None)
    colors: Sequence[str] = args.colors
    output_prefix: str | None = args.output_prefix
    output_dir: Path = paths.output_dir
    width_in = _size_to_inches(args.width)
    # argparse converts --country-code to country_code in namespace
    country_code: str | None = getattr(args, "country_code", None)
    if country_code:
        country_code = str(country_code).strip()
    else:
        country_code = None
    interactive: bool = getattr(args, "interactive", False)

    # Handle coordinates file - create polygon from points
    polygon_from_coords = None
    if coordinates_file is not None:
        if geojson_path is not None:
            raise ValueError(
                "Cannot specify both --geojson-path and --coordinates-file. "
                "Please use only one."
            )
        try:
            coordinates = read_coordinates_from_file(coordinates_file)
            # Create polygon object directly (no file creation)
            polygon_from_coords = polygon_from_coordinates(coordinates)
            # Optionally save to file if output_prefix is provided (for debugging/inspection)
            if output_prefix:
                geojson_path = create_geojson_from_points(
                    coordinates, name=output_prefix
                )
            else:
                # Use polygon object directly
                geojson_path = polygon_from_coords
        except Exception as e:
            raise ValueError(
                f"Error reading coordinates from file {coordinates_file}: {e}"
            ) from e

    # Determine geojson_path if not set
    if geojson_path is None:
        if city_name is None:
            raise ValueError(
                "Either CITY, --geojson-path, or --coordinates-file must be provided."
            )
        # Pass interactive callback if interactive mode is requested
        interactive_callback = None
        if interactive:
            from map_poster_creator.data.interactive import interactive_resolve_city

            interactive_callback = interactive_resolve_city
        geojson_path = get_geojson_path_from_geoboundaries(
            city=city_name,
            country=country_name,
            country_code=country_code,
            interactive=interactive,
            interactive_callback=interactive_callback,
        )

    # Determine shp_path if not set
    if shp_path is None:
        if city_name is None:
            raise ValueError(
                "When using --coordinates-file or --geojson-path without a city name, "
                "you must also provide --shp-path to specify the region's shapefile directory."
            )
        try:
            # Pass callbacks if interactive mode is requested
            interactive_callback = None
            region_callback = None
            if interactive:
                from map_poster_creator.data.interactive import (
                    interactive_resolve_city,
                    interactive_region_choose,
                )

                interactive_callback = interactive_resolve_city
                region_callback = interactive_region_choose
            shp_path = find_download_shp(
                city=city_name,
                country=country_name,
                interactive=interactive,
                calculate_point=True,
                interactive_callback=interactive_callback,
                region_callback=region_callback,
            )
        except (ValueError, NotImplementedError):
            shp_path = download_shp_interactive(city=city_name, country=country_name)

    if output_prefix is None:
        output_prefix = city_name or "polygon_poster"

    output_dir.mkdir(parents=True, exist_ok=True)
    for cscheme_name in colors:
        fname = f"{output_prefix}_{cscheme_name}.png"
        fpath = paths.output_dir / fname
        args.output_prefix
        try:
            create_poster(
                shp_dir=Path(shp_path),
                geojson_path=Path(geojson_path),
                color=get_colorscheme(cscheme_name),
                width=width_in,
                dpi=args.dpi,
                output=fpath,
            )
        except ValueError as exc:
            raise ValueError(
                "Error during poster creation. This can be due to a geojson "
                "passed with polygons defined, which do not belong to the "
                "SHP file. "
            ) from exc
        except KeyError:
            print(f"Skipping color {cscheme_name} as it is unknown.")
    return


_AVAILABLE_SERVICES = {
    "poster": _poster_service,
    "browse": _browse_service,
    "color": _color_service,
}


def get_parser() -> Tuple[ArgumentParser, Mapping[str, Callable]]:
    parser = ArgumentParser(prog="mapoc", description="Map Poster Creator")
    parser.add_argument(
        "-v", "--version", action="version", version="%(prog)s " + str(__version__)
    )
    subparsers = parser.add_subparsers(
        title="Available Map Poster services",
        description="Services that Map Poster provides.",
        help="Additional help for available services",
        dest="map_poster_services",
    )
    _add_poster_subparsers(subparsers)
    _add_browse_subparsers(subparsers)
    _add_color_subparsers(subparsers)
    return parser, {
        choice: subparser.print_help for choice, subparser in subparsers.choices.items()
    }


def map_poster(argv=None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    parser, help_dict = get_parser()
    args = parser.parse_args(argv)

    service = args.map_poster_services
    if not service:
        parser.print_help()
        return
    _AVAILABLE_SERVICES[service](args, help_dict[service])


if __name__ == "__main__":
    map_poster()
