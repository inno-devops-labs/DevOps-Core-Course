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

type Endpoint struct {
	Path        string `json:"path"`
	Method      string `json:"method"`
	Description string `json:"description"`
}

type ResponseRoot struct {
	Service   map[string]any `json:"service"`
	System    map[string]any `json:"system"`
	Runtime   map[string]any `json:"runtime"`
	Request   map[string]any `json:"request"`
	Endpoints []Endpoint     `json:"endpoints"`
}

func uptimeSeconds() int {
	return int(time.Since(startTime).Seconds())
}

func uptimeHuman(sec int) string {
	h := sec / 3600
	m := (sec % 3600) / 60
	return fmt.Sprintf("%d hour(s), %d minute(s)", h, m)
}

func hostname() string {
	h, err := os.Hostname()
	if err != nil {
		return ""
	}
	return h
}

func getClientIP(r *http.Request) string {
	xff := r.Header.Get("X-Forwarded-For")
	if xff != "" {
		for i := 0; i < len(xff); i++ {
			if xff[i] == ',' {
				return xff[:i]
			}
		}
		return xff
	}

	host, _, err := net.SplitHostPort(r.RemoteAddr)
	if err != nil {
		return r.RemoteAddr
	}
	return host
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	enc := json.NewEncoder(w)
	enc.SetIndent("", "  ")
	_ = enc.Encode(v)
}

func mainHandler(w http.ResponseWriter, r *http.Request) {
	up := uptimeSeconds()

	resp := ResponseRoot{
		Service: map[string]any{
			"name":        "devops-info-service",
			"version":     "1.0.0",
			"description": "DevOps course info service",
			"framework":   "Go net/http",
		},
		System: map[string]any{
			"hostname":         hostname(),
			"platform":         runtime.GOOS,
			"platform_version": "",
			"architecture":     runtime.GOARCH,
			"cpu_count":        runtime.NumCPU(),
			"python_version":   runtime.Version(),
		},
		Runtime: map[string]any{
			"uptime_seconds": up,
			"uptime_human":   uptimeHuman(up),
			"current_time":   time.Now().UTC().Format(time.RFC3339Nano),
			"timezone":       "UTC",
		},
		Request: map[string]any{
			"client_ip":  getClientIP(r),
			"user_agent": r.UserAgent(),
			"method":     r.Method,
			"path":       r.URL.Path,
		},
		Endpoints: []Endpoint{
			{Path: "/", Method: "GET", Description: "Service information"},
			{Path: "/health", Method: "GET", Description: "Health check"},
		},
	}

	log.Printf("Request: %s %s", r.Method, r.URL.Path)
	writeJSON(w, http.StatusOK, resp)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	log.Printf("Request: %s %s", r.Method, r.URL.Path)
	writeJSON(w, http.StatusOK, map[string]any{
		"status":         "healthy",
		"timestamp":      time.Now().UTC().Format(time.RFC3339Nano),
		"uptime_seconds": uptimeSeconds(),
	})
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	host := os.Getenv("HOST")
	if host == "" {
		host = "0.0.0.0"
	}

	http.HandleFunc("/", mainHandler)
	http.HandleFunc("/health", healthHandler)

	addr := host + ":" + port
	log.Printf("Starting Go app on %s", addr)
	log.Fatal(http.ListenAndServe(addr, nil))
}
