.PHONY: run install dev clean test lint format setup

# Default target
run:
	DEV_MODE=true python src/index.py

# Setup development environment
setup:
	conda env create -f environment.yml

# Install in development mode
install:
	pip install -e .

# Install with dev dependencies
dev:
	pip install -e .[dev]

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

# Format code
format:
	black src/

# Lint code
lint:
	flake8 src/

# Run tests (if added later)
test:
	pytest

# Create distribution package for console deployment
build: src/index.py assets/config/download.json
	mkdir -p dist
	cp src/index.py dist/dw.pygame
	cp assets/config/download.json dist/download.json
	@echo "Distribution created in dist/ folder"
	@echo "Copy dist/dw.pygame and dist/download.json to console pygame directory"

# Show help
help:
	@echo "Available targets:"
	@echo "  run      - Run the ROM downloader application"
	@echo "  setup    - Create conda environment"
	@echo "  install  - Install in development mode"
	@echo "  dev      - Install with dev dependencies"
	@echo "  clean    - Clean generated files and caches"
	@echo "  format   - Format code with black"
	@echo "  lint     - Lint code with flake8"
	@echo "  test     - Run tests with pytest"
	@echo "  build    - Create distribution package"
	@echo "  help     - Show this help message"

# Install git hooks
install-hooks:
	cp .git/hooks/pre-push.sample .git/hooks/pre-push 2>/dev/null || true
	chmod +x .git/hooks/pre-push
	@echo "Git hooks installed"

# Remove git hooks  
uninstall-hooks:
	rm -f .git/hooks/pre-push
	@echo "Git hooks removed"