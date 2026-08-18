import pandas as pd
import pytest
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.pipeline import Pipeline

from charger import lire_csv
from train import construire_pipeline


def test_pipeline_a_deux_etapes():
    pipeline = construire_pipeline()
    assert isinstance(pipeline, Pipeline)
    assert [nom for nom, _ in pipeline.steps] == ["preparation", "clf"]


def test_pipeline_estimateur_final():
    assert isinstance(construire_pipeline().named_steps["clf"], GradientBoostingClassifier)


def test_lire_csv_garde_les_colonnes_utiles(tmp_path):
    fichier = tmp_path / "mini.csv"
    fichier.write_text(
        "species,island,bill_length_mm,bill_depth_mm,"
        "flipper_length_mm,body_mass_g,sex,year\n"
        "Adelie,Torgersen,39.1,18.7,181,3750,male,2007\n"
    )

    df = lire_csv(str(fichier))

    assert list(df.columns) == [
        "species", "island", "bill_length_mm", "bill_depth_mm",
        "flipper_length_mm", "body_mass_g", "sex",
    ]
    assert len(df) == 1


def test_lire_csv_convertit_les_manquants_en_none(tmp_path):
    fichier = tmp_path / "trous.csv"
    fichier.write_text(
        "species,island,bill_length_mm,bill_depth_mm,"
        "flipper_length_mm,body_mass_g,sex\n"
        "Gentoo,Biscoe,,,,,\n"
    )

    valeurs = lire_csv(str(fichier)).iloc[0]

    assert valeurs["bill_length_mm"] is None
    assert valeurs["sex"] is None


def test_lire_csv_refuse_un_csv_incomplet(tmp_path):
    fichier = tmp_path / "casse.csv"
    fichier.write_text("species,island\nAdelie,Torgersen\n")

    with pytest.raises(ValueError, match="Colonnes absentes"):
        lire_csv(str(fichier))