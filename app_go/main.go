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

// Global variables
var startTime = time.Now()

// Struct definitions for JSON response
type ServiceInfo struct {
	Service   Service    `json:"service"`
	System    System     `json:"system"`
	Runtime   Runtime    `json:"runtime"`
	Request   Request    `json:"request"`
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
	Status        string `json:"status"`
	Timestamp     string `json:"timestamp"`
	UptimeSeconds int    `json:"uptime_seconds"`
}

// Helper functions
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

	var human string
	if hours > 0 {
		hourStr := "hour"
		if hours != 1 {
			hourStr = "hours"
		}
		minStr := "minute"
		if minutes != 1 {
			minStr = "minutes"
		}
		human = fmt.Sprintf("%d %s, %d %s", hours, hourStr, minutes, minStr)
	} else {
		minStr := "minute"
		if minutes != 1 {
			minStr = "minutes"
		}
		human = fmt.Sprintf("%d %s", minutes, minStr)
	}

	return seconds, human
}

func getClientIP(r *http.Request) string {
	// Try to get real IP from headers first
	if ip := r.Header.Get("X-Real-IP"); ip != "" {
		return ip
	}
	if ip := r.Header.Get("X-Forwarded-For"); ip != "" {
		return ip
	}
	return r.RemoteAddr
}

// HTTP Handlers
func mainHandler(w http.ResponseWriter, r *http.Request) {
	log.Printf("Request: %s %s", r.Method, r.URL.Path)

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
			CurrentTime:   time.Now().UTC().Format(time.RFC3339Nano),
			Timezone:      "UTC",
		},
		Request: Request{
			ClientIP:  getClientIP(r),
			UserAgent: r.UserAgent(),
			Method:    r.Method,
			Path:      r.URL.Path,
		},
		Endpoints: []Endpoint{
			{
				Path:        "/",
				Method:      "GET",
				Description: "Service information",
			},
			{
				Path:        "/health",
				Method:      "GET",
				Description: "Health check",
			},
		},
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(info)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	log.Printf("Health check: %s %s", r.Method, r.URL.Path)

	uptimeSeconds, _ := getUptime()

	health := HealthResponse{
		Status:        "healthy",
		Timestamp:     time.Now().UTC().Format(time.RFC3339Nano),
		UptimeSeconds: uptimeSeconds,
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(health)
}

func notFoundHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusNotFound)
	json.NewEncoder(w).Encode(map[string]string{
		"error":   "Not Found",
		"message": "Endpoint does not exist",
	})
}

func main() {
	// Configuration from environment variables
	host := os.Getenv("HOST")
	if host == "" {
		host = "0.0.0.0"
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	addr := fmt.Sprintf("%s:%s", host, port)

	// Setup routes
	http.HandleFunc("/", mainHandler)
	http.HandleFunc("/health", healthHandler)

	// Start server
	log.Printf("Starting DevOps Info Service on %s", addr)
	log.Printf("Go version: %s", runtime.Version())

	if err := http.ListenAndServe(addr, nil); err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}
