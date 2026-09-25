"""
seed.py — Aligne les notions et les compétences de la BDD sur le référentiel,
et crée les utilisateurs de la connexion de développement

Lancé au démarrage de l'application (voir lifespan dans app.py), les
utilisateurs de développement seulement avec AUTH_MODE=dev.

Idempotent : une notion est retrouvée par sa referentiel_key, une compétence
par son referentiel_code. Les lignes absentes sont insérées, les autres mises
à jour (titre, description, niveau, notion) en gardant leur identifiant.
Un utilisateur de développement est retrouvé par son email, et seulement
inséré s'il manque : son rôle a pu changer depuis la connexion de développement.
"""

from datetime import datetime
from uuid import uuid4

from sqlmodel import Session, select

from mathutrice import models
from mathutrice.referentiel import REFERENTIEL

# Description de chaque notion, par referentiel_key : le reste vient du REFERENTIEL.
DESCRIPTIONS = {
    "trigonometrie": (
        "Étude des fonctions trigonométriques, des angles et du cercle trigonométrique."
    ),
    "fractions_puissances_radicaux": (
        "Manipulation des fractions, puissances et radicaux."
    ),
    "logarithme_exponentielle": (
        "Étude des fonctions logarithme et exponentielle."
    ),
    "manipulation_expressions_litterales": (
        "Isolement et manipulation de variables dans des expressions algébriques."
    ),
    "equations_inequations": (
        "Résolution d'équations et d'inéquations du premier et second degré."
    ),
    "polynomes_factorisation": (
        "Étude des polynômes, factorisation et identités remarquables."
    ),
    "analyse_dimensionnelle": (
        "Dimensions, unités et homogénéité des formules physiques."
    ),
}

# Un utilisateur par rôle, pour la connexion de développement (AUTH_MODE=dev).
DEV_USERS = [
    {"email": "eleve@epfedu.fr", "name": "Élève Démo", "role": "Student"},
    {"email": "enseignant@epf.fr", "name": "Enseignant Démo", "role": "Teacher"},
    {"email": "admin@epf.fr", "name": "Admin Démo", "role": "Admin"},
]


def seed(session: Session) -> None:
    """Aligne les notions et compétences de la BDD sur le REFERENTIEL."""
    for referentiel_key, notion_data in REFERENTIEL.items():
        notion = session.exec(
            select(models.Notion).where(
                models.Notion.referentiel_key == referentiel_key
            )
        ).first()
        if not notion:
            notion = models.Notion(
                notion_id=uuid4(), referentiel_key=referentiel_key
            )
        notion.title = notion_data["notion_nom"]
        notion.description = DESCRIPTIONS[referentiel_key]
        session.add(notion)

        for comp in notion_data["competences"]:
            competence = session.exec(
                select(models.Competence).where(
                    models.Competence.referentiel_code == comp["code"]
                )
            ).first()
            if not competence:
                competence = models.Competence(
                    competence_id=uuid4(), referentiel_code=comp["code"]
                )
            competence.title = comp["nom"]
            competence.level = comp["niveau"]
            competence.notion_id = notion.notion_id
            session.add(competence)
    session.commit()


def seed_dev_users(session: Session) -> None:
    """Insère les DEV_USERS absents de la BDD."""
    for dev_user in DEV_USERS:
        exists = session.exec(
            select(models.User).where(models.User.email == dev_user["email"])
        ).first()
        if not exists:
            session.add(
                models.User(sso_id=uuid4(), created_at=datetime.utcnow(), **dev_user)
            )
    session.commit()
