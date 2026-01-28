# Screenshots Folder

This folder should contain the following screenshots after testing:

1. **01-main-endpoint.png** - Screenshot showing the main endpoint (GET /) response with complete JSON output
2. **02-health-check.png** - Screenshot showing the health endpoint (GET /health) response
3. **03-formatted-output.png** - Screenshot showing formatted/pretty-printed JSON output

## How to Capture Screenshots

After running the application:

```bash
# Start the app
python app.py

# Test main endpoint (in another terminal)
curl http://localhost:5000/

# Test health endpoint
curl http://localhost:5000/health

# Test formatted output
curl http://localhost:5000/ | python -m json.tool
```

Take screenshots of each command's output and save them here with the appropriate names.
