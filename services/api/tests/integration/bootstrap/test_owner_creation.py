from sqlalchemy import select
from sqlalchemy.orm import Session

from myhub.infrastructure.db.models import FamilyModel, MembershipModel, UserModel
from tests.conftest import TEST_TOKEN


def test_bootstrap_creates_exactly_one_initial_owner(client, engine) -> None:
    response = client.post(
        "/api/v1/bootstrap",
        headers={"X-MyHub-Bootstrap-Token": TEST_TOKEN},
        json={"family_name": "Family Test", "canonical_url": "https://family.example.com", "owner_display_name": "Initial Owner"},
    )
    assert response.status_code == 201

    with Session(engine) as session:
        families = session.scalars(select(FamilyModel)).all()
        users = session.scalars(select(UserModel)).all()
        owners = session.scalars(select(MembershipModel).where(MembershipModel.role == "Owner")).all()

    assert len(families) == 1
    assert len(users) == 1
    assert len(owners) == 1
    assert owners[0].tenant_id == families[0].id
    assert owners[0].user_id == users[0].id
