
import pytest
import torch
from prediction_logger.tensor_model import TensorModel
from unittest.mock import patch, MagicMock

def test_tensor_model_predict(monkeypatch):
    # Patch torch.load to return a dummy model
    class DummyModel(torch.nn.Module):
        def forward(self, x):
            return torch.ones_like(x)
    monkeypatch.setattr(torch, 'load', lambda *a, **kw: DummyModel())
    model = TensorModel('dummy.pt')
    model.load()
    features = [0.1, 0.2, 0.3]
    result = model.predict(features)
    assert isinstance(result, list)
