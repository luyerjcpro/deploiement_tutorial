from contextlib import asynccontextmanager 
# permet de créer un gestionnaire de contexte asynchrone. 
# Avec FastAPI, on l'utilise souvent pour définir ce qui doit se passer au démarrage 
# et à l'arrêt de l'application, par exemple charger un modèle ML une seule fois au démarrage.
from typing import Annotated

import joblib
import pandas as pd
from fastapi import Depends, FastAPI, HTTPException
# 1) Depends sert au système d'injection de dépendances de FastAPI. 
#    Ici, il servira à récupérer automatiquement une session SQLAlchemy
# 2) HTTPException permet de retourner proprement une erreur HTTP
from sqlalchemy.orm import Session
# Session représente une session SQLAlchemy.
# C'est l'objet qui te permet d'effectuer des opérations avec PostgreSQL
# Interface de travail SQLAlchemy pour dialoguer avec la base à travers l'engine.

from database import engine, get_session
# 1) engine contient la configuration permettant à SQLAlchemy de communiquer avec PostgreSQL
# 2) get_session crée puis ferme proprement une session pour les requêtes FastAPI
from models import Base, Penguin, Prediction
# import des modèles SQLAlchemy
# 1) Base la classe de base utilisée pour déclarer les tables
# 2) Penguin est une table contenant les données des manchots
# 3) Prediction est une table contenant les prédictions réalisées par le modèle
from schemas import PenguinIn, PenguinOut, PredictionOut
# Ici, ce ne sont pas les tables SQLAlchemy mais les schémas Pydantic
# SQLAlchemy
#     ↓
# structure des données dans PostgreSQL

# Pydantic
#     ↓
# structure des données entrantes/sortantes de l'API


MODELE_PATH = "modele.joblib"
ressources: dict = {}
# Création un dictionnaire vide.
# L'idée est de conserver en mémoire les ressources partagées par l'application, 
# notamment le modèle

SessionDep = Annotated[Session, Depends(get_session)]
# Session indique le type Python de l'objet.
# Depends dit à FastAPI : "Pour obtenir cet objet, appelle get_session()"
# Et Annotated[Session,Depends(get_session)] permet d'associer ces deux informations.
#### ROUTE ####
## On peut ensuite écrire une route comme :
# @app.get("/penguins")
# def get_penguins(session: SessionDep):
#     ...
#### FIN ROUTE ####
## FastAPI comprend :
# session
#   │
#   ├── doit être de type Session
#   │
#   └── doit être obtenue avec get_session()
# C'est donc essentiellement un alias de type.
#
## au lieu d'écrire partout :
# def fonction(
#     session: Annotated[Session, Depends(get_session)]
# ):
## on définit une seule fois :
# SessionDep = Annotated[Session, Depends(get_session)]
# puis :
# def fonction(session: SessionDep):

# Vue d'ensemble :
#                    FastAPI
#                       │
#           ┌───────────┴───────────┐
#           │                       │
#           ▼                       ▼
#     modèle ML                 PostgreSQL
#   modele.joblib                   │
#           │                       │
#        joblib                  SQLAlchemy
#           │                       │
#           ▼                       ▼
#  ressources["modele"]          Session
#                                   │
#                            get_session()

# Et lors d'une prédiction, le fonctionnement est :
                # Requête HTTP
                #     │
                #     ▼
                # PenguinIn
                # (Pydantic)
                #     │
                #     ▼
                # DataFrame pandas
                #     │
                #     ▼
                # modèle.joblib
                #     │
                #     ▼
                # prédiction
                #     │
                #     ├──→ Prediction SQLAlchemy → PostgreSQL
                #     │
                #     └──→ PredictionOut → réponse HTTP

# Le point à bien retenir pour le projet actuel est : 
# engine gère l'accès à PostgreSQL 
# Session permet de travailler avec la base 
# get_session() fournit cette session à FastAPI 
# SessionDep est simplement une écriture plus propre pour demander cette dépendance dans tes routes.


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    ressources["modele"] = joblib.load(MODELE_PATH)
    # L'intérêt est important : éviter de charger le fichier modele.joblib à chaque prédiction.
    yield
    ressources.clear()
## Au lieu de faire :
# requête
# → charger modèle
# → prédire

## On fait :
# démarrage FastAPI
#         ↓
# charger modèle une fois
#         ↓
#    ressources["modele"]

# requête 1 ─┐
# requête 2 ─┼─→ même modèle déjà en mémoire
# requête 3 ─┘


app = FastAPI(
    title="Penguins API",
    summary="En entrant les caractéristiques d'un pingouin, le modèle fournit une prédiction lié à son sexe.", 
    lifespan=lifespan)

# un endpoint = méthode HTTP + chemin URL
@app.get("/penguins/{penguin_id}", response_model=PenguinOut) # endpoint de l'API
def read_penguin(penguin_id: int, session: SessionDep):
    penguin = session.get(Penguin, penguin_id)
    if penguin is None:
        raise HTTPException(status_code=404, detail="Penguin introuvable")
    return penguin

    # Endpoint
    # ↓
    # POST /predict
    # ↓
    # fonction predire()
    # ↓
    # traitement ML + base de données
    # ↓
    # réponse HTTP


@app.post("/predict", response_model=PredictionOut, status_code=201)
# le décorateur ne lance pas immédiatement predire(). 
# Il enregistre la fonction comme route FastAPI pour les requêtes HTTP POST envoyées vers /predict
def predire(entree: PenguinIn, session: SessionDep):
    modele = ressources["modele"]
    df = pd.DataFrame([entree.model_dump()])

    classe = modele.predict(df)[0]
    proba = float(modele.predict_proba(df).max())

    prediction = Prediction(
        **entree.model_dump(), predicted_sex=classe, probability=proba
    )
    #  À ce stade, prediction est seulement un objet Python. Il n'est pas encore enregistré dans PostgreSQL.
    # Les trois méthodes correspondent à trois étapes différentes : 
    # 1) préparer l'insertion 
    # 2) l'enregistrer réellement 
    # 3) puis resynchroniser l'objet Python avec ce qui existe dans PostgreSQL.
    session.add(prediction)
    # Cela dit à SQLAlchemy :« Je veux que cet objet soit ajouté à la base lors de la prochaine synchronisation/transaction. »
    # Objet Python
    # Prediction(...)
    #     │
    #     │ session.add()
    #     ▼
    # Session SQLAlchemy
    # (objet en attente d'insertion)
    session.commit()
    # commit() valide la transaction : « Enregistre définitivement les modifications faites dans cette transaction. »
    # SQLAlchemy va notamment provoquer l'équivalent logique d'un :
        # INSERT INTO prediction (...)
        # VALUES (...);
    # puis effectuer :
        # COMMIT;
    session.refresh(prediction)
    # demande à SQLAlchemy de relire la ligne correspondante dans la base 
    # et de mettre à jour l'objet Python prediction

    return prediction

    # Prediction(...)
    #     │
    #     │ objet Python uniquement
    #     ▼
    # session.add(prediction)
    #     │
    #     │ objet suivi par SQLAlchemy
    #     ▼
    # session.commit()
    #     │
    #     │ INSERT + COMMIT
    #     ▼
    # PostgreSQL
    #     │
    #     │ lecture de la ligne
    #     ▼
    # session.refresh(prediction)
    #     │
    #     ▼
    # objet Python synchronisé
    #     │
    #     ▼
    # return prediction

# 1) add = placer l'objet sous gestion de SQLAlchemy
# 2) commit = valider les changements en base
# 3) refresh = relire l'état final depuis la base.