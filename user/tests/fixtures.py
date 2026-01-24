from unittest.mock import patch
import pytest


# MOCKED TASKS
@pytest.fixture
def mock_verification_email_task():
    with patch('user.tasks.send_verification_mail_task.delay') as mocked_task:
        yield mocked_task

@pytest.fixture
def mock_password_reset_email_task():
    with patch('user.tasks.send_password_reset_mail_task.delay') as mocked_task:
        yield mocked_task