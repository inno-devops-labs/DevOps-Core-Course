#### Overview ####
This is simple service that shows system info

[![python-app](https://github.com/TheVex/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)](https://github.com/TheVex/DevOps-Core-Course/actions/workflows/python-ci.yml)

[![Ansible Deployment](https://github.com/TheVex/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/TheVex/DevOps-Core-Course/actions/workflows/ansible-deploy.yml)

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
cd labs/app_python
python app.py
# Or with custom config
python app.py --host 127.0.0.1 --port 8080 --debug false
```

#### Docker ####

To run containerized:

```bash
docker build -t *your_tag* .
docker run -p *port*:*port* *your_tag*
docker pull thevex/simple-app:latest
```

#### Endpoints ####

   - `GET /` - Service and system information
   - `GET /health` - Health check
   - `GET /visit` – increments the visit counter and returns the new value.
   - `GET /visits` – returns the current counter value without incrementing.

#### Configuration ####

   - `--host` - Change host
   - `--port` - Change port
   - `--debug` - Turn on/off debug mode

#### Run tests ####

```bash
cd labs/app_python
pytest
```
