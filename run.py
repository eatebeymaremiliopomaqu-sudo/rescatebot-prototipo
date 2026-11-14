"""Punto de entrada: python run.py  (inicializa la base la primera vez)."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from rescatebot import create_app, db  # noqa: E402

app = create_app()
if __name__ == "__main__":
    with app.app_context():
        if not os.path.exists(app.config["DATABASE"]):
            db.init_db()
            print("Base de datos creada con datos de demostración.")
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False)
