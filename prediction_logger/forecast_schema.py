from pydantic import BaseModel, Field, ValidationError
from typing import Optional

class Forecast(BaseModel):
    scenario: str
    resistance: float
    support: Optional[float]
    sigma_plus: Optional[float]
    sigma_minus: Optional[float]

    class Config:
        extra = 'forbid'
