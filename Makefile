.PHONY: help install install-dev test test-verbose coverage lint format clean docker-build docker-run docker-stop

help:
	@echo "DevOps Info Service - Development Commands"
	@echo ""
	@echo "Installation:"
	@echo "  make install          Install production dependencies"
	@echo "  make install-dev      Install development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test            Run tests"
	@echo "  make test-verbose    Run tests with verbose output"
	@echo "  make coverage        Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint            Run flake8 linter"
	@echo "  make format          Format code with black"
	@echo "  make format-check    Check formatting without changes"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build    Build Docker image"
	@echo "  make docker-run      Run Docker container"
	@echo "  make docker-stop     Stop Docker container"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean           Remove cache and generated files"
	@echo "  make run             Run application locally"

install:
	pip install --upgrade pip
	pip install -r requirements.txt

install-dev:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:
	pytest app_python/tests/

test-verbose:
	pytest app_python/tests/ -v

coverage:
	pytest app_python/tests/ --cov=. --cov-report=term-missing --cov-report=html
	@echo ""
	@echo "Coverage report generated in htmlcov/index.html"

lint:
	flake8 . --count --statistics
	@echo ""
	@echo "✅ Linting complete"

format:
	black .
	@echo ""
	@echo "✅ Code formatted"

format-check:
	black --check --diff .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type f -name "coverage.xml" -delete 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete"

docker-build:
	docker build -t devops-info-service:local .
	@echo ""
	@echo "✅ Docker image built: devops-info-service:local"

docker-run:
	docker run -d -p 8000:8000 --name devops-info devops-info-service:local
	@echo ""
	@echo "✅ Container started: http://localhost:8000"
	@echo "View logs: docker logs -f devops-info"

docker-stop:
	docker stop devops-info 2>/dev/null || true
	docker rm devops-info 2>/dev/null || true
	@echo "✅ Container stopped and removed"

run:
	python app.py

# CI-like check - runs everything CI does
ci-check: clean lint format-check coverage
	@echo ""
	@echo "✅ All CI checks passed!"
