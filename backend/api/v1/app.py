#!/usr/bin/env python3
"""Flask application
"""
from flask import Flask, make_response, jsonify
from flask_session import Session

from config import config
from utils.logger import logger
from api.v1.views import api_bp, dashboard_bp


def create_app(cfg=None):
    """Create Flask application with configuration
    """
    app = Flask(__name__)
    app.config.from_object(cfg)

    Session(app)

    config.init_app(app)

    middlewares = []

    # Register blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(dashboard_bp)

    # Health check endpoint
    @app.route('/health', methods=['GET'], strict_slashes=False)
    def health():
        return make_response(jsonify({
            'status': 'ok',
        }), 200)

    @app.errorhandler(404)
    def handle_not_found(e):
        return make_response(jsonify({
            'error': 'Not found',
            'message': str(e),
        }))

    @app.errorhandler(400)
    def handle_bad_request(e):
        return make_response(jsonify({
            'error': 'Bad request',
            'message': str(e),
        }))

    @app.errorhandler(401)
    def handle_unauthorized(e):
        return make_response(jsonify({
            'error': 'Unauthorized',
            'message': str(e),
        }))

    @app.errorhandler(403)
    def handle_forbidden(e):
        return make_response(jsonify({
            'error': 'Forbidden',
            'message': str(e),
        }))

    @app.errorhandler(405)
    def handle_unimplemented(e):
        return make_response(jsonify({
            'error': 'Unimplemented',
            'message': str(e),
        }))

    @app.errorhandler(500)
    def handle_server_error(e):
        return make_response(jsonify({
            'error': 'Server error',
            'message': str(e),
        }))

    @app.errorhandler(429)
    def handle_rate_limit(e):
        return make_response(jsonify({
            'error': 'Too many requests',
            'message': str(e),
        }))

    @app.errorhandler(415)
    def handle_unsupported_media_type(e):
        return make_response(jsonify({
            'error': 'Unsupported media type',
            'message': str(e),
        }))

    return app


if __name__ == '__main__':
    server = create_app(config)

    logger.info("Starting server on port {}".format(config.SERVER_PORT))

    server.run(host=config.SERVER_HOST, port=config.SERVER_PORT,
               threaded=True, debug=config.SERVER_DEBUG)