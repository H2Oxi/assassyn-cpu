#!/bin/bash
# NOTE: This script should be sourced! Run as: source setup-env.sh

# Get the main repository root path
MAIN_REPO_PATH=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# Check if assassyn submodule exists and is initialized
if [ ! -d "$MAIN_REPO_PATH/assassyn/python" ]; then
  echo "ERROR: assassyn submodule not found or not initialized!"
  echo "Please run: git submodule update --init --recursive"
  return 1
fi

ASSASSYN_PATH="$MAIN_REPO_PATH/assassyn"

echo "=================================================="
echo "Setting up environment for assassyn-cpu"
echo "=================================================="

# Add assassyn python package to PYTHONPATH
echo "Adding $ASSASSYN_PATH/python to PYTHONPATH"
export PYTHONPATH="$ASSASSYN_PATH/python:$PYTHONPATH"

# Add project root to PYTHONPATH for impl.* imports
echo "Adding $MAIN_REPO_PATH to PYTHONPATH"
export PYTHONPATH="$MAIN_REPO_PATH:$PYTHONPATH"

# Set ASSASSYN_HOME to the submodule path
echo "Setting ASSASSYN_HOME to $ASSASSYN_PATH"
export ASSASSYN_HOME="$ASSASSYN_PATH"

# Set up Rust simulator runtime cache directory
echo "Setting CARGO_TARGET_DIR to $ASSASSYN_PATH/.sim-runtime-cache"
export CARGO_TARGET_DIR="$ASSASSYN_PATH/.sim-runtime-cache"

# Activate assassyn virtual environment if it exists
if [ -d "$ASSASSYN_PATH/.assassyn-venv" ]; then
  echo "Activating assassyn Python virtual environment..."
  source "$ASSASSYN_PATH/.assassyn-venv/bin/activate"
else
  echo "WARNING: No virtual environment found in assassyn submodule."
  echo "You may need to build assassyn first:"
  echo "  cd assassyn && source setup.sh && make build-all"
fi

# Set up Verilator if it exists in the submodule
if [ -d "$ASSASSYN_PATH/3rd-party/verilator" ]; then
  echo "Setting VERILATOR_ROOT to $ASSASSYN_PATH/3rd-party/verilator"
  export VERILATOR_ROOT="$ASSASSYN_PATH/3rd-party/verilator"
  export PATH="$VERILATOR_ROOT/bin:$PATH"
else
  echo "WARNING: Verilator not found in assassyn/3rd-party/verilator"
fi

echo "=================================================="
echo "Environment setup complete!"
echo ""
echo "You can now use assassyn in your Python scripts:"
echo "  from assassyn.frontend import *"
echo "  import assassyn"
echo "=================================================="
