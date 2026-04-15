# Lab 12 Solution

DevOps Info Service with visits counter and persistence.

## Local Testing

```bash
docker-compose up --build
```

Access http://localhost:8000 for root, http://localhost:8000/visits for count.

Data persists in ./data/visits across restarts.