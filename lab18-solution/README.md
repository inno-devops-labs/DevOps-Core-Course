# Lab 18: Decentralized Hosting with 4EVERLAND & IPFS

## IPFS Setup
Run IPFS node locally:
```bash
docker-compose up -d
```

Access Web UI: http://localhost:5001/webui
Gateway: http://localhost:8080

## Add Content
Create test file and add to IPFS:
```bash
echo "Hello IPFS from DevOps course!" > hello.txt
docker exec lab18-solution_ipfs_1 ipfs add hello.txt
```

## 4EVERLAND Deployment
https://devops-core-course-shxuxnkj-niotu.ipfs.4everland.app/
