// DevOps Info Service - Go Implementation
// Main application providing system information and health endpoints
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

// Service information
type Service struct {
	Name        string `json:"name"`
	Version     string `json:"version"`
	Description string `json:"description"`
	Framework   string `json:"framework"`
}

// System information
type System struct {
	Hostname        string `json:"hostname"`
	Platform        string `json:"platform"`
	PlatformVersion string `json:"platform_version"`
	Architecture    string `json:"architecture"`
	CPUCount        int    `json:"cpu_count"`
	GoVersion       string `json:"go_version"`
}

// Runtime information
type Runtime struct {
	UptimeSeconds int    `json:"uptime_seconds"`
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

// ServiceInfo is the main response structure
type ServiceInfo struct {
	Service   Service    `json:"service"`
	System    System     `json:"system"`
	Runtime   Runtime    `json:"runtime"`
	Request   Request    `json:"request"`
	Endpoints []Endpoint `json:"endpoints"`
}

// HealthResponse for health endpoint
type HealthResponse struct {
	Status        string `json:"status"`
	Timestamp     string `json:"timestamp"`
	UptimeSeconds int    `json:"uptime_seconds"`
}

// ErrorResponse for error handling
type ErrorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message"`
}

var startTime = time.Now()

func getHostname() string {
	hostname, err := os.Hostname()
	if err != nil {
		return "unknown"
	}
	return hostname
}

func getUptime() (int, string) {
	duration := time.Since(startTime)
	seconds := int(duration.Seconds())
	hours := seconds / 3600
	minutes := (seconds % 3600) / 60

	hourLabel := "hours"
	if hours == 1 {
		hourLabel = "hour"
	}
	minuteLabel := "minutes"
	if minutes == 1 {
		minuteLabel = "minute"
	}

	human := fmt.Sprintf("%d %s, %d %s", hours, hourLabel, minutes, minuteLabel)
	return seconds, human
}

func getClientIP(r *http.Request) string {
	// Check X-Forwarded-For header first
	forwarded := r.Header.Get("X-Forwarded-For")
	if forwarded != "" {
		return forwarded
	}
	// Check X-Real-IP header
	realIP := r.Header.Get("X-Real-IP")
	if realIP != "" {
		return realIP
	}
	// Fall back to RemoteAddr
	return r.RemoteAddr
}

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
			Hostname:        getHostname(),
			Platform:        runtime.GOOS,
			PlatformVersion: runtime.GOOS + "/" + runtime.GOARCH,
			Architecture:    runtime.GOARCH,
			CPUCount:        runtime.NumCPU(),
			GoVersion:       runtime.Version(),
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
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(info)
	log.Printf("Request: %s %s from %s", r.Method, r.URL.Path, getClientIP(r))
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	uptimeSeconds, _ := getUptime()

	health := HealthResponse{
		Status:        "healthy",
		Timestamp:     time.Now().UTC().Format(time.RFC3339),
		UptimeSeconds: uptimeSeconds,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(health)
}

func notFoundHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusNotFound)
	json.NewEncoder(w).Encode(ErrorResponse{
		Error:   "Not Found",
		Message: "Endpoint does not exist",
	})
}

func main() {
	// Get port from environment variable
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	// Get host from environment variable
	host := os.Getenv("HOST")
	if host == "" {
		host = "0.0.0.0"
	}

	// Register handlers
	http.HandleFunc("/", mainHandler)
	http.HandleFunc("/health", healthHandler)

	addr := fmt.Sprintf("%s:%s", host, port)
	log.Printf("DevOps Info Service starting on %s", addr)
	log.Printf("Endpoints: GET /, GET /health")

	if err := http.ListenAndServe(addr, nil); err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}
