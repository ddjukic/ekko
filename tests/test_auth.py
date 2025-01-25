"""
Unit tests for the authentication module.
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ekko_prototype.auth import DEMO_USER_TRANSCRIPT_LIMIT, EMAIL_REGEX, SimpleAuth


class TestSimpleAuth:
    """Test suite for SimpleAuth class."""

    @pytest.fixture
    def temp_user_data(self):
        """Create a temporary user data file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{}")
            temp_path = f.name
        yield temp_path
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def mock_streamlit(self):
        """Mock streamlit session state."""
        with patch("ekko_prototype.auth.st") as mock_st:
            mock_st.session_state = MagicMock()
            mock_st.session_state.authenticated = False
            mock_st.session_state.user_email = None
            mock_st.session_state.transcript_count = 0
            mock_st.session_state.last_reset = datetime.now()
            mock_st.session_state.session_id = "test_session_123"
            yield mock_st

    def test_email_validation(self):
        """Test email validation regex."""
        # Valid emails
        assert EMAIL_REGEX.match("user@example.com")
        assert EMAIL_REGEX.match("user.name@example.co.uk")
        assert EMAIL_REGEX.match("user+tag@example.com")
        assert EMAIL_REGEX.match("user_name@example-domain.com")

        # Invalid emails
        assert not EMAIL_REGEX.match("invalid")
        assert not EMAIL_REGEX.match("@example.com")
        assert not EMAIL_REGEX.match("user@")
        assert not EMAIL_REGEX.match("user @example.com")
        assert not EMAIL_REGEX.match("user@example")

    def test_auth_initialization(self, temp_user_data, mock_streamlit):
        """Test SimpleAuth initialization."""
        auth = SimpleAuth(user_data_file=temp_user_data)

        assert auth.user_data_file == Path(temp_user_data)
        assert not mock_streamlit.session_state.authenticated
        assert mock_streamlit.session_state.user_email is None
        assert mock_streamlit.session_state.transcript_count == 0

    def test_validate_email_method(self, temp_user_data, mock_streamlit):
        """Test validate_email method."""
        auth = SimpleAuth(user_data_file=temp_user_data)

        assert auth.validate_email("valid@example.com")
        assert not auth.validate_email("invalid.email")
        assert not auth.validate_email("")

    def test_check_rate_limit(self, temp_user_data, mock_streamlit):
        """Test rate limit checking."""
        auth = SimpleAuth(user_data_file=temp_user_data)

        # Initial state - should have full limit
        within_limit, remaining = auth.check_rate_limit()
        assert within_limit
        assert remaining == DEMO_USER_TRANSCRIPT_LIMIT

        # Use one transcript
        mock_streamlit.session_state.transcript_count = 1
        within_limit, remaining = auth.check_rate_limit()
        assert within_limit
        assert remaining == DEMO_USER_TRANSCRIPT_LIMIT - 1

        # Use all transcripts
        mock_streamlit.session_state.transcript_count = DEMO_USER_TRANSCRIPT_LIMIT
        within_limit, remaining = auth.check_rate_limit()
        assert not within_limit
        assert remaining == 0

    def test_rate_limit_daily_reset(self, temp_user_data, mock_streamlit):
        """Test that rate limit resets after 24 hours."""
        auth = SimpleAuth(user_data_file=temp_user_data)

        # Set count to limit
        mock_streamlit.session_state.transcript_count = DEMO_USER_TRANSCRIPT_LIMIT

        # Set last reset to 25 hours ago
        mock_streamlit.session_state.last_reset = datetime.now() - timedelta(hours=25)

        # Check rate limit - should reset
        within_limit, remaining = auth.check_rate_limit()
        assert within_limit
        assert remaining == DEMO_USER_TRANSCRIPT_LIMIT
        assert mock_streamlit.session_state.transcript_count == 0

    def test_increment_usage(self, temp_user_data, mock_streamlit):
        """Test incrementing usage counter."""
        auth = SimpleAuth(user_data_file=temp_user_data)

        initial_count = mock_streamlit.session_state.transcript_count
        auth.increment_usage()
        assert mock_streamlit.session_state.transcript_count == initial_count + 1

    def test_save_and_load_user_data(self, temp_user_data, mock_streamlit):
        """Test saving and loading user data."""
        auth = SimpleAuth(user_data_file=temp_user_data)

        # Set some session data
        mock_streamlit.session_state.authenticated = True
        mock_streamlit.session_state.user_email = "test@example.com"
        mock_streamlit.session_state.transcript_count = 1

        # Save data
        auth._save_user_data()

        # Verify file was written
        assert os.path.exists(temp_user_data)

        # Load and verify data
        with open(temp_user_data) as f:
            data = json.load(f)

        assert "sessions" in data
        assert "test_session_123" in data["sessions"]
        session_data = data["sessions"]["test_session_123"]
        assert session_data["email"] == "test@example.com"
        assert session_data["transcript_count"] == 1
        assert session_data["authenticated"]

    def test_can_transcribe(self, temp_user_data, mock_streamlit):
        """Test can_transcribe method."""
        auth = SimpleAuth(user_data_file=temp_user_data)

        # Not authenticated
        mock_streamlit.session_state.authenticated = False
        assert not auth.can_transcribe()

        # Authenticated with remaining limit
        mock_streamlit.session_state.authenticated = True
        mock_streamlit.session_state.transcript_count = 0
        assert auth.can_transcribe()

        # Authenticated but limit reached
        mock_streamlit.session_state.transcript_count = DEMO_USER_TRANSCRIPT_LIMIT
        assert not auth.can_transcribe()

    def test_require_auth(self, temp_user_data, mock_streamlit):
        """Test require_auth method."""
        auth = SimpleAuth(user_data_file=temp_user_data)

        # Not authenticated - should return False (login form shown)
        mock_streamlit.session_state.authenticated = False
        assert not auth.require_auth()

        # Authenticated - should return True
        mock_streamlit.session_state.authenticated = True
        assert auth.require_auth()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
