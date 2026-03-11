package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"runtime"
	"time"
)

// LogEntry represents a structured log entry
type LogEntry struct {
	Level     string `json:"level"`
	Message   string `json:"message"`
	Time      string `json:"time"`
	Service   string `json:"service,omitempty"`
	Version   string `json:"version,omitempty"`
	Method    string `json:"method,omitempty"`
	Path      string `json:"path,omitempty"`
	ClientIP  string `json:"client_ip,omitempty"`
	UserAgent string `json:"user_agent,omitempty"`
}

// logJSON logs a structured JSON message
func logJSON(entry LogEntry) {
	entry.Time = time.Now().UTC().Format(time.RFC3339)
	if err := json.NewEncoder(os.Stdout).Encode(entry); err != nil {
		log.Printf("Error encoding log: %v", err)
	}
}

// Service application start time for uptime calculation.
var startTime = time.Now().UTC()

// Service contains application metadata.
type Service struct {
	Name        string `json:"name"`
	Version     string `json:"version"`
	Description string `json:"description"`
	Framework   string `json:"framework"`
}

// SystemInfo contains static system information.
type SystemInfo struct {
	Hostname        string `json:"hostname"`
	Platform        string `json:"platform"`
	PlatformVersion string `json:"platform_version"`
	Architecture    string `json:"architecture"`
	CPUCount        int    `json:"cpu_count"`
	GoVersion       string `json:"go_version"`
}

// RuntimeInfo contains uptime and temporal data.
type RuntimeInfo struct {
	UptimeSeconds int64  `json:"uptime_seconds"`
	UptimeHuman   string `json:"uptime_human"`
	CurrentTime   string `json:"current_time"`
	Timezone      string `json:"timezone"`
}

// RequestInfo contains request metadata.
type RequestInfo struct {
	ClientIP  string `json:"client_ip"`
	UserAgent string `json:"user_agent"`
	Method    string `json:"method"`
	Path      string `json:"path"`
}

// FullResponse is the main response structure for the / endpoint.
type FullResponse struct {
	Service   Service             `json:"service"`
	System    SystemInfo          `json:"system"`
	Runtime   RuntimeInfo         `json:"runtime"`
	Request   RequestInfo         `json:"request"`
	Endpoints []map[string]string `json:"endpoints"`
}

// uptime returns uptime in seconds and human readable string.
func uptime() (int64, string) {
	secs := int64(time.Since(startTime).Seconds())
	h := secs / 3600
	m := (secs % 3600) / 60
	human := fmt.Sprintf("%d hour%s, %d minute%s", h, pluralize(h), m, pluralize(m))
	return secs, human
}

// pluralize returns "s" if n != 1, else empty string.
func pluralize(n int64) string {
	if n != 1 {
		return "s"
	}
	return ""
}

// mainHandler handles GET / request with service and system information.
func mainHandler(w http.ResponseWriter, r *http.Request) {
	logJSON(LogEntry{
		Level:     "info",
		Message:   "HTTP Request to index",
		Method:    r.Method,
		Path:      r.URL.Path,
		ClientIP:  r.RemoteAddr,
		UserAgent: r.UserAgent(),
	})

	hostname, _ := os.Hostname()
	secs, human := uptime()
	resp := FullResponse{
		Service: Service{
			Name:        "devops-info-service",
			Version:     "1.0.0",
			Description: "DevOps course info service",
			Framework:   "Go net/http",
		},
		System: SystemInfo{
			Hostname:        hostname,
			Platform:        runtime.GOOS,
			PlatformVersion: runtime.GOARCH,
			Architecture:    runtime.GOARCH,
			CPUCount:        runtime.NumCPU(),
			GoVersion:       runtime.Version(),
		},
		Runtime: RuntimeInfo{
			UptimeSeconds: secs,
			UptimeHuman:   human,
			CurrentTime:   time.Now().UTC().Format(time.RFC3339),
			Timezone:      "UTC",
		},
		Request: RequestInfo{
			ClientIP:  r.RemoteAddr,
			UserAgent: r.UserAgent(),
			Method:    r.Method,
			Path:      r.URL.Path,
		},
		Endpoints: []map[string]string{
			{"path": "/", "method": "GET", "description": "Service information"},
			{"path": "/health", "method": "GET", "description": "Health check"},
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

// healthHandler handles GET /health request (Kubernetes readiness/liveness probes).
func healthHandler(w http.ResponseWriter, r *http.Request) {
	logJSON(LogEntry{
		Level:     "info",
		Message:   "HTTP Request to health",
		Method:    r.Method,
		Path:      r.URL.Path,
		ClientIP:  r.RemoteAddr,
		UserAgent: r.UserAgent(),
	})

	secs, _ := uptime()

	// Define health response structure inline.
	type H struct {
		Status        string `json:"status"`
		Timestamp     string `json:"timestamp"`
		UptimeSeconds int64  `json:"uptime_seconds"`
	}

	h := H{
		Status:        "healthy",
		Timestamp:     time.Now().UTC().Format(time.RFC3339),
		UptimeSeconds: secs,
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(h)
}

// main starts the HTTP server on configured port.
func main() {
	logJSON(LogEntry{
		Level:   "info",
		Message: "Starting DevOps Info Service",
		Service: "devops-info-service",
		Version: "1.0.0",
	})

	http.HandleFunc("/", mainHandler)
	http.HandleFunc("/health", healthHandler)
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	logJSON(LogEntry{
		Level:   "info",
		Message: "Server starting",
		Service: "devops-info-service",
	})

	http.ListenAndServe(":"+port, nil)
}
