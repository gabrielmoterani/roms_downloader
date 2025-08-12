# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a PyGame-based ROM downloader application designed for handheld gaming consoles, specifically tested with Knulli RG35xxSP. The application provides an interactive menu system for downloading game ROMs from various configured sources.

**IMPORTANT SECURITY NOTE**: This project is designed as a download management tool only and contains no ROM data. It includes comprehensive legal disclaimers and emphasizes that users must only download content they legally own.

## Development Environment

### Setup Commands
```bash
# Using Make (Recommended)
make setup    # Create conda environment and install dependencies
make run      # Run with auto-restart on file changes
make help     # Show all available commands
make clean    # Clean generated files and caches
make format   # Format code with black
make lint     # Lint code with flake8
make build    # Create distribution package for console deployment

# Manual Setup
conda env create -f environment.yml
conda activate roms_downloader
pip install -e .[dev]

# Run application
python src/index.py
```

### Dependencies
**Runtime:**
- Python 3.11+
- pygame >= 2.0.0  
- requests >= 2.25.0

**Development:**
- watchdog (auto-restart during development)
- black (code formatting)
- flake8 (linting)
- pytest (testing framework)

## Architecture

### Core Components

**Main Application (`src/index.py`)**: Single-file application containing:
- **UI System**: PyGame-based interface with D-pad and keyboard navigation
- **Download Engine**: Multi-threaded downloading with progress tracking and resume capability
- **Configuration Management**: JSON-based system configuration and user settings
- **Image Caching**: Thumbnail loading and caching system for game artwork
- **Multi-format Support**: Handles various game file formats and automatic ZIP extraction
- **Platform Detection**: Auto-configures paths for Batocera vs development environments

### Key Features

**Navigation Modes**:
- `systems`: Browse available gaming systems 
- `games`: Browse and select games within a system
- `settings`: Configure application behavior

**View Types**:
- List view: Traditional vertical list with thumbnails
- Grid view: 4-column grid layout for visual browsing

**Download System**:
- Supports multiple source types: Direct URLs, HTML directory parsing, JSON APIs
- Automatic file extraction for ZIP archives
- Configurable work and ROM directories
- Real-time progress tracking with speed indicators

## Configuration

### System Configuration (`assets/config/download.json`)
Each gaming system entry supports:
- `name`: Display name
- `url`: Base URL for ROM directory listing  
- `file_format`: Supported file extensions
- `roms_folder`: Target directory for downloaded files
- `regex`: Custom regex for HTML parsing (optional)
- `boxarts`: Base URL for game thumbnails
- `should_unzip`: Auto-extract ZIP files

### User Settings (`config.json`)
Runtime settings stored in script directory:
- Display preferences (box-art, view type)
- Directory paths (work, ROM directories) 
- Cache settings and USA-only filtering

### Environment Detection
Application auto-detects platform and sets appropriate default paths:
- **Batocera/Console**: `/userdata/roms`, `/userdata/py_downloads`
- **Development**: Script directory relative paths (`./roms`, `./py_downloads`)
- **Distribution**: Built using `make build` for console deployment

## Development Guidelines

### Error Handling
All operations include comprehensive error logging to `error.log` with timestamps and stack traces. Check this file when debugging issues.

### Threading Model  
- Main UI thread handles all PyGame operations
- Background threads for image loading and file downloads
- Thread-safe queue system for image cache updates

### Platform Compatibility
Designed for embedded Linux systems but runs on desktop for development. Control mapping supports both joystick (primary) and keyboard input.

### File Operations
- Work directory for temporary downloads with configurable location
- Automatic cleanup of temporary files and failed downloads
- Atomic file moves to prevent corruption during transfers
- ZIP extraction with proper file organization
- Image cache management with automatic thumbnail loading

### Build System
- **Makefile**: Provides common development tasks
- **Conda Environment**: Isolated dependency management
- **Distribution Building**: Creates console-ready files in `dist/` directory
- **Code Quality**: Integrated formatting (black) and linting (flake8)