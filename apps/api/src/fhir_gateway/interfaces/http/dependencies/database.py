from collections.abc import Iterator

from fastapi import Request
from sqlalchemy.orm import Session, sessionmaker


def get_session_factory(request: Request) -> sessionmaker[Session]:
    return request.app.state.session_factory


def get_database_session(
    request: Request,
) -> Iterator[Session]:
    session_factory = get_session_factory(request)

    with session_factory() as session:
        yield session
