#!/bin/bash

# Check if 'uv' is installed
if ! command -v uv &> /dev/null; then
    echo "'uv' is not installed. Installing..."

    # Install via curl (adjust URL as needed based on platform or version)
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # After install, you might need to add it to PATH (if the install location isn't in PATH)
    if ! command -v uv &> /dev/null; then
        echo "'uv' was installed but not found in PATH. You may need to add it manually."
        echo "Try adding ~/.cargo/bin to your PATH:"
        echo 'export PATH="$HOME/.cargo/bin:$PATH"'
    else
        echo "'uv' installed successfully!"
    fi
else
    echo "'uv' is already installed."
fi

# Check if 'imessage-exporter' is installed
if ! command -v imessage-exporter &> /dev/null; then
    echo "'imessage-exporter' is not installed. Installing via Homebrew..."
    
    # Install via Homebrew
    brew install imessage-exporter
    
    # Verify installation
    if ! command -v imessage-exporter &> /dev/null; then
        echo "Error: Failed to install imessage-exporter"
        exit 1
    else
        echo "'imessage-exporter' installed successfully!"
    fi
else
    echo "'imessage-exporter' is already installed."
fi


