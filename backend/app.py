from flask import Flask

from src.api.faqs import faq_bp
from src.api.images import images_bp
from src.api.rainfall import rainfall_bp
from src.db import init_db
from src.jobs import bootstrap_images
from src.seed import seed_faqs


def create_app() -> Flask:
    app = Flask(__name__)

    init_db()
    seed_faqs()
    bootstrap_images()
    app.register_blueprint(images_bp, url_prefix="/api/images")
    app.register_blueprint(rainfall_bp, url_prefix="/api/rainfall")
    app.register_blueprint(faq_bp, url_prefix="/api/faqs")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
        return response

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
