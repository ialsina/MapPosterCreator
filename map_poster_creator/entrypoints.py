from argparse import ArgumentParser, Namespace
import logging
from pathlib import Path
from pprint import pprint
from typing import Callable, Tuple, Mapping
import sys
import webbrowser

from map_poster_creator.core import (
    create_poster,
    browser_get_geojson_path,
    find_shp,
)
from map_poster_creator.colorscheme import (
    ColorScheme,
    get_colorschemes,
    get_available_colorschemes,
    add_colorscheme,
)
from map_poster_creator import __version__

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def _add_poster_subparsers(parser_group) -> None:
    poster_parser = parser_group.add_parser(
        'poster',
        description='Create Map Poster',
        help='Poster creation',
    )
    poster_parser.add_argument(
        "-c", "--city",
        default=None,
        action="store",
        required=False,
        help=(
            "City to draw. Required if shp_path is not passed."
        ),
        metavar="CITY",
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
        '--geojson-path',
        default=None,
        action="store",
        required=False,
        help=(
            'Path to geojson file with boundary polygon. '
            'Type "mapoc browse geojson" to create and download.'
        ),
        metavar="GEOJSON_PATH",
    )
    poster_parser.add_argument(
        '--colors',
        help=(
            f'Provide one or several color schemes.'
            f'Default: "white". '
            f'Type "mapoc color list" to see a list of available colors.'
        ),
        default=["white"],
        nargs="+",
    )
    poster_parser.add_argument(
        '--output_prefix',
        help='Output file prefix. eq. "{OUTPUT_PREFIX}_{COLOR}.png". Default: "map"',
        type=str,
        default="map"
    )

def _add_color_add_subparser(parent_parser) -> None:
    color_parser = parent_parser.add_parser('add', description="List available colors")
    color_parser.add_argument('--name', help='Name of color scheme. eq. "blue"', required=True)
    color_parser.add_argument('--facecolor', help='MatPlot face hex color. eq. "#ffffff"', required=True)
    color_parser.add_argument('--water', help='MatPlot water hex color. eq. "#ffffff"', required=True)
    color_parser.add_argument('--greens', help='MatPlot greens hex color. eq. "#ffffff"', required=True)
    color_parser.add_argument('--roads', help='MatPlot roads hex color. eq. "#ffffff"', required=True)

def _add_browse_subparsers(parser_group) -> None:
    browse_commands_parser = parser_group.add_parser(
        'browse',
        description='browse services',
        help='browse services',
    )
    browse_commands_parser_group = browse_commands_parser.add_subparsers(
        title='browse management commands',
        description='browse',
        help='Additional help for available commands',
        dest='browse_commands',
    )
    browse_commands_parser_group.add_parser(
        'shp',
        description='Shp download',
    )
    browse_commands_parser_group.add_parser(
        'geojson',
        description='Create geoJSON',
    )

def _add_color_subparsers(parser_group) -> None:
    color_commands_parser = parser_group.add_parser(
        'color',
        description='Color services',
        help='Color services',
    )
    color_commands_parser_group = color_commands_parser.add_subparsers(
        title='color management commands',
        description='Color management',
        help='Additional help for available commands',
        dest='color_commands',
    )
    _add_color_add_subparser(color_commands_parser_group)
    color_commands_parser_group.add_parser(
        'list',
        description="List available colors",
    )


def _color_service(
        args: Namespace,
        print_help: Callable,
    ) -> None:
    command = args.color_commands
    if command == "list":
        pprint(get_colorschemes())
    elif command == "add":
        add_colorscheme(
            args.name,
            ColorScheme(
                facecolor=args.facecolor,
                water=args.water,
                greens=args.greens,
                roads=args.roads,
            )
        )
    else:
        print_help()

def _browse_service(
        args: Namespace,
        print_help: Callable
    ) -> None:
    command = args.browse_commands
    if command == 'shp':
        webbrowser.open_new_tab("https://download.geofabrik.de/")
    elif command == "geojson":
        webbrowser.open_new_tab("https://geojson.io/")
    else:
        print_help()

def _poster_service(args: Namespace, print_help: Callable) -> None:
    city_name = args.city
    shp_path = args.shp_path
    geojson_path = args.geojson_path

    if city_name is None:
        if shp_path is None or geojson_path is None:
            print_help()
            return
    else:
        if geojson_path is None:
            geojson_path = browser_get_geojson_path(city_name)
        if shp_path is None:
            shp_path = find_shp(city_name)

    colors = args.colors
    output_prefix = args.output_prefix

    create_poster(
        shp_dir=shp_path,
        geojson_path=geojson_path,
        color=colors,
        output_prefix=output_prefix,
    )
    return

_AVAILABLE_SERVICES = {
    'poster': _poster_service,
    'browse': _browse_service,
    'color': _color_service,
}

def get_parser() -> Tuple[ArgumentParser, Mapping[str, Callable]]:
    parser = ArgumentParser(
        prog='mapoc',
        description="Map Poster Creator"
    )
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + str(__version__))
    subparsers = parser.add_subparsers(
        title='Available Map Poster services',
        description='Services that Map Poster provides.',
        help='Additional help for available services',
        dest='map_poster_services',
    )
    _add_poster_subparsers(subparsers)
    _add_browse_subparsers(subparsers)
    _add_color_subparsers(subparsers)
    return parser, {
        choice: subparser.print_help
        for choice, subparser in subparsers.choices.items()
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


if __name__ == '__main__':
    map_poster()

