from argparse import ArgumentParser, Namespace
import logging
from pathlib import Path
from pprint import pprint
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
        "city",
        default=None,
        action="store",
        required=False,
        help="City to draw. Required if shp_path is not passed.",
        metavar="CITY",
    )
    poster_parser.add_argument(
        '--shp-path',
        default=None,
        action="store",
        required=False,
        help='Path to shp folder. Type "mapoc misc shp" to download.',
        metavar="SHP_PATH",
    )
    poster_parser.add_argument(
        '--geojson-path',
        default=None,
        action="store",
        required=False,
        help=(
            'Path to geojson file with boundary polygon. '
            'Type "mapoc misc geojson" to create and download.'
        ),
        metavar="GEOJSON_PATH",
    )
    poster_parser.add_argument(
        '--colors',
        help=(
            f'Provide colors. '
            f'eq "--colors white black coral". '
            f'Default: "white". '
            f'Available colors: {", ".join(get_available_colorschemes())}'
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

def _add_misc_subparsers(parser_group) -> None:
    misc_commands_parser = parser_group.add_parser(
        'misc',
        description='Misc services',
        help='Misc services',
    )
    misc_commands_parser_group = misc_commands_parser.add_subparsers(
        title='misc management commands',
        description='misc',
        help='Additional help for available commands',
        dest='misc_commands',
    )
    misc_commands_parser_group.add_parser(
        'shp',
        description='Shp download',
    )
    misc_commands_parser_group.add_parser(
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

def get_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog='mapoc',
        description="Map Poster Creator"
    )
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + str(__version__))
    poster_creator_services_parser_group = parser.add_subparsers(
        title='Available Map Poster services',
        description='Services that Map Poster provides.',
        help='Additional help for available services',
        dest='map_poster_services',
    )
    _add_poster_subparsers(poster_creator_services_parser_group)
    _add_misc_subparsers(poster_creator_services_parser_group)
    _add_color_subparsers(poster_creator_services_parser_group)
    return parser

def process_color_service_call(args: Namespace) -> None:
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

def process_misc_service_call(args: Namespace) -> None:
    command = args.misc_commands
    if command == 'shp':
        webbrowser.open_new_tab("https://download.geofabrik.de/")
    elif command == "geojson":
        webbrowser.open_new_tab("https://geojson.io/")

def get_shp_path(city: str) -> Path:
    raise NotImplementedError

def get_geojson_path(city: str) -> Path:
    raise NotImplementedError

def process_poster_service_call(args: Namespace) -> None:
    city_name = args.city
    shp_path = args.shp_path
    geojson_path = args.geojson_path

    if city_name is None:
        if shp_path is None or geojson_path is None:
            raise ValueError(
                "Please, pass either a city or "
                "SHP and geojson file paths."
            )
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

def map_poster(argv=None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    parser = get_parser()
    args = parser.parse_args(argv)

    service = args.map_poster_services
    available_services = {
        'poster': process_poster_service_call,
        'misc': process_misc_service_call,
        'color': process_color_service_call,
    }
    if not service:
        parser.print_help()
        parser.print_usage()
        return
    available_services[service](args)


if __name__ == '__main__':
    map_poster()

