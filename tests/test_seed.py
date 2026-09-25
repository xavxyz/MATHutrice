from uuid import UUID

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from mathutrice import models
from mathutrice.referentiel import REFERENTIEL
from mathutrice.fonctions_python.seed import DESCRIPTIONS, seed, seed_dev_users


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


def test_reseeding_updates_notions_and_competences_to_the_referentiel(session):
    seed(session)
    trigo = session.exec(
        select(models.Notion).where(models.Notion.referentiel_key == "trigonometrie")
    ).one()
    fractions = session.exec(
        select(models.Notion).where(
            models.Notion.referentiel_key == "fractions_puissances_radicaux"
        )
    ).one()
    competence = session.exec(
        select(models.Competence).where(models.Competence.referentiel_code == "tr01")
    ).one()
    notion_id, competence_id = trigo.notion_id, competence.competence_id
    trigo.title = "Ancien titre"
    trigo.description = "Ancienne description"
    competence.title = "Ancien nom"
    competence.level = "expert"
    competence.notion_id = fractions.notion_id
    session.commit()

    seed(session)

    session.refresh(trigo)
    session.refresh(competence)
    assert trigo.notion_id == notion_id
    assert trigo.title == REFERENTIEL["trigonometrie"]["notion_nom"]
    assert trigo.description == DESCRIPTIONS["trigonometrie"]
    expected = REFERENTIEL["trigonometrie"]["competences"][0]
    assert competence.competence_id == competence_id
    assert competence.title == expected["nom"]
    assert competence.level == expected["niveau"]
    assert competence.notion_id == notion_id


def test_seeds_one_dev_user_per_role(session):
    seed_dev_users(session)

    users = session.exec(select(models.User)).all()

    assert sorted(u.role for u in users) == ["Admin", "Student", "Teacher"]
    assert all(u.email.endswith(("@epfedu.fr", "@epf.fr")) for u in users)
    assert all(isinstance(u.sso_id, UUID) for u in users)


def test_reseeding_dev_users_keeps_existing_users(session):
    seed_dev_users(session)
    student = session.exec(
        select(models.User).where(models.User.role == "Student")
    ).one()
    sso_id = student.sso_id
    student.role = "Teacher"
    session.commit()

    seed_dev_users(session)

    session.refresh(student)
    assert len(session.exec(select(models.User)).all()) == 3
    assert student.sso_id == sso_id
    assert student.role == "Teacher"
