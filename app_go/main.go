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

var startTime = time.Now().UTC()

func getUptime() (int64, string) {
	seconds := int64(time.Since(startTime).Seconds())
	hours := seconds / 3600
	minutes := (seconds % 3600) / 60
	return seconds, fmt.Sprintf("%d hour, %d minutes", hours, minutes)
}

func indexHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		w.WriteHeader(http.StatusMethodNotAllowed)
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]string{"error": "method not allowed"})
		return
	}

	uptimeSeconds, uptimeHuman := getUptime()
	hostname, _ := os.Hostname()
	response := map[string]interface{}{
		"service": map[string]interface{}{
			"name":        "devops-info-service",
			"version":     "1.0.0",
			"description": "DevOps course info service",
			"framework":   "Flask",
		},
		"system": map[string]interface{}{
			"hostname":         hostname,
			"platform":         runtime.GOOS,
			"platform_version": "",
			"architecture":     runtime.GOARCH,
			"cpu_count":        runtime.NumCPU(),
			"python_version":   "",
		},
		"runtime": map[string]interface{}{
			"uptime_seconds": uptimeSeconds,
			"uptime_human":   uptimeHuman,
			"current_time":   time.Now().UTC().Format(time.RFC3339),
			"timezone":       "UTC",
		},
		"request": map[string]interface{}{
			"client_ip":  r.RemoteAddr,
			"user_agent": r.UserAgent(),
			"method":     r.Method,
			"path":       r.URL.Path,
		},
		"endpoints": []map[string]string{
			{"path": "/", "method": "GET", "description": "Service information"},
			{"path": "/health", "method": "GET", "description": "Health check"},
		},
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		w.WriteHeader(http.StatusMethodNotAllowed)
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]string{"error": "method not allowed"})
		return
	}
	uptimeSeconds, _ := getUptime()
	response := map[string]interface{}{
		"status":          "healthy",
		"timestamp":       time.Now().UTC().Format(time.RFC3339),
		"uptime_seconds":  uptimeSeconds,
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func newServer(host, port string) *http.Server {
	mux := http.NewServeMux()
	mux.HandleFunc("/", indexHandler)
	mux.HandleFunc("/health", healthHandler)
	srv := &http.Server{
		Addr:    host + ":" + port,
		Handler: mux,
	}
	return srv
}

func main() {
	host := os.Getenv("HOST")
	if host == "" {
		host = "0.0.0.0"
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	srv := newServer(host, port)
	log.Println("Starting Go service on", host+":"+port)
	log.Fatal(srv.ListenAndServe())
}