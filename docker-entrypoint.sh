#!/bin/bash
set -e

# Set environment variables (in case they're not set)
# These must be set before Python imports config, so set them early
export MAPOC_DATA_DIR="${MAPOC_DATA_DIR:-/app/data}"
export MAPOC_OUTPUT_DIR="${MAPOC_OUTPUT_DIR:-/app/output}"

# Ensure the directories exist
mkdir -p "$MAPOC_DATA_DIR" "$MAPOC_OUTPUT_DIR"

# Function to check if data directory exists and has required files with valid sizes
check_data_directory() {
	local dir="$1"
	if [ -d "$dir" ] && [ -n "$(ls -A "$dir" 2>/dev/null)" ] &&
		[ -f "${dir}/geofabrik_tree.nw" ]; then
		# Verify file size is reasonable (should be ~4MB, at least 100KB)
		local file_size=$(stat -c%s "${dir}/geofabrik_tree.nw" 2>/dev/null || stat -f%z "${dir}/geofabrik_tree.nw" 2>/dev/null || echo "0")
		if [ "$file_size" -lt 100000 ]; then
			echo "WARNING: geofabrik_tree.nw exists but is too small ($file_size bytes). Will re-copy."
			return 1
		fi
		return 0
	fi
	return 1
}

# Function to generate docc_colors.json when missing
ensure_docc_colors() {
	local data_dir="$1"
	if [ -f "${data_dir}/docc_colors.json" ]; then
		echo "✓ docc_colors.json already present in ${data_dir}"
		return 0
	fi

	echo "Generating docc_colors.json..."
	if MAPOC_DATA_DIR="$data_dir" python3 /app/scripts/fetch_docc_colors.py; then
		echo "✓ docc_colors.json created in ${data_dir}"
		return 0
	fi

	echo "Warning: Failed to generate docc_colors.json"
	return 1
}

# Function to prepare data directory using setup.sh
prepare_data_directory() {
	local output_dir="$1"
	echo "Data directory missing or incomplete. Creating it..."

	if [ ! -f "/app/scripts/setup.sh" ]; then
		echo "Error: setup.sh not found at /app/scripts/setup.sh"
		return 1
	fi

	mkdir -p "$output_dir"
	chmod +x /app/scripts/setup.sh

	# Run setup.sh in tiny mode to create data
	if /app/scripts/setup.sh --tiny --non-interactive --output "$output_dir"; then
		echo "Data directory created successfully: $output_dir"
		return 0
	else
		echo "Warning: setup.sh failed to create data directory"
		return 1
	fi
}

# Check for data sources in priority order:
# 1) /app/data_source (created during build from host data/ or setup.sh)
# 2) /app/data (from build context or volume mount)
# 3) Run setup.sh to create it in /app/data
# 4) Fallback to old locations
DATA_SOURCE=""

if check_data_directory "/app/data_source"; then
	echo "Using data from build: /app/data_source"
	DATA_SOURCE="/app/data_source"
elif check_data_directory "$MAPOC_DATA_DIR"; then
	echo "Using existing data directory: $MAPOC_DATA_DIR"
	DATA_SOURCE="$MAPOC_DATA_DIR"
else
	# Try to create data directory in MAPOC_DATA_DIR
	if prepare_data_directory "$MAPOC_DATA_DIR"; then
		if check_data_directory "$MAPOC_DATA_DIR"; then
			DATA_SOURCE="$MAPOC_DATA_DIR"
		fi
	fi

	# If still no data, try fallback locations
	if [ -z "$DATA_SOURCE" ]; then
		if check_data_directory "/app/data_built"; then
			DATA_SOURCE="/app/data_built"
			echo "Using fallback data from: /app/data_built"
		elif check_data_directory "/root/.mapoc"; then
			DATA_SOURCE="/root/.mapoc"
			echo "Using fallback data from: /root/.mapoc"
		else
			echo "Warning: No data source found. Application may not work correctly."
		fi
	fi
fi

# Copy data to MAPOC_DATA_DIR if we have a source and target is empty or missing key files
if [ -n "$DATA_SOURCE" ] && [ "$DATA_SOURCE" != "$MAPOC_DATA_DIR" ]; then
	if ! check_data_directory "$MAPOC_DATA_DIR"; then
		echo "Copying data from $DATA_SOURCE to $MAPOC_DATA_DIR..."
		mkdir -p "$MAPOC_DATA_DIR"

		# Remove corrupted/incomplete files before copying
		if [ -f "$MAPOC_DATA_DIR/geofabrik_tree.nw" ]; then
			existing_size=$(stat -c%s "$MAPOC_DATA_DIR/geofabrik_tree.nw" 2>/dev/null || stat -f%z "$MAPOC_DATA_DIR/geofabrik_tree.nw" 2>/dev/null || echo "0")
			source_size=$(stat -c%s "$DATA_SOURCE/geofabrik_tree.nw" 2>/dev/null || stat -f%z "$DATA_SOURCE/geofabrik_tree.nw" 2>/dev/null || echo "0")
			if [ "$existing_size" -ne "$source_size" ] && [ "$source_size" -gt 0 ]; then
				echo "Removing corrupted/incomplete geofabrik_tree.nw (${existing_size} bytes, expected ${source_size} bytes)..."
				rm -f "$MAPOC_DATA_DIR/geofabrik_tree.nw"
			fi
		fi

		# Use rsync if available for better progress and verification, otherwise use cp
		if command -v rsync >/dev/null 2>&1; then
			rsync -a --info=progress2 "$DATA_SOURCE/" "$MAPOC_DATA_DIR/" 2>/dev/null ||
				cp -r "$DATA_SOURCE"/* "$MAPOC_DATA_DIR"/ 2>/dev/null || true
		else
			cp -r "$DATA_SOURCE"/* "$MAPOC_DATA_DIR"/ 2>/dev/null || true
		fi

		# Sync to ensure files are fully written to disk
		sync

		echo "Data copied successfully to $MAPOC_DATA_DIR"
	else
		echo "Data directory $MAPOC_DATA_DIR already contains required files."
	fi
fi

# Final verification: ensure geofabrik_tree.nw exists where expected
if [ ! -f "$MAPOC_DATA_DIR/geofabrik_tree.nw" ]; then
	echo "WARNING: geofabrik_tree.nw not found in $MAPOC_DATA_DIR"
	echo "Expected location: $MAPOC_DATA_DIR/geofabrik_tree.nw"
	echo "This may cause runtime errors."
else
	# Verify the file is not empty and has reasonable content
	file_size=$(stat -c%s "$MAPOC_DATA_DIR/geofabrik_tree.nw" 2>/dev/null || stat -f%z "$MAPOC_DATA_DIR/geofabrik_tree.nw" 2>/dev/null || echo "0")
	if [ "$file_size" -lt 100000 ]; then
		echo "ERROR: geofabrik_tree.nw exists but appears too small ($file_size bytes, expected ~4MB)"
		echo "File is incomplete or corrupted. Please check data source."
		exit 1
	else
		echo "✓ Verified: geofabrik_tree.nw exists at $MAPOC_DATA_DIR/geofabrik_tree.nw (${file_size} bytes)"
	fi
fi

ensure_docc_colors "$MAPOC_DATA_DIR"

# Start the application
exec "$@"
