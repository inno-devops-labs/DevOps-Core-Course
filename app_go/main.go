// DevOps Info Service - Go Implementation
// A web service providing system information and health status
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"runtime"
	"time"

	"github.com/prometheus/client_golang/prometheus/promhttp"
)

// Service metadata
type Service struct {
	Name        string `json:"name"`
	Version     string `json:"version"`
	Description string `json:"description"`
	Framework   string `json:"framework"`
}

// System information
type System struct {
	Hostname     string `json:"hostname"`
	Platform     string `json:"platform"`
	Architecture string `json:"architecture"`
	CPUCount     int    `json:"cpu_count"`
	GoVersion    string `json:"go_version"`
}

// Runtime information
type Runtime struct {
	UptimeSeconds int64  `json:"uptime_seconds"`
	UptimeHuman   string `json:"uptime_human"`
	CurrentTime   string `json:"current_time"`
	Timezone      string `json:"timezone"`
}

// Request information
type Request struct {
	ClientIP  string `json:"client_ip"`
	UserAgent string `json:"user_agent"`
	Method    string `json:"method"`
	Path      string `json:"path"`
}

// Endpoint description
type Endpoint struct {
	Path        string `json:"path"`
	Method      string `json:"method"`
	Description string `json:"description"`
}

// ServiceInfo is the full response for GET /
type ServiceInfo struct {
	Service   Service    `json:"service"`
	System    System     `json:"system"`
	Runtime   Runtime    `json:"runtime"`
	Request   Request    `json:"request"`
	Endpoints []Endpoint `json:"endpoints"`
}

// HealthResponse is the response for GET /health
type HealthResponse struct {
	Status        string `json:"status"`
	Timestamp     string `json:"timestamp"`
	UptimeSeconds int64  `json:"uptime_seconds"`
}

// ErrorResponse for error handling
type ErrorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message"`
}

var startTime = time.Now()

func initFilePath() string {
	path := os.Getenv("INIT_FILE_PATH")
	if path == "" {
		return "/data/index.html"
	}
	return path
}

// getHostname returns the system hostname
func getHostname() string {
	hostname, err := os.Hostname()
	if err != nil {
		return "unknown"
	}
	return hostname
}

// getUptime returns uptime in seconds and human-readable format
func getUptime() (int64, string) {
	elapsed := time.Since(startTime)
	seconds := int64(elapsed.Seconds())
	hours := seconds / 3600
	minutes := (seconds % 3600) / 60

	hourStr := "hours"
	if hours == 1 {
		hourStr = "hour"
	}
	minStr := "minutes"
	if minutes == 1 {
		minStr = "minute"
	}

	human := fmt.Sprintf("%d %s, %d %s", hours, hourStr, minutes, minStr)
	return seconds, human
}

// getClientIP extracts client IP from request
func getClientIP(r *http.Request) string {
	// Check X-Forwarded-For header first (for proxies)
	forwarded := r.Header.Get("X-Forwarded-For")
	if forwarded != "" {
		return forwarded
	}
	// Fall back to RemoteAddr
	return r.RemoteAddr
}

// mainHandler handles GET /
func mainHandler(w http.ResponseWriter, r *http.Request) {
	// Only handle root path
	if r.URL.Path != "/" {
		notFoundHandler(w, r)
		return
	}

	uptimeSeconds, uptimeHuman := getUptime()

	info := ServiceInfo{
		Service: Service{
			Name:        "devops-info-service",
			Version:     "1.0.0",
			Description: "DevOps course info service",
			Framework:   "net/http",
		},
		System: System{
			Hostname:     getHostname(),
			Platform:     runtime.GOOS,
			Architecture: runtime.GOARCH,
			CPUCount:     runtime.NumCPU(),
			GoVersion:    runtime.Version(),
		},
		Runtime: Runtime{
			UptimeSeconds: uptimeSeconds,
			UptimeHuman:   uptimeHuman,
			CurrentTime:   time.Now().UTC().Format(time.RFC3339),
			Timezone:      "UTC",
		},
		Request: Request{
			ClientIP:  getClientIP(r),
			UserAgent: r.Header.Get("User-Agent"),
			Method:    r.Method,
			Path:      r.URL.Path,
		},
		Endpoints: []Endpoint{
			{Path: "/", Method: "GET", Description: "Service information"},
			{Path: "/health", Method: "GET", Description: "Health check"},
			{Path: "/init-file", Method: "GET", Description: "Content downloaded by init container"},
			{Path: "/metrics", Method: "GET", Description: "Prometheus metrics"},
		},
	}

	log.Printf("Request: %s %s from %s", r.Method, r.URL.Path, getClientIP(r))

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(info)
}

// healthHandler handles GET /health
func healthHandler(w http.ResponseWriter, r *http.Request) {
	uptimeSeconds, _ := getUptime()

	health := HealthResponse{
		Status:        "healthy",
		Timestamp:     time.Now().UTC().Format(time.RFC3339),
		UptimeSeconds: uptimeSeconds,
	}

	log.Printf("Health check from %s", getClientIP(r))

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(health)
}

// initFileHandler returns the file prepared by the init container.
func initFileHandler(w http.ResponseWriter, r *http.Request) {
	content, err := os.ReadFile(initFilePath())
	if err != nil {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusNotFound)
		json.NewEncoder(w).Encode(ErrorResponse{
			Error:   "Init file not found",
			Message: err.Error(),
		})
		return
	}

	w.Header().Set("Content-Type", "text/plain; charset=utf-8")
	w.Write(content)
}

// notFoundHandler handles 404 errors
func notFoundHandler(w http.ResponseWriter, r *http.Request) {
	log.Printf("404 Not Found: %s", r.URL.Path)

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusNotFound)
	json.NewEncoder(w).Encode(ErrorResponse{
		Error:   "Not Found",
		Message: "Endpoint does not exist",
	})
}

func registerHandlers(mux *http.ServeMux) {
	mux.HandleFunc("/", mainHandler)
	mux.HandleFunc("/health", healthHandler)
	mux.HandleFunc("/init-file", initFileHandler)
	mux.Handle("/metrics", promhttp.Handler())
}

func main() {
	// Configuration from environment variables
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	host := os.Getenv("HOST")
	if host == "" {
		host = "0.0.0.0"
	}

	addr := fmt.Sprintf("%s:%s", host, port)

	mux := http.NewServeMux()
	registerHandlers(mux)

	log.Printf("Starting DevOps Info Service (Go) on %s", addr)

	if err := http.ListenAndServe(addr, mux); err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}
