# GO — Language Selection Justification

## Overview

For the bonus part of Lab 01, the DevOps Info Service was reimplemented using **Go**, a compiled programming language widely used in modern DevOps.
The goal of this implementation is to demonstrate the advantages of compiled languages in terms of performance, deployment, and containerization.

---

## Why Go?

Go was selected for the following reasons:

### 1. Compiled Language

Go compiles source code into a **single native binary**, which eliminates the need for a runtime interpreter (unlike Python).
This results in:

* Faster application startup
* Lower runtime overhead
* Simpler deployment process

---

### 2. Standard Library for Web Services

Go provides a powerful and production-ready HTTP server through the standard `net/http` package.
This allows building web services without relying on external frameworks, reducing dependencies and potential security risks.

---

### 3. Performance and Resource Efficiency

Compared to interpreted languages, Go applications:

* Use less memory
* Handle concurrent requests efficiently
* Scale well under load

This makes Go a popular choice for infrastructure tools, monitoring systems, and backend services.

---

## Comparison with Python Implementation

| Aspect                | Python (Flask)          | Go                      |
| --------------------- | ----------------------- | ----------------------- |
| Language Type         | Interpreted             | Compiled                |
| Startup Time          | Slower                  | Faster                  |
| Deployment            | Requires Python runtime | Single binary           |
| Docker Image Size     | Larger                  | Smaller                 |
| Performance           | Good for small services | High                    |
| Dependency Management | External packages       | Mostly standard library |

---

## Conclusion

Go was chosen for the bonus implementation because it provides a clean, efficient, and production-ready approach to building web services.
Using Go alongside Python in this lab demonstrates the trade-offs between interpreted and compiled languages and prepares the project for future DevOps tasks such as containerization, CI/CD pipelines, and Kubernetes deployments.
