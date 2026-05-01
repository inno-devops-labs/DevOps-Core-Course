package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"net"
	"net/http"
	"os"
	"runtime"
	"strings"
	"time"
)

type service struct {
	Name        string `json:"name"`
	Version     string `json:"version"`
	Description string `json:"description"`
	Framework   string `json:"framework"`
}

type systemInfo struct {
	Hostname         string `json:"hostname"`
	Platform         string `json:"platform"`
	PlatformVersion  string `json:"platform_version"`
	Architecture     string `json:"architecture"`
	CPUCount         int    `json:"cpu_count"`
	GoVersion        string `json:"go_version"`
}

type runtimeInfo struct {
	UptimeSeconds int64  `json:"uptime_seconds"`
	UptimeHuman   string `json:"uptime_human"`
	CurrentTime   string `json:"current_time"`
	Timezone      string `json:"timezone"`
}

type requestInfo struct {
	ClientIP  string `json:"client_ip"`
	UserAgent string `json:"user_agent"`
	Method    string `json:"method"`
	Path      string `json:"path"`
}

type endpoint struct {
	Path        string `json:"path"`
	Method      string `json:"method"`
	Description string `json:"description"`
}

type infoResponse struct {
	Service   service     `json:"service"`
	System    systemInfo  `json:"system"`
	Runtime   runtimeInfo `json:"runtime"`
	Request   requestInfo `json:"request"`
	Endpoints []endpoint  `json:"endpoints"`
}

type healthResponse struct {
	Status        string `json:"status"`
	Timestamp     string `json:"timestamp"`
	UptimeSeconds int64  `json:"uptime_seconds"`
}

var startTime = time.Now()

func main() {
	host := envOrDefault("HOST", "0.0.0.0")
	port := envOrDefault("PORT", "8080")

	logger := log.New(os.Stdout, "[devops-info-service-go] ", log.LstdFlags|log.Lmicroseconds)
	logger.Printf("Starting service on %s:%s", host, port)

	mux := http.NewServeMux()
	mux.HandleFunc("/health", healthHandler)
	mux.HandleFunc("/", mainHandler)

	address := net.JoinHostPort(host, port)
	if err := http.ListenAndServe(address, loggingMiddleware(logger, mux)); err != nil {
		logger.Fatalf("failed to start server: %v", err)
	}
}

func mainHandler(w http.ResponseWriter, r *http.Request) {
	response := infoResponse{
		Service: service{
			Name:        "devops-info-service",
			Version:     "1.0.0",
			Description: "DevOps course info service (Go implementation)",
			Framework:   "net/http",
		},
		System: systemInfo{
			Hostname:        getHostname(),
			Platform:        runtime.GOOS,
			PlatformVersion: getPlatformVersion(),
			Architecture:    runtime.GOARCH,
			CPUCount:        runtime.NumCPU(),
			GoVersion:       runtime.Version(),
		},
		Runtime: runtimeInfo{
			UptimeSeconds: uptimeSeconds(),
			UptimeHuman:   uptimeHuman(),
			CurrentTime:   time.Now().UTC().Format(time.RFC3339),
			Timezone:      time.Now().Location().String(),
		},
		Request: requestInfo{
			ClientIP:  getClientIP(r),
			UserAgent: r.UserAgent(),
			Method:    r.Method,
			Path:      r.URL.Path,
		},
		Endpoints: []endpoint{
			{Path: "/", Method: http.MethodGet, Description: "Service information"},
			{Path: "/health", Method: http.MethodGet, Description: "Health check"},
		},
	}

	writeJSON(w, http.StatusOK, response)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	response := healthResponse{
		Status:        "healthy",
		Timestamp:     time.Now().UTC().Format(time.RFC3339),
		UptimeSeconds: uptimeSeconds(),
	}
	writeJSON(w, http.StatusOK, response)
}

func loggingMiddleware(logger *log.Logger, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next.ServeHTTP(w, r)
		logger.Printf("%s %s from %s in %v", r.Method, r.URL.Path, getClientIP(r), time.Since(start))
	})
}

func writeJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)

	encoder := json.NewEncoder(w)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(payload); err != nil {
		http.Error(w, fmt.Sprintf("failed to encode response: %v", err), http.StatusInternalServerError)
	}
}

func envOrDefault(key, fallback string) string {
	value := strings.TrimSpace(os.Getenv(key))
	if value == "" {
		return fallback
	}
	return value
}

func uptimeSeconds() int64 {
	return int64(time.Since(startTime).Seconds())
}

func uptimeHuman() string {
	seconds := uptimeSeconds()
	hours := seconds / 3600
	minutes := (seconds % 3600) / 60
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
	// Prefer X-Forwarded-For when present, fallback to remote address
	if forwarded := r.Header.Get("X-Forwarded-For"); forwarded != "" {
		parts := strings.Split(forwarded, ",")
		return strings.TrimSpace(parts[0])
	}

	host, _, err := net.SplitHostPort(r.RemoteAddr)
	if err != nil {
		return r.RemoteAddr
	}
	return host
}

func getPlatformVersion() string {
	// Best-effort read from /etc/os-release
	data, err := os.ReadFile("/etc/os-release")
	if err != nil {
		return "unknown"
	}

	lines := strings.Split(string(data), "\n")
	for _, line := range lines {
		key, value, err := parseKVLine(line)
		if err != nil {
			continue
		}
		if key == "PRETTY_NAME" {
			return value
		}
	}
	return "unknown"
}

func parseKVLine(line string) (string, string, error) {
	line = strings.TrimSpace(line)
	if line == "" || strings.HasPrefix(line, "#") {
		return "", "", errors.New("skip")
	}
	parts := strings.SplitN(line, "=", 2)
	if len(parts) != 2 {
		return "", "", errors.New("invalid")
	}
	key := strings.TrimSpace(parts[0])
	value := strings.Trim(parts[1], `"'`)
	return key, value, nil
}
