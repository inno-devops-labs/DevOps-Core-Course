// DevOps Info Service in Go.
package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"runtime"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

const (
	serviceName        = "devops-info-service"
	serviceVersion     = "1.8.0"
	serviceDescription = "DevOps course info service"
	serviceFramework   = "Go net/http"
	serviceLoggerName  = "devops_info_service"
	accessLoggerName   = "http.access"
)

type ServiceInfo struct {
	Name        string `json:"name"`
	Version     string `json:"version"`
	Description string `json:"description"`
	Framework   string `json:"framework"`
}

type SystemInfo struct {
	Hostname        string `json:"hostname"`
	Platform        string `json:"platform"`
	PlatformVersion string `json:"platform_version"`
	Architecture    string `json:"architecture"`
	CPUCount        int    `json:"cpu_count"`
	PythonVersion   string `json:"python_version"`
}

type UptimeInfo struct {
	Seconds int64  `json:"seconds"`
	Human   string `json:"human"`
}

type RequestInfo struct {
	ClientIP  string `json:"client_ip"`
	UserAgent string `json:"user_agent"`
	Method    string `json:"method"`
	Path      string `json:"path"`
}

type EndpointInfo struct {
	Path        string `json:"path"`
	Method      string `json:"method"`
	Description string `json:"description"`
}

type RootResponse struct {
	Service   ServiceInfo    `json:"service"`
	System    SystemInfo     `json:"system"`
	Runtime   UptimeInfo     `json:"runtime"`
	Request   RequestInfo    `json:"request"`
	Endpoints []EndpointInfo `json:"endpoints"`
}

type StatusResponse struct {
	Status        string `json:"status"`
	Timestamp     string `json:"timestamp"`
	UptimeSeconds int64  `json:"uptime_seconds"`
}

var (
	// startTime is used for uptime calculations.
	startTime = time.Now().UTC()
	logMu     sync.Mutex
	logOutput io.Writer = os.Stdout
	// metricsRegistry only exposes service metrics, matching the Python app.
	metricsRegistry   = prometheus.NewRegistry()
	httpRequestsTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "http_requests_total",
			Help: "Total HTTP requests handled by the service.",
		},
		[]string{"method", "endpoint", "status_code"},
	)
	httpRequestDurationSeconds = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name: "http_request_duration_seconds",
			Help: "HTTP request duration in seconds.",
		},
		[]string{"method", "endpoint", "status_code"},
	)
	httpRequestsInProgress = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "http_requests_in_progress",
			Help: "HTTP requests currently being processed.",
		},
		[]string{"method", "endpoint"},
	)
	endpointCallsTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "devops_info_endpoint_calls_total",
			Help: "Total calls to application endpoints.",
		},
		[]string{"endpoint"},
	)
	systemInfoDurationSeconds = prometheus.NewHistogram(
		prometheus.HistogramOpts{
			Name: "devops_info_system_info_duration_seconds",
			Help: "Time spent collecting system information.",
		},
	)
	metricsHTTPHandler = promhttp.HandlerFor(
		metricsRegistry,
		promhttp.HandlerOpts{},
	)
	// endpoints is a static list used to mirror the Python app output.
	endpoints = []EndpointInfo{
		{Path: "/", Method: http.MethodGet, Description: "Service information."},
		{Path: "/health", Method: http.MethodGet, Description: "Health check."},
		{Path: "/ready", Method: http.MethodGet, Description: "Readiness check."},
		{Path: "/metrics", Method: http.MethodGet, Description: "Prometheus metrics."},
	}
)

func init() {
	metricsRegistry.MustRegister(
		httpRequestsTotal,
		httpRequestDurationSeconds,
		httpRequestsInProgress,
		endpointCallsTotal,
		systemInfoDurationSeconds,
	)
}

type responseRecorder struct {
	http.ResponseWriter
	statusCode   int
	bytesWritten int
}

// getServiceInfo returns static service metadata.
func getServiceInfo() ServiceInfo {
	return ServiceInfo{
		Name:        serviceName,
		Version:     serviceVersion,
		Description: serviceDescription,
		Framework:   serviceFramework,
	}
}

// getSystemInfo returns host and runtime information.
func getSystemInfo() SystemInfo {
	startedAt := time.Now()
	defer systemInfoDurationSeconds.Observe(time.Since(startedAt).Seconds())

	hostname, err := os.Hostname()
	if err != nil {
		hostname = "unknown"
	}

	return SystemInfo{
		Hostname:        hostname,
		Platform:        platformName(),
		PlatformVersion: platformVersion(),
		Architecture:    runtime.GOARCH,
		CPUCount:        runtime.NumCPU(),
		PythonVersion:   runtime.Version(),
	}
}

// platformName maps GOOS to a human-readable name.
func platformName() string {
	switch runtime.GOOS {
	case "linux":
		return "Linux"
	case "windows":
		return "Windows"
	case "darwin":
		return "Darwin"
	default:
		return runtime.GOOS
	}
}

// platformVersion attempts to return a friendly OS version.
func platformVersion() string {
	switch runtime.GOOS {
	case "linux":
		if pretty := linuxPrettyName(); pretty != "" {
			return pretty
		}
	case "windows":
		if osName := os.Getenv("OS"); osName != "" {
			return osName
		}
	}

	return runtime.GOOS
}

// linuxPrettyName reads PRETTY_NAME from /etc/os-release if available.
func linuxPrettyName() string {
	data, err := os.ReadFile("/etc/os-release")
	if err != nil {
		return ""
	}

	for _, line := range strings.Split(string(data), "\n") {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "PRETTY_NAME=") {
			value := strings.TrimPrefix(line, "PRETTY_NAME=")
			return strings.Trim(value, "\"")
		}
	}

	return ""
}

// getUptime returns elapsed time since startTime.
func getUptime() UptimeInfo {
	seconds := int64(time.Since(startTime).Seconds())
	hours := seconds / 3600
	minutes := (seconds % 3600) / 60

	return UptimeInfo{
		Seconds: seconds,
		Human:   fmt.Sprintf("%d hours, %d minutes", hours, minutes),
	}
}

// getRequestInfo captures minimal request metadata.
func getRequestInfo(r *http.Request) RequestInfo {
	return RequestInfo{
		ClientIP:  clientIP(r),
		UserAgent: r.Header.Get("User-Agent"),
		Method:    r.Method,
		Path:      r.URL.Path,
	}
}

// clientIP attempts to derive the client IP from proxy headers or RemoteAddr.
func clientIP(r *http.Request) string {
	if forwarded := r.Header.Get("X-Forwarded-For"); forwarded != "" {
		parts := strings.Split(forwarded, ",")
		return strings.TrimSpace(parts[0])
	}

	host, _, err := net.SplitHostPort(r.RemoteAddr)
	if err == nil {
		return host
	}

	return r.RemoteAddr
}

// listEndpoints returns the advertised endpoints for the root response.
func listEndpoints() []EndpointInfo {
	return endpoints
}

func normalizeEndpointLabel(path string) string {
	switch path {
	case "/", "/health", "/metrics", "/ready":
		return path
	default:
		return "unmatched"
	}
}

func recordEndpointCall(endpoint string) {
	endpointCallsTotal.WithLabelValues(endpoint).Inc()
}

func newResponseRecorder(w http.ResponseWriter) *responseRecorder {
	return &responseRecorder{
		ResponseWriter: w,
		statusCode:     http.StatusOK,
	}
}

func (recorder *responseRecorder) WriteHeader(statusCode int) {
	recorder.statusCode = statusCode
	recorder.ResponseWriter.WriteHeader(statusCode)
}

func (recorder *responseRecorder) Write(data []byte) (int, error) {
	written, err := recorder.ResponseWriter.Write(data)
	recorder.bytesWritten += written
	return written, err
}

func emitLog(level, loggerName, message string, fields map[string]any) {
	payload := map[string]any{
		"timestamp": time.Now().UTC().Format(time.RFC3339Nano),
		"level":     level,
		"logger":    loggerName,
	}

	if message != "" {
		payload["message"] = message
	}

	for key, value := range fields {
		payload[key] = value
	}

	encoded, err := json.Marshal(payload)
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to marshal log entry: %v\n", err)
		return
	}

	logMu.Lock()
	defer logMu.Unlock()

	if _, err := fmt.Fprintln(logOutput, string(encoded)); err != nil {
		fmt.Fprintf(os.Stderr, "failed to write log entry: %v\n", err)
	}
}

func queryString(r *http.Request) string {
	if r.URL.RawQuery == "" {
		return ""
	}

	return "?" + r.URL.RawQuery
}

// mainHandler serves GET /.
func mainHandler(w http.ResponseWriter, r *http.Request) {
	recordEndpointCall("/")
	payload := RootResponse{
		Service:   getServiceInfo(),
		System:    getSystemInfo(),
		Runtime:   getUptime(),
		Request:   getRequestInfo(r),
		Endpoints: listEndpoints(),
	}

	writeJSON(w, http.StatusOK, payload)
}

// healthHandler serves GET /health.
func healthHandler(w http.ResponseWriter, r *http.Request) {
	recordEndpointCall("/health")
	writeStatusResponse(w, "healthy")
}

// readinessHandler serves GET /ready.
func readinessHandler(w http.ResponseWriter, r *http.Request) {
	recordEndpointCall("/ready")
	writeStatusResponse(w, "ready")
}

func writeStatusResponse(w http.ResponseWriter, status string) {
	payload := StatusResponse{
		Status:        status,
		Timestamp:     time.Now().UTC().Format("2006-01-02T15:04:05.000000-07:00"),
		UptimeSeconds: getUptime().Seconds,
	}

	writeJSON(w, http.StatusOK, payload)
}

// metricsHandler serves GET /metrics.
func metricsHandler(w http.ResponseWriter, r *http.Request) {
	recordEndpointCall("/metrics")
	metricsHTTPHandler.ServeHTTP(w, r)
}

// notFound returns a JSON 404.
func notFound(w http.ResponseWriter, r *http.Request) {
	emitLog("WARNING", serviceLoggerName, "request returned not found", map[string]any{
		"client_ip":   clientIP(r),
		"method":      r.Method,
		"path":        r.URL.Path,
		"status_code": http.StatusNotFound,
		"user_agent":  r.Header.Get("User-Agent"),
	})
	writeJSON(w, http.StatusNotFound, map[string]string{
		"error":   "Not Found",
		"message": "Endpoint does not exist",
	})
}

// router dispatches requests to handlers.
func router(w http.ResponseWriter, r *http.Request) {
	switch {
	case r.URL.Path == "/" && r.Method == http.MethodGet:
		mainHandler(w, r)
	case r.URL.Path == "/health" && r.Method == http.MethodGet:
		healthHandler(w, r)
	case r.URL.Path == "/metrics" && r.Method == http.MethodGet:
		metricsHandler(w, r)
	case r.URL.Path == "/ready" && r.Method == http.MethodGet:
		readinessHandler(w, r)
	default:
		notFound(w, r)
	}
}

// recoverMiddleware converts panics into JSON 500 responses.
func recoverMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if err := recover(); err != nil {
				emitLog("ERROR", serviceLoggerName, "request panic recovered", map[string]any{
					"error":      fmt.Sprint(err),
					"client_ip":  clientIP(r),
					"method":     r.Method,
					"path":       r.URL.Path,
					"query":      queryString(r),
					"user_agent": r.Header.Get("User-Agent"),
				})
				writeJSON(w, http.StatusInternalServerError, map[string]string{
					"error":   "Internal Server Error",
					"message": "An unexpected error occurred",
				})
			}
		}()
		next.ServeHTTP(w, r)
	})
}

func requestLoggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		startedAt := time.Now()
		recorder := newResponseRecorder(w)

		next.ServeHTTP(recorder, r)

		emitLog("INFO", accessLoggerName, "", map[string]any{
			"client_ip":       clientIP(r),
			"method":          r.Method,
			"path":            r.URL.Path,
			"query":           queryString(r),
			"status_code":     recorder.statusCode,
			"response_bytes":  fmt.Sprintf("%d", recorder.bytesWritten),
			"request_time_us": time.Since(startedAt).Microseconds(),
			"user_agent":      r.Header.Get("User-Agent"),
		})
	})
}

func metricsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		endpoint := normalizeEndpointLabel(r.URL.Path)
		httpRequestsInProgress.WithLabelValues(r.Method, endpoint).Inc()
		defer httpRequestsInProgress.WithLabelValues(r.Method, endpoint).Dec()

		startedAt := time.Now()
		recorder := newResponseRecorder(w)

		next.ServeHTTP(recorder, r)

		statusCode := strconv.Itoa(recorder.statusCode)
		httpRequestsTotal.WithLabelValues(r.Method, endpoint, statusCode).Inc()
		httpRequestDurationSeconds.WithLabelValues(
			r.Method,
			endpoint,
			statusCode,
		).Observe(time.Since(startedAt).Seconds())
	})
}

// writeJSON serializes a payload with the given status code.
func writeJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(payload); err != nil {
		emitLog("ERROR", serviceLoggerName, "failed to encode response", map[string]any{
			"status_code": status,
			"error":       err.Error(),
		})
	}
}

func main() {
	host := os.Getenv("HOST")
	if host == "" {
		host = "0.0.0.0"
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "5000"
	}

	addr := net.JoinHostPort(host, port)
	emitLog("INFO", serviceLoggerName, "application starting", map[string]any{
		"address": addr,
		"service": serviceName,
		"version": serviceVersion,
	})

	handler := requestLoggingMiddleware(
		metricsMiddleware(recoverMiddleware(http.HandlerFunc(router))),
	)
	if err := http.ListenAndServe(addr, handler); err != nil {
		emitLog("ERROR", serviceLoggerName, "server error", map[string]any{
			"error": err.Error(),
		})
		os.Exit(1)
	}
}
