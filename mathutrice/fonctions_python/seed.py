"""
seed.py — Insère les notions et les compétences du référentiel en BDD

Usage :
  python -m mathutrice.fonctions_python.seed

Idempotent : une notion est retrouvée par sa referentiel_key, une compétence
par son referentiel_code ; seules les lignes absentes sont insérées.
"""

from uuid import uuid4

from sqlmodel import Session, SQLModel, select

from mathutrice import models
from mathutrice.fonctions_python.referentiel import REFERENTIEL

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


def seed(session: Session) -> None:
    """Insère les notions et compétences du REFERENTIEL absentes de la BDD."""
    for referentiel_key, notion_data in REFERENTIEL.items():
        notion = session.exec(
            select(models.Notion).where(
                models.Notion.referentiel_key == referentiel_key
            )
        ).first()
        if not notion:
            notion = models.Notion(
                notion_id=uuid4(),
                referentiel_key=referentiel_key,
                title=notion_data["notion_nom"],
                description=DESCRIPTIONS[referentiel_key],
            )
            session.add(notion)

        for comp in notion_data["competences"]:
            existing = session.exec(
                select(models.Competence).where(
                    models.Competence.referentiel_code == comp["code"]
                )
            ).first()
            if not existing:
                session.add(
                    models.Competence(
                        competence_id=uuid4(),
                        referentiel_code=comp["code"],
                        title=comp["nom"],
                        level=comp["niveau"],
                        notion_id=notion.notion_id,
                    )
                )
    session.commit()


if __name__ == "__main__":
    from mathutrice.database import engine

    # Crée toutes les tables
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        seed(session)
    print("Notions et compétences insérées.")
