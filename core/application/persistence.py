"""Application-level persistence orchestration for GameSession."""

from core.persistence import FilePersistenceAdapter, RestoreContract

from .session import GameSession


class SessionPersistenceService:
    """Load a validated persistence document into an existing GameSession."""

    @staticmethod
    def load_into(session: GameSession, path) -> GameSession:
        if not isinstance(session, GameSession):
            raise TypeError("session must be GameSession.")

        document = FilePersistenceAdapter.load(path)
        state = document.to_state()
        plan = RestoreContract.prepare(state)
        session.activate_restore(plan)
        return session
