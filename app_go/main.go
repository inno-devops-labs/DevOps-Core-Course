package main

import (
	"encoding/json"
	"log"
	"net"
	"net/http"
	"os"
	"runtime"
	"strconv"
	"strings"
	"time"
)

const (
	serviceName = "devops-info-service"
	serviceVersion = "1.0.0"
	serviceDescription = "DevOps course info service"
	serviceFramework = "net/http"
)

var startTime = time.Now().UTC()

type Endpoint struct {
	Path        string `json:"path"`
	Method      string `json:"method"`
	Description string `json:"description"`
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
	PythonVersion   string `json:"python_version"`
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

type RootResponse struct {
	Service   Service     `json:"service"`
	System    System      `json:"system"`
	Runtime   RuntimeInfo `json:"runtime"`
	Request   RequestInfo `json:"request"`
	Endpoints []Endpoint  `json:"endpoints"`
}

type HealthResponse struct {
	Status        string `json:"status"`
	Timestamp     string `json:"timestamp"`
	UptimeSeconds int    `json:"uptime_seconds"`
}

func nowISO() string {
	return time.Now().UTC().Format(time.RFC3339Nano)
}

func uptimeSeconds() int {
	return int(time.Since(startTime).Seconds())
}

func uptimeHuman(sec int) string {
	hours := sec / 3600
	minutes := (sec % 3600) / 60

	h := "hours"
	if hours == 1 {
		h = "hour"
	}
	m := "minutes"
	if minutes == 1 {
		m = "minute"
	}
	return strconv.Itoa(hours) + " " + h + ", " + strconv.Itoa(minutes) + " " + m
}

func endpoints() []Endpoint {
	return []Endpoint{
		{Path: "/", Method: "GET", Description: "Service information"},
		{Path: "/health", Method: "GET", Description: "Health check"},
	}
}

func hostname() string {
	h, err := os.Hostname()
	if err != nil {
		return "unknown"
	}
	return h
}

func platformVersion() string {
	if runtime.GOOS != "linux" {
		return runtime.GOOS
	}
	b, err := os.ReadFile("/etc/os-release")
	if err != nil {
		return "unknown"
	}
	for _, line := range strings.Split(string(b), "\n") {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "PRETTY_NAME=") {
			val := strings.Trim(strings.TrimPrefix(line, "PRETTY_NAME="), `"'`)
			if val != "" {
				return val
			}
		}
	}
	return "unknown"
}

func clientIP(r *http.Request) string {
	if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
		return strings.TrimSpace(strings.Split(xff, ",")[0])
	}
	host, _, err := net.SplitHostPort(r.RemoteAddr)
	if err == nil && host != "" {
		return host
	}
	return r.RemoteAddr
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}

func notFound(w http.ResponseWriter) {
	writeJSON(w, http.StatusNotFound, map[string]string{
		"error":   "Not Found",
		"message": "Endpoint does not exist",
	})
}

func rootHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/" {
		notFound(w)
		return
	}

	sec := uptimeSeconds()
	resp := RootResponse{
		Service: Service{
			Name:        serviceName,
			Version:     serviceVersion,
			Description: serviceDescription,
			Framework:   serviceFramework,
		},
		System: System{
			Hostname:        hostname(),
			Platform:        runtime.GOOS,
			PlatformVersion: platformVersion(),
			Architecture:    runtime.GOARCH,
			CPUCount:        runtime.NumCPU(),
			PythonVersion:   "n/a",
		},
		Runtime: RuntimeInfo{
			UptimeSeconds: sec,
			UptimeHuman:   uptimeHuman(sec),
			CurrentTime:   nowISO(),
			Timezone:      "UTC",
		},
		Request: RequestInfo{
			ClientIP:  clientIP(r),
			UserAgent: r.Header.Get("User-Agent"),
			Method:    r.Method,
			Path:      r.URL.Path,
		},
		Endpoints: endpoints(),
	}

	writeJSON(w, http.StatusOK, resp)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/health" {
		notFound(w)
		return
	}
	writeJSON(w, http.StatusOK, HealthResponse{
		Status:        "healthy",
		Timestamp:     nowISO(),
		UptimeSeconds: uptimeSeconds(),
	})
}

func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		log.Printf("Request: %s %s", r.Method, r.URL.Path)
		next.ServeHTTP(w, r)
	})
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

	mux := http.NewServeMux()
	mux.HandleFunc("/health", healthHandler)
	mux.HandleFunc("/", rootHandler)

	addr := host + ":" + port
	log.Printf("Starting %s on %s", serviceName, addr)
	log.Fatal(http.ListenAndServe(addr, loggingMiddleware(mux)))
}