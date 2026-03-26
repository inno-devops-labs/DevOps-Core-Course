package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"runtime"
	"time"
)

var startTime = time.Now()

type HealthResponse struct {
	Status        string `json:"status"`
	Timestamp     string `json:"timestamp"`
	UptimeSeconds int64  `json:"uptime_seconds"`
}

type InfoResponse struct {
	Service ServiceInfo `json:"service"`
	System  SystemInfo  `json:"system"`
	Runtime RuntimeInfo `json:"runtime"`
}

type ServiceInfo struct {
	Name        string `json:"name"`
	Version     string `json:"version"`
	Description string `json:"description"`
	Language    string `json:"language"`
}

type SystemInfo struct {
	OS           string `json:"os"`
	Architecture string `json:"architecture"`
	GoVersion    string `json:"go_version"`
}

type RuntimeInfo struct {
	UptimeSeconds int64  `json:"uptime_seconds"`
	Timestamp     string `json:"timestamp"`
}

func main() {
	http.HandleFunc("/health", handleHealth)
	http.HandleFunc("/app2/health", handleHealth)
	http.HandleFunc("/", handleInfo)
	http.HandleFunc("/info", handleInfo)
	http.HandleFunc("/app2", handleInfo)
	http.HandleFunc("/app2/", handleInfo)
	http.HandleFunc("/app2/info", handleInfo)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("Server starting on port %s\n", port)
	log.Fatal(http.ListenAndServe(":"+port, logMiddleware(http.DefaultServeMux)))
}

func handleHealth(w http.ResponseWriter, r *http.Request) {
	response := HealthResponse{
		Status:        "healthy",
		Timestamp:     time.Now().UTC().Format(time.RFC3339),
		UptimeSeconds: int64(time.Since(startTime).Seconds()),
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	if err := json.NewEncoder(w).Encode(response); err != nil {
		http.Error(w, "internal server error", http.StatusInternalServerError)
		log.Printf("encode health response: %v", err)
		return
	}
}

func handleInfo(w http.ResponseWriter, r *http.Request) {
	uptime := int64(time.Since(startTime).Seconds())

	response := InfoResponse{
		Service: ServiceInfo{
			Name:        "devops-info-service-go",
			Version:     "1.0.0",
			Description: "DevOps course info service in Go",
			Language:    "Go",
		},
		System: SystemInfo{
			OS:           runtime.GOOS,
			Architecture: runtime.GOARCH,
			GoVersion:    runtime.Version(),
		},
		Runtime: RuntimeInfo{
			UptimeSeconds: uptime,
			Timestamp:     time.Now().UTC().Format(time.RFC3339),
		},
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	if err := json.NewEncoder(w).Encode(response); err != nil {
		http.Error(w, "internal server error", http.StatusInternalServerError)
		log.Printf("encode info response: %v", err)
		return
	}
}

func logMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		log.Printf("%s %s\n", r.Method, r.RequestURI)
		next.ServeHTTP(w, r)
	})
}
