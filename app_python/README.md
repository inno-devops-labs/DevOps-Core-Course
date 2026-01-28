# DevOps Info Service
A lightweight demo Python web application that system information via HTTP endpoints

### Prerequisites
Python 3.10+
Flask 3.1.0

### Installation
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running the Application
```bash
python3 app.py
# Or with custom config
PORT=8080 python3 app.py
```

### API Endpoints
There are few main endpoints:
- `GET /` - Service and system information
- `GET /health` - Health check

### Configuration

| Variable | Value  | Purpose                              |
| -------- | ------ | ------------------------------------ |
| Host     | string | A host to run app on                 |
| Port     | int    | A port to assign for web application |
| Debug    | bool   | Should debug output be enabled       |
