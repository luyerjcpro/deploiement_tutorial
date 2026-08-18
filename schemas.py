from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

class PenguinOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_penguin: int
    species: str
    island: str
    bill_length_mm: float | None = None
    bill_depth_mm: float | None = None
    flipper_length_mm: float | None = None
    body_mass_g: float | None = None
    sex: str | None = None


class PenguinIn(BaseModel):
    species: Literal["Adelie", "Chinstrap", "Gentoo"]
    island: Literal["Biscoe", "Dream", "Torgersen"]
    bill_length_mm: float = Field(gt=0, lt=100)
    bill_depth_mm: float = Field(gt=0, lt=50)
    flipper_length_mm: float = Field(gt=0, lt=300)
    body_mass_g: float = Field(gt=0, lt=10000)


class PredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_prediction: int
    predicted_sex: str
    probability: float