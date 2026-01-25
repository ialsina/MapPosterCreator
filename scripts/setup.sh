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
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
}

echo ""
echo -e "${GREEN}Starting data download process...${NC}"
echo ""

# Step 1: Create geonames headers file
echo -e "${YELLOW}[1/6] Creating geonames headers file...${NC}"
python3 "${SCRIPT_DIR}/create_geonames_headers.py" || {
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
python3 "${SCRIPT_DIR}/fetch_data_geonames.py" || {
    echo -e "${RED}Failed to fetch GeoNames cities data${NC}"
    exit 1
}
echo -e "${GREEN}✓ Cities data fetched${NC}"
echo ""

# Step 4: Build region tree from GeoFabrik
echo -e "${YELLOW}[4/6] Building GeoFabrik region tree...${NC}"
echo -e "${YELLOW}This will crawl the GeoFabrik website and may take several minutes...${NC}"
python3 "${SCRIPT_DIR}/build_region_tree.py" || {
    echo -e "${RED}Failed to build region tree${NC}"
    exit 1
}
echo -e "${GREEN}✓ Region tree built${NC}"
echo ""

# Step 5: Fetch geoboundaries data
echo -e "${YELLOW}[5/6] Fetching geoboundaries data...${NC}"
echo -e "${YELLOW}This is a large file and may take several minutes...${NC}"
python3 "${SCRIPT_DIR}/fetch_geoboundaries.py" || {
    echo -e "${RED}Failed to fetch geoboundaries data${NC}"
    exit 1
}
echo -e "${GREEN}✓ Geoboundaries data fetched${NC}"
echo ""

# Step 6: Fetch color schemes (optional)
echo -e "${YELLOW}[6/6] Fetching color schemes (optional)...${NC}"
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
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Data files are stored in: ~/.mapoc/"
echo ""
echo "You can now use Map Poster Creator:"
echo "  mapoc poster create --shp_path PATH --geojson PATH --colors white black coral"
echo ""

