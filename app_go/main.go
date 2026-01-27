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

// Service represents service metadata
type Service struct {
	Name        string `json:"name"`
	Version     string `json:"version"`
	Description string `json:"description"`
	Framework   string `json:"framework"`
}

// System represents system information
type System struct {
	Hostname        string `json:"hostname"`
	Platform        string `json:"platform"`
	PlatformVersion string `json:"platform_version"`
	Architecture    string `json:"architecture"`
	CPUCount        int    `json:"cpu_count"`
	GoVersion       string `json:"go_version"`
}

// Runtime represents runtime information
type Runtime struct {
	UptimeSeconds int    `json:"uptime_seconds"`
	UptimeHuman   string `json:"uptime_human"`
	CurrentTime   string `json:"current_time"`
	Timezone      string `json:"timezone"`
}

// Request represents request information
type Request struct {
	ClientIP  string `json:"client_ip"`
	UserAgent string `json:"user_agent"`
	Method    string `json:"method"`
	Path      string `json:"path"`
}

// Endpoint represents an API endpoint
type Endpoint struct {
	Path        string `json:"path"`
	Method      string `json:"method"`
	Description string `json:"description"`
}

// ServiceInfo represents the complete response for main endpoint
type ServiceInfo struct {
	Service   Service    `json:"service"`
	System    System     `json:"system"`
	Runtime   Runtime    `json:"runtime"`
	Request   Request    `json:"request"`
	Endpoints []Endpoint `json:"endpoints"`
}

// HealthResponse represents health check response
type HealthResponse struct {
	Status        string `json:"status"`
	Timestamp     string `json:"timestamp"`
	UptimeSeconds int    `json:"uptime_seconds"`
}

// getSystemInfo collects system information
func getSystemInfo() System {
	hostname, err := os.Hostname()
	if err != nil {
		hostname = "unknown"
		log.Printf("Error getting hostname: %v", err)
	}

	return System{
		Hostname:        hostname,
		Platform:        runtime.GOOS,
		PlatformVersion: runtime.GOOS + " " + runtime.GOARCH,
		Architecture:    runtime.GOARCH,
		CPUCount:        runtime.NumCPU(),
		GoVersion:       runtime.Version(),
	}
}

// getUptime calculates application uptime
func getUptime() (int, string) {
	duration := time.Since(startTime)
	seconds := int(duration.Seconds())
	hours := seconds / 3600
	minutes := (seconds % 3600) / 60

	var human string
	if hours > 0 {
		hourText := "hour"
		if hours != 1 {
			hourText = "hours"
		}
		minuteText := "minute"
		if minutes != 1 {
			minuteText = "minutes"
		}
		human = fmt.Sprintf("%d %s, %d %s", hours, hourText, minutes, minuteText)
	} else if minutes > 0 {
		minuteText := "minute"
		if minutes != 1 {
			minuteText = "minutes"
		}
		human = fmt.Sprintf("%d %s", minutes, minuteText)
	} else {
		secondText := "second"
		if seconds != 1 {
			secondText = "seconds"
		}
		human = fmt.Sprintf("%d %s", seconds, secondText)
	}

	return seconds, human
}

// getRequestInfo extracts request information
func getRequestInfo(r *http.Request) Request {
	clientIP := r.RemoteAddr
	if forwarded := r.Header.Get("X-Forwarded-For"); forwarded != "" {
		clientIP = forwarded
	}

	userAgent := r.UserAgent()
	if userAgent == "" {
		userAgent = "unknown"
	}

	return Request{
		ClientIP:  clientIP,
		UserAgent: userAgent,
		Method:    r.Method,
		Path:      r.URL.Path,
	}
}

// mainHandler handles the main endpoint
func mainHandler(w http.ResponseWriter, r *http.Request) {
	log.Printf("Request: %s %s from %s", r.Method, r.URL.Path, r.RemoteAddr)

	uptimeSeconds, uptimeHuman := getUptime()

	info := ServiceInfo{
		Service: Service{
			Name:        "devops-info-service",
			Version:     "1.0.0",
			Description: "DevOps course info service",
			Framework:   "Go net/http",
		},
		System: getSystemInfo(),
		Runtime: Runtime{
			UptimeSeconds: uptimeSeconds,
			UptimeHuman:   uptimeHuman,
			CurrentTime:   time.Now().UTC().Format(time.RFC3339Nano),
			Timezone:      "UTC",
		},
		Request: getRequestInfo(r),
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

	if err := json.NewEncoder(w).Encode(info); err != nil {
		log.Printf("Error encoding JSON: %v", err)
	}
}

// healthHandler handles the health check endpoint
func healthHandler(w http.ResponseWriter, r *http.Request) {
	log.Printf("Health check from %s", r.RemoteAddr)

	uptimeSeconds, _ := getUptime()

	health := HealthResponse{
		Status:        "healthy",
		Timestamp:     time.Now().UTC().Format(time.RFC3339Nano),
		UptimeSeconds: uptimeSeconds,
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)

	if err := json.NewEncoder(w).Encode(health); err != nil {
		log.Printf("Error encoding JSON: %v", err)
	}
}

// notFoundHandler handles 404 errors
func notFoundHandler(w http.ResponseWriter, r *http.Request) {
	log.Printf("404 error: %s", r.URL.Path)

	errorResponse := map[string]interface{}{
		"error":   "Not Found",
		"message": "Endpoint does not exist",
		"path":    r.URL.Path,
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusNotFound)

	if err := json.NewEncoder(w).Encode(errorResponse); err != nil {
		log.Printf("Error encoding JSON: %v", err)
	}
}

func main() {
	// Get configuration from environment variables
	host := os.Getenv("HOST")
	if host == "" {
		host = "0.0.0.0"
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	addr := host + ":" + port

	// Setup routes
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/" {
			mainHandler(w, r)
		} else {
			notFoundHandler(w, r)
		}
	})
	http.HandleFunc("/health", healthHandler)

	// Start server
	log.Printf("Starting DevOps Info Service...")
	log.Printf("Host: %s, Port: %s", host, port)
	log.Printf("Visit: http://%s/", addr)
	log.Printf("Server starting on %s", addr)

	if err := http.ListenAndServe(addr, nil); err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}
