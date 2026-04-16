package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
	"sync"
	"time"
)

type ServiceInfo struct {
	Service   Service    `json:"service"`
	System    System     `json:"system"`
	Runtime   Runtime    `json:"runtime"`
	Request   Request    `json:"request"`
	Visits    int64      `json:"visits"`
	Endpoints []Endpoint `json:"endpoints"`
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
	GoVersion       string `json:"go_version"`
}

type Runtime struct {
	UptimeSeconds float64 `json:"uptime_seconds"`
	UptimeHuman   string  `json:"uptime_human"`
	CurrentTime   string  `json:"current_time"`
	Timezone      string  `json:"timezone"`
}

type Request struct {
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

type HealthResponse struct {
	Status        string  `json:"status"`
	Timestamp     string  `json:"timestamp"`
	UptimeSeconds float64 `json:"uptime_seconds"`
}

type VisitsResponse struct {
	Visits int64  `json:"visits"`
	File   string `json:"file"`
}

var startTime = time.Now()

// visitsFile is the path to the persistent visits counter file.
// Configurable via VISITS_FILE env var; defaults to /data/visits.
var visitsFile = func() string {
	if p := os.Getenv("VISITS_FILE"); p != "" {
		return p
	}
	return "/data/visits"
}()

var visitsMu sync.Mutex

func readVisits() int64 {
	visitsMu.Lock()
	defer visitsMu.Unlock()
	data, err := os.ReadFile(visitsFile)
	if err != nil {
		return 0
	}
	n, err := strconv.ParseInt(strings.TrimSpace(string(data)), 10, 64)
	if err != nil {
		return 0
	}
	return n
}

func incrementVisits() int64 {
	visitsMu.Lock()
	defer visitsMu.Unlock()

	var count int64
	data, err := os.ReadFile(visitsFile)
	if err == nil {
		n, _ := strconv.ParseInt(strings.TrimSpace(string(data)), 10, 64)
		count = n
	}
	count++

	dir := filepath.Dir(visitsFile)
	if mkErr := os.MkdirAll(dir, 0755); mkErr != nil {
		log.Printf("visits: failed to create dir %s: %v", dir, mkErr)
		return count
	}
	if wErr := os.WriteFile(visitsFile, []byte(strconv.FormatInt(count, 10)), 0644); wErr != nil {
		log.Printf("visits: failed to write counter: %v", wErr)
	}
	return count
}

type statusCapturingResponseWriter struct {
	http.ResponseWriter
	status int
}

func (w *statusCapturingResponseWriter) WriteHeader(statusCode int) {
	w.status = statusCode
	w.ResponseWriter.WriteHeader(statusCode)
}

func withAccessLog(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		sw := &statusCapturingResponseWriter{ResponseWriter: w, status: http.StatusOK}

		next(sw, r)

		durationMs := float64(time.Since(start).Nanoseconds()) / 1e6
		log.Printf(
			"request completed method=%s path=%s status=%d client_ip=%s duration_ms=%.2f",
			r.Method,
			r.URL.Path,
			sw.status,
			getClientIP(r),
			durationMs,
		)
	}
}

func getHostname() string {
	hostname, err := os.Hostname()
	if err != nil {
		return "unknown"
	}
	return hostname
}

func formatUptime(seconds float64) string {
	hours := int(seconds) / 3600
	minutes := int(seconds) % 3600 / 60
	secs := int(seconds) % 60

	parts := []string{}
	if hours > 0 {
		part := fmt.Sprintf("%d hour", hours)
		if hours != 1 {
			part += "s"
		}
		parts = append(parts, part)
	}
	if minutes > 0 {
		part := fmt.Sprintf("%d minute", minutes)
		if minutes != 1 {
			part += "s"
		}
		parts = append(parts, part)
	}
	if secs > 0 || len(parts) == 0 {
		part := fmt.Sprintf("%d second", secs)
		if secs != 1 {
			part += "s"
		}
		parts = append(parts, part)
	}

	return strings.Join(parts, ", ")
}

func getClientIP(r *http.Request) string {
	ip := r.Header.Get("X-Forwarded-For")
	if ip != "" {
		return strings.Split(ip, ",")[0]
	}
	ip = r.Header.Get("X-Real-Ip")
	if ip != "" {
		return ip
	}
	ip = r.RemoteAddr
	if idx := strings.LastIndex(ip, ":"); idx != -1 {
		ip = ip[:idx]
	}
	return ip
}

func mainHandler(w http.ResponseWriter, r *http.Request) {
	visits := incrementVisits()
	uptimeSeconds := time.Since(startTime).Seconds()

	info := ServiceInfo{
		Service: Service{
			Name:        "devops-info-service",
			Version:     "1.0.0",
			Description: "DevOps course info service",
			Framework:   "Go net/http",
		},
		System: System{
			Hostname:        getHostname(),
			Platform:        runtime.GOOS,
			PlatformVersion: runtime.Version(),
			Architecture:    runtime.GOARCH,
			CPUCount:        runtime.NumCPU(),
			GoVersion:       runtime.Version(),
		},
		Runtime: Runtime{
			UptimeSeconds: roundFloat(uptimeSeconds, 2),
			UptimeHuman:   formatUptime(uptimeSeconds),
			CurrentTime:   time.Now().UTC().Format("2006-01-02T15:04:05.000Z"),
			Timezone:      "UTC",
		},
		Request: Request{
			ClientIP:  getClientIP(r),
			UserAgent: r.Header.Get("User-Agent"),
			Method:    r.Method,
			Path:      r.URL.Path,
		},
		Visits: visits,
		Endpoints: []Endpoint{
			{Path: "/", Method: "GET", Description: "Service information + visit counter increment"},
			{Path: "/health", Method: "GET", Description: "Health check"},
			{Path: "/visits", Method: "GET", Description: "Current visit count"},
		},
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(info); err != nil {
		log.Printf("failed to encode response: %v", err)
	}
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	uptimeSeconds := time.Since(startTime).Seconds()

	health := HealthResponse{
		Status:        "healthy",
		Timestamp:     time.Now().UTC().Format("2006-01-02T15:04:05.000Z"),
		UptimeSeconds: roundFloat(uptimeSeconds, 2),
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	if err := json.NewEncoder(w).Encode(health); err != nil {
		log.Printf("failed to encode health response: %v", err)
	}
}

func visitsHandler(w http.ResponseWriter, r *http.Request) {
	visits := readVisits()

	resp := VisitsResponse{
		Visits: visits,
		File:   visitsFile,
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(resp); err != nil {
		log.Printf("failed to encode visits response: %v", err)
	}
}

func roundFloat(val float64, precision int) float64 {
	multiplier := 1.0
	for i := 0; i < precision; i++ {
		multiplier *= 10
	}
	return float64(int(val*multiplier+0.5)) / multiplier
}

func main() {
	log.Printf("visits counter file: %s", visitsFile)

	http.HandleFunc("/", withAccessLog(mainHandler))
	http.HandleFunc("/health", withAccessLog(healthHandler))
	http.HandleFunc("/visits", withAccessLog(visitsHandler))

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("starting server port=%s", port)
	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatalf("server failed: %v", err)
	}
}
