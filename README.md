# Cache Memory Simulator

**COA B.Tech CSE Project**
Computer Organization & Architecture

---

## 🚀 Quick Start

### 1. Start the Server

Double-click **`start_server.bat`** OR run from terminal:

```
cd "Cache Memory Simulator"
"C:\Users\Usha Sri\AppData\Roaming\uv\python\cpython-3.14-windows-x86_64-none\python.exe" backend/app.py
```

### 2. Open the Application

Open your browser and go to: **http://127.0.0.1:5000**

---

## 📁 Project Structure

```
Cache Memory Simulator/
│
├── cpp/                      ← C++17 Simulation Engine Source
│   ├── cache.h               ← Core data structures & declarations
│   ├── cache.cpp             ← Validation & address breakdown
│   ├── DirectMapping.cpp     ← Direct mapping implementation
│   ├── FullyAssociative.cpp  ← Fully associative implementation
│   ├── SetAssociative.cpp    ← Set associative (N-way) implementation
│   ├── ReplacementPolicy.cpp ← FIFO & LRU algorithms
│   └── main.cpp              ← C++ main (JSON in/out)
│
├── backend/
│   ├── app.py                ← Flask REST API (7 endpoints)
│   ├── cache_engine.py       ← Python simulation engine (mirrors C++)
│   └── requirements.txt      ← Python dependencies
│
├── frontend/
│   ├── index.html            ← Main SPA (7 pages)
│   ├── css/styles.css        ← Complete UI styling
│   └── js/simulator.js       ← Frontend logic & API communication
│
├── tests/
│   └── test_cache.py         ← 35+ automated tests
│
├── site-packages/            ← Flask & dependencies (auto-installed)
│
├── start_server.bat          ← Start the application
├── run_tests.bat             ← Run all tests
├── compile_cpp.bat           ← Compile C++ engine (needs g++)
└── README.md                 ← This file
```

---

## ⚙️ Configuration Options

| Parameter        | Supported Values                   |
|------------------|------------------------------------|
| Main Memory Size | Power of 2 (Bytes, KB, MB)        |
| Cache Size       | Power of 2, ≤ main memory         |
| Block Size       | Power of 2 (e.g. 4, 8, 16, 32 B) |
| Mapping          | Direct / Fully Associative / Set Associative |
| Associativity    | 2, 4, 8, … (for Set Associative)  |
| Replacement      | LRU / FIFO                         |

---

## 🔌 API Endpoints

| Method | Endpoint         | Description                       |
|--------|------------------|-----------------------------------|
| GET    | /api/health      | Backend health check              |
| POST   | /api/configure   | Validate cache configuration      |
| POST   | /api/simulate    | Run simulation, get all events    |
| GET    | /api/sample      | Get 5 sample demonstrations       |
| GET    | /api/algorithms  | List supported algorithms         |
| POST   | /api/reset       | Reset simulation state            |

---

## 🧪 Running Tests

```
run_tests.bat
```

Tests cover:
- Configuration validation (8 tests)
- Sample Demo 1 — Direct Mapping (12 tests)
- Fully Associative FIFO (4 tests)
- Fully Associative LRU (4 tests)
- 2-Way Set Associative LRU (4 tests)
- Statistics formula verification (6 tests)
- Conflict miss detection (1 test)
- FIFO vs LRU difference (2 tests)
- Address breakdown (5 tests)

---

## 🖥️ Compiling the C++ Engine

The simulator works with the Python engine by default.
If you have g++ (MinGW-w64) installed:

```
compile_cpp.bat
```

The Flask backend automatically uses the C++ binary when available.

---

## 📚 Concepts Covered

- CPU, Cache Memory, Main Memory
- Cache Lines, Memory Blocks, Tags, Valid Bits
- Block Offset, Cache Index, Set Index
- Cache Hit, Cache Miss, Hit/Miss Ratio
- Direct Mapping
- Fully Associative Mapping
- Set Associative Mapping
- FIFO Replacement
- LRU Replacement
- 32-bit Address Breakdown: TAG | INDEX | OFFSET

---

## 🛠️ Technologies

- **C++17** — Cache simulation algorithms
- **G++** — C++ compiler (optional)
- **Python 3** — Backend & simulation engine
- **Flask** — REST API backend
- **Flask-CORS** — Cross-origin support
- **HTML5 / CSS3 / JavaScript** — Frontend SPA
