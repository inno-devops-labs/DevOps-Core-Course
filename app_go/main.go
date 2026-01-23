package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net"
	"net/http"
	"os"
	"runtime"
	"sort"
	"strings"
	"time"
)

// Service describes metadata about the running service.
type Service struct {
	Name        string `json:"name"`
	Version     string `json:"version"`
	Description string `json:"description"`
	Framework   string `json:"framework"`
}

// System contains basic host and runtime details.
type System struct {
	Hostname        string `json:"hostname"`
	Platform        string `json:"platform"`
	PlatformVersion string `json:"platform_version"`
	Architecture    string `json:"architecture"`
	CPUCount        int    `json:"cpu_count"`
	GoVersion       string `json:"go_version"`
}

// RuntimeInfo reports uptime and current timestamp.
type RuntimeInfo struct {
	UptimeSeconds int    `json:"uptime_seconds"`
	UptimeHuman   string `json:"uptime_human"`
	CurrentTime   string `json:"current_time"`
	Timezone      string `json:"timezone"`
}

// RequestInfo captures request metadata.
type RequestInfo struct {
	ClientIP  string `json:"client_ip"`
	UserAgent string `json:"user_agent"`
	Method    string `json:"method"`
	Path      string `json:"path"`
}

// Endpoint represents a single API route.
type Endpoint struct {
	Method      string `json:"method"`
	Path        string `json:"path"`
	Description string `json:"description"`
}

// RootResponse is the response schema for the root endpoint.
type RootResponse struct {
	Service   Service     `json:"service"`
	System    System      `json:"system"`
	Runtime   RuntimeInfo `json:"runtime"`
	Request   RequestInfo `json:"request"`
	Endpoints []Endpoint  `json:"endpoints"`
}

// HealthResponse is the response schema for /health.
type HealthResponse struct {
	Status        string `json:"status"`
	Timestamp     string `json:"timestamp"`
	UptimeSeconds int    `json:"uptime_seconds"`
}

// ErrorResponse is a JSON error payload for non-200 responses.
type ErrorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message"`
}

// routeKey uniquely identifies a route by method and path.
type routeKey struct {
	Method string
	Path   string
}

// route binds a handler with route metadata.
type route struct {
	Method      string
	Path        string
	Description string
	Handler     http.HandlerFunc
}

// router is a tiny HTTP router for exact method+path matches.
type router struct {
	routes    map[routeKey]route
	endpoints []Endpoint
}

// newRouter initializes an empty router instance.
func newRouter() *router {
	return &router{
		routes:    make(map[routeKey]route),
		endpoints: make([]Endpoint, 0),
	}
}

// Handle registers a handler for an exact HTTP method and path.
func (rt *router) Handle(method, path, description string, h http.HandlerFunc) {
	key := routeKey{Method: method, Path: path}
	rt.routes[key] = route{
		Method:      method,
		Path:        path,
		Description: description,
		Handler:     h,
	}

	rt.endpoints = append(rt.endpoints, Endpoint{
		Method:      method,
		Path:        path,
		Description: description,
	})
}

// Endpoints returns a sorted copy of the registered endpoints list.
func (rt *router) Endpoints() []Endpoint {
	out := make([]Endpoint, len(rt.endpoints))
	copy(out, rt.endpoints)
	sort.Slice(out, func(i, j int) bool {
		if out[i].Path == out[j].Path {
			return out[i].Method < out[j].Method
		}
		return out[i].Path < out[j].Path
	})
	return out
}

// ServeHTTP dispatches the request to a registered route or returns a 404 JSON error.
// Note: method mismatch is treated as "not found" in this simplified router.
func (rt *router) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	key := routeKey{Method: r.Method, Path: r.URL.Path}
	if rr, ok := rt.routes[key]; ok {
		rr.Handler(w, r)
		return
	}

	writeJSON(w, http.StatusNotFound, ErrorResponse{
		Error:   "Not Found",
		Message: "Endpoint does not exist",
	})
}

var (
	// startTime is captured once at startup and used to compute uptime.
	startTime = time.Now().UTC()

	// service contains static service metadata returned by the root endpoint.
	service = Service{
		Name:        "devops-info-service",
		Version:     "1.0.0",
		Description: "DevOps course info service",
		Framework:   "Go net/http",
	}
)

// systemInfo collects basic system/runtime information.
func systemInfo() System {
	hostname, _ := os.Hostname()

	return System{
		Hostname:        hostname,
		Platform:        runtime.GOOS,
		PlatformVersion: linuxKernelRelease(),
		Architecture:    runtime.GOARCH,
		CPUCount:        runtime.NumCPU(),
		GoVersion:       runtime.Version(),
	}
}

// runtimeInfo computes uptime and generates a UTC timestamp in ISO 8601 format.
func runtimeInfo() RuntimeInfo {
	now := time.Now().UTC()
	uptime := now.Sub(startTime)

	seconds := int(uptime.Seconds())
	hours := seconds / 3600
	minutes := (seconds % 3600) / 60

	return RuntimeInfo{
		UptimeSeconds: seconds,
		UptimeHuman:   fmt.Sprintf("%d hour, %d minutes", hours, minutes),
		CurrentTime:   now.Format("2006-01-02T15:04:05Z"),
		Timezone:      "UTC",
	}
}

// requestInfo extracts request metadata for the JSON response payload.
func requestInfo(r *http.Request) RequestInfo {
	return RequestInfo{
		ClientIP:  clientIP(r),
		UserAgent: r.UserAgent(),
		Method:    r.Method,
		Path:      r.URL.Path,
	}
}

// clientIP returns the best-effort client IP address.
// If behind a proxy, the first X-Forwarded-For value is preferred.
func clientIP(r *http.Request) string {
	xff := r.Header.Get("X-Forwarded-For")
	if xff != "" {
		parts := strings.Split(xff, ",")
		if len(parts) > 0 {
			return strings.TrimSpace(parts[0])
		}
	}

	host, _, err := net.SplitHostPort(r.RemoteAddr)
	if err == nil && host != "" {
		return host
	}
	return r.RemoteAddr
}

// linuxKernelRelease reads Linux kernel release from /proc as a best-effort value.
// On non-Linux platforms (or if the file is missing), it returns an empty string.
func linuxKernelRelease() string {
	if runtime.GOOS != "linux" {
		return ""
	}
	b, err := os.ReadFile("/proc/sys/kernel/osrelease")
	if err != nil {
		return ""
	}
	return strings.TrimSpace(string(b))
}

// writeJSON writes a JSON response with the given HTTP status code.
func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}

type statusWriter struct {
	http.ResponseWriter
	status int
}

// WriteHeader captures the status code for logging.
func (sw *statusWriter) WriteHeader(code int) {
	sw.status = code
	sw.ResponseWriter.WriteHeader(code)
}

// loggingMiddleware logs request metadata and the final status code.
func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		sw := &statusWriter{ResponseWriter: w, status: http.StatusOK}
		next.ServeHTTP(sw, r)

		lat := time.Since(start)
		log.Printf("Request %s %s from %s UA=%s -> %d (%s)",
			r.Method,
			r.URL.Path,
			clientIP(r),
			r.UserAgent(),
			sw.status,
			lat,
		)
	})
}

// recoverMiddleware converts panics into a JSON 500 response.
func recoverMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if rec := recover(); rec != nil {
				log.Printf("ERROR 500 Internal Server Error: %v", rec)
				writeJSON(w, http.StatusInternalServerError, ErrorResponse{
					Error:   "Internal Server Error",
					Message: "An unexpected error occurred",
				})
			}
		}()
		next.ServeHTTP(w, r)
	})
}

// rootHandler returns the service diagnostic payload.
func rootHandler(rt *router) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		payload := RootResponse{
			Service:   service,
			System:    systemInfo(),
			Runtime:   runtimeInfo(),
			Request:   requestInfo(r),
			Endpoints: rt.Endpoints(),
		}
		writeJSON(w, http.StatusOK, payload)
	}
}

// healthHandler returns a minimal health probe response (HTTP 200 on success).
func healthHandler(w http.ResponseWriter, r *http.Request) {
	rt := runtimeInfo()
	writeJSON(w, http.StatusOK, HealthResponse{
		Status:        "healthy",
		Timestamp:     rt.CurrentTime,
		UptimeSeconds: rt.UptimeSeconds,
	})
}

// crashHandler intentionally panics to verify 500 error handling.
// func crashHandler(w http.ResponseWriter, r *http.Request) {
// 	panic("crash test")
// }

func main() {
	host := os.Getenv("HOST")
	if host == "" {
		host = "0.0.0.0"
	}
	port := os.Getenv("PORT")
	if port == "" {
		port = "5000"
	}
	debug := strings.ToLower(os.Getenv("DEBUG")) == "true"

	if debug {
		log.SetFlags(log.LstdFlags | log.Lmicroseconds)
		log.Println("DEBUG enabled")
	} else {
		log.SetFlags(log.LstdFlags)
	}

	rt := newRouter()
	rt.Handle(http.MethodGet, "/", "Root endpoint: returns service metadata and diagnostic information.", rootHandler(rt))
	rt.Handle(http.MethodGet, "/health", "Health check endpoint for monitoring and Kubernetes probes.", healthHandler)
	// rt.Handle(http.MethodGet, "/crash", "Intentional error to test 500 handler.", crashHandler) 


	handler := recoverMiddleware(loggingMiddleware(rt))

	addr := net.JoinHostPort(host, port)
	log.Printf("Listening on http://%s", addr)

	srv := &http.Server{
		Addr:              addr,
		Handler:           handler,
		ReadHeaderTimeout: 5 * time.Second,
	}

	log.Fatal(srv.ListenAndServe())
}
