#!/bin/bash

# Script to remove all www subdomain references from documentation

echo "Removing www subdomain references..."

# Find all markdown, shell, text, and conf files
find . -type f \( -name "*.md" -o -name "*.sh" -o -name "*.txt" -o -name "*.conf" \) | while read file; do
    # Skip this script itself
    if [ "$file" = "./remove-www.sh" ]; then
        continue
    fi
    
    # Remove www.civicfix-server.asolvitra.tech references
    sed -i 's/-d www\.civicfix-server\.asolvitra\.tech \\//g' "$file"
    sed -i 's/-d www\.civicfix-server\.asolvitra\.tech//g' "$file"
    sed -i 's/www\.civicfix-server\.asolvitra\.tech//g' "$file"
    sed -i 's/server_name civicfix-server\.asolvitra\.tech ;/server_name civicfix-server.asolvitra.tech;/g' "$file"
    sed -i '/WWW:.*https:\/\/civicfix-server\.asolvitra\.tech/d' "$file"
    sed -i '/\*\*WWW\*\*/d' "$file"
    sed -i '/WWW subdomain:/d' "$file"
    sed -i '/| A | www | YOUR_VM_IP | 3600 |/d' "$file"
    
    echo "Updated: $file"
done

echo "Done! All www references removed."
