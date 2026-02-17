"""Tests for Deep Work input validation.

This test suite validates the input validation added to the
plan_existing_project function to prevent silent failures.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from pocketpaw.deep_work.session import VALID_RESEARCH_DEPTHS, DeepWorkSession
from pocketpaw.mission_control import (
    FileMissionControlStore,
    MissionControlManager,
)


@pytest.fixture
async def session(tmp_path):
    """Create a DeepWorkSession with a temporary store for testing."""
    store = FileMissionControlStore(tmp_path)
    manager = MissionControlManager(store)

    # Create mock executor
    executor = MagicMock()
    executor.stop_task = AsyncMock()
    executor.is_task_running = MagicMock(return_value=False)

    session = DeepWorkSession(manager=manager, executor=executor)
    
    # Create a test project
    project = await manager.create_project(
        title="Test Project",
        description="Test project for validation tests",
    )
    
    # Store project_id for tests to use
    session._test_project_id = project.id
    
    return session


class TestResearchDepthValidation:
    """Test validation of research_depth parameter."""

    @pytest.mark.asyncio
    async def test_valid_research_depths_constant_exists(self):
        """The VALID_RESEARCH_DEPTHS constant should be defined."""
        assert VALID_RESEARCH_DEPTHS is not None
        assert len(VALID_RESEARCH_DEPTHS) == 4
        assert "none" in VALID_RESEARCH_DEPTHS
        assert "quick" in VALID_RESEARCH_DEPTHS
        assert "standard" in VALID_RESEARCH_DEPTHS
        assert "deep" in VALID_RESEARCH_DEPTHS

    @pytest.mark.asyncio
    async def test_invalid_research_depth(self, session):
        """Invalid research_depth should raise ValueError with clear message."""
        with pytest.raises(ValueError) as exc_info:
            await session.plan_existing_project(
                session._test_project_id,
                "Build a todo app",
                "invalid_depth"
            )
        
        error_msg = str(exc_info.value)
        assert "Invalid research_depth" in error_msg
        assert "invalid_depth" in error_msg
        assert "none" in error_msg or "quick" in error_msg  # Shows valid options

    @pytest.mark.asyncio
    async def test_empty_research_depth(self, session):
        """Empty string research_depth should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            await session.plan_existing_project(
                session._test_project_id,
                "Build a todo app",
                ""
            )
        
        assert "Invalid research_depth" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_case_sensitive_research_depth(self, session):
        """research_depth should be case-sensitive (STANDARD != standard)."""
        with pytest.raises(ValueError) as exc_info:
            await session.plan_existing_project(
                session._test_project_id,
                "Build a todo app",
                "STANDARD"  # uppercase
            )
        
        assert "Invalid research_depth" in str(exc_info.value)


class TestUserInputValidation:
    """Test validation of user_input parameter."""

    @pytest.mark.asyncio
    async def test_empty_user_input(self, session):
        """Empty user_input should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            await session.plan_existing_project(
                session._test_project_id,
                "",
                "standard"
            )
        
        assert "cannot be empty" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_whitespace_only_user_input(self, session):
        """Whitespace-only user_input should raise ValueError."""
        test_cases = [
            "   ",
            "\n",
            "\t",
            "  \n  \t  ",
        ]
        
        for whitespace_input in test_cases:
            with pytest.raises(ValueError) as exc_info:
                await session.plan_existing_project(
                    session._test_project_id,
                    whitespace_input,
                    "standard"
                )
            
            assert "cannot be empty" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_user_input_too_long(self, session):
        """User input over 5000 chars should raise ValueError."""
        long_input = "a" * 5001
        
        with pytest.raises(ValueError) as exc_info:
            await session.plan_existing_project(
                session._test_project_id,
                long_input,
                "standard"
            )
        
        error_msg = str(exc_info.value)
        assert "too long" in error_msg
        assert "5000" in error_msg

    @pytest.mark.asyncio
    async def test_user_input_exactly_5000_chars(self, session):
        """User input of exactly 5000 chars should be accepted."""
        # Mock the planner to avoid requiring real LLM configuration
        session.planner = MagicMock()
        session.planner.plan = AsyncMock(return_value=None)
        # Mock _broadcast_planning_complete to avoid asyncio errors in mock
        session._broadcast_planning_complete = MagicMock()

        exact_input = "a" * 5000

        # If validation is correct, this should not raise a ValueError
        # (It will fail later because our mock planner returns None, but we just check validation)
        try:
            await session.plan_existing_project(
                session._test_project_id,
                exact_input,
                "standard",
            )
        except AttributeError:
             # Expected failure because mock returns None for result
             pass
        except ValueError as e:
             pytest.fail(f"Validation failed unexpectedly: {e}")


class TestValidInputAcceptance:
    """Test that valid inputs are accepted (don't raise validation errors)."""

    @pytest.mark.asyncio
    async def test_minimal_valid_input(self, session):
        """Minimal valid input should pass validation."""
        # Mock the planner to avoid requiring real LLM configuration
        session.planner = MagicMock()
        session.planner.plan = AsyncMock(return_value=None)
        session._broadcast_planning_complete = MagicMock()

        # If validation is correct, this should not raise a ValueError
        try:
            await session.plan_existing_project(
                session._test_project_id,
                "a",  # single character
                "none",  # no research needed
            )
        except AttributeError:
             pass
        except ValueError as e:
             pytest.fail(f"Validation failed unexpectedly: {e}")

    @pytest.mark.asyncio
    async def test_all_valid_research_depths_pass_validation(self, session):
        """All valid research_depth values should pass validation."""
        # Mock the planner to avoid requiring real LLM configuration
        session.planner = MagicMock()
        session.planner.plan = AsyncMock(return_value=None)
        session._broadcast_planning_complete = MagicMock()

        for depth in VALID_RESEARCH_DEPTHS:
            try:
                await session.plan_existing_project(
                    session._test_project_id,
                    "Build a simple app",
                    depth,
                )
            except AttributeError:
                pass
            except ValueError as e:
                pytest.fail(f"Validation failed unexpectedly for depth {depth}: {e}")