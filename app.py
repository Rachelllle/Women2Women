"""Women2Women — application entry point.

Thin assembly layer: create the Flask app, wire login + CORS, register every
feature blueprint, init the database, and serve the single-page front-end.
All real logic lives in the feature packages (auth, profile, recommandation,
prediction, chatbot, alerts, database).
"""
import os
from flask import Flask, send_from_directory
from flask_cors import CORS

from database.schema import init_db
from database.admin_panel import admin_bp
from auth import login_manager
from auth.routes import auth_bp
from profiles.routes import profile_bp
from recommandation.routes import rec_bp
from prediction.routes import prediction_bp
from history.routes import history_bp
from chat.routes import chat_bp
from alerting.routes import alerting_bp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.secret_key = "change-me-before-deploying"
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_HTTPONLY"] = True
CORS(app, supports_credentials=True)

login_manager.init_app(app)

# Feature blueprints
app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(rec_bp)
app.register_blueprint(prediction_bp)
app.register_blueprint(history_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(alerting_bp)

init_db()


@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "Women2Women.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000, use_reloader=False)
