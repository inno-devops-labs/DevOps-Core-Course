# go language justification

## why go for the bonus task

### compiled language benefits

| criteria | go | python |
|----------|-----|--------|
| compilation | produces single binary | interpreted, requires runtime |
| deployment | copy one file | install python + pip + dependencies |
| startup time | milliseconds | seconds |
| memory usage | lower | higher |
| binary size | ~6-8 mb | n/a (needs interpreter) |

### go specific advantages

**1 simple concurrency model**
- goroutines for handling multiple requests
- built into the language, not a library

**2 standard library http server**
- no external dependencies needed
- production-ready out of the box

**3 cross-compilation**
- build for any platform from any platform
- `GOOS=linux GOARCH=amd64 go build`

**4 docker optimization**
- multi-stage builds produce tiny images
- scratch or alpine base images possible
- typical final image: 10-20 mb vs 100+ mb for python

### comparison with other compiled languages

| language | learning curve | build time | binary size | ecosystem |
|----------|----------------|------------|-------------|-----------|
| go | gentle | fast | small | mature |
| rust | steep | slow | smaller | growing |
| java | moderate | slow | large | enterprise |
| c# | moderate | moderate | medium | enterprise |

### why go over rust for this lab

- simpler syntax, faster to learn
- faster compilation times
- excellent for web services and devops tooling
- kubernetes, docker, terraform all written in go

## implementation notes

the go implementation uses only standard library packages:
- `encoding/json` for json serialization
- `net/http` for the http server
- `os` for environment variables and hostname
- `runtime` for system information
- `time` for timestamps and uptime
- `fmt` for string formatting
- `log` for logging

no external dependencies required
