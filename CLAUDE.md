# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a PyGame-based ROM downloader application designed for handheld gaming consoles, specifically tested with Knulli RG35xxSP. The application provides an interactive menu system for downloading game ROMs from various configured sources.

**IMPORTANT SECURITY NOTE**: This project is designed as a download management tool only and contains no ROM data. It includes comprehensive legal disclaimers and emphasizes that users must only download content they legally own.

## Development Environment

### Setup Commands
```bash
# Create and activate conda environment
conda env create -f environment.yml
conda activate roms_downloader

# Alternative: Use Make for common tasks
make setup    # Create conda environment
make run      # Run the application
make install  # Install in development mode
make dev      # Install with dev dependencies
make clean    # Clean generated files
make help     # Show all available commands

# Direct Python execution
python src/index.py
```

### Dependencies
- Python 3.11+
- pygame >= 2.0.0  
- requests >= 2.25.0

## Architecture

### Core Components

**Main Application (`src/index.py`)**: Single-file application containing:
- **UI System**: PyGame-based interface with support for both D-pad and keyboard navigation
- **Download Engine**: Multi-threaded downloading with progress tracking and resume capability
- **Configuration Management**: JSON-based system configuration and user settings
- **Image Caching**: Thumbnail loading and caching system for game artwork
- **Multi-format Support**: Handles various game file formats and automatic extraction

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
- Batocera: `/userdata/roms`, `/userdata/py_downloads`
- Development: Script directory relative paths

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
- Work directory for temporary downloads
- Automatic cleanup of temporary files
- Atomic file moves to prevent corruption