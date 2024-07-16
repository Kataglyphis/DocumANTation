#!/bin/bash

# Define the directories
TARGET_DIR="/root/texmf/tex/latex/commonstuff"
SOURCE_DIR="md2pdfLib/presentation/template/latex"

# Step 1: Remove the old .sty files
echo "Removing old .sty files..."
rm -rf "$TARGET_DIR/awesome-beamer" "$TARGET_DIR/smile"
rm -rf "$TARGET_DIR"

echo "Update database with removed .sty files"
texhash

# Step 2: Create the target directory if it doesn't exist
echo "Creating target directory..."
mkdir -p "$TARGET_DIR"

# Step 3: Add the updated .sty files
echo "Copying updated .sty files..."
cp -r "$SOURCE_DIR/awesome-beamer" "$TARGET_DIR/"
cp -r "$SOURCE_DIR/smile" "$TARGET_DIR/"

# Step 4: Update the TeX file database
echo "Updating TeX file database..."
texhash

echo "Update complete."
