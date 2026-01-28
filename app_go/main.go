package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"runtime"
	"strings"
	"time"
)

type ServiceInfo struct {
	Service   map[string]string   `json:"service"`
	System    map[string]any      `json:"system"`
	Runtime   map[string]any      `json:"runtime"`
	Request   map[string]string   `json:"request"`
	Endpoints []map[string]string `json:"endpoints"`
}

var startTime = time.Now()

func getEnv(key, fallback string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	return fallback
}

func getUptime() map[string]any {
	uptime := time.Since(startTime)
	seconds := int(uptime.Seconds())
	hours := seconds / 3600
	minutes := (seconds % 3600) / 60
	return map[string]any{
		"seconds": seconds,
		"human":   fmt.Sprintf("%d hours, %d minutes", hours, minutes),
	}
}

func mainHandler(w http.ResponseWriter, r *http.Request) {
	log.Printf("Request: %s %s from %s", r.Method, r.URL.Path, r.RemoteAddr)

	hostname, _ := os.Hostname()
	uptime := getUptime()
	debugMode := strings.ToLower(getEnv("DEBUG", "false")) == "true"

	info := ServiceInfo{
		Service: map[string]string{
			"name":        "devops-info-service",
			"version":     "1.0.0",
			"description": "DevOps course info service (Go version)",
			"framework":   "Standard net/http",
		},
		System: map[string]any{
			"hostname":      hostname,
			"platform":      runtime.GOOS,
			"architecture":  runtime.GOARCH,
			"cpu_count":     runtime.NumCPU(),
			"go_version":    runtime.Version(),
			"debug_enabled": debugMode,
		},
		Runtime: map[string]any{
			"uptime_seconds": uptime["seconds"],
			"uptime_human":   uptime["human"],
			"current_time":   time.Now().UTC().Format(time.RFC3339),
			"timezone":       "UTC",
		},
		Request: map[string]string{
			"client_ip":  r.RemoteAddr,
			"user_agent": r.UserAgent(),
			"method":     r.Method,
			"path":       r.URL.Path,
		},
		Endpoints: []map[string]string{
			{"path": "/", "method": "GET", "description": "Service information"},
			{"path": "/health", "method": "GET", "description": "Health check"},
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(info)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	uptime := getUptime()
	response := map[string]any{
		"status":         "healthy",
		"timestamp":      time.Now().UTC().Format(time.RFC3339),
		"uptime_seconds": uptime["seconds"],
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func main() {
	host := getEnv("HOST", "0.0.0.0")
	port := getEnv("PORT", "8080")

	http.HandleFunc("/", mainHandler)
	http.HandleFunc("/health", healthHandler)

	addr := fmt.Sprintf("%s:%s", host, port)
	log.Printf("Go Application starting on %s...", addr)

	if err := http.ListenAndServe(addr, nil); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
