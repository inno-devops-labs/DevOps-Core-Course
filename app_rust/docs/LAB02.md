# Lab 02 - Docker Containerization (Rust, Bonus)

## Multi-Stage Build Strategy

- Stage 1 (builder): `rust:1.88-slim-bookworm` to compile the binary with all build tooling.
- Stage 2 (runtime): `gcr.io/distroless/cc-debian12` to run only the compiled binary with minimal OS surface.

Why this matters: build tools and Cargo caches are large. Multi-stage keeps the runtime image small and reduces the attack surface.

Dockerfile used:

```Dockerfile
FROM rust:1.88-slim-bookworm AS builder

WORKDIR /app

COPY Cargo.toml Cargo.lock ./
COPY src ./src

RUN cargo build --release

FROM gcr.io/distroless/cc-debian12

WORKDIR /app

COPY --from=builder /app/target/release/devops-info-service /app/devops-info-service

USER 65532

EXPOSE 8080

CMD ["/app/devops-info-service"]
```

## Size Comparison and Analysis

Image size output:

```
devops-info-service-rust           lab02                e0cc957fccac   40.9MB
devops-info-service-rust-builder   lab02                0e8896bff782   1.34GB
```

Analysis:
- Builder image includes Rust toolchain and build dependencies, so it is large.
- Runtime image contains only the binary and minimal OS libs, resulting in a much smaller image.
- Smaller runtime images reduce storage, transfer time, and the vulnerability surface.

## Build Process Output

Docker build output:

```
#0 building with "orbstack" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 398B done
#1 DONE 0.1s

#2 [internal] load metadata for docker.io/library/rust:1.88-slim-bookworm
#2 DONE 0.0s

#3 [internal] load metadata for gcr.io/distroless/cc-debian12:latest
#3 DONE 0.7s

#4 [internal] load .dockerignore
#4 transferring context: 2B done
#4 DONE 0.0s

#5 [builder 1/5] FROM docker.io/library/rust:1.88-slim-bookworm
#5 DONE 0.0s

#6 [stage-1 1/3] FROM gcr.io/distroless/cc-debian12:latest@sha256:72344f7f909a8bf003c67f55687e6d51a441b49661af8f660aa7b285f00e57df
#6 DONE 0.0s

#7 [stage-1 2/3] WORKDIR /app
#7 CACHED

#8 [internal] load build context
#8 transferring context: 265B done
#8 DONE 0.0s

#9 [builder 2/5] WORKDIR /app
#9 CACHED

#10 [builder 3/5] COPY Cargo.toml Cargo.lock ./
#10 CACHED

#11 [builder 4/5] COPY src ./src
#11 CACHED

#12 [builder 5/5] RUN cargo build --release
#12 0.880     Updating crates.io index
#12 5.935  Downloading crates ...
#12 6.688   Downloaded alloc-no-stdlib v2.0.4
#12 6.743   Downloaded block-buffer v0.10.4
#12 6.759   Downloaded actix-utils v3.0.1
#12 6.854   Downloaded anstream v0.6.21
#12 6.869   Downloaded actix-service v2.0.3
#12 6.879   Downloaded actix-router v0.5.3
#12 6.889   Downloaded actix-rt v2.11.0
#12 6.906   Downloaded either v1.15.0
#12 6.913   Downloaded anstyle-parse v0.2.7
#12 6.918   Downloaded adler2 v2.0.1
#12 6.922   Downloaded crossbeam-epoch v0.9.18
#12 6.930   Downloaded autocfg v1.5.0
#12 6.936   Downloaded actix-macros v0.2.4
#12 6.963   Downloaded errno v0.3.14
#12 6.969   Downloaded colorchoice v1.0.4
#12 6.971   Downloaded anstyle-query v1.1.5
#12 6.977   Downloaded httpdate v1.0.3
#12 6.982   Downloaded httparse v1.10.1
#12 6.990   Downloaded actix-web-codegen v4.3.0
#12 7.004   Downloaded semver v1.0.27
#12 7.054   Downloaded futures-core v0.3.31
#12 7.058   Downloaded displaydoc v0.2.5
#12 7.072   Downloaded getrandom v0.3.4
#12 7.079   Downloaded bytestring v1.5.0
#12 7.083   Downloaded bitflags v2.10.0
#12 7.094   Downloaded alloc-stdlib v0.2.2
#12 7.096   Downloaded actix-codec v0.5.2
#12 7.100   Downloaded generic-array v0.14.7
#12 7.103   Downloaded cpufeatures v0.2.17
#12 7.106   Downloaded anstyle v1.0.13
#12 7.113   Downloaded pin-utils v0.1.0
#12 7.119   Downloaded percent-encoding v2.3.2
#12 7.121   Downloaded local-waker v0.1.4
#12 7.125   Downloaded smallvec v1.15.1
#12 7.130   Downloaded pkg-config v0.3.32
#12 7.134   Downloaded itoa v1.0.17
#12 7.137   Downloaded cfg-if v1.0.4
#12 7.141   Downloaded num-conv v0.2.0
#12 7.145   Downloaded mime v0.3.17
#12 7.150   Downloaded impl-more v0.1.9
#12 7.162   Downloaded futures-task v0.3.31
#12 7.165   Downloaded futures-sink v0.3.31
#12 7.169   Downloaded form_urlencoded v1.2.2
#12 7.171   Downloaded equivalent v1.0.2
#12 7.174   Downloaded env_filter v0.1.4
#12 7.179   Downloaded digest v0.10.7
#12 7.185   Downloaded local-channel v0.1.5
#12 7.187   Downloaded potential_utf v0.1.4
#12 7.193   Downloaded pin-project-lite v0.2.16
#12 7.220   Downloaded crossbeam-utils v0.8.21
#12 7.230   Downloaded lock_api v0.4.14
#12 7.233   Downloaded actix-server v2.6.0
#12 7.239   Downloaded iana-time-zone v0.1.64
#12 7.243   Downloaded cookie v0.16.2
#12 7.252   Downloaded signal-hook-registry v1.4.8
#12 7.256   Downloaded foldhash v0.1.5
#12 7.260   Downloaded find-msvc-tools v0.1.8
#12 7.262   Downloaded fnv v1.0.7
#12 7.264   Downloaded convert_case v0.10.0
#12 7.268   Downloaded litemap v0.8.1
#12 7.273   Downloaded is_terminal_polyfill v1.70.2
#12 7.274   Downloaded idna_adapter v1.2.1
#12 7.276   Downloaded env_logger v0.11.8
#12 7.279   Downloaded deranged v0.5.5
#12 7.283   Downloaded quote v1.0.44
#12 7.289   Downloaded jobserver v0.1.34
#12 7.295   Downloaded crossbeam-deque v0.8.6
#12 7.299   Downloaded crypto-common v0.1.7
#12 7.301   Downloaded crc32fast v1.5.0
#12 7.304   Downloaded stable_deref_trait v1.2.1
#12 7.307   Downloaded socket2 v0.5.10
#12 7.315   Downloaded slab v0.4.11
#12 7.318   Downloaded simd-adler32 v0.3.8
#12 7.321   Downloaded parking_lot v0.12.5
#12 7.328   Downloaded once_cell v1.21.3
#12 7.335   Downloaded language-tags v0.3.2
#12 7.338   Downloaded log v0.4.29
#12 7.342   Downloaded icu_provider v2.1.1
#12 7.366   Downloaded num-traits v0.2.19
#12 7.379   Downloaded parking_lot_core v0.9.12
#12 7.387   Downloaded icu_properties v2.1.2
#12 7.395   Downloaded icu_collections v2.1.1
#12 7.411   Downloaded actix-web v4.12.1
#12 7.487   Downloaded zstd v0.13.3
#12 7.498   Downloaded brotli v8.0.2
#12 7.539   Downloaded icu_normalizer v2.1.1
#12 7.545   Downloaded actix-http v3.11.2
#12 7.561   Downloaded h2 v0.3.27
#12 7.664   Downloaded writeable v0.6.2
#12 7.710   Downloaded icu_locale_core v2.1.1
#12 7.725   Downloaded icu_normalizer_data v2.1.1
#12 7.730   Downloaded bytes v1.11.0
#12 7.742   Downloaded utf8_iter v1.0.4
#12 7.743   Downloaded cc v1.2.54
#12 7.750   Downloaded derive_more v2.1.1
#12 7.777   Downloaded miniz_oxide v0.8.9
#12 7.781   Downloaded http v0.2.12
#12 7.791   Downloaded derive_more-impl v2.1.1
#12 7.805   Downloaded base64 v0.22.1
#12 7.815   Downloaded hashbrown v0.16.1
#12 7.826   Downloaded memchr v2.7.6
#12 7.836   Downloaded indexmap v2.13.0
#12 7.847   Downloaded mio v1.1.1
#12 7.856   Downloaded futures-util v0.3.31
#12 7.884   Downloaded aho-corasick v1.1.4
#12 7.893   Downloaded idna v1.1.0
#12 7.898   Downloaded icu_properties_data v2.1.2
#12 7.929   Downloaded yoke-derive v0.8.1
#12 7.931   Downloaded chrono v0.4.43
#12 7.944   Downloaded encoding_rs v0.8.35
#12 7.974   Downloaded flate2 v1.1.8
#12 7.982   Downloaded brotli-decompressor v5.0.0
#12 7.993   Downloaded rand v0.9.2
#12 8.048   Downloaded jiff v0.2.18
#12 8.080   Downloaded libc v0.2.180
#12 8.145   Downloaded powerfmt v0.2.0
#12 8.175   Downloaded utf8parse v0.2.2
#12 8.234   Downloaded sha1 v0.10.6
#12 8.297   Downloaded serde_urlencoded v0.7.1
#12 8.300   Downloaded zerofrom-derive v0.1.6
#12 8.303   Downloaded time-core v0.1.8
#12 8.353   Downloaded tinystr v0.8.2
#12 8.361   Downloaded zstd-safe v7.2.4
#12 8.417   Downloaded yoke v0.8.1
#12 8.475   Downloaded scopeguard v1.2.0
#12 8.478   Downloaded rustc_version_runtime v0.3.0
#12 8.592   Downloaded zerofrom v0.1.6
#12 8.600   Downloaded version_check v0.9.5
#12 8.657   Downloaded rustc_version v0.4.1
#12 8.719   Downloaded zmij v1.0.17
#12 8.773   Downloaded time-macros v0.2.26
#12 8.831   Downloaded unicode-xid v0.2.6
#12 8.892   Downloaded shlex v1.3.0
#12 8.896   Downloaded tracing-attributes v0.1.31
#12 8.901   Downloaded synstructure v0.13.2
#12 9.014   Downloaded zerovec-derive v0.11.2
#12 9.075   Downloaded rand_core v0.9.5
#12 9.078   Downloaded ppv-lite86 v0.2.21
#12 9.134   Downloaded unicode-ident v1.0.22
#12 9.251   Downloaded serde_derive v1.0.228
#12 9.427   Downloaded rand_chacha v0.9.0
#12 9.552   Downloaded socket2 v0.6.2
#12 9.613   Downloaded ryu v1.0.22
#12 9.672   Downloaded proc-macro2 v1.0.106
#12 9.792   Downloaded serde_core v1.0.228
#12 9.805   Downloaded tracing-core v0.1.36
#12 9.973   Downloaded sysinfo v0.32.1
#12 10.52   Downloaded zstd-sys v2.0.16+zstd.1.5.7
#12 10.56   Downloaded typenum v1.19.0
#12 10.74   Downloaded tokio-util v0.7.18
#12 10.77   Downloaded serde_json v1.0.149
#12 10.82   Downloaded syn v2.0.114
#12 10.93   Downloaded url v2.5.8
#12 10.98   Downloaded zerovec v0.11.5
#12 11.59   Downloaded regex-automata v0.4.13
#12 11.77   Downloaded tokio v1.49.0
#12 11.87   Downloaded rayon-core v1.13.0
#12 11.88   Downloaded serde v1.0.228
#12 11.88   Downloaded rayon v1.11.0
#12 11.94   Downloaded zerotrie v0.2.3
#12 12.01   Downloaded regex-lite v0.1.8
#12 12.06   Downloaded unicode-segmentation v1.12.0
#12 12.25   Downloaded regex v1.12.2
#12 12.28   Downloaded time v0.3.46
#12 12.48   Downloaded zerocopy v0.8.35
#12 12.55   Downloaded regex-syntax v0.8.8
#12 12.61   Downloaded tracing v0.1.44
#12 12.74    Compiling proc-macro2 v1.0.106
#12 12.74    Compiling quote v1.0.44
#12 12.74    Compiling unicode-ident v1.0.22
#12 12.74    Compiling libc v0.2.180
#12 12.74    Compiling cfg-if v1.0.4
#12 12.74    Compiling smallvec v1.15.1
#12 12.74    Compiling stable_deref_trait v1.2.1
#12 12.74    Compiling log v0.4.29
#12 12.76    Compiling pin-project-lite v0.2.16
#12 12.76    Compiling serde_core v1.0.228
#12 12.76    Compiling version_check v0.9.5
#12 13.06    Compiling parking_lot_core v0.9.12
#12 13.07    Compiling memchr v2.7.6
#12 13.07    Compiling bytes v1.11.0
#12 13.24    Compiling scopeguard v1.2.0
#12 13.33    Compiling futures-core v0.3.31
#12 13.35    Compiling lock_api v0.4.14
#12 13.40    Compiling typenum v1.19.0
#12 13.42    Compiling shlex v1.3.0
#12 13.50    Compiling itoa v1.0.17
#12 13.53    Compiling find-msvc-tools v0.1.8
#12 13.53    Compiling generic-array v0.14.7
#12 13.64    Compiling litemap v0.8.1
#12 13.66    Compiling once_cell v1.21.3
#12 13.73    Compiling pkg-config v0.3.32
#12 13.74    Compiling writeable v0.6.2
#12 13.83    Compiling icu_normalizer_data v2.1.1
#12 13.89    Compiling tracing-core v0.1.36
#12 13.95    Compiling crossbeam-utils v0.8.21
#12 14.09    Compiling getrandom v0.3.4
#12 14.12    Compiling icu_properties_data v2.1.2
#12 14.26    Compiling zerocopy v0.8.35
#12 14.46    Compiling aho-corasick v1.1.4
#12 14.51    Compiling syn v2.0.114
#12 14.60    Compiling futures-sink v0.3.31
#12 14.62    Compiling percent-encoding v2.3.2
#12 14.67    Compiling regex-syntax v0.8.8
#12 14.99    Compiling errno v0.3.14
#12 15.03    Compiling jobserver v0.1.34
#12 15.24    Compiling signal-hook-registry v1.4.8
#12 15.64    Compiling cc v1.2.54
#12 15.65    Compiling parking_lot v0.12.5
#12 15.86    Compiling mio v1.1.1
#12 16.03    Compiling socket2 v0.6.2
#12 16.51    Compiling tokio v1.49.0
#12 16.58    Compiling zstd-safe v7.2.4
#12 16.88    Compiling futures-task v0.3.31
#12 17.06    Compiling local-waker v0.1.4
#12 17.24    Compiling fnv v1.0.7
#12 17.27    Compiling pin-utils v0.1.0
#12 17.34    Compiling unicode-segmentation v1.12.0
#12 17.35    Compiling alloc-no-stdlib v2.0.4
#12 17.45    Compiling serde v1.0.228
#12 18.02    Compiling crc32fast v1.5.0
#12 18.11    Compiling convert_case v0.10.0
#12 18.16    Compiling alloc-stdlib v0.2.2
#12 18.16    Compiling http v0.2.12
#12 18.34    Compiling futures-util v0.3.31
#12 18.74    Compiling regex-automata v0.4.13
#12 19.07    Compiling zstd-sys v2.0.16+zstd.1.5.7
#12 20.48    Compiling rand_core v0.9.5
#12 21.89    Compiling block-buffer v0.10.4
#12 22.35    Compiling crypto-common v0.1.7
#12 22.84    Compiling crossbeam-epoch v0.9.18
#12 24.23    Compiling hashbrown v0.16.1
#12 24.49    Compiling time-core v0.1.8
#12 24.67    Compiling adler2 v2.0.1
#12 24.93    Compiling equivalent v1.0.2
#12 25.04    Compiling synstructure v0.13.2
#12 25.15    Compiling simd-adler32 v0.3.8
#12 25.69    Compiling rayon-core v1.13.0
#12 25.97    Compiling zmij v1.0.17
#12 26.30    Compiling unicode-xid v0.2.6
#12 26.40    Compiling httparse v1.10.1
#12 26.55    Compiling num-conv v0.2.0
#12 27.16    Compiling autocfg v1.5.0
#12 27.67    Compiling regex v1.12.2
#12 28.07    Compiling semver v1.0.27
#12 28.39    Compiling ppv-lite86 v0.2.21
#12 28.67    Compiling powerfmt v0.2.0
#12 28.86    Compiling num-traits v0.2.19
#12 29.18    Compiling rustc_version v0.4.1
#12 29.22    Compiling tracing v0.1.44
#12 29.32    Compiling deranged v0.5.5
#12 29.40    Compiling rand_chacha v0.9.0
#12 29.55    Compiling bytestring v1.5.0
#12 29.69    Compiling time-macros v0.2.26
#12 29.73    Compiling indexmap v2.13.0
#12 31.12    Compiling zerofrom-derive v0.1.6
#12 31.50    Compiling yoke-derive v0.8.1
#12 32.53    Compiling zerovec-derive v0.11.2
#12 32.61    Compiling displaydoc v0.2.5
#12 33.04    Compiling tracing-attributes v0.1.31
#12 33.17    Compiling tokio-util v0.7.18
#12 33.30    Compiling serde_derive v1.0.228
#12 36.80    Compiling actix-rt v2.11.0
#12 37.53    Compiling derive_more-impl v2.1.1
#12 38.10    Compiling zerofrom v0.1.6
#12 38.50    Compiling yoke v0.8.1
#12 39.32    Compiling zerotrie v0.2.3
#12 39.41    Compiling zerovec v0.11.5
#12 39.48    Compiling miniz_oxide v0.8.9
#12 39.81    Compiling crossbeam-deque v0.8.6
#12 40.30    Compiling digest v0.10.7
#12 40.73    Compiling brotli-decompressor v5.0.0
#12 40.86    Compiling tinystr v0.8.2
#12 40.87    Compiling potential_utf v0.1.4
#12 40.99    Compiling icu_collections v2.1.1
#12 41.03    Compiling icu_locale_core v2.1.1
#12 41.09    Compiling actix-utils v3.0.1
#12 41.27    Compiling cpufeatures v0.2.17
#12 41.36    Compiling form_urlencoded v1.2.2
#12 41.91    Compiling actix-service v2.0.3
#12 42.15    Compiling cookie v0.16.2
#12 42.41    Compiling icu_provider v2.1.1
#12 42.47    Compiling utf8_iter v1.0.4
#12 42.62    Compiling bitflags v2.10.0
#12 42.70    Compiling serde_json v1.0.149
#12 43.25    Compiling icu_normalizer v2.1.1
#12 43.28    Compiling icu_properties v2.1.2
#12 43.46    Compiling utf8parse v0.2.2
#12 43.63    Compiling regex-lite v0.1.8
#12 44.21    Compiling slab v0.4.11
#12 44.43    Compiling h2 v0.3.27
#12 44.65    Compiling derive_more v2.1.1
#12 44.77    Compiling actix-router v0.5.3
#12 45.06    Compiling idna_adapter v1.2.1
#12 45.22    Compiling idna v1.1.0
#12 45.42    Compiling time v0.3.46
#12 45.64    Compiling anstyle-parse v0.2.7
#12 45.93    Compiling actix-codec v0.5.2
#12 45.96    Compiling brotli v8.0.2
#12 46.07    Compiling sha1 v0.10.6
#12 46.15    Compiling flate2 v1.1.8
#12 46.61    Compiling rustc_version_runtime v0.3.0
#12 47.08    Compiling rand v0.9.2
#12 48.21    Compiling local-channel v0.1.5
#12 48.48    Compiling socket2 v0.5.10
#12 48.87    Compiling encoding_rs v0.8.35
#12 49.81    Compiling foldhash v0.1.5
#12 50.19    Compiling language-tags v0.3.2
#12 50.83    Compiling anstyle v1.0.13
#12 51.45    Compiling mime v0.3.17
#12 51.53    Compiling ryu v1.0.22
#12 51.73    Compiling colorchoice v1.0.4
#12 51.98    Compiling anstyle-query v1.1.5
#12 52.13    Compiling httpdate v1.0.3
#12 52.17    Compiling either v1.15.0
#12 53.01    Compiling is_terminal_polyfill v1.70.2
#12 53.01    Compiling base64 v0.22.1
#12 53.17    Compiling anstream v0.6.21
#12 54.49    Compiling rayon v1.11.0
#12 54.51    Compiling serde_urlencoded v0.7.1
#12 55.44    Compiling actix-server v2.6.0
#12 59.03    Compiling actix-web-codegen v4.3.0
#12 59.81    Compiling url v2.5.8
#12 60.84    Compiling actix-macros v0.2.4
#12 61.20    Compiling env_filter v0.1.4
#12 61.93    Compiling iana-time-zone v0.1.64
#12 61.93    Compiling impl-more v0.1.9
#12 62.15    Compiling jiff v0.2.18
#12 62.21    Compiling sysinfo v0.32.1
#12 62.52    Compiling chrono v0.4.43
#12 77.94    Compiling env_logger v0.11.8
#12 82.62    Compiling zstd v0.13.3
#12 82.90    Compiling actix-http v3.11.2
#12 85.19    Compiling actix-web v4.12.1
#12 94.10    Compiling devops-info-service v1.0.0 (/app)
#12 98.58     Finished `release` profile [optimized] target(s) in 1m 37s
#12 DONE 99.7s

#13 [stage-1 3/3] COPY --from=builder /app/target/release/devops-info-service /app/devops-info-service
#13 DONE 0.3s

#14 exporting to image
#14 exporting layers
#14 exporting layers 0.2s done
#14 writing image sha256:e0cc957fccac1e0a6cbd14ec981ed83fa58f30ef3619144faa195b46086d66bf done
#14 naming to docker.io/library/devops-info-service-rust:lab02 0.0s done
#14 DONE 0.4s

View build details: docker-desktop://dashboard/build/orbstack/orbstack/814jz10nbcbmbe2iz2b5q7d3h
```

Builder stage tagged output:

```
#0 building with "orbstack" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 398B done
#1 DONE 0.0s

#2 [internal] load metadata for docker.io/library/rust:1.88-slim-bookworm
#2 DONE 0.0s

#3 [internal] load .dockerignore
#3 transferring context: 2B done
#3 DONE 0.0s

#4 [builder 1/5] FROM docker.io/library/rust:1.88-slim-bookworm
#4 DONE 0.0s

#5 [internal] load build context
#5 transferring context: 265B done
#5 DONE 0.0s

#6 [builder 2/5] WORKDIR /app
#6 CACHED

#7 [builder 4/5] COPY src ./src
#7 CACHED

#8 [builder 3/5] COPY Cargo.toml Cargo.lock ./
#8 CACHED

#9 [builder 5/5] RUN cargo build --release
#9 CACHED

#10 exporting to image
#10 exporting layers
#10 exporting layers 2.5s done
#10 writing image sha256:0e8896bff782f4e15fbd542460dac2da514960a791947084b1526ed6ab804bf7 done
#10 naming to docker.io/library/devops-info-service-rust-builder:lab02 done
#10 DONE 2.6s

View build details: docker-desktop://dashboard/build/orbstack/orbstack/46zw8g3iggus992uu5ug2pv03
```

## Run and Endpoint Tests

Docker run output:

```
fae26f8f2961d1c5abd7d31a61decbf71247cbbfb0c83a64777e27108818506f
```

Container running:

```
CONTAINER ID   IMAGE                            COMMAND                  CREATED         STATUS         PORTS                                       NAMES
fae26f8f2961   devops-info-service-rust:lab02   "/app/devops-info-se…"   3 seconds ago   Up 2 seconds   0.0.0.0:8080->8080/tcp, :::8080->8080/tcp   devops-info-service-rust
```

Endpoint test output:

```
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"Actix-web"},"system":{"hostname":"fae26f8f2961","platform":"linux","platform_version":"Linux 12 Debian GNU/Linux","architecture":"aarch64","cpu_count":11,"rust_version":"1.88.0"},"runtime":{"uptime_seconds":6,"uptime_human":"0 hours, 0 minutes","current_time":"2026-02-04T11:41:15.959867365+00:00","timezone":"UTC"},"request":{"client_ip":"192.168.215.1","user_agent":"curl/8.7.1","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}
```

```
{"status":"healthy","timestamp":"2026-02-04T11:41:19.889550949+00:00","uptime_seconds":10}
```

## Technical Analysis

- Each stage purpose: the builder stage compiles the binary; the runtime stage runs the binary on a minimal base image.

- Why multi-stage matters: it removes compilers and Cargo caches from the final image, reducing size and risk.

- Security benefits: distroless image has no shell and fewer packages, and the runtime uses a non-root user.

- Trade-offs: debugging inside a distroless container is harder, so troubleshooting is done in the builder image or via logs.

## Challenges & Solutions

- Cargo.lock required a newer Rust toolchain due to `time` crate minimum rustc version.
Solution: updated the builder base image to `rust:1.88-slim-bookworm` to match the dependency requirements.
