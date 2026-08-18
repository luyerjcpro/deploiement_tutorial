MESURES = {
    "species": "Adelie",
    "island": "Torgersen",
    "bill_length_mm": 39.1,
    "bill_depth_mm": 18.7,
    "flipper_length_mm": 181.0,
    "body_mass_g": 3750.0,
}


def test_lire_pingouin_existant(client, pingouin):
    reponse = client.get(f"/penguins/{pingouin.id_penguin}")
    assert reponse.status_code == 200
    assert reponse.json()["species"] == "Adelie"


def test_lire_pingouin_absent(client):
    assert client.get("/penguins/9999").status_code == 404


def test_predire_renvoie_201(client):
    reponse = client.post("/predict", json=MESURES)
    assert reponse.status_code == 201
    corps = reponse.json()
    assert corps["predicted_sex"] in {"male", "female"}
    assert 0 <= corps["probability"] <= 1


def test_predire_espece_inconnue(client):
    assert client.post("/predict", json={**MESURES, "species": "Pinguin"}).status_code == 422


def test_predire_journalise(client, session):
    from models import Prediction

    client.post("/predict", json=MESURES)
    lignes = session.query(Prediction).all()
    assert len(lignes) == 1
    assert lignes[0].bill_length_mm == 39.1