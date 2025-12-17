# Integration Tests

This directory contains integration tests for the RoutePlanner application.

## Testing Strategy

This project uses **integration tests** rather than granular unit tests. Each tab in the UI has a corresponding test file that validates the complete workflow through the `ProblemState` object.

## Test Structure

- `conftest.py` - Shared pytest fixtures and configuration
- `test_parse_tab.py` - Tests for CSV parsing functionality
- `test_geocode_tab.py` - Tests for geocoding with caching
- `test_cluster_tab.py` - Tests for clustering functionality (TODO)
- `test_solve_tab.py` - Tests for route solving functionality (TODO)

## Running Tests

To run all tests:
```bash
pytest tests/
```

To run tests for a specific tab:
```bash
pytest tests/test_geocode_tab.py
pytest tests/test_cluster_tab.py

python3 -m pytest tests/test_cluster_tab.py -v
```

To run with verbose output:
```bash
pytest tests/ -v
```

To run with coverage:
```bash
pytest tests/ --cov=. --cov-report=html
```

Run single test
```bash
uv run pytest tests/test_parse_tab.py::TestParseTab::test_parse_excel -v
uv run pytest tests/test_cluster_tab.py::TestClusterTab::test_cluster_sites_with_manual_k -v
```

## Test Fixtures

### `temp_workspace`
Creates a temporary workspace directory for testing. Automatically cleaned up after each test.

### `sample_csv_data`
Provides sample CSV data with sites for testing.

### `problem_state`
Creates a `ProblemState` instance with a temporary workspace.

## Writing New Tests

When adding new functionality:

1. Add tests to the appropriate tab test file
2. Use the `ProblemState` object as the main assertion point
3. Test the complete workflow from input to persisted state
4. Use fixtures for common setup (workspace, sample data, etc.)

## Test Coverage

Integration tests should cover:
- ✅ CSV parsing with various formats
- ✅ Geocoding with cache hits and misses
- ✅ Geocoding persistence
- 🚧 Clustering algorithms and persistence
- 🚧 Route solving and optimization
- 🚧 Route export functionality
