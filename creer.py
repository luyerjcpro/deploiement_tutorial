from database import engine
from models import Base, Penguin, Prediction

Base.metadata.create_all(engine)
# L'URL se lit de droite à gauche : 
# - localhost:5432 c'est le port que ton docker run a ouvert, 
# - postgres:motdepasse c'est l'utilisateur et le mot de passe que tu as fixés, 
# - postgresql+psycopg indique le dialecte SQL et le pilote à employer.

# echo=True affiche tout le SQL envoyé.
# tu vas voir le CREATE TABLE que SQLAlchemy a écrit à ta place, à partir de ta classe.

# import Penguin peut sembler inutile. 
# Il l'est pourtant : sans lui, la classe n'est pas chargée, Base ne la connaît pas, 
# et create_all ne crée rien.