package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"runtime"
	"time"
)

var startTime = time.Now().UTC()

type Service struct {
	Name        string `json:"name"`
	Version     string `json:"version"`
	Description string `json:"description"`
	Framework   string `json:"framework"`
}

type System struct {
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
	Method string `json:"method"`
	Path   string `json:"path"`
}

type Endpoint struct {
	Path        string `json:"path"`
	Method      string `json:"method"`
	Description string `json:"description"`
}

type ServiceInfo struct {
	Service   Service     `json:"service"`
	System    System      `json:"system"`
	Runtime   RuntimeInfo `json:"runtime"`
	Request   RequestInfo `json:"request"`
	Endpoints []Endpoint  `json:"endpoints"`
}

func getUptime() (int, string) {
	seconds := int(time.Since(startTime).Seconds())
	hours := seconds / 3600
	minutes := (seconds % 3600) / 60
	return seconds, fmt.Sprintf("%d hours %d minutes", hours, minutes)
}

func mainHandler(w http.ResponseWriter, r *http.Request) {
	hostname, _ := os.Hostname()
	uptimeSeconds, uptimeHuman := getUptime()

	info := ServiceInfo{
		Service: Service{
			Name:        "devops-info-service",
			Version:     "1.0.0",
			Description: "DevOps Course Info Service",
			Framework:   "Go net/http",
		},
		System: System{
			Hostname:     hostname,
			Platform:     runtime.GOOS,
			Architecture: runtime.GOARCH,
			CPUCount:     runtime.NumCPU(),
			GoVersion:    runtime.Version(),
		},
		Runtime: RuntimeInfo{
			UptimeSeconds: uptimeSeconds,
			UptimeHuman:   uptimeHuman,
			CurrentTime:   time.Now().UTC().Format(time.RFC3339),
			Timezone:      "UTC",
		},
		Request: RequestInfo{
			Method: r.Method,
			Path:   r.URL.Path,
		},
		Endpoints: []Endpoint{
			{Path: "/", Method: "GET", Description: "Main service information endpoint"},
			{Path: "/health", Method: "GET", Description: "Health check endpoint"},
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(info)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	uptimeSeconds, _ := getUptime()

	response := map[string]interface{}{
		"status":         "healthy",
		"timestamp":      time.Now().UTC().Format(time.RFC3339),
		"uptime_seconds": uptimeSeconds,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func main() {
	http.HandleFunc("/", mainHandler)
	http.HandleFunc("/health", healthHandler)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	http.ListenAndServe(":"+port, nil)
}
