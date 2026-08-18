from contextlib import asynccontextmanager
from typing import Annotated

import joblib
import pandas as pd
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from database import engine, get_session
from models import Base, Penguin, Prediction
from schemas import PenguinIn, PenguinOut, PredictionOut

MODELE_PATH = "modele.joblib"
ressources: dict = {}

SessionDep = Annotated[Session, Depends(get_session)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    ressources["modele"] = joblib.load(MODELE_PATH)
    yield
    ressources.clear()


app = FastAPI(title="Penguins API", lifespan=lifespan)


@app.get("/penguins/{penguin_id}", response_model=PenguinOut)
def read_penguin(penguin_id: int, session: SessionDep):
    penguin = session.get(Penguin, penguin_id)
    if penguin is None:
        raise HTTPException(status_code=404, detail="Penguin introuvable")
    return penguin


@app.post("/predict", response_model=PredictionOut, status_code=201)
def predire(entree: PenguinIn, session: SessionDep):
    modele = ressources["modele"]
    df = pd.DataFrame([entree.model_dump()])

    classe = modele.predict(df)[0]
    proba = float(modele.predict_proba(df).max())

    prediction = Prediction(
        **entree.model_dump(), predicted_sex=classe, probability=proba
    )
    session.add(prediction)
    session.commit()
    session.refresh(prediction)

    return prediction