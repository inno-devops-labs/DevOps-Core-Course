#### Overview ####
This is simple service that shows system info

#### Prerequisites ####

Python 3.11.1\

###### Libraries ######

Fastapi 0.128.0\
Requests 2.32.5\
Uvicorn 0.40.0

#### Installation ####
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Running ####

```bash
python app.py
# Or with custom config
python app.py --host 127.0.0.1 --port 8080 --debug false
```

#### Endpoints ####
   - `GET /` - Service and system information
   - `GET /health` - Health check

#### Configuration ####
   - `--host` - Change host
   - `--port` - Change port
   - `--debug` - Turn on/off debug mode