import os
import sys
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from rescatebot import create_app, db  # noqa: E402


@pytest.fixture
def app(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db"), "SECRET_KEY": "test"})
    with app.app_context():
        db.init_db()
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def ingresar(client, correo="operador@rescatebot.bo", clave="Operador123"):
    return client.post("/", data={"correo": correo, "clave": clave}, follow_redirects=True)
