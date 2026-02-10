package main

import (
	"encoding/json"
	"log"
	"net"
	"net/http"
	"os"
	"runtime"
	"strings"
	"time"
)

// startTime is used to calculate service uptime.
var startTime = time.Now().UTC()

// Service describes the service metadata returned by the "/" endpoint.
type Service struct {
	Name        string `json:"name"`
	Version     string `json:"version"`
	Description string `json:"description"`
	Framework   string `json:"framework"`
}

// System describes basic system/runtime environment details.
type System struct {
	Hostname        string `json:"hostname"`
	Platform        string `json:"platform"`
	PlatformVersion string `json:"platform_version"`
	Architecture    string `json:"architecture"`
	CPUCount        int    `json:"cpu_count"`

	PythonVersion string `json:"python_version"`
}

// RuntimeInfo describes service runtime characteristics.
type RuntimeInfo struct {
	UptimeSeconds int    `json:"uptime_seconds"`
	UptimeHuman   string `json:"uptime_human"`
	CurrentTime   string `json:"current_time"`
	Timezone      string `json:"timezone"`
}

// RequestInfo describes the incoming request metadata.
type RequestInfo struct {
	ClientIP  string `json:"client_ip"`
	UserAgent string `json:"user_agent"`
	Method    string `json:"method"`
	Path      string `json:"path"`
}

// Endpoint describes an available endpoint (for the "endpoints" list).
type Endpoint struct {
	Path        string `json:"path"`
	Method      string `json:"method"`
	Description string `json:"description"`
}

// MainResponse is the JSON payload returned by GET "/".
type MainResponse struct {
	Service   Service     `json:"service"`
	System    System      `json:"system"`
	Runtime   RuntimeInfo `json:"runtime"`
	Request   RequestInfo `json:"request"`
	Endpoints []Endpoint  `json:"endpoints"`
}

// HealthResponse is the JSON payload returned by GET "/health".
type HealthResponse struct {
	Status        string `json:"status"`
	Timestamp     string `json:"timestamp"`
	UptimeSeconds int    `json:"uptime_seconds"`
}

// ErrorResponse is a consistent JSON format for errors.
type ErrorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message"`
}

func main() {
	// Read host/port from environment to match course requirement about configurability.
	host := getenv("HOST", "0.0.0.0")
	port := getenv("PORT", "8080")

	// Use a ServeMux for simple routing.
	mux := http.NewServeMux()

	mux.HandleFunc("/", indexHandler)
	mux.HandleFunc("/health", healthHandler)

	addr := net.JoinHostPort(host, port)

	// Basic server hardening: set ReadHeaderTimeout to mitigate slowloris-style header attacks.
	server := &http.Server{
		Addr:              addr,
		Handler:           withLogging(mux),
		ReadHeaderTimeout: 5 * time.Second,
	}

	log.Printf("Starting Go DevOps Info Service on http://%s\n", addr)
	if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("server error: %v", err)
	}
}

func indexHandler(w http.ResponseWriter, r *http.Request) {
	// Exact path check because "/" is a catch-all in ServeMux.
	if r.URL.Path != "/" {
		respondJSON(w, http.StatusNotFound, ErrorResponse{
			Error: "Not Found", Message: "Endpoint does not exist",
		})
		return
	}

	if r.Method != http.MethodGet {
		respondJSON(w, http.StatusMethodNotAllowed, ErrorResponse{
			Error: "Method Not Allowed", Message: "Only GET is supported",
		})
		return
	}

	uptimeSeconds, uptimeHuman := getUptime()
	sys := getSystemInfo()
	req := getRequestInfo(r)

	// Build the response payload so it matches the Python version structure.
	resp := MainResponse{
		Service: Service{
			Name:        "devops-info-service",
			Version:     "1.0.0",
			Description: "DevOps course info service",
			Framework:   "net/http (Go)",
		},
		System: sys,
		Runtime: RuntimeInfo{
			UptimeSeconds: uptimeSeconds,
			UptimeHuman:   uptimeHuman,
			CurrentTime:   time.Now().UTC().Format(time.RFC3339Nano),
			Timezone:      "UTC",
		},
		Request: req,
		Endpoints: []Endpoint{
			{Path: "/", Method: "GET", Description: "Service information"},
			{Path: "/health", Method: "GET", Description: "Health check"},
		},
	}

	// Pretty JSON helps readability and is useful for screenshots.
	respondJSONPretty(w, http.StatusOK, resp)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	// Keep strict routing behavior consistent.
	if r.URL.Path != "/health" {
		respondJSON(w, http.StatusNotFound, ErrorResponse{
			Error: "Not Found", Message: "Endpoint does not exist",
		})
		return
	}

	if r.Method != http.MethodGet {
		respondJSON(w, http.StatusMethodNotAllowed, ErrorResponse{
			Error: "Method Not Allowed", Message: "Only GET is supported",
		})
		return
	}

	uptimeSeconds, _ := getUptime()
	resp := HealthResponse{
		Status:        "healthy",
		Timestamp:     time.Now().UTC().Format(time.RFC3339Nano),
		UptimeSeconds: uptimeSeconds,
	}
	respondJSON(w, http.StatusOK, resp)
}

func getUptime() (int, string) {
	// Uptime is measured from process start.
	d := time.Since(startTime)
	secs := int(d.Seconds())
	hours := secs / 3600
	minutes := (secs % 3600) / 60
	return secs, formatUptime(hours, minutes)
}

func formatUptime(hours, minutes int) string {
	return itoa(hours) + " hours, " + itoa(minutes) + " minutes"
}

func itoa(n int) string {
	if n == 0 {
		return "0"
	}
	sign := ""
	if n < 0 {
		sign = "-"
		n = -n
	}
	var b [32]byte
	i := len(b)
	for n > 0 {
		i--
		b[i] = byte('0' + (n % 10))
		n /= 10
	}
	return sign + string(b[i:])
}

func getSystemInfo() System {
	hostname, _ := os.Hostname()
	return System{
		Hostname:        hostname,
		Platform:        runtime.GOOS,
		PlatformVersion: detectPlatformVersion(),
		Architecture:    runtime.GOARCH,
		CPUCount:        runtime.NumCPU(),
		PythonVersion:   runtime.Version(), // stored under the required JSON key
	}
}

func detectPlatformVersion() string {
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
			return strings.Trim(val, `"'`)
		}
	}
	return "unknown"
}

func getRequestInfo(r *http.Request) RequestInfo {
	return RequestInfo{
		ClientIP:  getClientIP(r),
		UserAgent: r.UserAgent(),
		Method:    r.Method,
		Path:      r.URL.Path,
	}
}

func getClientIP(r *http.Request) string {
	if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
		parts := strings.Split(xff, ",")
		return strings.TrimSpace(parts[0])
	}
	if xrip := r.Header.Get("X-Real-IP"); xrip != "" {
		return strings.TrimSpace(xrip)
	}

	// Default: parse RemoteAddr (ip:port).
	host, _, err := net.SplitHostPort(r.RemoteAddr)
	if err == nil {
		return host
	}

	// Fallback for unusual RemoteAddr formats.
	if ip := net.ParseIP(r.RemoteAddr); ip != nil {
		return r.RemoteAddr
	}
	return r.RemoteAddr
}

func respondJSON(w http.ResponseWriter, status int, payload any) {
	// Always return JSON for consistency.
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)

	enc := json.NewEncoder(w)
	_ = enc.Encode(payload)
}

func respondJSONPretty(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)

	b, err := json.MarshalIndent(payload, "", "  ")
	if err != nil {
		respondJSON(w, http.StatusInternalServerError, ErrorResponse{
			Error: "Internal Server Error", Message: "Failed to marshal JSON",
		})
		return
	}
	_, _ = w.Write(append(b, '\n'))
}

func getenv(key, def string) string {
	// Simple helper for environment-based configuration.
	v := os.Getenv(key)
	if v == "" {
		return def
	}
	return v
}

func withLogging(next http.Handler) http.Handler {
	// Minimal access logging (method, path, client IP, latency).
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next.ServeHTTP(w, r)
		log.Printf("%s %s %s (%s)", r.Method, r.URL.Path, getClientIP(r), time.Since(start))
	})
}
