"""
test_api.py  --  Flask API endpoint tests
Run with: python tests/test_api.py
Requires Flask server to NOT be running (uses Flask test client).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "site-packages"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app import app

PASS = FAIL = 0

def test(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        print(f"  ✅ PASS  {name}")
        PASS += 1
    else:
        print(f"  ❌ FAIL  {name}  {detail}")
        FAIL += 1

client = app.test_client()

# ================================================================
print("\n--- API: /api/health ---")
r = client.get("/api/health")
d = r.get_json()
test("Status 200",         r.status_code == 200)
test("status == ok",       d.get("status") == "ok")
test("python_engine true", d.get("python_engine") == True)

# ================================================================
print("\n--- API: /api/algorithms ---")
r = client.get("/api/algorithms")
d = r.get_json()
test("Status 200",           r.status_code == 200)
test("Has mapping_techniques", "mapping_techniques" in d)
test("3 mapping techniques", len(d["mapping_techniques"]) == 3)
test("2 replacement policies", len(d["replacement_policies"]) == 2)

# ================================================================
print("\n--- API: /api/sample ---")
r = client.get("/api/sample")
d = r.get_json()
test("Status 200",    r.status_code == 200)
test("Has samples",   "samples" in d)
test("5 samples",     len(d["samples"]) == 5)
test("Sample 1 name contains 'Direct'",
     "Direct" in d["samples"][0]["name"])

# ================================================================
print("\n--- API: /api/configure (valid) ---")
cfg_valid = dict(main_memory_size=256, cache_size=64, block_size=4,
                 mapping="direct", associativity=1, replacement="lru")
r = client.post("/api/configure", json=cfg_valid)
d = r.get_json()
test("Status 200",          r.status_code == 200)
test("valid == True",       d.get("valid") == True)
test("num_cache_lines==16", d["config"]["num_cache_lines"] == 16)
test("offset_bits==2",      d["config"]["offset_bits"] == 2)
test("index_bits==4",       d["config"]["index_bits"] == 4)
test("tag_bits==26",        d["config"]["tag_bits"] == 26)

# ================================================================
print("\n--- API: /api/configure (invalid configs) ---")
bad_cases = [
    (dict(main_memory_size=256, cache_size=64,  block_size=3, mapping="direct",          associativity=1, replacement="lru"), "block_size=3 not power of 2"),
    (dict(main_memory_size=256, cache_size=300, block_size=4, mapping="direct",          associativity=1, replacement="lru"), "cache_size=300 not power of 2"),
    (dict(main_memory_size=32,  cache_size=64,  block_size=4, mapping="direct",          associativity=1, replacement="lru"), "cache > main memory"),
    (dict(main_memory_size=256, cache_size=16,  block_size=4, mapping="set_associative", associativity=3, replacement="lru"), "assoc=3 not divisor of lines"),
]
for body, label in bad_cases:
    r = client.post("/api/configure", json=body)
    d = r.get_json()
    test(f"Reject: {label}", r.status_code == 400 and "error" in d)

# ================================================================
print("\n--- API: /api/simulate (Demo 1) ---")
payload = {
    "config": dict(main_memory_size=256, cache_size=64, block_size=4,
                   mapping="direct", associativity=1, replacement="lru"),
    "addresses": [0, 4, 0, 64, 4, 64]
}
r = client.post("/api/simulate", json=payload)
d = r.get_json()
test("Status 200",          r.status_code == 200)
test("Has events",          "events" in d)
test("6 events",            len(d["events"]) == 6)
test("hits==3",             d["statistics"]["hits"] == 3)
test("misses==3",           d["statistics"]["misses"] == 3)
test("hit_pct==50.0",       d["statistics"]["hit_percentage"] == 50.0)
test("event[0] MISS",       d["events"][0]["event_type"] == "MISS")
test("event[2] HIT",        d["events"][2]["event_type"] == "HIT")
test("event[3] MISS_REPLACE", d["events"][3]["event_type"] == "MISS_REPLACE")
test("addr64 tag==1",       d["events"][3]["tag"] == 1)
test("addr64 index==0",     d["events"][3]["index"] == 0)

# ================================================================
print("\n--- API: /api/simulate (error cases) ---")
test("Missing body",        client.post("/api/simulate", data="bad").status_code == 400)
test("Missing config",      client.post("/api/simulate", json={"addresses":[0]}).status_code == 400)
test("Missing addresses",   client.post("/api/simulate", json={"config":cfg_valid}).status_code == 400)
test("Empty addresses",     client.post("/api/simulate", json={"config":cfg_valid,"addresses":[]}).status_code == 400)
test("Negative address",    client.post("/api/simulate", json={"config":cfg_valid,"addresses":[-1]}).status_code == 400)
test("Address out of range",client.post("/api/simulate", json={"config":cfg_valid,"addresses":[9999]}).status_code == 400)

# ================================================================
print("\n--- API: /api/reset ---")
r = client.post("/api/reset")
d = r.get_json()
test("Status 200",          r.status_code == 200)
test("status==reset",       d.get("status") == "reset")

# ================================================================
print(f"\n{'='*50}")
print(f"  API TESTS: {PASS} passed, {FAIL} failed")
print(f"{'='*50}")
if FAIL == 0:
    print("  🎉 ALL API TESTS PASSED!")
