package info

import (
	"encoding/json"
	"log"
	"net"
	"net/http"
	"os"
	"runtime"
	"time"

	"devops-info-service-go/internal/uptime"
)

// MainHandler returns an http.HandlerFunc for the "/" endpoint.
func MainHandler(logger *log.Logger) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		logger.Printf("Handling main endpoint: method=%s path=%s", r.Method, r.URL.Path)

		uptimeSeconds, uptimeHuman := uptime.Get()

		hostname, err := os.Hostname()
		if err != nil {
			logger.Printf("error getting hostname: %v", err)
			hostname = "unknown"
		}

		now := time.Now().UTC()

		clientIP, _, err := net.SplitHostPort(r.RemoteAddr)
		if err != nil {
			clientIP = r.RemoteAddr
		}

		info := ServiceInfo{
			Service: Service{
				Name:        "devops-info-service",
				Version:     "1.0.0",
				Description: "DevOps course info service (Go)",
				Framework:   "net/http",
			},
			System: System{
				Hostname:        hostname,
				Platform:        runtime.GOOS,
				PlatformVersion: runtime.Version(),
				Architecture:    runtime.GOARCH,
				CPUCount:        runtime.NumCPU(),
				GoVersion:       runtime.Version(),
			},
			Runtime: Runtime{
				UptimeSeconds: uptimeSeconds,
				UptimeHuman:   uptimeHuman,
				CurrentTime:   now.Format(time.RFC3339Nano),
				Timezone:      "UTC",
			},
			Request: Request{
				ClientIP:  clientIP,
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
		if err := json.NewEncoder(w).Encode(info); err != nil {
			logger.Printf("error encoding main response: %v", err)
		} else {
			logger.Printf("Successfully handled main endpoint for client_ip=%s", info.Request.ClientIP)
		}
	}
}

// HealthHandler returns an http.HandlerFunc for the "/health" endpoint.
func HealthHandler(logger *log.Logger) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		logger.Printf("Handling health endpoint: method=%s path=%s", r.Method, r.URL.Path)

		uptimeSeconds, _ := uptime.Get()

		now := time.Now().UTC()

		health := Health{
			Status:        "healthy",
			Timestamp:     now.Format(time.RFC3339Nano),
			UptimeSeconds: uptimeSeconds,
		}

		w.Header().Set("Content-Type", "application/json")
		if err := json.NewEncoder(w).Encode(health); err != nil {
			logger.Printf("error encoding health response: %v", err)
		} else {
			logger.Printf("Successfully handled health endpoint, uptime_seconds=%d", health.UptimeSeconds)
		}
	}
}
