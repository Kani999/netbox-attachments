#!/bin/bash

# swap_netbox_config.sh - Quick NetBox configuration swapper
#
# This script helps quickly swap between different netbox_attachments configurations
# for testing on a running NetBox web server.
#
# Usage:
#   ./swap_netbox_config.sh <config_number> [--no-backup]
#
# Examples:
#   ./swap_netbox_config.sh 1        # Load config_01_minimal.py
#   ./swap_netbox_config.sh 5        # Load config_05_left_page.py
#   ./swap_netbox_config.sh 12       # Load config_12_production.py
#   ./swap_netbox_config.sh 1 --no-backup  # Don't create backup

set -e

CONFIG_DIR="/opt/netbox-attachments/netbox_attachments/tests/fixtures"
NETBOX_CONFIG="/opt/netbox/netbox/netbox/configuration.py"
BACKUP_DIR="/tmp/netbox_config_backups"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check arguments
if [ -z "$1" ]; then
    echo "Usage: $0 <config_number> [--no-backup]"
    echo ""
    echo "Available configurations:"
    ls -1 "$CONFIG_DIR"/config_*.py | sed 's/.*config_/  Config /' | sed 's/_.*//'
    exit 1
fi

CONFIG_NUM=$1
NO_BACKUP=$2

# Find config file with glob expansion
CONFIG_FILE=$(ls "$CONFIG_DIR"/config_$(printf "%02d" "$CONFIG_NUM")_*.py 2>/dev/null | head -1)

# Find config file
if [ -z "$CONFIG_FILE" ] || [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}Error: Configuration file not found for config $CONFIG_NUM${NC}"
    echo "Checked: $CONFIG_DIR/config_$(printf "%02d" "$CONFIG_NUM")_*.py"
    exit 1
fi

CONFIG_NAME=$(basename "$CONFIG_FILE" .py)

# Create backup if requested
if [ "$NO_BACKUP" != "--no-backup" ]; then
    mkdir -p "$BACKUP_DIR"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/configuration_${TIMESTAMP}.py"
    cp "$NETBOX_CONFIG" "$BACKUP_FILE"
    echo -e "${GREEN}✓ Backup created: $BACKUP_FILE${NC}"
fi

# Extract netbox_attachments config from the config file
echo -e "${YELLOW}Loading configuration: $CONFIG_NAME${NC}"

# Use Python to safely replace only the netbox_attachments configuration block
export CONFIG_FILE NETBOX_CONFIG
python3 << 'PYTHON_SCRIPT'
import os
import re
import json

config_file = os.environ['CONFIG_FILE']
netbox_config = os.environ['NETBOX_CONFIG']

# Read the new configuration file
with open(config_file, 'r') as f:
    new_config_content = f.read()
# Extract the entire netbox_attachments config from the new config file
# Find the netbox_attachments key and extract its brace-balanced value
key_pattern = "['\"]netbox_attachments['\"]\\s*:"
key_match = re.search(key_pattern, new_config_content)

if not key_match:
    print("Error: Could not find netbox_attachments config in config file")
    exit(1)

# Find the opening brace after the key
start_pos = key_match.end()
while start_pos < len(new_config_content) and new_config_content[start_pos] != '{':
    start_pos += 1

if start_pos >= len(new_config_content):
    print("Error: Could not find opening brace for netbox_attachments config")
    exit(1)

# Extract brace-balanced block
brace_count = 0
end_pos = start_pos
for i in range(start_pos, len(new_config_content)):
    char = new_config_content[i]
    if char == '{':
        brace_count += 1
    elif char == '}':
        brace_count -= 1
        if brace_count == 0:
            end_pos = i + 1
            break

if brace_count != 0:
    print("Error: Unbalanced braces in netbox_attachments config")
    exit(1)

# Extract the key:value pair
new_attachment_config = new_config_content[key_match.start():end_pos]

# Read the NetBox configuration file
with open(netbox_config, 'r') as f:
    netbox_content = f.read()

# Replace only the netbox_attachments section in PLUGINS_CONFIG
key_pattern_netbox = "['\"]netbox_attachments['\"]\\s*:"
key_match_netbox = re.search(key_pattern_netbox, netbox_content)

if not key_match_netbox:
    print("Error: Could not find netbox_attachments section in NetBox configuration")
    exit(1)

# Find the opening brace and extract brace-balanced block in netbox_content
start_pos_netbox = key_match_netbox.end()
while start_pos_netbox < len(netbox_content) and netbox_content[start_pos_netbox] != '{':
    start_pos_netbox += 1

brace_count_netbox = 0
end_pos_netbox = start_pos_netbox
for i in range(start_pos_netbox, len(netbox_content)):
    char = netbox_content[i]
    if char == '{':
        brace_count_netbox += 1
    elif char == '}':
        brace_count_netbox -= 1
        if brace_count_netbox == 0:
            end_pos_netbox = i + 1
            break

# Replace the old netbox_attachments config with the new one
updated_content = netbox_content[:key_match_netbox.start()] + new_attachment_config + netbox_content[end_pos_netbox:]

# Write the updated configuration
with open(netbox_config, 'w') as f:
    f.write(updated_content)

print("✓ Configuration updated successfully")

PYTHON_SCRIPT
PYTHON_STATUS=$?

if [ $PYTHON_STATUS -eq 0 ]; then
    echo -e "${GREEN}✓ Successfully loaded $CONFIG_NAME${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Restart NetBox web server"
    echo "  2. Visit http://localhost:8000 to verify"
    echo ""
    if [ -n "$BACKUP_DIR" ] && [ -d "$BACKUP_DIR" ]; then
        echo "Backup location:"
        echo "  $BACKUP_DIR/"
    fi
else
    echo -e "${RED}Error: Failed to update configuration${NC}"
    exit 1
fi
