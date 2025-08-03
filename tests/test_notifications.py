
import pytest
from unittest.mock import patch
from prediction_logger import notifications

@patch('prediction_logger.notifications.requests.post')
@patch('prediction_logger.notifications.load_config')
def test_notify_slack_success(mock_load_config, mock_post):
    mock_load_config.return_value = {'slack_webhook_url': 'http://fake', 'secondary_webhook_url': None, 'notify_email_to': None}
    mock_post.return_value.status_code = 200
    mock_post.return_value.raise_for_status = lambda: None
    # Should not raise
    notifications.notify("test message")