# DevOps Info Service (ASP.NET)

## Overview
A simple DevOps information service that displays system, runtime, and request data.  
Includes a health-check endpoint for monitoring.
Implemented as a **modules for [ModuWeb (self-made application)](https://github.com/Chaleshka/ModuWeb)** on top of ASP.NET Core. 
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
