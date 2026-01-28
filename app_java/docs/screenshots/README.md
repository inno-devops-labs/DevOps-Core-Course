# Screenshots Folder

This folder should contain the following screenshots after building and testing:

1. **04-java-build.png** - Screenshot showing successful Maven build with "BUILD SUCCESS"
2. **05-java-main-endpoint.png** - Screenshot showing the main endpoint (GET /) response
3. **06-java-health-check.png** - Screenshot showing the health endpoint (GET /health) response

## How to Capture Screenshots

### 1. Build Screenshot

```powershell
cd app_java
$env:PATH = "C:\Users\пк\maven\apache-maven-3.9.6\bin;$env:PATH"
mvn clean package
```

Take screenshot showing "BUILD SUCCESS" → save as `04-java-build.png`

### 2. Run and Test

```powershell
# Start the app (in background or separate terminal)
java -jar target/devops-info-service.jar

# Wait for app to start (look for "Started Application" message)

# Test main endpoint
(curl http://localhost:8080/ -UseBasicParsing).Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

Take screenshot → save as `05-java-main-endpoint.png`

### 3. Health Check

```powershell
(curl http://localhost:8080/health -UseBasicParsing).Content | ConvertFrom-Json | ConvertTo-Json
```

Take screenshot → save as `06-java-health-check.png`
