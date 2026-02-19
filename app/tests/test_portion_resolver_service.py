from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base
from app.services.portion_resolver_service import PortionResolverService


def test_portion_resolver_falls_back_by_category_and_caches() -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as db:
        grams = PortionResolverService.resolve_portion_grams(
            db=db,
            food_name="olive oil",
            unit="tablespoon",
        )

        assert grams > 10

        cached = PortionResolverService.resolve_portion_grams(
            db=db,
            food_name="olive oil",
            unit="tablespoon",
        )

        assert cached == grams
