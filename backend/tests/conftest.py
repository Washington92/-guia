"""Fixtures de autenticação para testes de negócio legados.

Somente a suíte de autenticação usa tokens reais; as demais usam um
administrador fictício para testar regras de negócio isoladamente.
"""
import pytest
from app.main import app
from app.routers.auth import get_current_user
from app.models import UserAccount

@pytest.fixture(autouse=True)
def authenticated_test_actor(request):
    if request.module.__name__.endswith("test_auth"):
        yield
        return
    original = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = lambda: UserAccount(
        id=1, username="test-admin", password_hash="not-a-real-password", role="admin", active=1
    )
    try:
        yield
    finally:
        if original is None:
            app.dependency_overrides.pop(get_current_user, None)
        else:
            app.dependency_overrides[get_current_user] = original
