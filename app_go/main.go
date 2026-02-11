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

var startTime = time.Now()

type ServiceInfo struct {
	Name        string `json:"name"`
	Version     string `json:"version"`
	Description string `json:"description"`
	Framework   string `json:"framework"`
}

type SystemInfo struct {
	Hostname     string `json:"hostname"`
	Platform     string `json:"platform"`
	Architecture string `json:"architecture"`
	CPUCount     int    `json:"cpu_count"`
	GoVersion    string `json:"go_version"`
}

type RuntimeInfo struct {
	UptimeSeconds int    `json:"uptime_seconds"`
	UptimeHuman   string `json:"uptime_human"`
	CurrentTime   string `json:"current_time"`
	Timezone      string `json:"timezone"`
}

type RequestInfo struct {
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

type MainResponse struct {
	Service   ServiceInfo   `json:"service"`
	System    SystemInfo    `json:"system"`
	Runtime   RuntimeInfo   `json:"runtime"`
	Request   RequestInfo   `json:"request"`
	Endpoints []Endpoint    `json:"endpoints"`
}

type HealthResponse struct {
	Status        string `json:"status"`
	Timestamp     string `json:"timestamp"`
	UptimeSeconds int    `json:"uptime_seconds"`
}

type ErrorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message"`
	Path    string `json:"path,omitempty"`
}

func getUptime() (int, string) {
	seconds := int(time.Since(startTime).Seconds())
	hours := seconds / 3600
	minutes := (seconds % 3600) / 60
	return seconds, fmt.Sprintf("%d hours, %d minutes", hours, minutes)
}

func mainHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/" {
		notFoundHandler(w, r)
		return
	}

	hostname, _ := os.Hostname()
	uptimeSec, uptimeHuman := getUptime()

	response := MainResponse{
		Service: ServiceInfo{
			Name:        "devops-info-service",
			Version:     "1.0.0",
			Description: "DevOps course info service",
			Framework:   "net/http",
		},
		System: SystemInfo{
			Hostname:     hostname,
			Platform:     runtime.GOOS,
			Architecture: runtime.GOARCH,
			CPUCount:     runtime.NumCPU(),
			GoVersion:    runtime.Version(),
		},
		Runtime: RuntimeInfo{
			UptimeSeconds: uptimeSec,
			UptimeHuman:   uptimeHuman,
			CurrentTime:   time.Now().UTC().Format(time.RFC3339),
			Timezone:      "UTC",
		},
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

	log.Printf("Request received: %s %s", r.Method, r.URL.Path)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	uptimeSec, _ := getUptime()

	response := HealthResponse{
		Status:        "healthy",
		Timestamp:     time.Now().UTC().Format(time.RFC3339),
		UptimeSeconds: uptimeSec,
	}

	log.Printf("Health check requested")

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func notFoundHandler(w http.ResponseWriter, r *http.Request) {
	log.Printf("404 error: %s", r.URL.Path)

	response := ErrorResponse{
		Error:   "Not Found",
		Message: "The requested endpoint does not exist",
		Path:    r.URL.Path,
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusNotFound)
	json.NewEncoder(w).Encode(response)
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	host := os.Getenv("HOST")
	if host == "" {
		host = "0.0.0.0"
	}

	http.HandleFunc("/", mainHandler)
	http.HandleFunc("/health", healthHandler)

	addr := fmt.Sprintf("%s:%s", host, port)
	log.Printf("Starting DevOps Info Service on %s", addr)
	log.Fatal(http.ListenAndServe(addr, nil))
}
