"""
app.py  –  Flask Backend for Cache Memory Simulator
COA B.Tech Project
"""
import sys
import os
import json
import subprocess
import time

# Add site-packages path for Flask
SITE_PKG = os.path.join(os.path.dirname(os.path.dirname(__file__)), "site-packages")
if os.path.isdir(SITE_PKG) and SITE_PKG not in sys.path:
    sys.path.insert(0, SITE_PKG)

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Import our Python simulation engine
sys.path.insert(0, os.path.dirname(__file__))
from cache_engine import run_simulation, validate_config, CacheConfig, breakdown_address, is_power_of_two

app = Flask(__name__, static_folder=None)
CORS(app)

# ---- Path to compiled C++ binary (optional) -----------------
CPP_DIR    = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cpp")
CPP_BINARY = os.path.join(CPP_DIR, "cache_sim.exe")

# ---- Frontend folder ----------------------------------------
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")


# =============================================================
# Health Check
# =============================================================
@app.route("/api/health", methods=["GET"])
def health():
    cpp_available = os.path.isfile(CPP_BINARY)
    return jsonify({
        "status": "ok",
        "engine": "cpp" if cpp_available else "python",
        "cpp_binary": CPP_BINARY,
        "cpp_available": cpp_available,
        "python_engine": True,
        "timestamp": time.time(),
    })


# =============================================================
# Supported Algorithms
# =============================================================
@app.route("/api/algorithms", methods=["GET"])
def algorithms():
    return jsonify({
        "mapping_techniques": [
            {"id": "direct",           "name": "Direct Mapping"},
            {"id": "fully_associative","name": "Fully Associative Mapping"},
            {"id": "set_associative",  "name": "Set Associative Mapping"},
        ],
        "replacement_policies": [
            {"id": "lru",  "name": "LRU (Least Recently Used)"},
            {"id": "fifo", "name": "FIFO (First In First Out)"},
        ],
    })


# =============================================================
# Sample Configurations
# =============================================================
@app.route("/api/sample", methods=["GET"])
def sample():
    samples = [
        {
            "id": 1,
            "name": "Demo 1 – Direct Mapping",
            "description": "Classic direct mapping with 256B main memory, 64B cache, 4B blocks.",
            "config": {
                "main_memory_size": 256,
                "cache_size": 64,
                "block_size": 4,
                "mapping": "direct",
                "associativity": 1,
                "replacement": "lru",
            },
            "addresses": [0, 4, 0, 64, 4, 64],
            "expected": {
                "total_accesses": 6,
                "hits": 3,
                "misses": 3,
                "hit_percentage": 50.0,
                "miss_percentage": 50.0,
            }
        },
        {
            "id": 2,
            "name": "Demo 2 – Fully Associative (FIFO)",
            "description": "Small 3-line cache with FIFO replacement.",
            "config": {
                "main_memory_size": 256,
                "cache_size": 16,
                "block_size": 4,
                "mapping": "fully_associative",
                "associativity": 4,
                "replacement": "fifo",
            },
            "addresses": [0, 4, 8, 12, 0, 16, 4],
        },
        {
            "id": 3,
            "name": "Demo 3 – Fully Associative (LRU)",
            "description": "Same config as Demo 2 but with LRU to show different eviction.",
            "config": {
                "main_memory_size": 256,
                "cache_size": 16,
                "block_size": 4,
                "mapping": "fully_associative",
                "associativity": 4,
                "replacement": "lru",
            },
            "addresses": [0, 4, 8, 12, 0, 16, 4],
        },
        {
            "id": 4,
            "name": "Demo 4 – 2-Way Set Associative (LRU)",
            "description": "2-way set associative with LRU replacement.",
            "config": {
                "main_memory_size": 256,
                "cache_size": 32,
                "block_size": 4,
                "mapping": "set_associative",
                "associativity": 2,
                "replacement": "lru",
            },
            "addresses": [0, 4, 8, 0, 12, 4],
        },
        {
            "id": 5,
            "name": "Demo 5 – LRU vs FIFO Difference",
            "description": "Sequence to show that FIFO evicts oldest insertion, LRU evicts least recently used.",
            "config": {
                "main_memory_size": 256,
                "cache_size": 16,
                "block_size": 4,
                "mapping": "fully_associative",
                "associativity": 4,
                "replacement": "lru",
            },
            "addresses": [0, 4, 8, 12, 0, 4, 8, 16],
        },
    ]
    return jsonify({"samples": samples})


# =============================================================
# Simulate
# =============================================================
@app.route("/api/simulate", methods=["POST"])
def simulate():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON body."}), 400

    # --- Extract config ---
    config = data.get("config")
    if not config:
        return jsonify({"error": "Missing 'config' field."}), 400

    # --- Extract addresses ---
    addresses_raw = data.get("addresses")
    if addresses_raw is None:
        return jsonify({"error": "Missing 'addresses' field."}), 400
    if not isinstance(addresses_raw, list):
        return jsonify({"error": "'addresses' must be a list."}), 400
    if len(addresses_raw) == 0:
        return jsonify({"error": "Address list is empty."}), 400

    # Validate and convert addresses
    addresses = []
    for i, a in enumerate(addresses_raw):
        try:
            val = int(a)
            if val < 0:
                return jsonify({"error": f"Address at index {i} is negative: {val}"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": f"Invalid address at index {i}: {a}"}), 400
        addresses.append(val)

    # Validate config
    try:
        cfg_obj = CacheConfig(
            main_memory_size=int(config.get("main_memory_size", 0)),
            cache_size=int(config.get("cache_size", 0)),
            block_size=int(config.get("block_size", 0)),
            mapping=str(config.get("mapping", "direct")),
            associativity=int(config.get("associativity", 1)),
            replacement=str(config.get("replacement", "lru")),
        )
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid config parameter: {e}"}), 400

    cfg_err = validate_config(cfg_obj)
    if cfg_err:
        return jsonify({"error": cfg_err}), 400

    cfg_obj.compute_derived()

    # Validate addresses against address space
    max_addr = cfg_obj.main_memory_size - 1
    for i, a in enumerate(addresses):
        if a > max_addr:
            return jsonify({"error": f"Address {a} at index {i} exceeds main memory range (max {max_addr})."}), 400

    # Try C++ engine first, fall back to Python
    result = None
    if os.path.isfile(CPP_BINARY):
        result = _run_cpp_engine(config, addresses, CPP_BINARY)
        if result and "error" in result:
            result = None  # fall back to Python

    if result is None:
        result = run_simulation(config, addresses)

    if "error" in result:
        return jsonify(result), 400

    return jsonify(result)


def _run_cpp_engine(config: dict, addresses: list, binary: str) -> dict:
    """Execute C++ binary via subprocess with timeout."""
    payload = json.dumps({"config": config, "addresses": addresses})
    try:
        proc = subprocess.run(
            [binary],
            input=payload,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode != 0:
            return {"error": f"C++ engine error: {proc.stderr}"}
        return json.loads(proc.stdout)
    except subprocess.TimeoutExpired:
        return {"error": "C++ engine timed out."}
    except (json.JSONDecodeError, FileNotFoundError) as e:
        return {"error": str(e)}


# =============================================================
# Configure (validation only – state is session-less)
# =============================================================
@app.route("/api/configure", methods=["POST"])
def configure():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON body."}), 400

    try:
        cfg = CacheConfig(
            main_memory_size=int(data.get("main_memory_size", 0)),
            cache_size=int(data.get("cache_size", 0)),
            block_size=int(data.get("block_size", 0)),
            mapping=str(data.get("mapping", "direct")),
            associativity=int(data.get("associativity", 1)),
            replacement=str(data.get("replacement", "lru")),
        )
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid parameter: {e}"}), 400

    err = validate_config(cfg)
    if err:
        return jsonify({"error": err, "valid": False}), 400

    cfg.compute_derived()
    return jsonify({
        "valid": True,
        "config": {
            "main_memory_size": cfg.main_memory_size,
            "cache_size": cfg.cache_size,
            "block_size": cfg.block_size,
            "mapping": cfg.mapping,
            "associativity": cfg.associativity,
            "replacement": cfg.replacement,
            "num_blocks": cfg.num_blocks,
            "num_cache_lines": cfg.num_cache_lines,
            "num_sets": cfg.num_sets,
            "offset_bits": cfg.offset_bits,
            "index_bits": cfg.index_bits,
            "tag_bits": cfg.tag_bits,
        }
    })


# =============================================================
# Reset  (stateless engine – just confirms)
# =============================================================
@app.route("/api/reset", methods=["POST"])
def reset():
    return jsonify({"status": "reset", "message": "Simulation state cleared."})


# =============================================================
# Serve frontend static files
# =============================================================
@app.route("/", defaults={"path": "index.html"})
@app.route("/<path:path>")
def serve_frontend(path):
    if os.path.isdir(FRONTEND_DIR):
        return send_from_directory(FRONTEND_DIR, path)
    return jsonify({"error": "Frontend not found."}), 404


# =============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  Cache Memory Simulator – Flask Backend")
    print("  Open http://127.0.0.1:5000 in your browser")
    print("=" * 60)
    app.run(debug=False, port=5000, host="127.0.0.1")
