
import pytest
from unittest.mock import patch
from prediction_logger.translator import Translator

@patch('prediction_logger.translator.openai.ChatCompletion.create')
def test_summarize_tensor_output(mock_create):
    mock_create.return_value.choices = [type('obj', (object,), {"message": {"content": "summary text"}})()]
    t = Translator(api_key='sk-test')
    result = t.summarize_tensor_output([1,2,3], context="test context")
    assert "summary" in result
