# Project Overview

## Script JSON Conversion Evaluation System

A comprehensive automated evaluation system for validating script-to-JSON conversion quality.

## Quick Facts

- **Language**: Python 3.9+
- **Main Framework**: DeepEval 0.21+
- **LLM Provider**: DeepSeek API
- **Validation**: Pydantic 2.5+
- **Type**: Quality Assurance / NLP System

## Core Purpose

This system evaluates the quality of converting screenplay/script text into structured JSON format using a three-tier evaluation architecture:

1. **Structure Layer**: JSON format and field completeness validation
2. **Statistical Layer**: Scene boundary, character recognition metrics
3. **Semantic Layer**: LLM-as-Judge deep semantic evaluation

## Key Features

- Three-tier evaluation architecture (structure, statistics, semantics)
- Multi-scenario support (standard scripts and story outlines)
- Rich evaluation metrics (F1, Precision, Recall for boundaries, character extraction)
- DeepSeek API integration with smart retry and cost tracking
- Detailed reporting (JSON and HTML formats)
- Full Docker containerization support

## Project Structure

```
Script-JSON-Conversion-Evaluation-System/
├── src/              # Source code
│   ├── models/       # Pydantic data models
│   ├── metrics/      # Evaluation metrics
│   ├── llm/          # LLM integration (DeepSeek)
│   ├── evaluators/   # Evaluation orchestrators
│   └── utils/        # Utility functions
├── tests/            # Test suites
├── configs/          # YAML configurations
├── prompts/          # LLM prompt templates
├── docs/             # Documentation
├── scripts/          # Utility scripts
└── ref/              # Reference documentation (this directory)
```

## Quick Start

### Local Python
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env  # Add DEEPSEEK_API_KEY

# Run system test
python scripts/test_system.py
```

## Related Documentation

- [Architecture](./architecture.md) - System design and components
- [Development Guide](./development.md) - Development workflows
- [API Reference](./api-reference.md) - Code API documentation
- [Project Structure](../docs/project_structure.md) - Detailed structure
