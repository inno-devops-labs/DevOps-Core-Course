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

// Data structures
type ServiceInfo struct {
	Service  Service    `json:"service"`
	System   System     `json:"system"`
	Runtime  Runtime    `json:"runtime"`
	Request  Request    `json:"request"`
	Endpoints []Endpoint `json:"endpoints"`
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

type Runtime struct {
	UptimeSeconds int    `json:"uptime_seconds"`
	UptimeHuman   string `json:"uptime_human"`
	CurrentTime   string `json:"current_time"`
	Timezone      string `json:"timezone"`
}

type Request struct {
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

type HealthResponse struct {
	Status       string `json:"status"`
	Timestamp    string `json:"timestamp"`
	UptimeSeconds int   `json:"uptime_seconds"`
}

// Global variables
var startTime time.Time

func init() {
	startTime = time.Now()
}

// Helper functions
func getSystemInfo() System {
	hostname, err := os.Hostname()
	if err != nil {
		hostname = "unknown"
	}

	return System{
		Hostname:        hostname,
		Platform:        runtime.GOOS,
		PlatformVersion: getOSVersion(),
		Architecture:    runtime.GOARCH,
		CPUCount:        runtime.NumCPU(),
		GoVersion:       runtime.Version(),
	}
}

func getOSVersion() string {
	switch runtime.GOOS {
	case "linux":
		return "Linux Kernel"
	case "darwin":
		return "macOS"
	case "windows":
		return "Windows"
	default:
		return runtime.GOOS
	}
}

func getUptime() (int, string) {
	duration := time.Since(startTime)
	seconds := int(duration.Seconds())
	
	hours := seconds / 3600
	minutes := (seconds % 3600) / 60
	
	return seconds, fmt.Sprintf("%d hours, %d minutes", hours, minutes)
}

func getCurrentTime() string {
	return time.Now().UTC().Format(time.RFC3339)
}

// HTTP handlers
func mainHandler(w http.ResponseWriter, r *http.Request) {
	// Handle only root path
	if r.URL.Path != "/" {
		notFoundHandler(w, r)
		return
	}
	
	systemInfo := getSystemInfo()
	uptimeSeconds, uptimeHuman := getUptime()
	
	response := ServiceInfo{
		Service: Service{
			Name:        "devops-info-service",
			Version:     "1.0.0",
			Description: "DevOps course info service",
			Framework:   "Go",
		},
		System: systemInfo,
		Runtime: Runtime{
			UptimeSeconds: uptimeSeconds,
			UptimeHuman:   uptimeHuman,
			CurrentTime:   getCurrentTime(),
			Timezone:      "UTC",
		},
		Request: Request{
			ClientIP:  r.RemoteAddr,
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
	json.NewEncoder(w).Encode(response)
	
	log.Printf("Request: %s %s from %s", r.Method, r.URL.Path, r.RemoteAddr)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	uptimeSeconds, _ := getUptime()
	
	response := HealthResponse{
		Status:       "healthy",
		Timestamp:    getCurrentTime(),
		UptimeSeconds: uptimeSeconds,
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
	
	log.Printf("Health check from %s", r.RemoteAddr)
}

func notFoundHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusNotFound)
	json.NewEncoder(w).Encode(map[string]string{
		"error":   "Not Found",
		"message": "Endpoint does not exist",
	})
	
	log.Printf("404 Not Found: %s", r.URL.Path)
}

// Main function
func main() {
	// Read environment variables
	port := os.Getenv("PORT")
	if port == "" {
		port = "5000"
	}
	
	host := os.Getenv("HOST")
	if host == "" {
		host = "0.0.0.0"
	}
	
	// Setup HTTP routes
	http.HandleFunc("/", mainHandler) 
	http.HandleFunc("/health", healthHandler)
	
	// Start server
	addr := fmt.Sprintf("%s:%s", host, port)
	log.Printf("Starting DevOps Info Service on %s", addr)
	log.Fatal(http.ListenAndServe(addr, nil))
}