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

// ServiceInfo represents the complete response structure
type ServiceInfo struct {
	Service   ServiceDetails `json:"service"`
	System    SystemInfo     `json:"system"`
	Runtime   RuntimeInfo    `json:"runtime"`
	Request   RequestInfo    `json:"request"`
	Endpoints []EndpointInfo `json:"endpoints"`
}

// ServiceDetails contains service metadata
type ServiceDetails struct {
	Name        string `json:"name"`
	Version     string `json:"version"`
	Description string `json:"description"`
	Framework   string `json:"framework"`
}

// SystemInfo contains system information
type SystemInfo struct {
	Hostname        string `json:"hostname"`
	Platform        string `json:"platform"`
	PlatformVersion string `json:"platform_version"`
	Architecture    string `json:"architecture"`
	CPUCount        int    `json:"cpu_count"`
	GoVersion       string `json:"go_version"`
}

// RuntimeInfo contains runtime metrics
type RuntimeInfo struct {
	UptimeSeconds int    `json:"uptime_seconds"`
	UptimeHuman   string `json:"uptime_human"`
	CurrentTime   string `json:"current_time"`
	Timezone      string `json:"timezone"`
}

// RequestInfo contains request details
type RequestInfo struct {
	ClientIP  string `json:"client_ip"`
	UserAgent string `json:"user_agent"`
	Method    string `json:"method"`
	Path      string `json:"path"`
}

// EndpointInfo describes an available endpoint
type EndpointInfo struct {
	Path        string `json:"path"`
	Method      string `json:"method"`
	Description string `json:"description"`
}

// HealthResponse represents the health check response
type HealthResponse struct {
	Status        string `json:"status"`
	Timestamp     string `json:"timestamp"`
	UptimeSeconds int    `json:"uptime_seconds"`
}

var (
	startTime = time.Now().UTC()
	host      = getEnv("HOST", "0.0.0.0")
	port      = getEnv("PORT", "8080")
	debug     = getEnv("DEBUG", "false") == "true"
)

// getEnv returns environment variable value or default
func getEnv(key, defaultVal string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return defaultVal
}

// getUptime returns uptime in seconds and human-readable format
func getUptime() (int, string) {
	delta := time.Since(startTime)
	seconds := int(delta.Seconds())
	hours := seconds / 3600
	minutes := (seconds % 3600) / 60

	hourLabel := "hour"
	if hours != 1 {
		hourLabel = "hours"
	}
	minuteLabel := "minute"
	if minutes != 1 {
		minuteLabel = "minutes"
	}

	return seconds, fmt.Sprintf("%d %s, %d %s", hours, hourLabel, minutes, minuteLabel)
}

// getSystemInfo collects system information
func getSystemInfo() SystemInfo {
	hostname, _ := os.Hostname()
	return SystemInfo{
		Hostname:        hostname,
		Platform:        runtime.GOOS,
		PlatformVersion: runtime.Version(),
		Architecture:    runtime.GOARCH,
		CPUCount:        runtime.NumCPU(),
		GoVersion:       strings.TrimPrefix(runtime.Version(), "go"),
	}
}

// getRequestInfo extracts information from HTTP request
func getRequestInfo(r *http.Request) RequestInfo {
	clientIP := r.RemoteAddr
	// Extract IP without port
	if idx := strings.LastIndex(clientIP, ":"); idx != -1 {
		clientIP = clientIP[:idx]
	}

	return RequestInfo{
		ClientIP:  clientIP,
		UserAgent: r.Header.Get("User-Agent"),
		Method:    r.Method,
		Path:      r.URL.Path,
	}
}

// getEndpoints returns list of available endpoints
func getEndpoints() []EndpointInfo {
	return []EndpointInfo{
		{
			Path:        "/",
			Method:      "GET",
			Description: "Service and system information",
		},
		{
			Path:        "/health",
			Method:      "GET",
			Description: "Health check endpoint",
		},
	}
}

// handleIndex handles the main endpoint
func handleIndex(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/" {
		http.NotFound(w, r)
		return
	}

	uptimeSeconds, uptimeHuman := getUptime()

	response := ServiceInfo{
		Service: ServiceDetails{
			Name:        "devops-info-service",
			Version:     "1.0.0",
			Description: "DevOps course info service",
			Framework:   "Go (http)",
		},
		System: getSystemInfo(),
		Runtime: RuntimeInfo{
			UptimeSeconds: uptimeSeconds,
			UptimeHuman:   uptimeHuman,
			CurrentTime:   time.Now().UTC().Format(time.RFC3339Nano),
			Timezone:      "UTC",
		},
		Request:   getRequestInfo(r),
		Endpoints: getEndpoints(),
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)

	if debug {
		log.Printf("Served / endpoint")
	}
}

// handleHealth handles the health check endpoint
func handleHealth(w http.ResponseWriter, r *http.Request) {
	uptimeSeconds, _ := getUptime()

	response := HealthResponse{
		Status:        "healthy",
		Timestamp:     time.Now().UTC().Format(time.RFC3339Nano),
		UptimeSeconds: uptimeSeconds,
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)

	if debug {
		log.Printf("Served /health endpoint")
	}
}

// handleNotFound handles 404 errors
func handleNotFound(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusNotFound)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"error":       "Not Found",
		"message":     "The requested endpoint does not exist",
		"status_code": 404,
		"path":        r.URL.Path,
	})
}

// notFoundHandler wraps the mux to handle 404s with JSON
type notFoundHandler struct {
	mux http.Handler
}

func (h *notFoundHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	// Check if the path is one of our valid endpoints
	if r.URL.Path != "/" && r.URL.Path != "/health" {
		handleNotFound(w, r)
		return
	}
	h.mux.ServeHTTP(w, r)
}

func main() {
	mux := http.NewServeMux()

	mux.HandleFunc("/", handleIndex)
	mux.HandleFunc("/health", handleHealth)
	fmt.Println("🚀 Starting DevOps Info Service...")
	fmt.Printf("📍 Server: http://%s:%s\n", host, port)
	fmt.Printf("📊 Debug mode: %v\n", debug)
	fmt.Printf("⏰ Started at: %s\n", startTime.Format(time.RFC3339Nano))
	fmt.Println("\nAvailable endpoints:")
	fmt.Println("  GET /       - Service and system information")
	fmt.Println("  GET /health - Health check")
	fmt.Println("\n" + strings.Repeat("=", 50) + "\n")

	// Wrap mux with 404 handler
	handler := &notFoundHandler{mux: mux}

	addr := net.JoinHostPort(host, port)

	log.Printf("Listening on %s", addr)
	if err := http.ListenAndServe(addr, handler); err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}
