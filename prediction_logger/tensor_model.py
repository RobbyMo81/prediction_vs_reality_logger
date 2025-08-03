import torch
import logging
from pathlib import Path

class TensorModel:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None

    def load(self):
        if not Path(self.model_path).exists():
            logging.error(f"Tensor model file not found: {self.model_path}")
            raise FileNotFoundError(f"Tensor model file not found: {self.model_path}")
        self.model = torch.load(self.model_path, map_location='cpu')
        self.model.eval()
        logging.info(f"Loaded tensor model from {self.model_path}")

    def predict(self, features):
        if self.model is None:
            raise RuntimeError("Tensor model not loaded. Call load() first.")
        with torch.no_grad():
            input_tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0)
            output = self.model(input_tensor)
            return output.squeeze().tolist()
