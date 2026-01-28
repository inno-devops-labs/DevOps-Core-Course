package main

import (
	"encoding/json"
	"log"
	"net"
	"net/http"
	"os"
	"runtime"
	"strconv"
	"time"
)

// Service metadata
type Service struct {
	Name        string `json:"name"`
	Version     string `json:"version"`
	Description string `json:"description"`
	Framework   string `json:"framework"`
}

// System information
type System struct {
	Hostname       string `json:"hostname"`
	Platform       string `json:"platform"`
	PlatformVersion string `json:"platform_version"`
	Architecture   string `json:"architecture"`
	CPUCount       int    `json:"cpu_count"`
	PythonVersion  string `json:"python_version"` // reused key name for compatibility, holds Go version
}

// Runtime information
type RuntimeInfo struct {
	UptimeSeconds int64  `json:"uptime_seconds"`
	UptimeHuman   string `json:"uptime_human"`
	CurrentTime   string `json:"current_time"`
	Timezone      string `json:"timezone"`
}

// Request information
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

// Root endpoint response
type RootResponse struct {
	Service   Service      `json:"service"`
	System    System       `json:"system"`
	Runtime   RuntimeInfo  `json:"runtime"`
	Request   RequestInfo  `json:"request"`
	Endpoints []Endpoint   `json:"endpoints"`
}

// Health endpoint response
type HealthResponse struct {
	Status        string `json:"status"`
	Timestamp     string `json:"timestamp"`
	UptimeSeconds int64  `json:"uptime_seconds"`
}

var (
	startTime = time.Now().UTC()
	logger    = log.New(os.Stdout, "", log.LstdFlags)
)

func getUptime() (int64, string) {
	elapsed := time.Since(startTime)
	seconds := int64(elapsed.Seconds())
	hours := seconds / 3600
	minutes := (seconds % 3600) / 60
	return seconds, formatUptime(hours, minutes)
}

func formatUptime(hours, minutes int64) string {
	return formatInt(hours) + " hours, " + formatInt(minutes) + " minutes"
}

func formatInt(v int64) string {
	return strconv.FormatInt(v, 10)
}

func getSystemInfo() System {
	hostname, err := os.Hostname()
	if err != nil {
		hostname = "unknown"
	}

	return System{
		Hostname:       hostname,
		Platform:       runtime.GOOS,
		PlatformVersion: runtime.Version(),
		Architecture:   runtime.GOARCH,
		CPUCount:       runtime.NumCPU(),
		PythonVersion:  runtime.Version(),
	}
}

func getClientIP(r *http.Request) string {
	// Try X-Forwarded-For first (common in proxies)
	if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
		return xff
	}
	host, _, err := net.SplitHostPort(r.RemoteAddr)
	if err != nil {
		return r.RemoteAddr
	}
	return host
}

func indexHandler(w http.ResponseWriter, r *http.Request) {
	logger.Printf("Handling request: %s %s", r.Method, r.URL.Path)

	uptimeSeconds, uptimeHuman := getUptime()

	response := RootResponse{
		Service: Service{
			Name:        "devops-info-service",
			Version:     "1.0.0",
			Description: "DevOps course info service (Go implementation)",
			Framework:   "net/http",
		},
		System: getSystemInfo(),
		Runtime: RuntimeInfo{
			UptimeSeconds: uptimeSeconds,
			UptimeHuman:   uptimeHuman,
			CurrentTime:   time.Now().UTC().Format(time.RFC3339Nano),
			Timezone:      "UTC",
		},
		Request: RequestInfo{
			ClientIP:  getClientIP(r),
			UserAgent: r.UserAgent(),
			Method:    r.Method,
			Path:      r.URL.Path,
		},
		Endpoints: []Endpoint{
			{Path: "/", Method: http.MethodGet, Description: "Service information"},
			{Path: "/health", Method: http.MethodGet, Description: "Health check"},
		},
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(response); err != nil {
		logger.Printf("ERROR encoding JSON response: %v", err)
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
	}
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	uptimeSeconds, _ := getUptime()

	response := HealthResponse{
		Status:        "healthy",
		Timestamp:     time.Now().UTC().Format(time.RFC3339Nano),
		UptimeSeconds: uptimeSeconds,
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(response); err != nil {
		logger.Printf("ERROR encoding JSON health response: %v", err)
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
	}
}

func main() {
	logger.Println("DevOps Info Service (Go) starting...")

	http.HandleFunc("/", indexHandler)
	http.HandleFunc("/health", healthHandler)

	host := os.Getenv("HOST")
	if host == "" {
		host = "0.0.0.0"
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	addr := host + ":" + port
	logger.Printf("Listening on %s", addr)

	if err := http.ListenAndServe(addr, nil); err != nil {
		logger.Fatalf("Server failed: %v", err)
	}
}


