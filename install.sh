#!/bin/bash

# Claude Code Skills Installation Script
# This script helps team members quickly set up Claude Code skills

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

# Header
echo "=========================================="
echo "  Claude Code Skills Installation"
echo "=========================================="
echo

# Check if script is being sourced or executed
if [ "${BASH_SOURCE[0]}" != "${0}" ]; then
  log_error "This script should be executed, not sourced."
  log_error "Run: bash install.sh"
  return 1
fi

# Determine the script location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILLS_DIR="$HOME/.claude/skills"

echo "Script location: $SCRIPT_DIR"
echo "Target skills directory: $SKILLS_DIR"
echo

# Step 1: Check prerequisites
log_info "Checking prerequisites..."

# Check for Git
if ! command -v git &> /dev/null; then
  log_error "Git is not installed. Please install Git first."
  exit 1
fi
log_info "Git found: $(git --version)"

# Check for Node.js
if ! command -v node &> /dev/null; then
  log_warn "Node.js is not installed."
  echo "  Install from: https://nodejs.org/"
  read -p "  Continue anyway? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
else
  log_info "Node.js found: $(node --version)"
fi

# Check for npm
if ! command -v npm &> /dev/null; then
  log_warn "npm is not installed."
  read -p "  Continue anyway? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
else
  log_info "npm found: $(npm --version)"
fi

echo

# Step 2: Set up skills directory
log_info "Setting up skills directory..."

if [ "$SCRIPT_DIR" = "$SKILLS_DIR" ]; then
  log_info "Already in correct location: $SKILLS_DIR"
elif [ -L "$SKILLS_DIR" ] && [ "$(readlink "$SKILLS_DIR")" = "$SCRIPT_DIR" ]; then
  log_info "Symlink already exists: $SKILLS_DIR -> $SCRIPT_DIR"
else
  if [ -e "$SKILLS_DIR" ]; then
    log_warn "Directory $SKILLS_DIR already exists."
    echo "  Options:"
    echo "    1. Backup and replace with symlink"
    echo "    2. Keep existing and skip"
    echo "    3. Cancel installation"
    read -p "  Choose (1/2/3): " -n 1 -r
    echo
    case $REPLY in
      1)
        backup_dir="$SKILLS_DIR.backup.$(date +%Y%m%d_%H%M%S)"
        mv "$SKILLS_DIR" "$backup_dir"
        log_info "Backed up to: $backup_dir"
        ln -s "$SCRIPT_DIR" "$SKILLS_DIR"
        log_info "Created symlink: $SKILLS_DIR -> $SCRIPT_DIR"
        ;;
      2)
        log_info "Keeping existing directory"
        ;;
      *)
        log_error "Installation cancelled"
        exit 1
        ;;
    esac
  else
    mkdir -p "$(dirname "$SKILLS_DIR")"
    ln -s "$SCRIPT_DIR" "$SKILLS_DIR"
    log_info "Created symlink: $SKILLS_DIR -> $SCRIPT_DIR"
  fi
fi

echo

# Step 3: Install Gemini CLI
log_info "Checking Gemini CLI..."

if command -v gemini &> /dev/null; then
  log_info "Gemini CLI already installed: $(gemini --version 2>&1 || echo 'version unknown')"
  read -p "  Reinstall/update? (y/n) " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    npm install -g @google/gemini-cli
    log_info "Gemini CLI updated"
  fi
else
  log_warn "Gemini CLI not found. Installing..."
  if npm install -g @google/gemini-cli; then
    log_info "Gemini CLI installed successfully"
  else
    log_error "Failed to install Gemini CLI"
    log_error "You may need to run with sudo:"
    log_error "  sudo npm install -g @google/gemini-cli"
  fi
fi

echo

# Step 4: Check API key
log_info "Checking GEMINI_API_KEY..."

if [ -n "$GEMINI_API_KEY" ]; then
  log_info "GEMINI_API_KEY is set"
else
  log_warn "GEMINI_API_KEY is not set"
  echo
  echo "  To set your API key:"
  echo "    1. Get key from: https://aistudio.google.com/app/apikey"
  echo "    2. Add to your shell profile (~/.zshrc or ~/.bashrc):"
  echo "       export GEMINI_API_KEY=\"your-api-key-here\""
  echo
  read -p "  Do you want to set it now? (y/n) " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "  Enter your API key: " api_key
    export GEMINI_API_KEY="$api_key"

    # Detect shell and add to profile
    if [ -n "$ZSH_VERSION" ] || [ "$SHELL" = "/bin/zsh" ]; then
      profile="$HOME/.zshrc"
    else
      profile="$HOME/.bashrc"
    fi

    if [ -f "$profile" ]; then
      if grep -q "GEMINI_API_KEY" "$profile"; then
        log_warn "GEMINI_API_KEY already found in $profile"
        log_warn "Please update it manually if needed"
      else
        echo "export GEMINI_API_KEY=\"$api_key\"" >> "$profile"
        log_info "Added GEMINI_API_KEY to $profile"
        log_warn "Run 'source $profile' or restart your terminal"
      fi
    else
      log_warn "Could not find shell profile. Set manually."
    fi
  fi
fi

echo

# Step 5: Make scripts executable
log_info "Setting script permissions..."
find "$SCRIPT_DIR" -name "*.sh" -type f -exec chmod +x {} \;
log_info "All shell scripts are now executable"

echo

# Step 6: Verify installation
log_info "Verifying installation..."

# Check skills directory
if [ -d "$SKILLS_DIR/code-review-gemini" ]; then
  log_info "Skill found: code-review-gemini"
else
  log_error "Skill not found: code-review-gemini"
fi

# Test Gemini CLI
if command -v gemini &> /dev/null; then
  if [ -n "$GEMINI_API_KEY" ]; then
    log_info "Gemini CLI is ready"
  else
    log_warn "Gemini CLI installed but API key not set"
  fi
else
  log_error "Gemini CLI not available"
fi

echo
echo "=========================================="
echo "  Installation Complete!"
echo "=========================================="
echo
echo "Next steps:"
echo "  1. Make sure GEMINI_API_KEY is set (see above)"
echo "  2. Navigate to a git repository"
echo "  3. Stage some changes: git add <files>"
echo "  4. Start Claude Code: claude"
echo "  5. Try: 'Review the staged files'"
echo
echo "Documentation:"
echo "  - Quick start: $SCRIPT_DIR/README.md"
echo "  - Setup guide: $SCRIPT_DIR/SETUP.md"
echo "  - Troubleshooting: $SCRIPT_DIR/TROUBLESHOOTING.md"
echo
