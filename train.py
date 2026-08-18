import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from database import engine

MODELE_PATH = "modele.joblib"

CATEGORIELLES = ["species", "island"]
NUMERIQUES = ["bill_length_mm", "bill_depth_mm", "flipper_length_mm", "body_mass_g"]
CIBLE = "sex"


def lire_donnees() -> pd.DataFrame:
    requete = """
        SELECT species, island, bill_length_mm, bill_depth_mm,
               flipper_length_mm, body_mass_g, sex
        FROM penguins
        WHERE sex IS NOT NULL
          AND bill_length_mm IS NOT NULL
          AND bill_depth_mm IS NOT NULL
          AND flipper_length_mm IS NOT NULL
          AND body_mass_g IS NOT NULL
    """
    df = pd.read_sql(requete, engine)
    if df.empty:
        raise RuntimeError("Aucune ligne exploitable — la table penguins est-elle chargée ?")
    return df


def construire_pipeline() -> Pipeline:
    preparation = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(drop="first", handle_unknown="ignore",
                                  sparse_output=False), CATEGORIELLES),
            ("num", StandardScaler(), NUMERIQUES),
        ]
    )
    return Pipeline(
        steps=[
            ("preparation", preparation),
            ("clf", GradientBoostingClassifier(random_state=42)),
        ]
    )


def entrainer() -> Pipeline:
    df = lire_donnees()
    X = df[CATEGORIELLES + NUMERIQUES]
    y = df[CIBLE]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    pipeline = construire_pipeline()
    pipeline.fit(X_train, y_train)

    print(classification_report(y_test, pipeline.predict(X_test)))
    return pipeline


if __name__ == "__main__":
    modele = entrainer()
    joblib.dump(modele, MODELE_PATH)
    print(f"Modèle enregistré dans {MODELE_PATH}")