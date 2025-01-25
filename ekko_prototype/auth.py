"""
Simple email-based authentication and rate limiting for ekko.

This module provides a lightweight authentication system using email validation
and session-based rate limiting for transcription actions.
"""

import hashlib
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st

# Email validation regex
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

# Rate limiting settings
DEMO_USER_TRANSCRIPT_LIMIT = 2
AUTHENTICATED_USER_TRANSCRIPT_LIMIT = 10


class SimpleAuth:
    """
    Simple email-based authentication and rate limiting system.

    :ivar user_data_file: Path to store user data persistently
    :vartype user_data_file: Path
    """

    def __init__(self, user_data_file: str = "./user_data.json"):
        """
        Initialize the authentication system.

        :param user_data_file: Path to store user data
        :type user_data_file: str
        """
        self.user_data_file = Path(user_data_file)
        self._ensure_session_state()
        self._load_user_data()

    def _ensure_session_state(self) -> None:
        """
        Ensure all required session state variables are initialized.
        """
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False

        if "user_email" not in st.session_state:
            st.session_state.user_email = None

        if "transcript_count" not in st.session_state:
            st.session_state.transcript_count = 0

        if "last_reset" not in st.session_state:
            st.session_state.last_reset = datetime.now()

        if "session_id" not in st.session_state:
            # Generate a unique session ID
            st.session_state.session_id = hashlib.md5(
                f"{datetime.now().isoformat()}".encode()
            ).hexdigest()

    def _load_user_data(self) -> None:
        """
        Load user data from persistent storage.
        """
        if self.user_data_file.exists():
            try:
                with open(self.user_data_file) as f:
                    data = json.load(f)

                # If we have a session that matches, restore it
                if st.session_state.session_id in data.get("sessions", {}):
                    session = data["sessions"][st.session_state.session_id]
                    st.session_state.user_email = session.get("email")
                    st.session_state.transcript_count = session.get(
                        "transcript_count", 0
                    )
                    st.session_state.authenticated = session.get("authenticated", False)

                    # Check if we need to reset daily limit
                    last_reset = datetime.fromisoformat(
                        session.get("last_reset", datetime.now().isoformat())
                    )
                    if datetime.now() - last_reset > timedelta(days=1):
                        st.session_state.transcript_count = 0
                        st.session_state.last_reset = datetime.now()
                    else:
                        st.session_state.last_reset = last_reset

            except Exception as e:
                st.warning(f"Could not load user data: {e}")

    def _save_user_data(self) -> None:
        """
        Save user data to persistent storage.
        """
        try:
            # Load existing data
            if self.user_data_file.exists():
                with open(self.user_data_file) as f:
                    data = json.load(f)
            else:
                data = {"users": {}, "sessions": {}}

            # Update session data
            data["sessions"][st.session_state.session_id] = {
                "email": st.session_state.user_email,
                "transcript_count": st.session_state.transcript_count,
                "authenticated": st.session_state.authenticated,
                "last_reset": st.session_state.last_reset.isoformat(),
            }

            # Update user data
            if st.session_state.user_email:
                if st.session_state.user_email not in data["users"]:
                    data["users"][st.session_state.user_email] = {
                        "created": datetime.now().isoformat(),
                        "total_transcripts": 0,
                    }
                data["users"][st.session_state.user_email]["last_seen"] = (
                    datetime.now().isoformat()
                )
                data["users"][st.session_state.user_email]["total_transcripts"] = (
                    data["users"][st.session_state.user_email].get(
                        "total_transcripts", 0
                    )
                    + st.session_state.transcript_count
                )

            # Save data
            with open(self.user_data_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            st.warning(f"Could not save user data: {e}")

    def validate_email(self, email: str) -> bool:
        """
        Validate email format.

        :param email: Email address to validate
        :type email: str

        :return: True if email is valid
        :rtype: bool
        """
        return bool(EMAIL_REGEX.match(email))

    def login_form(self) -> bool:
        """
        Display login form and handle authentication.

        :return: True if user is authenticated
        :rtype: bool
        """
        if st.session_state.authenticated:
            return True

        with st.container():
            st.markdown("### Welcome to ekko! 🎙️")
            st.markdown(
                "Please enter your email to continue. You'll get **2 free transcript generations** as a demo user."
            )

            with st.form("login_form"):
                email = st.text_input(
                    "Email Address",
                    placeholder="your.email@example.com",
                    help="We'll use this to track your usage and provide support",
                )

                col1, col2 = st.columns([1, 3])
                with col1:
                    submit = st.form_submit_button(
                        "Continue", type="primary", use_container_width=True
                    )

                if submit:
                    if not email:
                        st.error("Please enter an email address")
                        return False

                    if not self.validate_email(email):
                        st.error("Please enter a valid email address")
                        return False

                    # Authenticate user
                    st.session_state.authenticated = True
                    st.session_state.user_email = email

                    # Check if returning user
                    if self.user_data_file.exists():
                        try:
                            with open(self.user_data_file) as f:
                                data = json.load(f)
                                if email in data.get("users", {}):
                                    st.success(f"Welcome back, {email}! 👋")
                                else:
                                    st.success(f"Welcome to ekko, {email}! 🎉")
                        except:
                            st.success(f"Welcome to ekko, {email}! 🎉")
                    else:
                        st.success(f"Welcome to ekko, {email}! 🎉")

                    self._save_user_data()
                    st.rerun()

        return False

    def check_rate_limit(self) -> tuple[bool, int]:
        """
        Check if user has exceeded rate limit.

        :return: Tuple of (within_limit, remaining_transcripts)
        :rtype: Tuple[bool, int]
        """
        # Reset daily counter if needed
        if datetime.now() - st.session_state.last_reset > timedelta(days=1):
            st.session_state.transcript_count = 0
            st.session_state.last_reset = datetime.now()
            self._save_user_data()

        limit = DEMO_USER_TRANSCRIPT_LIMIT
        remaining = limit - st.session_state.transcript_count

        return remaining > 0, remaining

    def increment_usage(self) -> None:
        """
        Increment transcript usage counter.
        """
        st.session_state.transcript_count += 1
        self._save_user_data()

    def clear_session_state(self) -> None:
        """
        Clear all session state except persistent identifiers.
        This ensures a clean state on sign out.
        """
        # Clear authentication-related state
        st.session_state.authenticated = False
        st.session_state.user_email = None
        st.session_state.transcript_count = 0

        # Clear app-specific state to prevent stale data
        keys_to_clear = ["selected_podcast", "feedback_round", "question_counter"]

        # Also clear any message history keys (for chatbot)
        keys_to_remove = []
        for key in st.session_state:
            if key in keys_to_clear or key.endswith("_messages"):
                keys_to_remove.append(key)

        for key in keys_to_remove:
            st.session_state.pop(key, None)

    def display_usage_info(self) -> None:
        """
        Display usage information in the sidebar.
        """
        if st.session_state.authenticated:
            st.sidebar.divider()
            st.sidebar.markdown("### 👤 Account")
            st.sidebar.markdown(f"**Email:** {st.session_state.user_email}")

            within_limit, remaining = self.check_rate_limit()

            if within_limit:
                st.sidebar.markdown(f"**Transcripts remaining today:** {remaining}")
                progress = (
                    st.session_state.transcript_count / DEMO_USER_TRANSCRIPT_LIMIT
                )
                st.sidebar.progress(progress)
            else:
                st.sidebar.error("Daily transcript limit reached!")
                st.sidebar.markdown(
                    "Come back tomorrow for more free transcripts, or contact us for unlimited access."
                )

            if st.sidebar.button("Sign Out", use_container_width=True):
                self.clear_session_state()
                st.rerun()

    def require_auth(self) -> bool:
        """
        Ensure user is authenticated before proceeding.

        :return: True if authenticated
        :rtype: bool
        """
        if not st.session_state.authenticated:
            return self.login_form()
        return True

    def can_transcribe(self) -> bool:
        """
        Check if user can perform a transcription.

        :return: True if user can transcribe
        :rtype: bool
        """
        if not st.session_state.authenticated:
            st.error("Please sign in to use transcription features.")
            return False

        within_limit, remaining = self.check_rate_limit()

        if not within_limit:
            st.error(
                "You've reached your daily limit of 2 free transcripts. "
                "Come back tomorrow or contact us for unlimited access!"
            )
            return False

        return True


# Singleton instance
auth = SimpleAuth()
