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

// Application start time for uptime calculation
var startTime = time.Now()

// Service metadata structure
type Service struct {
	Name        string `json:"name"`
	Version     string `json:"version"`
	Description string `json:"description"`
	Framework   string `json:"framework"`
}

// System information structure
type System struct {
	Hostname        string `json:"hostname"`
	Platform        string `json:"platform"`
	PlatformVersion string `json:"platform_version"`
	Architecture    string `json:"architecture"`
	CPUCount        int    `json:"cpu_count"`
	GoVersion       string `json:"go_version"`
}

// Runtime information structure
type Runtime struct {
	UptimeSeconds int    `json:"uptime_seconds"`
	UptimeHuman   string `json:"uptime_human"`
	CurrentTime   string `json:"current_time"`
	Timezone      string `json:"timezone"`
}

// Request information structure
type Request struct {
	ClientIP  string `json:"client_ip"`
	UserAgent string `json:"user_agent"`
	Method    string `json:"method"`
	Path      string `json:"path"`
}

// Endpoint information structure
type Endpoint struct {
	Path        string `json:"path"`
	Method      string `json:"method"`
	Description string `json:"description"`
}

// Complete service information structure
type ServiceInfo struct {
	Service   Service    `json:"service"`
	System    System     `json:"system"`
	Runtime   Runtime    `json:"runtime"`
	Request   Request    `json:"request"`
	Endpoints []Endpoint `json:"endpoints"`
}

// Health check response structure
type HealthResponse struct {
	Status        string `json:"status"`
	Timestamp     string `json:"timestamp"`
	UptimeSeconds int    `json:"uptime_seconds"`
}

// Calculate uptime information
func getUptime() (int, string) {
	elapsed := time.Since(startTime)
	seconds := int(elapsed.Seconds())
	hours := seconds / 3600
	minutes := (seconds % 3600) / 60
	return seconds, fmt.Sprintf("%d hours, %d minutes", hours, minutes)
}

// Get system hostname
func getHostname() string {
	hostname, err := os.Hostname()
	if err != nil {
		log.Printf("Error getting hostname: %v", err)
		return "unknown"
	}
	return hostname
}

// Get client IP address
func getClientIP(r *http.Request) string {
	// Try X-Forwarded-For header first (for proxy/load balancer)
	forwarded := r.Header.Get("X-Forwarded-For")
	if forwarded != "" {
		return forwarded
	}
	return r.RemoteAddr
}

// Main endpoint handler
func mainHandler(w http.ResponseWriter, r *http.Request) {
	log.Printf("Request: %s %s from %s", r.Method, r.URL.Path, getClientIP(r))

	// Only respond to root path
	if r.URL.Path != "/" {
		http.NotFound(w, r)
		return
	}

	uptimeSeconds, uptimeHuman := getUptime()
	location, _ := time.Now().Local().Zone()

	info := ServiceInfo{
		Service: Service{
			Name:        "devops-info-service",
			Version:     "1.0.0",
			Description: "DevOps course info service",
			Framework:   "Go net/http",
		},
		System: System{
			Hostname:        getHostname(),
			Platform:        runtime.GOOS,
			PlatformVersion: runtime.Version(),
			Architecture:    runtime.GOARCH,
			CPUCount:        runtime.NumCPU(),
			GoVersion:       runtime.Version(),
		},
		Runtime: Runtime{
			UptimeSeconds: uptimeSeconds,
			UptimeHuman:   uptimeHuman,
			CurrentTime:   time.Now().Format(time.RFC3339),
			Timezone:      location,
		},
		Request: Request{
			ClientIP:  getClientIP(r),
			UserAgent: r.UserAgent(),
			Method:    r.Method,
			Path:      r.URL.Path,
		},
		Endpoints: []Endpoint{
			{Path: "/", Method: "GET", Description: "Service information"},
			{Path: "/health", Method: "GET", Description: "Health check"},
		},
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	
	encoder := json.NewEncoder(w)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(info); err != nil {
		log.Printf("Error encoding JSON: %v", err)
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
	}
}

// Health check endpoint handler
func healthHandler(w http.ResponseWriter, r *http.Request) {
	log.Printf("Health check from %s", getClientIP(r))

	uptimeSeconds, _ := getUptime()

	health := HealthResponse{
		Status:        "healthy",
		Timestamp:     time.Now().UTC().Format(time.RFC3339),
		UptimeSeconds: uptimeSeconds,
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	
	encoder := json.NewEncoder(w)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(health); err != nil {
		log.Printf("Error encoding JSON: %v", err)
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
	}
}

// 404 Not Found handler
func notFoundHandler(w http.ResponseWriter, r *http.Request) {
	log.Printf("404 Not Found: %s %s", r.Method, r.URL.Path)
	
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusNotFound)
	
	response := map[string]string{
		"error":   "Not Found",
		"message": "Endpoint does not exist",
	}
	
	json.NewEncoder(w).Encode(response)
}

func main() {
	// Configuration from environment variables
	host := os.Getenv("HOST")
	if host == "" {
		host = "0.0.0.0"
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8000"
	}

	// Setup logging
	log.SetFlags(log.LstdFlags | log.Lshortfile)
	log.Printf("Starting DevOps Info Service (Go) on %s:%s", host, port)
	log.Printf("Go version: %s", runtime.Version())
	log.Printf("Platform: %s/%s", runtime.GOOS, runtime.GOARCH)

	// Setup routes
	http.HandleFunc("/", mainHandler)
	http.HandleFunc("/health", healthHandler)

	// Start server
	addr := fmt.Sprintf("%s:%s", host, port)
	log.Printf("Server is running on http://%s", addr)
	log.Printf("Press Ctrl+C to stop")

	if err := http.ListenAndServe(addr, nil); err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}

