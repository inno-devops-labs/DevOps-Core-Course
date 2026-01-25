package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net"
	"net/http"
	"os"
	"runtime"
	"strings"
	"time"
)

type ServiceInfo struct {
	Service   Service     `json:"service"`
	System    System      `json:"system"`
	Runtime   RuntimeInfo `json:"runtime"`
	Request   RequestInfo `json:"request"`
	Endpoints []Endpoint  `json:"endpoints"`
}

type Service struct {
	Name        string `json:"name"`
	Version     string `json:"version"`
	Description string `json:"description"`
	Framework   string `json:"framework"`
}

type System struct {
	Hostname        string `json:"hostname"`
	Platform        string `json:"platform"`
	PlatformVersion string `json:"platform_version"`
	Architecture    string `json:"architecture"`
	CPUCount        int    `json:"cpu_count"`
	GoVersion       string `json:"go_version"`
}

type RuntimeInfo struct {
	UptimeSeconds int    `json:"uptime_seconds"`
	UptimeHuman   string `json:"uptime_human"`
	CurrentTime   string `json:"current_time"`
	Timezone      string `json:"timezone"`
}

type RequestInfo struct {
	ClientIP  string `json:"client_ip"`
	UserAgent string `json:"user_agent"`
	Method    string `json:"method"`
	Path      string `json:"path"`
}

type Endpoint struct {
	Path        string `json:"path"`
	Method      string `json:"method"`
	Description string `json:"description"`
}

type ErrorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message"`
}

var startTime = time.Now().UTC()

func main() {
	host := getenv("HOST", "0.0.0.0")
	port := getenv("PORT", "8080")
	debug := strings.ToLower(getenv("DEBUG", "false")) == "true"

	logger := log.New(os.Stdout, "", log.LstdFlags)
	if debug {
		logger.SetFlags(log.LstdFlags | log.Lshortfile)
	}

	mux := http.NewServeMux()

	// endpoints
	mux.HandleFunc("/", mainHandler)
	mux.HandleFunc("/health", healthHandler)

	// wrap with middleware: recover + logging + 404
	handler := withRecover(logger)(withLogging(logger)(withNotFound(mux)))

	addr := fmt.Sprintf("%s:%s", host, port)
	logger.Printf("Application starting on http://%s\n", addr)

	// http.Server allows timeouts (good practice)
	srv := &http.Server{
		Addr:              addr,
		Handler:           handler,
		ReadHeaderTimeout: 5 * time.Second,
	}

	if err := srv.ListenAndServe(); err != nil {
		logger.Fatalf("server error: %v", err)
	}
}

func mainHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/" {
		// will be caught by notFound wrapper, but this is extra safety
		writeJSON(w, http.StatusNotFound, ErrorResponse{
			Error:   "Not Found",
			Message: "Endpoint does not exist",
		})
		return
	}

	info := ServiceInfo{
		Service: Service{
			Name:        "devops-info-service",
			Version:     "1.0.0",
			Description: "DevOps course info service",
			Framework:   "Go net/http",
		},
		System: System{
			Hostname:        hostname(),
			Platform:        runtime.GOOS,
			PlatformVersion: platformVersion(),
			Architecture:    runtime.GOARCH,
			CPUCount:        runtime.NumCPU(),
			GoVersion:       runtime.Version(),
		},
		Runtime: runtimeInfo(),
		Request: requestInfo(r),
		Endpoints: []Endpoint{
			{Path: "/", Method: "GET", Description: "Service information"},
			{Path: "/health", Method: "GET", Description: "Health check"},
		},
	}

	writeJSON(w, http.StatusOK, info)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	uptimeSeconds, _ := uptime()
	resp := map[string]any{
		"status":         "healthy",
		"timestamp":      isoUTCNow(),
		"uptime_seconds": uptimeSeconds,
	}
	writeJSON(w, http.StatusOK, resp)
}

func runtimeInfo() RuntimeInfo {
	secs, human := uptime()
	return RuntimeInfo{
		UptimeSeconds: secs,
		UptimeHuman:   human,
		CurrentTime:   isoUTCNow(),
		Timezone:      "UTC",
	}
}

func requestInfo(r *http.Request) RequestInfo {
	ip := clientIP(r)
	ua := r.Header.Get("User-Agent")
	return RequestInfo{
		ClientIP:  ip,
		UserAgent: ua,
		Method:    r.Method,
		Path:      r.URL.Path,
	}
}

func uptime() (int, string) {
	delta := time.Since(startTime)
	seconds := int(delta.Seconds())
	hours := seconds / 3600
	minutes := (seconds % 3600) / 60
	return seconds, fmt.Sprintf("%d hours, %d minutes", hours, minutes)
}

func isoUTCNow() string {
	// "2026-01-07T14:30:00.000Z"
	return time.Now().UTC().Format("2006-01-02T15:04:05.000Z")
}

func hostname() string {
	h, err := os.Hostname()
	if err != nil {
		return "unknown"
	}
	return h
}

func platformVersion() string {
	// Best effort for Linux: /etc/os-release PRETTY_NAME (e.g., "Ubuntu 24.04.1 LTS")
	if runtime.GOOS != "linux" {
		return "unknown"
	}
	data, err := os.ReadFile("/etc/os-release")
	if err != nil {
		return "unknown"
	}
	lines := strings.Split(string(data), "\n")
	for _, line := range lines {
		if strings.HasPrefix(line, "PRETTY_NAME=") {
			val := strings.TrimPrefix(line, "PRETTY_NAME=")
			val = strings.Trim(val, `"`)
			if val != "" {
				return val
			}
		}
	}
	return "unknown"
}

func clientIP(r *http.Request) string {
	// If behind proxy, you might consider X-Forwarded-For, but for lab keep it simple.
	host, _, err := net.SplitHostPort(r.RemoteAddr)
	if err == nil && host != "" {
		return host
	}
	// fallback: may already be just an IP
	return r.RemoteAddr
}

func writeJSON(w http.ResponseWriter, statusCode int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	_ = json.NewEncoder(w).Encode(payload)
}

func getenv(key, def string) string {
	v := os.Getenv(key)
	if v == "" {
		return def
	}
	return v
}

/* ---------------- Middleware (Best Practices) ---------------- */

func withLogging(logger *log.Logger) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			start := time.Now()
			next.ServeHTTP(w, r)
			logger.Printf("%s %s (%s) from %s in %s",
				r.Method, r.URL.Path, r.Proto, r.RemoteAddr, time.Since(start))
		})
	}
}

func withRecover(logger *log.Logger) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			defer func() {
				if rec := recover(); rec != nil {
					logger.Printf("panic recovered: %v", rec)
					writeJSON(w, http.StatusInternalServerError, ErrorResponse{
						Error:   "Internal Server Error",
						Message: "An unexpected error occurred",
					})
				}
			}()
			next.ServeHTTP(w, r)
		})
	}
}

func withNotFound(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Use ServeMux; if it doesn't match, it still calls handler with pattern "/"
		// So we enforce our own 404 for unknown endpoints.
		if r.URL.Path != "/" && r.URL.Path != "/health" {
			writeJSON(w, http.StatusNotFound, ErrorResponse{
				Error:   "Not Found",
				Message: "Endpoint does not exist",
			})
			return
		}
		next.ServeHTTP(w, r)
	})
}
