"""Smoke tests for Phase 3 buildings."""
import pytest
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_museum_imports():
    from src.orson.buildings.museum import MuseumState, render_museum
    state = MuseumState()
    assert state.is_visible == False
    panel = render_museum(state)
    assert panel is not None


def test_apartments_imports():
    from src.orson.buildings.apartments import ApartmentsState, render_apartments
    state = ApartmentsState()
    assert state.capacity == 10
    panel = render_apartments(state)
    assert panel is not None


def test_school_imports():
    from src.orson.buildings.school import SchoolState, render_school, TASK_TYPES
    state = SchoolState()
    assert "ADD_STUB" in TASK_TYPES
    panel = render_school(state)
    assert panel is not None


def test_mcdonalds_imports():
    from src.orson.buildings.mcdonalds import McDonaldsState, render_mcdonalds
    state = McDonaldsState()
    assert state.queue == []
    panel = render_mcdonalds(state)
    assert panel is not None


def test_newspaper_imports():
    from src.orson.buildings.newspaper import NewspaperState, render_newspaper
    state = NewspaperState()
    assert state.watch_list == []
    panel = render_newspaper(state)
    assert panel is not None


def test_components_has_buildings():
    from src.orson.components import Building, ICONS
    assert hasattr(Building, 'MUSEUM')
    assert hasattr(Building, 'APARTMENTS')
    assert hasattr(Building, 'SCHOOL')
    assert hasattr(Building, 'MCDONALDS')
    assert hasattr(Building, 'NEWSPAPER')
    assert 'MUSEUM' in ICONS
    assert 'APARTMENTS' in ICONS


def test_cli_state_has_visibility_flags():
    from src.orson.cli import SwarmState
    state = SwarmState()
    # Check that visibility attributes exist
    assert hasattr(state, 'museum_visible')
    assert hasattr(state, 'newspaper_visible')
    assert hasattr(state, 'school_visible')
    assert hasattr(state, 'mcdonalds_visible')
    # Check default values
    assert state.museum_visible == False
    assert state.newspaper_visible == False
    assert state.school_visible == False
    assert state.mcdonalds_visible == False


def test_cli_state_has_building_states():
    from src.orson.cli import SwarmState
    from src.orson.buildings.museum import MuseumState
    from src.orson.buildings.newspaper import NewspaperState
    from src.orson.buildings.school import SchoolState
    from src.orson.buildings.mcdonalds import McDonaldsState

    state = SwarmState()
    assert isinstance(state.museum_state, MuseumState)
    assert isinstance(state.newspaper_state, NewspaperState)
    assert isinstance(state.school_state, SchoolState)
    assert isinstance(state.mcdonalds_state, McDonaldsState)
