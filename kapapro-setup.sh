#!/bin/bash

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Function to print error message and exit
error_exit() {
    echo -e "${RED}Error: $1${NC}"
    exit 1
}

# Function to print success message
print_success() {
    echo -e "${GREEN}$1${NC}"
}

# 1. Install dhanhq package
print_success "Installing dhanhq package..."
if ! pip install dhanhq; then
    error_exit "Failed to install dhanhq package."
fi
print_success "dhanhq package installed successfully!"

# 2. Update requirements.txt with dhanhq
print_success "Updating requirements.txt..."
if ! grep -q 'dhanhq' requirements.txt; then
    echo 'dhanhq' >> requirements.txt
fi
print_success "requirements.txt updated successfully!"

# 3. Set up environment variables
print_success "Setting up environment variables..."
echo "export DHAN_API_KEY='your_api_key'" >> ~/.bashrc
source ~/.bashrc
print_success "Environment variables set up successfully!"

# 4. Validate the installation
print_success "Validating installation..."
if python3 -c "import dhanhq"; then
    print_success "Installation validated: dhanhq package is available."
else
    error_exit "Installation validation failed: dhanhq package not found."
fi

# 5. Provide instructions for Dhan API credentials
print_success "Please set your Dhan API credentials in the ~/.bashrc file as follows:
export DHAN_API_KEY='your_api_key'  # Your Dhan API key
export DHAN_API_SECRET='your_api_secret'  # Your Dhan API secret"