# Lab 2 — Docker Containerization

![difficulty](https://img.shields.io/badge/difficulty-beginner-success)
![topic](https://img.shields.io/badge/topic-Containerization-blue)
![points](https://img.shields.io/badge/points-10%2B2.5-orange)
![tech](https://img.shields.io/badge/tech-Docker-informational)

> Containerize your Python app from Lab 1 using Docker best practices and publish it to Docker Hub.

## Overview

Take your Lab 1 application and package it into a Docker container. Learn image optimization, security basics, and the Docker workflow used in production.

**What You'll Learn:**
- Writing production-ready Dockerfiles
- Docker best practices and security
- Image optimization techniques
- Docker Hub workflow

**Tech Stack:** Docker 25+ | Python 3.13-slim | Multi-stage builds

---

## Tasks

### Task 1 — Create Dockerfile (4 pts)

**Objective:** Write a Dockerfile that containerizes your Python app following best practices.

Create `app_python/Dockerfile` with these requirements:

**Must Have:**
- Non-root user (mandatory)
- Specific base image version (e.g., `python:3.13-slim` or `python:3.12-slim`)
- Only copy necessary files
- Proper layer ordering
- `.dockerignore` file

**Your app should work the same way in the container as it did locally.**

<details>
<summary>💡 Dockerfile Concepts & Resources</summary>

**Key Dockerfile Instructions to Research:**
- `FROM` - Choose your base image (look at python:3.13-slim, python:3.12-slim, python:3.13-alpine)
- `RUN` - Execute commands (creating users, installing packages)
- `WORKDIR` - Set working directory
- `COPY` - Copy files into the image
- `USER` - Switch to non-root user
- `EXPOSE` - Document which port your app uses
- `CMD` - Define how to start your application

**Critical Concepts:**
- **Layer Caching**: Why does the order of COPY commands matter?
- **Non-root User**: How do you create and switch to a non-root user?
- **Base Image Selection**: What's the difference between slim, alpine, and full images?
- **Dependency Installation**: Why copy requirements.txt separately from application code?

**Resources:**
- [Dockerfile Reference](https://docs.docker.com/reference/dockerfile/)
- [Best Practices Guide](https://docs.docker.com/build/building/best-practices/)
- [Python Image Variants](https://hub.docker.com/_/python) - Use 3.13-slim or 3.12-slim

**Think About:**
- What happens if you copy all files before installing dependencies?
- Why shouldn't you run as root?
- How does layer caching speed up rebuilds?

</details>

<details>
<summary>💡 .dockerignore Concepts</summary>

**Purpose:** Prevent unnecessary files from being sent to Docker daemon during build (faster builds, smaller context).

**What Should You Exclude?**
Think about what doesn't need to be in your container:
- Development artifacts (like Python's `__pycache__`, `*.pyc`)
- Version control files (`.git` directory)
- IDE configuration files
- Virtual environments (`venv/`, `.venv/`)
- Documentation that's not needed at runtime
- Test files (if not running tests in container)

**Key Question:** Why does excluding files from the build context matter for build speed?

**Resources:**
- [.dockerignore Documentation](https://docs.docker.com/engine/reference/builder/#dockerignore-file)
- Look at your `.gitignore` for inspiration - many patterns overlap

**Exercise:** Start minimal and add exclusions as needed, rather than copying a huge list you don't understand.

</details>

**Test Your Container:**

You should be able to:
1. Build your image using the `docker build` command
2. Run a container from your image with proper port mapping
3. Access your application endpoints from the host machine

Verify that your application works the same way in the container as it did locally.

---

### Task 2 — Docker Hub (2 pts)

**Objective:** Publish your image to Docker Hub.

**Requirements:**
1. Create a Docker Hub account (if you don't have one)
2. Tag your image with your Docker Hub username
3. Authenticate with Docker Hub
4. Push your image to the registry
5. Verify the image is publicly accessible

**Documentation Required:**
- Terminal output showing successful push
- Docker Hub repository URL
- Explanation of your tagging strategy

<details>
<summary>💡 Docker Hub Resources</summary>

**Useful Commands:**
- `docker tag` - Tag images for registry push
- `docker login` - Authenticate with Docker Hub
- `docker push` - Upload image to registry
- `docker pull` - Download image from registry

**Resources:**
- [Docker Hub Quickstart](https://docs.docker.com/docker-hub/quickstart/)
- [Docker Tag Reference](https://docs.docker.com/reference/cli/docker/image/tag/)
- [Best Practices for Tagging](https://docs.docker.com/build/building/best-practices/#tagging)

</details>

---

### Task 3 — Documentation (4 pts)

**Objective:** Document your Docker implementation with focus on understanding and decisions.

#### 3.1 Update `app_python/README.md`

Add a **Docker** section explaining how to use your containerized application. Include command patterns (not exact commands) for:
- Building the image locally
- Running a container
- Pulling from Docker Hub

#### 3.2 Create `app_python/docs/LAB02.md`

Document your implementation with these sections:

**Required Sections:**

1. **Docker Best Practices Applied**
   - List each practice you implemented (non-root user, layer caching, .dockerignore, etc.)
   - Explain WHY each matters (not just what it does)
   - Include relevant Dockerfile snippets with explanations

2. **Image Information & Decisions**
   - Base image chosen and justification (why this specific version?)
   - Final image size and your assessment
   - Layer structure explanation
   - Optimization choices you made

3. **Build & Run Process**
   - Complete terminal output from your build process
   - Terminal output showing container running
   - Terminal output from testing endpoints (curl/httpie)
   - Docker Hub repository URL

4. **Technical Analysis**
   - Why does your Dockerfile work the way it does?
   - What would happen if you changed the layer order?
   - What security considerations did you implement?
   - How does .dockerignore improve your build?

5. **Challenges & Solutions**
   - Issues encountered during implementation
   - How you debugged and resolved them
   - What you learned from the process

---

## Bonus Task — Multi-Stage Build (2.5 pts)

**Objective:** Containerize your compiled language app (from Lab 1 bonus) using multi-stage builds.

**Why Multi-Stage?** Separate build environment from runtime → smaller final image.

**Example Flow:**
1. **Stage 1 (Builder):** Compile the app (large image with compilers)
2. **Stage 2 (Runtime):** Copy only the binary (small image, no build tools)

<details>
<summary>💡 Multi-Stage Build Concepts</summary>

**The Problem:** Compiled language images include the entire compiler/SDK in the final image (huge!).

**The Solution:** Use multiple `FROM` statements:
- **Stage 1 (Builder)**: Use full SDK image, compile your application
- **Stage 2 (Runtime)**: Use minimal base image, copy only the compiled binary

**Key Concepts to Research:**
- How to name build stages (`AS builder`)
- How to copy files from previous stages (`COPY --from=builder`)
- Choosing runtime base images (alpine, distroless, scratch)
- Static vs dynamic compilation (affects what base image you can use)

**Questions to Explore:**
- What's the size difference between your builder and final image?
- Why can't you just use the builder image as your final image?
- What security benefits come from smaller images?
- Can you use `FROM scratch`? Why or why not?

**Resources:**
- [Multi-Stage Builds Documentation](https://docs.docker.com/build/building/multi-stage/)
- [Distroless Base Images](https://github.com/GoogleContainerTools/distroless)
- Language-specific: Search "Go static binary Docker" or "Rust alpine Docker"

**Challenge:** Try to get your final image under 20MB.

</details>

**Requirements:**
- Multi-stage Dockerfile in `app_go/` (or your chosen language)
- Working containerized application
- Documentation in `app_go/docs/LAB02.md` explaining:
  - Your multi-stage build strategy
  - Size comparison with analysis (builder vs final image)
  - Why multi-stage builds matter for compiled languages
  - Terminal output showing build process and image sizes
  - Technical explanation of each stage's purpose

**Bonus Points Given For:**
- Significant size reduction achieved with clear metrics
- Deep understanding of multi-stage build benefits
- Analysis of security implications (smaller attack surface)
- Explanation of trade-offs and decisions made

---

## How to Submit

1. **Create Branch:** Create a new branch called `lab02`

2. **Commit Work:**
   - Add your changes (app_python/ directory with Dockerfile, .dockerignore, updated docs)
   - Commit with a descriptive message following conventional commits format
   - Push to your fork

3. **Create Pull Requests:**
   - **PR #1:** `your-fork:lab02` → `course-repo:master`
   - **PR #2:** `your-fork:lab02` → `your-fork:master`

---

## Acceptance Criteria

### Main Tasks (10 points)

**Dockerfile (4 pts):**
- [ ] Dockerfile exists in `app_python/`
- [ ] Uses specific base image version
- [ ] Runs as non-root user (USER directive)
- [ ] Proper layer ordering (dependencies before code)
- [ ] Only copies necessary files
- [ ] `.dockerignore` file present
- [ ] Image builds successfully
- [ ] Container runs and app works

**Docker Hub (2 pts):**
- [ ] Image pushed to Docker Hub
- [ ] Image is publicly accessible
- [ ] Correct tagging used
- [ ] Can pull and run from Docker Hub

**Documentation (4 pts):**
- [ ] `app_python/README.md` has Docker section with command patterns
- [ ] `app_python/docs/LAB02.md` complete with:
  - [ ] Best practices explained with WHY (not just what)
  - [ ] Image information and justifications for choices
  - [ ] Terminal output from build, run, and testing
  - [ ] Technical analysis demonstrating understanding
  - [ ] Challenges and solutions documented
  - [ ] Docker Hub repository URL provided

### Bonus Task (2.5 points)

- [ ] Multi-stage Dockerfile for compiled language app
- [ ] Working containerized application
- [ ] Documentation in `app_<language>/docs/LAB02.md` with:
  - [ ] Multi-stage strategy explained
  - [ ] Terminal output showing image sizes (builder vs final)
  - [ ] Analysis of size reduction and why it matters
  - [ ] Technical explanation of each stage
  - [ ] Security benefits discussed

---

## Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **Dockerfile** | 4 pts | Correct, secure, optimized |
| **Docker Hub** | 2 pts | Successfully published |
| **Documentation** | 4 pts | Complete and clear |
| **Bonus** | 2.5 pts | Multi-stage implementation |
| **Total** | 12.5 pts | 10 pts required + 2.5 pts bonus |

**Grading:**
- **10/10:** Perfect Dockerfile, deep understanding demonstrated, excellent analysis
- **8-9/10:** Working container, good practices, solid understanding shown
- **6-7/10:** Container works, basic security, surface-level explanations
- **<6/10:** Missing requirements, runs as root, copy-paste without understanding

---

## Resources

<details>
<summary>📚 Docker Documentation</summary>

- [Dockerfile Best Practices](https://docs.docker.com/build/building/best-practices/)
- [Dockerfile Reference](https://docs.docker.com/reference/dockerfile/)
- [Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [.dockerignore](https://docs.docker.com/reference/dockerfile/#dockerignore-file)
- [Docker Build Guide](https://docs.docker.com/build/guide/)

</details>

<details>
<summary>🔒 Security Resources</summary>

- [Docker Security Best Practices](https://docs.docker.com/build/building/best-practices/#security)
- [Snyk Docker Security](https://snyk.io/learn/docker-security-scanning/)
- [Why Non-Root Containers](https://docs.docker.com/build/building/best-practices/#user)
- [Distroless Images](https://github.com/GoogleContainerTools/distroless) - Minimal base images

</details>

<details>
<summary>🛠️ Tools</summary>

- [Hadolint](https://github.com/hadolint/hadolint) - Dockerfile linter
- [Dive](https://github.com/wagoodman/dive) - Explore image layers
- [Docker Hub](https://hub.docker.com/) - Container registry

</details>

---

## Looking Ahead

- **Lab 3:** CI/CD will automatically build these Docker images
- **Lab 7-8:** Deploy containers with docker-compose for logging/monitoring
- **Lab 9:** Run these containers in Kubernetes
- **Lab 13:** ArgoCD will deploy containerized apps automatically

---

**Good luck!** 🚀

> **Remember:** Understanding beats copy-paste. Explain your decisions, not just your actions. Run as non-root or no points!
