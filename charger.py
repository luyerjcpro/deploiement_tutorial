import pandas as pd
from sqlalchemy import select, func

from database import SessionLocal
from models import Penguin

CSV_PATH = "data/penguins.csv"

COLONNES = [
    "species",
    "island",
    "bill_length_mm",
    "bill_depth_mm",
    "flipper_length_mm",
    "body_mass_g",
    "sex",
]


def lire_csv(chemin: str) -> pd.DataFrame:
    df = pd.read_csv(chemin)
    manquantes = set(COLONNES) - set(df.columns)
    if manquantes:
        raise ValueError(f"Colonnes absentes du CSV : {sorted(manquantes)}")
    return df[COLONNES].astype(object).where(pd.notna(df[COLONNES]), None)


def charger() -> int:
    df = lire_csv(CSV_PATH)

    with SessionLocal() as session:
        deja_presents = session.scalar(select(func.count()).select_from(Penguin))
        if deja_presents:
            raise RuntimeError(
                f"{deja_presents} pingouins déjà en base — videz la table avant de recharger."
            )

        session.add_all([Penguin(**ligne) for ligne in df.to_dict(orient="records")])
        session.commit()

    return len(df)


if __name__ == "__main__":
    print(f"{charger()} pingouins insérés.")