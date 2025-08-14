.PHONY: run watch install dev clean setup build-pygame build-linux build-apk build

CONDA_ENV = roms_downloader
CONDA_ACTIVATE = conda run -n $(CONDA_ENV)

# Default target
run:
	DEV_MODE=true $(CONDA_ACTIVATE) watchmedo auto-restart --patterns="*.py;download.json" --recursive --signal SIGTERM python src/index.py

# Setup development environment
setup:
	conda env create -f environment.yml
	$(CONDA_ACTIVATE) pip install -e .[dev]

# Install in development mode
install:
	$(CONDA_ACTIVATE) pip install -e .

# Install with dev dependencies
dev:
	$(CONDA_ACTIVATE) pip install -e .[dev]

# Clean generated files
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -f error.log
	rm -f config.json
	rm -rf py_downloads/
	rm -rf roms/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Create distribution package for console deployment
build-pygame:
	mkdir -p dist
	cp src/index.py dist/dw.pygame
	zip -r dist/pygame.zip dist/dw.pygame
	rm -rf dist/dw.pygame
	@echo "Distribution created in dist/ folder"
	@echo "Copy dist/dw.pygame and dist/download.json to console pygame directory"

# Build Linux binary with PyInstaller
build-linux:
	mkdir -p dist
	$(CONDA_ACTIVATE) pyinstaller --clean --onefile --hidden-import pygame --hidden-import requests --hidden-import nsz --distpath dist --name linux src/index.py
	@echo "Linux binary created in dist/rom-downloader"
	rm -rf build/

# Build APK with buildozer (local - requires Android SDK)
build-apk:
	@echo "Setting up Android SDK requirements..."
	mkdir -p dist
	$(CONDA_ACTIVATE) buildozer android debug
	cp bin/*.apk dist/ 2>/dev/null || echo "APK build completed, check bin/ folder"
	@echo "APK created in dist/ folder"
	rm -rf build/

# Build all targets (local)
build: build-pygame build-linux build-apk

# Show help
help:
	@echo "Available targets:"
	@echo "  run         - Run the ROM downloader application"
	@echo "  watch       - Run with file watching (auto-restart on changes)"
	@echo "  setup       - Create conda environment"
	@echo "  install     - Install in development mode"
	@echo "  dev         - Install with dev dependencies"
	@echo "  clean       - Clean generated files and caches"
	@echo "  format      - Format code with black"
	@echo "  lint        - Lint code with flake8"
	@echo "  test        - Run tests with pytest"
	@echo "  build       - Create distribution package for console"
	@echo "  build-linux - Build Linux binary with PyInstaller (simple)"
	@echo "  build-apk   - Build Android APK with buildozer (custom Docker)"
	@echo "  help        - Show this help message"