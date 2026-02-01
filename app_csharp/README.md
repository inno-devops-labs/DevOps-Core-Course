# DevOps Info Service (ASP.NET)

## Overview
A simple DevOps information service that displays system, runtime, and request data.  
Includes a health-check endpoint for monitoring.
Implemented as a **modules for [ModuWeb (self-made application)](https://github.com/Chaleshka/ModuWeb)** on top of ASP.NET Core. <br/>
***ModueWeb** - is a .NET web application that supports dynamic runtime loading, reloading, and unloading of external modules (.dll files). Each module is self-contained and can expose custom HTTP routes, CORS policies, and request handlers.*


## [Prerequisites](https://github.com/Chaleshka/ModuWeb/?tab=readme-ov-file#-getting-started)
- .NET SDK 9.0.2+
- Microsoft.AspNetCore.App 9.0.2+

## Installation
Download the latest [release of ModuWeb](https://github.com/Chaleshka/ModuWeb/releases).
Build modules.
```bash
cd path/to/module/src
dotnet build
```

## Running the Application
#### For first run:
Run ModuWeb and move modules into created `module/` folder.
#### Run app
```bash
#Linux
./ModuWeb

#Windows
./ModuWeb.exe
```

Custom configuration edit via editing `appsettings.json`. For this app configuration:
```
{
  "BaseApiPath": "/",
  "BaseDbPath": "db/",
  "MaxRequestBodySize": 50, //In MB
  "UseHttps": false,
  "Kestrel": {
    "Endpoints": {
      "Https": {
        "Url": "http://*:5001"
      }
    }
  },
  "LoadOrder": [

  ]
}
```

## API Endpoints
| Method | Path | Description |
|---------|------|--------------|
| GET | `/` | Returns system and service information |
| GET | `/health` | Returns health and uptime status |

## Configuration
| Variable | Default | Description |
|-----------|----------|-------------|
| HOST | 0.0.0.0 | Host address |
| PORT | 5000 | Listening port |
| DEBUG | False | Enables Flask debug mode |

## Docker

The application can be run in a container. The image runs as a non-root user and listens on port 5000.

### Build the image locally
From the `app_csharp/` directory, run `docker build` with a tag (e.g. `devops-info-service-cs:latest`).
```
docker build -t <image-name>:<tag> .
```

### Run a container
Use `docker run` with port mapping so the app is reachable on the host (e.g. map container port 5001 to a host port 5001):
```
docker run -d -p <host-port>:5001 --name <container-name> <image-name>:<tag>
```
After `docker run` you can view long via this command:
```
docker logs <container-name>
```

### Pull from Docker Hub
You can pull latest app from docker hub:
```
docker pull chaleshka/devops-info-service-cs:latest
```
And run as:
```
docker run -d -p <host-port>:5000 --name <container-name> chaleshka/devops-info-service-cs:latest
```
