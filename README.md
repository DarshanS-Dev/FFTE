# FFTE: Failure-First Testing Engine

**Automatically discover, attack, and reproduce API crashes before your users do.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 The Problem

In the era of "vibe coding" where developers share localhost links with clients and ship APIs without proper testing, FFTE ensures your endpoints don't crash in production. No more division by zero errors, SQL injections, or unhandled edge cases slipping through.

## 🚀 What is FFTE?

FFTE is an intelligent API testing engine that:
- **Discovers** all endpoints from your OpenAPI specification
- **Generates** aggressive edge-case payloads (zero values, SQL injections, max integers, null bytes, etc.)
- **Executes** real HTTP requests to stress-test your API
- **Reports** failures as instant, reproducible `curl` commands

### Real Example

```bash
# Your API crashes on division by zero
curl -X POST "http://127.0.0.1:8000/divide" \
  -H "Content-Type: application/json" \
  -d '{"a": 10, "b": 0}'

# FFTE finds it automatically and gives you this exact curl command to reproduce
```

---

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/DarshanS-Dev/Failure-First-Testing-Agent
cd Failure-First-Testing-Agent

# Install Python dependencies
pip install -r requirements.txt

# Install Frontend dependencies
cd Frontend/home
npm install
cd ../..
```

**Requirements:**
- Python 3.10+
- Node.js 16+ and npm
- FastAPI
- uvicorn
- requests
- pydantic

---

## ⚡ Quick Start

### 1. Start Your API
```bash
# Example: Run the vulnerable victim API
uvicorn victim:app --reload
```

### 2. Run FFTE

**CLI Mode:**
```bash
python app.py http://127.0.0.1:8000/openapi.json
```

**API Mode:**
```bash
# Start FFTE API server
python ffte_api_fixed.py

# Submit a scan via REST API
curl -X POST "http://localhost:8001/api/scan/start" \
  -H "Content-Type: application/json" \
  -d '{
    "spec_url": "http://127.0.0.1:8000/openapi.json",
    "scan_name": "My API Security Scan"
  }'
```

### 3. Launch Web Interface

**Terminal 1 - React Homepage:**
```bash
cd Frontend/home
npm run dev
# Runs on http://localhost:5173
```

**Terminal 2 - Command Center & UI Pages:**
```bash
cd Frontend
python -m http.server 3000
# Serves command-center.html, the-lab.html, war-room.html on http://localhost:3000
```

**Terminal 3 - FFTE API (Optional):**
```bash
python ffte_api_fixed.py
# API server runs on http://localhost:8001
```

### 4. View Results

FFTE generates a detailed report with:
- ✅ Total tests executed
- ❌ Failures detected
- 🔧 Reproducible `curl` commands for each bug
- 📊 Failure classification (crashes, timeouts, server errors, client errors)

---

## 🛠️ Features

### 🔍 **Surface Discovery**
Parses OpenAPI/Swagger specs to extract:
- All HTTP endpoints
- Request parameters and schemas
- Expected data types and constraints

### 🎯 **Intelligent Input Generation**
Generates edge cases for every data type:
- **Integers:** `0`, `-1`, `2147483647`, `−2147483648`
- **Strings:** Empty strings, SQL injections, XSS payloads, Unicode, null bytes
- **Numbers:** `0.0`, `Infinity`, `-Infinity`, `NaN`
- **Booleans:** `true`, `false`
- **Arrays/Objects:** Empty, null elements, nested structures

### ⚡ **Real Execution**
- Sends actual HTTP requests to your API
- Configurable timeouts and concurrency
- Captures full request/response details

### 📋 **Failure Detection**
Classifies failures into:
- **Crashes** - Connection errors, DNS failures
- **Server Errors** - 500-level HTTP responses
- **Timeouts** - Requests exceeding time limits
- **Client Errors** - 400-level HTTP responses (optional)
- **Invalid JSON** - Malformed response bodies

### 📦 **Reproducible Reports**
Generates ready-to-run `curl` commands:
```bash
## server_error (7 occurrence(s))

### Example 1
curl -X POST "http://127.0.0.1:8000/divide" -d '{"a": 10, "b": 0}' -H "Content-Type: application/json"

### Example 2
curl -X POST "http://127.0.0.1:8000/divide" -d '{"a": 0, "b": 0}' -H "Content-Type: application/json"
```

---

## 🎨 Web Interface

FFTE includes a sleek "High Noir" web interface with four main sections:

### **00 - HOME** (http://localhost:5173)
Landing page with:
- Feature showcase
- Live animation demos
- Process visualization
- Getting started guide

### **01 - COMMAND CENTER** (http://localhost:3000/command-center.html)
Configure and launch scans:
- Specify OpenAPI spec URL
- Set scan parameters
- Monitor live execution logs

### **02 - THE LAB** (http://localhost:3000/the-lab.html)
Real-time scan monitoring:
- Progress tracking
- Endpoint discovery visualization
- Live failure detection

### **03 - WAR ROOM** (http://localhost:3000/war-room.html)
View detailed results:
- Failure statistics
- Complete curl reproduction commands
- Filterable failure types

---

## 🚀 Complete Startup Guide

For the full FFTE experience, run all components:

```bash
# Terminal 1: Start victim API (for testing)
uvicorn victim:app --reload --port 8000

# Terminal 2: Start FFTE API server
python ffte_api_fixed.py

# Terminal 3: Start React homepage
cd Frontend/home
npm run dev

# Terminal 4: Start HTML UI pages
cd Frontend
python -m http.server 3000
```

**Access Points:**
- 🏠 Homepage: http://localhost:5173
- 🎛️ Command Center: http://localhost:3000/command-center.html
- 🔬 The Lab: http://localhost:3000/the-lab.html
- 📊 War Room: http://localhost:3000/war-room.html
- 🔌 API Server: http://localhost:8001
- 🎯 Test API: http://localhost:8000

---

## 🗄️ Database Setup

1. **Install PostgreSQL**
   - Make sure PostgreSQL is installed and running on your machine.
2. **Configure environment variables**
   - Copy `.env.example` to `.env` and update `DATABASE_URL` with your credentials:
     ```bash
     cp .env.example .env
     # then edit .env to match your local Postgres setup
     ```
3. **Initialize the database**
   - Create the database and tables using SQLModel:
     ```bash
     python scripts/init_db.py
     ```
   - Optionally seed development data:
     ```bash
     INIT_DB_SEED=true python scripts/init_db.py
     ```
4. **Start the FFTE server**
   - Run the API server (it will use `DATABASE_URL` from your `.env`):
     ```bash
     python ffte_api_fixed.py
     ```

---

## 📖 Architecture

```
ffte/
├── surface_discovery/      # OpenAPI parsing
│   └── openapi_parser.py
├── input_generation/       # Edge case generation
│   └── edge_cases.py
├── execution/              # HTTP request executor
│   └── http_executor.py
├── failure_detection/      # Rule-based classifiers
│   └── rules.py
├── reporting/              # Report generation
│   └── report.py
├── core/                   # Main orchestrator
│   └── runner.py
├── app.py                  # CLI interface
├── ffte_api_fixed.py       # REST API server
└── Frontend/
    ├── home/               # React landing page
    │   ├── src/
    │   ├── package.json
    │   └── vite.config.js
    ├── command-center.html # Scan configuration
    ├── the-lab.html        # Live monitoring
    ├── war-room.html       # Results dashboard
    ├── styles.css          # High Noir styling
    └── main.js             # UI logic + audio effects
```

---

## 🧪 Example: Finding Division by Zero

**Vulnerable API (`victim.py`):**
```python
@app.post("/divide")
def divide(data: DivideInput):
    return {"result": data.a // data.b}  # No validation!
```

**FFTE automatically tests:**
```python
{"a": 10, "b": 2}   # ✅ Works
{"a": 10, "b": 0}   # ❌ CRASH: ZeroDivisionError
{"a": 0, "b": 0}    # ❌ CRASH
{"a": 2147483647, "b": 0}  # ❌ CRASH
```

**Output:**
```
💥 FOUND 7 BUG(S)!

🔧 Reproduce with:
curl -X POST 'http://127.0.0.1:8000/divide' \
  -H 'Content-Type: application/json' \
  -d '{"a": 10, "b": 0}'
```

---

## 🔧 Configuration

Customize FFTE behavior in `core/runner.py`:

```python
report = run(
    spec_url="http://127.0.0.1:8000/openapi.json",
    base_url="http://127.0.0.1:8000",
    timeout=10.0,              # Request timeout in seconds
    limit_endpoints=None       # Test only first N endpoints
)
```

---

## 🎵 Sound Effects

The web interface includes a "High Noir" audio system with:
- Click sounds for button interactions
- Hover effects for navigation
- Processing sounds during scans
- Success/error audio feedback

*Audio auto-resumes on first user interaction per browser policy.*

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🎯 Use Cases

- **Pre-deployment testing** - Catch bugs before shipping
- **CI/CD integration** - Automated security checks
- **API security audits** - Discover injection vulnerabilities
- **Regression testing** - Ensure fixes stay fixed
- **Developer onboarding** - Learn common API vulnerabilities

---

## 💡 Why "Failure-First"?

Traditional testing focuses on happy paths. FFTE inverts this:
1. **Assume failure** - Every input is potentially malicious
2. **Force crashes** - Aggressive edge cases reveal hidden bugs
3. **Prove resilience** - APIs that survive FFTE are production-ready

---

## 🚨 Disclaimer

FFTE is designed for **testing your own APIs**. Do not use it to test APIs you don't own or have permission to test. Always respect terms of service and legal boundaries.

---

**Built with ❤️ for developers who ship fast but want to ship safe.**

