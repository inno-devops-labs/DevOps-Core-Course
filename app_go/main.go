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

var startTime = time.Now().UTC()

func getEnv(key, defaultValue string) string {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}
	return value
}

func getUptime() (int64, string) {
	seconds := int64(time.Since(startTime).Seconds())
	hours := seconds / 3600
	minutes := (seconds % 3600) / 60
	return seconds,
		formatUptime(hours, minutes)
}

func formatUptime(hours, minutes int64) string {
	return fmt.Sprintf("%d hours, %d minutes", hours, minutes)
}

func getHostname() string {
	hostname, err := os.Hostname()
	if err != nil {
		return "unknown"
	}
	return hostname
}

func getClientIP(r *http.Request) string {
	ip, _, err := net.SplitHostPort(r.RemoteAddr)
	if err != nil {
		return r.RemoteAddr
	}
	return ip
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	uptimeSeconds, _ := getUptime()

	response := map[string]interface{}{
		"status":         "healthy",
		"timestamp":      time.Now().UTC().Format(time.RFC3339),
		"uptime_seconds": uptimeSeconds,
	}

	log.Printf("Health check from %s", getClientIP(r))
	writeJSON(w, http.StatusOK, response)
}

func mainHandler(w http.ResponseWriter, r *http.Request) {
	uptimeSeconds, uptimeHuman := getUptime()

	response := map[string]interface{}{
		"service": map[string]interface{}{
			"name":        "devops-info-service",
			"version":     "1.0.0",
			"description": "DevOps course info service",
			"framework":   "net/http",
		},
		"system": map[string]interface{}{
			"hostname":         getHostname(),
			"platform":         runtime.GOOS,
			"platform_version": runtime.Version(),
			"architecture":     runtime.GOARCH,
			"cpu_count":        runtime.NumCPU(),
			"go_version":       runtime.Version(),
		},
		"runtime": map[string]interface{}{
			"uptime_seconds": uptimeSeconds,
			"uptime_human":   uptimeHuman,
			"current_time":   time.Now().UTC().Format(time.RFC3339),
			"timezone":       "UTC",
		},
		"request": map[string]interface{}{
			"client_ip":  getClientIP(r),
			"user_agent": r.UserAgent(),
			"method":     r.Method,
			"path":       r.URL.Path,
		},
		"endpoints": []map[string]string{
			{
				"path":        "/",
				"method":      "GET",
				"description": "Service information",
			},
			{
				"path":        "/health",
				"method":      "GET",
				"description": "Health check",
			},
		},
	}

	log.Printf("%s %s from %s", r.Method, r.URL.Path, getClientIP(r))
	writeJSON(w, http.StatusOK, response)
}

func writeJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(data)
}

func main() {
	host := getEnv("HOST", "0.0.0.0")
	port := getEnv("PORT", "5000")

	log.Printf("Starting Go DevOps Info Service on %s:%s", host, port)

	http.HandleFunc("/", mainHandler)
	http.HandleFunc("/health", healthHandler)

	err := http.ListenAndServe(host+":"+port, nil)
	if err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}
