package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net"
	"net/http"
	"os"
	"runtime"
	"time"
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
	Hostname       string `json:"hostname"`
	Platform       string `json:"platform"`
	PlatformVersion string `json:"platform_version"`
	Architecture   string `json:"architecture"`
	CPUCount       int    `json:"cpu_count"`
	GoVersion      string `json:"go_version"`
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

// Endpoint metadata
type Endpoint struct {
	Path        string `json:"path"`
	Method      string `json:"method"`
	Description string `json:"description"`
}

// Complete service response
type ServiceInfo struct {
	Service   Service    `json:"service"`
	System    System     `json:"system"`
	Runtime   Runtime    `json:"runtime"`
	Request   Request    `json:"request"`
	Endpoints []Endpoint `json:"endpoints"`
}

// Health response
type HealthResponse struct {
	Status       string `json:"status"`
	Timestamp    string `json:"timestamp"`
	UptimeSeconds int   `json:"uptime_seconds"`
}

// Error response
type ErrorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message"`
}

var startTime = time.Now()

// getUptime calculates application uptime
func getUptime() Runtime {
	delta := time.Since(startTime)
	seconds := int(delta.Seconds())
	hours := seconds / 3600
	minutes := (seconds % 3600) / 60
	secs := seconds % 60

	var human string
	if hours > 0 {
		human = fmt.Sprintf("%d hour%s, %d minute%s", hours, plural(hours), minutes, plural(minutes))
	} else if minutes > 0 {
		human = fmt.Sprintf("%d minute%s, %d second%s", minutes, plural(minutes), secs, plural(secs))
	} else {
		human = fmt.Sprintf("%d second%s", secs, plural(secs))
	}

	return Runtime{
		UptimeSeconds: seconds,
		UptimeHuman:   human,
		CurrentTime:   time.Now().UTC().Format(time.RFC3339),
		Timezone:      "UTC",
	}
}

// plural returns 's' if n != 1, empty string otherwise
func plural(n int) string {
	if n != 1 {
		return "s"
	}
	return ""
}

// getSystemInfo collects system information
func getSystemInfo() System {
	hostname, _ := os.Hostname()
	return System{
		Hostname:        hostname,
		Platform:        runtime.GOOS,
		PlatformVersion: "unknown", // Platform version varies by OS
		Architecture:    runtime.GOARCH,
		CPUCount:        runtime.NumCPU(),
		GoVersion:       runtime.Version(),
	}
}

// getRequestInfo collects request information
func getRequestInfo(r *http.Request) Request {
	// Get client IP, handle X-Forwarded-For for proxies
	clientIP := r.RemoteAddr
	if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
		clientIP = xff
	}

	// Remove port if present
	if host, _, err := net.SplitHostPort(clientIP); err == nil {
		clientIP = host
	}

	return Request{
		ClientIP:  clientIP,
		UserAgent: r.Header.Get("User-Agent"),
		Method:    r.Method,
		Path:      r.URL.Path,
	}
}

// mainHandler handles the main endpoint
func mainHandler(w http.ResponseWriter, r *http.Request) {
	uptime := getUptime()
	info := ServiceInfo{
		Service: Service{
			Name:        "devops-info-service",
			Version:     "1.0.0",
			Description: "DevOps course info service",
			Framework:   "Go net/http",
		},
		System:    getSystemInfo(),
		Runtime:   uptime,
		Request:   getRequestInfo(r),
		Endpoints: []Endpoint{
			{Path: "/", Method: "GET", Description: "Service information"},
			{Path: "/health", Method: "GET", Description: "Health check"},
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(info)
	log.Printf("Serving info request from %s", r.RemoteAddr)
}

// healthHandler handles health check endpoint
func healthHandler(w http.ResponseWriter, r *http.Request) {
	uptime := getUptime()
	response := HealthResponse{
		Status:        "healthy",
		Timestamp:     time.Now().UTC().Format(time.RFC3339),
		UptimeSeconds: uptime.UptimeSeconds,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// errorHandler handles 404 errors
func errorHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusNotFound)
	json.NewEncoder(w).Encode(ErrorResponse{
		Error:   "Not Found",
		Message: "Endpoint does not exist",
	})
}

func main() {
	// Configuration from environment variables
	host := getEnv("HOST", "0.0.0.0")
	port := getEnv("PORT", "8080")
	addr := net.JoinHostPort(host, port)

	// Set up handlers
	http.HandleFunc("/", mainHandler)
	http.HandleFunc("/health", healthHandler)

	// Log startup
	log.Printf("Starting DevOps Info Service on %s", addr)
	log.Printf("Go version: %s", runtime.Version())
	log.Printf("Platform: %s/%s", runtime.GOOS, runtime.GOARCH)
	log.Printf("CPU count: %d", runtime.NumCPU())

	// Start server
	if err := http.ListenAndServe(addr, nil); err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}

// getEnv gets environment variable with fallback
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
