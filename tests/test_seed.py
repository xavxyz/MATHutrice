from uuid import UUID

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from mathutrice import models
from mathutrice.fonctions_python.referentiel import REFERENTIEL
from mathutrice.fonctions_python.seed import seed


@pytest.fixture
def session():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_seeds_one_notion_per_referentiel_key(session):
    seed(session)

    notions = session.exec(select(models.Notion)).all()

    assert {n.referentiel_key for n in notions} == set(REFERENTIEL)
    for n in notions:
        assert n.title == REFERENTIEL[n.referentiel_key]["notion_nom"]
    assert all(isinstance(n.notion_id, UUID) for n in notions)


def test_seeds_every_competence_under_its_notion(session):
    seed(session)

    for key, notion_data in REFERENTIEL.items():
        notion = session.exec(
            select(models.Notion).where(models.Notion.referentiel_key == key)
        ).one()
        seeded = {c.referentiel_code: c for c in notion.competences}

        assert set(seeded) == {c["code"] for c in notion_data["competences"]}
        for comp in notion_data["competences"]:
            assert seeded[comp["code"]].title == comp["nom"]
            assert seeded[comp["code"]].level == comp["niveau"]


def test_seeding_twice_changes_nothing(session):
    seed(session)
    notion_ids = set(session.exec(select(models.Notion.notion_id)).all())
    competence_ids = set(session.exec(select(models.Competence.competence_id)).all())

    seed(session)

    assert set(session.exec(select(models.Notion.notion_id)).all()) == notion_ids
    assert (
        set(session.exec(select(models.Competence.competence_id)).all())
        == competence_ids
    )
