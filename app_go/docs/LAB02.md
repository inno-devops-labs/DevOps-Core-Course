# Lab 02 - Docker Multi-Stage Build (Bonus)

## Multi-stage build strategy

### builder stage

- uses golang:1.21-alpine as base (~300mb)
- contains full go toolchain for compilation
- compiles application with static linking
- produces single binary file

### runtime stage

- uses scratch (empty image, 0 bytes base)
- contains only the compiled binary
- no shell, no package manager, no extra files
- minimal attack surface

### why scratch works for go

- go can produce fully static binaries with CGO_ENABLED=0
- no runtime dependencies needed (unlike python or java)
- all libraries compiled into single executable
- binary is self-contained and portable

## Size comparison

### image sizes

![[image sizes]](screenshots/image_sizes.png)

### size reduction analysis

- builder image: 221 mb (includes go compiler, tools, libraries)
- final image: 6.52 mb (only compiled binary)
- reduction: ~97% smaller than builder
- reason: discarded compiler, source code, build tools after compilation

## Technical explanation

### CGO_ENABLED=0

- disables c go interface
- produces pure go binary without c dependencies
- required for scratch base image (no libc available)
- ensures binary works without any system libraries

### ldflags stripping

- -s removes symbol table
- -w removes dwarf debugging information
- reduces binary size by ~30%
- no impact on runtime functionality

### static compilation benefits

- single file deployment
- no dependency resolution at runtime
- works on any linux system
- compatible with minimal base images

## Security benefits

### minimal attack surface

- no shell means no shell injection possible
- no package manager means no supply chain attacks via container
- no extra utilities means fewer potential vulnerabilities
- only your code runs in the container

### no shell in scratch

- cannot exec into container with shell
- attackers cannot install tools if they gain access
- forces immutable infrastructure pattern
- debugging requires different approaches (logging, metrics)

## Build and run process

### build output

![[multi-stage docker build]](screenshots/go_build.png)

### endpoint testing

![[curl tests]](screenshots/run_curl_go.png)
