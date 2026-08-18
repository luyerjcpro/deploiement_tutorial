from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import CheckConstraint, ForeignKey

# Base est un registre. Toute classe qui en hérite s'y inscrit automatiquement,
# c'est ainsi que SQLAlchemy saura, tout à l'heure, quelles tables créer.
class Base(DeclarativeBase):
    pass

class Penguin(Base):
    __tablename__ = "penguins"

    id_penguin: Mapped[int] = mapped_column(primary_key=True)
    species: Mapped[str]
    island: Mapped[str]
    bill_length_mm: Mapped[float | None]
    bill_depth_mm: Mapped[float | None]
    flipper_length_mm: Mapped[float | None]
    body_mass_g: Mapped[float | None]
    sex: Mapped[str | None]

# __tablename__ est le nom côté PostgreSQL. 
# La classe s'appelle Penguin, la table penguins. Les deux noms sont indépendants.

# Mapped[int] donne le type Python, mapped_column(...) les options SQL. 
# Chaque ligne dit donc deux choses à la fois : 
# « en Python c'est un entier » et « en base c'est un INTEGER NOT NULL PRIMARY KEY ».

# Une remarque sur nullable : la clé primaire est NOT NULL d'office, tu n'as rien à préciser. 
# Pour les autres colonnes, Mapped[float] sans | None implique déjà NOT NULL

# Le ForeignKey prend une chaîne : "penguins.id_penguin". 
# Nom de la table (pas de la classe) et nom de la colonne. 
# C'est cette ligne qui crée le lien relationnel, désormais PostgreSQL refusera toute prédiction 
# dont l'id_penguin n'existe pas dans penguins.

# Le CheckConstraint contient du SQL brut, pas du Python. 
# __table_args__ est un tuple — la virgule finale est obligatoire, 
# sinon Python ne voit pas un tuple et SQLAlchemy lève une erreur peu claire.
class Prediction(Base):
    __tablename__ = "predictions"

    id_prediction: Mapped[int] = mapped_column(primary_key=True)
    id_penguin: Mapped[int | None] = mapped_column(
        ForeignKey("penguins.id_penguin", ondelete="RESTRICT")
    )

    species: Mapped[str]
    island: Mapped[str]
    bill_length_mm: Mapped[float]
    bill_depth_mm: Mapped[float]
    flipper_length_mm: Mapped[float]
    body_mass_g: Mapped[float]

    predicted_sex: Mapped[str]
    probability: Mapped[float]

    __table_args__ = (
        CheckConstraint("probability >= 0 AND probability <= 1", name="ck_proba"),
    )