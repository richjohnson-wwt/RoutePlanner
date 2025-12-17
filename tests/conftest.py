"""
Pytest configuration and shared fixtures for integration tests.
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from models.problem_state import ProblemState


@pytest.fixture
def temp_workspace():
    """
    Create a temporary workspace directory for testing.
    Yields the path and cleans up after the test.
    """
    temp_dir = tempfile.mkdtemp()
    workspace_path = Path(temp_dir)
    
    yield workspace_path
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_csv_data():
    """
    Return sample CSV data for testing.
    """
    return """SiteID,Address,State,Lat,Lng
Site1,123 Main St,CA,37.7749,-122.4194
Site2,456 Oak Ave,NY,40.7128,-74.0060
Site3,789 Pine Rd,TX,29.7604,-95.3698"""


@pytest.fixture
def problem_state_workspace():
    """
    Create a properly structured workspace directory for ProblemState.
    Returns tuple of (base_dir, state_dir) and cleans up after test.
    """
    temp_dir = tempfile.mkdtemp()
    base_dir = Path(temp_dir)
    
    # Create the expected directory structure: base_dir/client/workspace/state_code
    state_dir = base_dir / "test_client" / "test_workspace" / "CA"
    state_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a minimal addresses.csv so ProblemState can load
    addresses_csv = state_dir / "addresses.csv"
    addresses_csv.write_text("SiteID,Address,State\n")
    
    yield base_dir, state_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def problem_state(problem_state_workspace):
    """
    Create a ProblemState instance with a temporary workspace.
    """
    base_dir, state_dir = problem_state_workspace
    return ProblemState.from_workspace(
        client="test_client",
        workspace="test_workspace",
        entity_type="site",
        state_code="CA",
        base_dir=base_dir
    )
