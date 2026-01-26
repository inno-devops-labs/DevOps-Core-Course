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

var startTime = time.Now().UTC()

type jsonMap map[string]any

func main() {
	host := getEnv("HOST", "0.0.0.0")
	port := getEnvInt("PORT", 5000)
	debug := strings.EqualFold(getEnv("DEBUG", "False"), "true")

	logger := log.New(os.Stdout, "", log.LstdFlags)
	logger.Printf("Starting devops-info-service (go). host=%s port=%d debug=%v", host, port, debug)

	mux := http.NewServeMux()
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/" {
			writeJSON(w, http.StatusNotFound, jsonMap{"error": "Not Found", "message": "Endpoint does not exist"})
			return
		}
		if r.Method != http.MethodGet {
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}

		if debug {
			logger.Printf("Received request from %s. Method: %s, Path: %s", r.RemoteAddr, r.Method, r.URL.Path)
		}

		uptimeSeconds, uptimeHuman := getUptime()

		payload := jsonMap{
			"service": jsonMap{
				"name":        "devops-info-service",
				"version":     "1.0.0",
				"description": "DevOps course info service",
			},
			"system": jsonMap{
				"hostname":         getHostname(),
				"platform":         runtime.GOOS,
				"platform_version": getKernelRelease(),
				"architecture":     runtime.GOARCH,
				"cpu_count":        runtime.NumCPU(),
				// Kept for strict JSON parity with the Python version.
				"python_version": runtime.Version(),
			},
			"runtime": jsonMap{
				"uptime_seconds": uptimeSeconds,
				"uptime_human":   uptimeHuman,
				"current-time":   time.Now().UTC().Format(time.RFC3339Nano),
				"timezone":       "UTC",
			},
			"request": jsonMap{
				"client_ip":  getClientIP(r),
				"user_agent": r.Header.Get("User-Agent"),
				"method":     r.Method,
				"path":       r.URL.Path,
			},
			"endpoints": []jsonMap{
				{"path": "/", "method": "GET", "description": "Service information"},
				{"path": "/health", "method": "GET", "description": "Health check"},
			},
		}

		writeJSON(w, http.StatusOK, payload)
	})

	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		if debug {
			logger.Printf("Health check requested")
		}
		uptimeSeconds, _ := getUptime()
		writeJSON(w, http.StatusOK, jsonMap{
			"status":         "healthy",
			"timestamp":      time.Now().UTC().Format(time.RFC3339Nano),
			"uptime_seconds": uptimeSeconds,
		})
	})

	addr := net.JoinHostPort(host, strconv.Itoa(port))
	server := &http.Server{
		Addr:              addr,
		Handler:           recoverMiddleware(logger, mux),
		ReadHeaderTimeout: 5 * time.Second,
	}

	logger.Printf("Listening on http://%s", addr)
	if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		logger.Fatalf("server error: %v", err)
	}
}

func recoverMiddleware(logger *log.Logger, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if rec := recover(); rec != nil {
				logger.Printf("panic recovered: %v", rec)
				writeJSON(w, http.StatusInternalServerError, jsonMap{
					"error":   "Internal Server Error",
					"message": "An unexpected error occurred",
				})
			}
		}()
		next.ServeHTTP(w, r)
	})
}

func writeJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	enc := json.NewEncoder(w)
	enc.SetEscapeHTML(false)
	_ = enc.Encode(payload)
}

func getUptime() (int, string) {
	delta := time.Since(startTime)
	sec := int(delta.Seconds())
	hours := sec / 3600
	minutes := (sec % 3600) / 60
	return sec, strconv.Itoa(hours) + " hours, " + strconv.Itoa(minutes) + " minutes"
}

func getClientIP(r *http.Request) string {
	xff := r.Header.Get("X-Forwarded-For")
	if xff != "" {
		parts := strings.Split(xff, ",")
		if len(parts) > 0 {
			return strings.TrimSpace(parts[0])
		}
	}
	host, _, err := net.SplitHostPort(r.RemoteAddr)
	if err == nil && host != "" {
		return host
	}
	return r.RemoteAddr
}

func getHostname() string {
	h, err := os.Hostname()
	if err != nil {
		return ""
	}
	return h
}

func getKernelRelease() string {
	// Best-effort Linux kernel release; empty string on non-Linux or when unavailable.
	b, err := os.ReadFile("/proc/sys/kernel/osrelease")
	if err != nil {
		return ""
	}
	return strings.TrimSpace(string(b))
}

func getEnv(key, def string) string {
	v := os.Getenv(key)
	if v == "" {
		return def
	}
	return v
}

func getEnvInt(key string, def int) int {
	v := strings.TrimSpace(os.Getenv(key))
	if v == "" {
		return def
	}
	n, err := strconv.Atoi(v)
	if err != nil {
		return def
	}
	return n
}
