"""
SkyBalance AVL — Flask application entry-point.
Serves the REST API *and* the static front-end files.
"""

import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from controllers.app_controller import AppController

# ------------------------------------------------------------------
# App factory
# ------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR)
CORS(app)

controller = AppController()

# ------------------------------------------------------------------
# Static front-end
# ------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(FRONTEND_DIR, path)

# ------------------------------------------------------------------
# Load / Export
# ------------------------------------------------------------------

@app.route("/api/load", methods=["POST"])
def load():
    data = request.get_json()
    mode = data.get("load_mode", "topology")
    return jsonify(controller.load_from_json(data, mode))

@app.route("/api/export", methods=["GET"])
def export_tree():
    return jsonify(controller.export_tree())

# ------------------------------------------------------------------
# Tree state
# ------------------------------------------------------------------

@app.route("/api/tree", methods=["GET"])
def get_tree():
    return jsonify(controller.get_tree_state())

# ------------------------------------------------------------------
# Flight CRUD
# ------------------------------------------------------------------

@app.route("/api/flight", methods=["POST"])
def create_flight():
    return jsonify(controller.create_flight(request.get_json()))

@app.route("/api/flight/<code>", methods=["PUT"])
def modify_flight(code):
    return jsonify(controller.modify_flight(code, request.get_json()))

@app.route("/api/flight/<code>", methods=["DELETE"])
def delete_flight(code):
    return jsonify(controller.delete_flight(code))

@app.route("/api/flight/<code>/cancel", methods=["POST"])
def cancel_flight(code):
    return jsonify(controller.cancel_flight(code))

# ------------------------------------------------------------------
# Undo
# ------------------------------------------------------------------

@app.route("/api/undo", methods=["POST"])
def undo():
    return jsonify(controller.undo())

@app.route("/api/undo/history", methods=["GET"])
def undo_history():
    return jsonify(controller.flight_manager.get_undo_history())

# ------------------------------------------------------------------
# Smart delete
# ------------------------------------------------------------------

@app.route("/api/smart-delete", methods=["POST"])
def smart_delete():
    return jsonify(controller.smart_delete())

# ------------------------------------------------------------------
# Versions
# ------------------------------------------------------------------

@app.route("/api/version", methods=["POST"])
def save_version():
    name = request.get_json().get("name", "")
    return jsonify(controller.save_version(name))

@app.route("/api/versions", methods=["GET"])
def list_versions():
    return jsonify(controller.list_versions())

@app.route("/api/version/<name>/restore", methods=["POST"])
def restore_version(name):
    return jsonify(controller.restore_version(name))

# ------------------------------------------------------------------
# Queue / Concurrency
# ------------------------------------------------------------------

@app.route("/api/queue/add", methods=["POST"])
def queue_add():
    return jsonify(controller.schedule_insertion(request.get_json()))

@app.route("/api/queue/process-next", methods=["POST"])
def queue_process_next():
    return jsonify(controller.process_next())

@app.route("/api/queue/process-all", methods=["POST"])
def queue_process_all():
    return jsonify(controller.process_all())

@app.route("/api/queue/status", methods=["GET"])
def queue_status():
    return jsonify(controller.get_queue_status())

# ------------------------------------------------------------------
# Stress mode
# ------------------------------------------------------------------

@app.route("/api/stress/toggle", methods=["POST"])
def toggle_stress():
    return jsonify(controller.toggle_stress())

@app.route("/api/stress/rebalance", methods=["POST"])
def global_rebalance():
    return jsonify(controller.global_rebalance())

# ------------------------------------------------------------------
# Audit
# ------------------------------------------------------------------

@app.route("/api/audit", methods=["POST"])
def audit():
    return jsonify(controller.audit())

# ------------------------------------------------------------------
# Metrics / Traversals
# ------------------------------------------------------------------

@app.route("/api/metrics", methods=["GET"])
def metrics():
    return jsonify(controller.get_metrics())

@app.route("/api/traversals", methods=["GET"])
def traversals():
    return jsonify(controller.get_traversals())

# ------------------------------------------------------------------
# Penalty
# ------------------------------------------------------------------

@app.route("/api/penalty/depth", methods=["PUT"])
def set_depth():
    depth = request.get_json().get("depth", 5)
    return jsonify(controller.set_critical_depth(int(depth)))

# ------------------------------------------------------------------
# Profitability
# ------------------------------------------------------------------

@app.route("/api/profitability", methods=["GET"])
def profitability():
    return jsonify(controller.get_profitability_ranking())

# ------------------------------------------------------------------
# Error handlers
# ------------------------------------------------------------------

@app.errorhandler(ValueError)
def handle_value_error(e):
    return jsonify({"error": str(e)}), 400

@app.errorhandler(Exception)
def handle_error(e):
    return jsonify({"error": str(e)}), 500

# ------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)
