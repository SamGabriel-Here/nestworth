"""HTTP API plus the static frontend."""

from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src import predictor
from src.pipeline.generate import CITIES, LOCATIONS, TYPES


class Property(BaseModel):
    area: int = Field(ge=300, le=9000)
    bedrooms: int = Field(ge=1, le=5)
    bathrooms: int = Field(ge=1, le=4)
    stories: int = Field(ge=1, le=4)
    city: Literal[tuple(CITIES)]
    location: Literal[tuple(LOCATIONS)]
    property_type: Literal[tuple(TYPES)]
    house_age: int = Field(ge=0, le=60)
    parking: int = Field(ge=0, le=3)
    main_road: Literal["yes", "no"]
    furnishing_status: Literal["furnished", "semi-furnished", "unfurnished"]


app = FastAPI(title="NestWorth")


@app.post("/api/predict")
def predict(prop: Property) -> dict:
    return predictor.value(prop.model_dump())


app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True))
