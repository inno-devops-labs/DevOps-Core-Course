# DevOps Engineering: Core Practices

[![Labs](https://img.shields.io/badge/Labs-18-blue)](#labs)
[![Exam](https://img.shields.io/badge/Exam-Optional-green)](#exam-alternative)
[![Duration](https://img.shields.io/badge/Duration-18%20Weeks-lightgrey)](#course-roadmap)

Master **production-grade DevOps practices** through hands-on labs. Build, containerize, deploy, monitor, and scale applications using industry-standard tools.

---

## Quick Start

1. **Fork** this repository
2. **Clone** your fork locally
3. **Start with Lab 1** and progress sequentially
4. **Submit PRs** for each lab (details below)

---

## Course Roadmap

| Week | Lab | Topic | Key Technologies |
|------|-----|-------|------------------|
| 1 | 1 | Web Application Development | Python/Go, Best Practices |
| 2 | 2 | Containerization | Docker, Multi-stage Builds |
| 3 | 3 | Continuous Integration | GitHub Actions, Snyk |
| 4 | 4 | Infrastructure as Code | Terraform, Cloud Providers |
| 5 | 5 | Configuration Management | Ansible Basics |
| 6 | 6 | Continuous Deployment | Ansible Advanced |
| 7 | 7 | Logging | Promtail, Loki, Grafana |
| 8 | 8 | Monitoring | Prometheus, Grafana |
| 9 | 9 | Kubernetes Basics | Minikube, Deployments, Services |
| 10 | 10 | Helm Charts | Templating, Hooks |
| 11 | 11 | Secrets Management | K8s Secrets, HashiCorp Vault |
| 12 | 12 | Configuration & Storage | ConfigMaps, PVCs |
| 13 | 13 | GitOps | ArgoCD |
| 14 | 14 | Progressive Delivery | Argo Rollouts |
| 15 | 15 | StatefulSets | Persistent Storage, Headless Services |
| 16 | 16 | Cluster Monitoring | Kube-Prometheus, Init Containers |
| — | **Exam Alternative Labs** | | |
| 17 | 17 | Edge Deployment | Fly.io, Global Distribution |
| 18 | 18 | Reproducible Builds | Nix, Deterministic Builds, Flakes |

---

## Grading

### Grade Composition

| Component | Weight | Points |
|-----------|--------|--------|
| **Labs (16 required)** | 80% | 160 pts |
| **Final Exam** | 20% | 40 pts |
| **Bonus Tasks** | Extra | +40 pts max |
| **Total** | 100% | 200 pts |

### Exam Alternative

Don't want to take the exam? Complete **both** bonus labs:

| Lab | Topic | Points |
|-----|-------|--------|
| **Lab 17** | Fly.io Edge Deployment | 20 pts |
| **Lab 18** | Reproducible Builds with Nix | 20 pts |

**Requirements:**
- Complete both labs (17 + 18 = 40 pts, replaces exam)
- Minimum 16/20 on each lab
- Deadline: **1 week before exam date**
- Can still take exam if you need more points for desired grade

<details>
<summary>📊 Grade Scale</summary>

| Grade | Points | Percentage |
|-------|--------|------------|
| **A** | 180-200+ | 90-100% |
| **B** | 150-179 | 75-89% |
| **C** | 120-149 | 60-74% |
| **D** | 0-119 | 0-59% |

**Minimum to Pass:** 120 points (60%)

</details>

<details>
<summary>📈 Grade Examples</summary>

**Scenario 1: Labs + Exam**
```
Labs: 16 × 9 = 144 pts
Bonus: 5 labs × 2.5 = 12.5 pts
Exam: 35/40 pts
Total: 191.5 pts = 96% (A)
```

**Scenario 2: Labs + Exam Alternative**
```
Labs: 16 × 9 = 144 pts
Bonus: 8 labs × 2.5 = 20 pts
Lab 17: 18 pts
Lab 18: 17 pts
Total: 199 pts = 99.5% (A)
```

</details>

---

## Lab Structure

Each lab is worth **10 points** (main tasks) + **2.5 points** (bonus).

- **Minimum passing score:** 6/10 per lab
- **Late submissions:** Max 6/10 (within 1 week)
- **Very late (>1 week):** Not accepted

<details>
<summary>📋 Lab Categories</summary>

**Foundation (Labs 1-2)**
- Web app development
- Docker containerization

**CI/CD & Infrastructure (Labs 3-4)**
- GitHub Actions
- Terraform

**Configuration Management (Labs 5-6)**
- Ansible playbooks and roles

**Observability (Labs 7-8)**
- Loki logging stack
- Prometheus monitoring

**Kubernetes Core (Labs 9-12)**
- K8s basics, Helm
- Secrets, ConfigMaps

**Advanced Kubernetes (Labs 13-16)**
- ArgoCD, Argo Rollouts
- StatefulSets, Monitoring

**Exam Alternative (Labs 17-18)**
- Fly.io, Nix Reproducible Builds

</details>

---

## How to Submit

```bash
# 1. Create branch
git checkout -b lab1

# 2. Complete lab tasks

# 3. Commit and push
git add .
git commit -m "Complete lab1"
git push -u origin lab1

# 4. Create TWO Pull Requests:
#    PR #1: your-fork:lab1 → course-repo:master
#    PR #2: your-fork:lab1 → your-fork:master
```

<details>
<summary>📝 Submission Checklist</summary>

- [ ] All main tasks completed
- [ ] Documentation files created
- [ ] Screenshots where required
- [ ] Code tested and working
- [ ] Markdown validated ([linter](https://dlaa.me/markdownlint/))
- [ ] Both PRs created

</details>

---

## Resources

<details>
<summary>🛠️ Required Tools</summary>

| Tool | Purpose |
|------|---------|
| Git | Version control |
| Docker | Containerization |
| kubectl | Kubernetes CLI |
| Helm | K8s package manager |
| Minikube | Local K8s cluster |
| Terraform | Infrastructure as Code |
| Ansible | Configuration management |

</details>

<details>
<summary>📚 Documentation Links</summary>

**Core:**
- [Docker](https://docs.docker.com/)
- [Kubernetes](https://kubernetes.io/docs/)
- [Helm](https://helm.sh/docs/)

**CI/CD:**
- [GitHub Actions](https://docs.github.com/en/actions)
- [Terraform](https://www.terraform.io/docs)
- [Ansible](https://docs.ansible.com/)

**Observability:**
- [Prometheus](https://prometheus.io/docs/)
- [Grafana](https://grafana.com/docs/)

**Advanced:**
- [ArgoCD](https://argo-cd.readthedocs.io/)
- [Argo Rollouts](https://argoproj.github.io/argo-rollouts/)
- [HashiCorp Vault](https://developer.hashicorp.com/vault/docs)

</details>

<details>
<summary>💡 Tips for Success</summary>

1. **Start early** - Don't wait until deadline
2. **Read instructions fully** before starting
3. **Test everything** before submitting
4. **Document as you go** - Don't leave it for the end
5. **Ask questions early** - Don't wait until last minute
6. **Use proper Git workflow** - Branches, commits, PRs

</details>

<details>
<summary>🔧 Common Issues</summary>

**Docker:**
- Daemon not running → Start Docker Desktop
- Permission denied → Add user to docker group

**Minikube:**
- Won't start → Try `--driver=docker`
- Resource issues → Allocate more memory/CPU

**Kubernetes:**
- ImagePullBackOff → Check image name/registry
- CrashLoopBackOff → Check logs: `kubectl logs <pod>`

</details>

---

## Course Completion

After completing all 16 core labs (+ optional Labs 17-18), you'll have:

✅ Full-stack DevOps expertise
✅ Production-ready portfolio with 16-18 projects
✅ Container and Kubernetes mastery
✅ CI/CD pipeline experience
✅ Infrastructure as Code skills
✅ Monitoring and observability knowledge
✅ GitOps workflow experience

---

**Ready to begin? Start with [Lab 1](labs/lab01.md)!**

Questions? Check the course Moodle page or ask during office hours.
