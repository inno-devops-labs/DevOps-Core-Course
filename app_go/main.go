package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"runtime"
	"time"
	"fmt"
)

var startTime = time.Now()

// Service metadata
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

// Runtime metrics
type Runtime struct {
	UptimeSeconds int64  `json:"uptime_seconds"`
	UptimeHuman   string `json:"uptime_human"`
	CurrentTime   string `json:"current_time"`
	Timezone      string `json:"timezone"`
}

// Request details
type RequestInfo struct {
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

// Main response structure
type InfoResponse struct {
	Service   Service       `json:"service"`
	System    System        `json:"system"`
	Runtime   Runtime       `json:"runtime"`
	Request   RequestInfo   `json:"request"`
	Endpoints []Endpoint    `json:"endpoints"`
}

// Health check response
type HealthResponse struct {
	Status        string `json:"status"`
	Timestamp     string `json:"timestamp"`
	UptimeSeconds int64  `json:"uptime_seconds"`
}

// Calculate uptime
func getRuntime() Runtime {
	uptime := time.Since(startTime)
	seconds := int64(uptime.Seconds())
	hours := seconds / 3600
	minutes := (seconds % 3600) / 60

	return Runtime{
		UptimeSeconds: seconds,
		UptimeHuman:   formatUptime(hours, minutes),
		CurrentTime:   time.Now().UTC().Format(time.RFC3339),
		Timezone:      "UTC",
	}
}

func formatUptime(hours, minutes int64) string {
	return fmt.Sprintf("%d hours, %d minutes", hours, minutes)
}

// Main endpoint handler
func mainHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/" {
		http.NotFound(w, r)
		return
	}

	hostname, _ := os.Hostname()
	
	response := InfoResponse{
		Service: Service{
			Name:        "devops-info-service",
			Version:     "1.0.0",
			Description: "DevOps course info service",
			Framework:   "Go net/http",
		},
		System: System{
			Hostname:        hostname,
			Platform:        runtime.GOOS,
			PlatformVersion: "N/A",
			Architecture:    runtime.GOARCH,
			CPUCount:        runtime.NumCPU(),
			GoVersion:       runtime.Version(),
		},
		Runtime: getRuntime(),
		Request: RequestInfo{
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
	log.Printf("Root endpoint called by %s", r.RemoteAddr)
}

// Health check handler
func healthHandler(w http.ResponseWriter, r *http.Request) {
	runtime := getRuntime()
	
	response := HealthResponse{
		Status:        "healthy",
		Timestamp:     time.Now().UTC().Format(time.RFC3339),
		UptimeSeconds: runtime.UptimeSeconds,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	http.HandleFunc("/", mainHandler)
	http.HandleFunc("/health", healthHandler)

	log.Printf("Starting server on :%s", port)
	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatal(err)
	}
}
