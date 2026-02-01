#!/bin/bash

# Map Poster Creator Setup Script
# This script downloads and prepares all required data files for Map Poster Creator

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Parse command line arguments
TINY_MODE=false
SKIP_COLORS=false
NON_INTERACTIVE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --tiny)
            TINY_MODE=true
            shift
            ;;
        --skip-colors)
            SKIP_COLORS=true
            shift
            ;;
        --non-interactive)
            NON_INTERACTIVE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--tiny] [--skip-colors] [--non-interactive]"
            echo ""
            echo "Options:"
            echo "  --tiny            Minimal setup: only build region tree (coordinates-only mode)"
            echo "                    and fetch color schemes."
            echo "                    This disables city name lookups and API features"
            echo "  --skip-colors     Skip fetching color schemes (for faster builds)"
            echo "  --non-interactive Run in non-interactive mode (no prompts)"
            echo "  -h, --help        Show this help message"
            echo ""
            echo "Note: Set MAPOC_DATA_DIR environment variable to override data directory"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if MAPOC_DATA_DIR is set, otherwise use default
if [ -n "$MAPOC_DATA_DIR" ]; then
    echo -e "${YELLOW}Using data directory: $MAPOC_DATA_DIR${NC}"
    echo ""
fi

# Add --yes for non-interactive mode
YES_ARG="--yes"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Map Poster Creator Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 is not installed${NC}"
    exit 1
fi

# Check if we're in a virtual environment or if packages are installed
echo -e "${YELLOW}Checking Python dependencies...${NC}"
python3 -c "import map_poster_creator" 2>/dev/null || {
    echo -e "${YELLOW}Note: map_poster_creator package not found.${NC}"
    echo -e "${YELLOW}You may need to install it first: pip install -e .${NC}"
    echo ""
    if [ "$NON_INTERACTIVE" = false ]; then
        read -p "Continue anyway? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo -e "${YELLOW}Non-interactive mode: continuing anyway...${NC}"
    fi
}

echo ""
if [ "$TINY_MODE" = true ]; then
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}TINY MODE: Minimal setup${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}Only building region tree for coordinate-based usage${NC}"
    echo -e "${YELLOW}and fetching color schemes.${NC}"
    echo -e "${YELLOW}City name lookups and API features will be disabled.${NC}"
    echo ""
fi
echo -e "${GREEN}Starting data download process...${NC}"
echo ""

if [ "$TINY_MODE" = false ]; then
    # Step 1: Create geonames headers file
    echo -e "${YELLOW}[1/6] Creating geonames headers file...${NC}"
    python3 "${SCRIPT_DIR}/create_geonames_headers.py" $YES_ARG || {
        echo -e "${RED}Failed to create geonames headers${NC}"
        exit 1
    }
    echo -e "${GREEN}✓ Geonames headers created${NC}"
    echo ""

    # Step 2: Fetch countries data
    echo -e "${YELLOW}[2/6] Fetching countries data...${NC}"
    python3 "${SCRIPT_DIR}/fetch_countries.py" || {
        echo -e "${RED}Failed to fetch countries data${NC}"
        exit 1
    }
    echo -e "${GREEN}✓ Countries data fetched${NC}"
    echo ""

    # Step 3: Fetch cities data from GeoNames
    echo -e "${YELLOW}[3/6] Fetching cities data from GeoNames...${NC}"
    echo -e "${YELLOW}This may take a few minutes...${NC}"
    python3 "${SCRIPT_DIR}/fetch_data_geonames.py" $YES_ARG || {
        echo -e "${RED}Failed to fetch GeoNames cities data${NC}"
        exit 1
    }
    echo -e "${GREEN}✓ Cities data fetched${NC}"
    echo ""
fi

# Step 4: Build region tree from GeoFabrik (always run)
if [ "$TINY_MODE" = true ]; then
    echo -e "${YELLOW}[1/2] Building GeoFabrik region tree...${NC}"
else
    echo -e "${YELLOW}[4/6] Building GeoFabrik region tree...${NC}"
fi
echo -e "${YELLOW}This will crawl the GeoFabrik website and may take several minutes...${NC}"
python3 "${SCRIPT_DIR}/build_region_tree.py" || {
    echo -e "${RED}Failed to build region tree${NC}"
    exit 1
}
echo -e "${GREEN}✓ Region tree built${NC}"
echo ""

if [ "$TINY_MODE" = true ] && [ "$SKIP_COLORS" = false ]; then
    # Step 2: Fetch color schemes in tiny mode
    echo -e "${YELLOW}[2/2] Fetching color schemes...${NC}"
    python3 "${SCRIPT_DIR}/fetch_docc_colors.py" || {
        echo -e "${YELLOW}Warning: Failed to fetch color schemes (non-critical)${NC}"
    }
    echo -e "${GREEN}✓ Color schemes fetched${NC}"
    echo ""
elif [ "$TINY_MODE" = true ] && [ "$SKIP_COLORS" = true ]; then
    echo -e "${YELLOW}[2/2] Skipping color schemes (--skip-colors)${NC}"
    echo ""
fi

if [ "$TINY_MODE" = false ]; then
    # Step 5: Fetch geoboundaries data
    echo -e "${YELLOW}[5/6] Fetching geoboundaries data...${NC}"
    echo -e "${YELLOW}This is a large file and may take several minutes...${NC}"
    python3 "${SCRIPT_DIR}/fetch_geoboundaries.py" $YES_ARG || {
        echo -e "${RED}Failed to fetch geoboundaries data${NC}"
        exit 1
    }
    echo -e "${GREEN}✓ Geoboundaries data fetched${NC}"
    echo ""

    # Step 6: Fetch color schemes (optional)
    if [ "$SKIP_COLORS" = false ]; then
        echo -e "${YELLOW}[6/6] Fetching color schemes (optional)...${NC}"
        if [ "$NON_INTERACTIVE" = true ]; then
            # Non-interactive: skip colors by default for faster builds
            echo -e "${YELLOW}Skipping color schemes (non-interactive mode)${NC}"
        else
            read -p "Download additional color schemes from Dictionary of Color Combinations? [y/N] " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                python3 "${SCRIPT_DIR}/fetch_docc_colors.py" || {
                    echo -e "${YELLOW}Warning: Failed to fetch color schemes (non-critical)${NC}"
                }
                echo -e "${GREEN}✓ Color schemes fetched${NC}"
            else
                echo -e "${YELLOW}Skipping color schemes${NC}"
            fi
        fi
        echo ""
    else
        echo -e "${YELLOW}[6/6] Skipping color schemes (--skip-colors)${NC}"
        echo ""
    fi
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
if [ -n "$MAPOC_DATA_DIR" ]; then
    echo "Data files are stored in: $MAPOC_DATA_DIR"
else
    echo "Data files are stored in: ~/.mapoc/"
fi
echo ""
if [ "$TINY_MODE" = true ]; then
    echo -e "${YELLOW}Note: Running in TINY mode.${NC}"
    echo -e "${YELLOW}City name lookups and API features are disabled.${NC}"
    echo -e "${YELLOW}Only coordinate-based usage is available.${NC}"
    echo ""
fi
echo "You can now use Map Poster Creator:"
echo "  mapoc poster create --shp_path PATH --geojson PATH --colors white black coral"
echo ""

