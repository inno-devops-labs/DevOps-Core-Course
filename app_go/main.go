// DevOps Info Service — Go implementation.
// Same endpoints and JSON structure as the Python version.

package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"log"
	"net"
	"net/http"
	"os"
	"runtime"
	"strings"
	"time"
)

type ServiceInfo struct {
	Service  Service   `json:"service"`
	System   System    `json:"system"`
	Runtime  Runtime   `json:"runtime"`
	Request  Request   `json:"request"`
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
	UptimeSeconds int    `json:"uptime_seconds"`
	UptimeHuman   string `json:"uptime_human"`
	CurrentTime   string `json:"current_time"`
	Timezone      string `json:"timezone"`
}

type Request struct {
	ClientIP string `json:"client_ip"`
	UserAgent string `json:"user_agent"`
	Method   string `json:"method"`
	Path     string `json:"path"`
}

type Endpoint struct {
	Path        string `json:"path"`
	Method      string `json:"method"`
	Description string `json:"description"`
}

type HealthResponse struct {
	Status        string `json:"status"`
	Timestamp     string `json:"timestamp"`
	UptimeSeconds int    `json:"uptime_seconds"`
}

var startTime = time.Now().UTC()

func getHostname() string {
	h, err := os.Hostname()
	if err != nil {
		return "unknown"
	}
	return h
}

func getPlatformVersion() string {
	f, err := os.Open("/etc/os-release")
	if err != nil {
		return runtime.GOOS
	}
	defer f.Close()
	s := bufio.NewScanner(f)
	for s.Scan() {
		line := strings.TrimSpace(s.Text())
		if strings.HasPrefix(line, "PRETTY_NAME=") {
			v := strings.TrimPrefix(line, "PRETTY_NAME=")
			v = strings.Trim(v, "\"")
			return v
		}
	}
	return runtime.GOOS
}

func uptime() (seconds int, human string) {
	d := time.Since(startTime)
	sec := int(d.Seconds())
	h := sec / 3600
	m := (sec % 3600) / 60
	return sec, fmt.Sprintf("%d hours, %d minutes", h, m)
}

func nowUTC() string {
	return time.Now().UTC().Format("2006-01-02T15:04:05.000Z")
}

func clientIP(r *http.Request) string {
	ra := r.RemoteAddr
	if h := r.Header.Get("X-Forwarded-For"); h != "" {
		if idx := strings.Index(h, ","); idx > 0 {
			ra = strings.TrimSpace(h[:idx])
		} else {
			ra = strings.TrimSpace(h)
		}
		return ra
	}
	host, _, err := net.SplitHostPort(ra)
	if err != nil {
		return ra
	}
	return host
}

func mainHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/" {
		http.NotFound(w, r)
		return
	}
	log.Printf("Handling GET /")

	sec, human := uptime()
	info := ServiceInfo{
		Service: Service{
			Name:        "devops-info-service",
			Version:     "1.0.0",
			Description: "DevOps course info service",
			Framework:   "net/http",
		},
		System: System{
			Hostname:        getHostname(),
			Platform:        runtime.GOOS,
			PlatformVersion: getPlatformVersion(),
			Architecture:    runtime.GOARCH,
			CPUCount:        runtime.NumCPU(),
			GoVersion:       strings.TrimPrefix(runtime.Version(), "go"),
		},
		Runtime: Runtime{
			UptimeSeconds: sec,
			UptimeHuman:   human,
			CurrentTime:   nowUTC(),
			Timezone:      "UTC",
		},
		Request: Request{
			ClientIP: clientIP(r),
			UserAgent: r.Header.Get("User-Agent"),
			Method:   r.Method,
			Path:     r.URL.Path,
		},
		Endpoints: []Endpoint{
			{Path: "/", Method: "GET", Description: "Service information"},
			{Path: "/health", Method: "GET", Description: "Health check"},
		},
	}
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(info)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	log.Printf("Handling GET /health")
	sec, _ := uptime()
	resp := HealthResponse{
		Status:        "healthy",
		Timestamp:     nowUTC(),
		UptimeSeconds: sec,
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(resp)
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "5000"
	}
	host := os.Getenv("HOST")
	if host == "" {
		host = "0.0.0.0"
	}
	addr := net.JoinHostPort(host, port)
	log.Printf("Starting DevOps Info Service on %s", addr)
	http.HandleFunc("/health", healthHandler)
	http.HandleFunc("/", mainHandler)
	log.Fatal(http.ListenAndServe(addr, nil))
}
