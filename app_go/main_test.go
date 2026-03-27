package main

import (
	"bytes"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"strconv"
	"strings"
	"testing"
)

func captureLogOutput(w io.Writer) func() {
	logMu.Lock()
	previous := logOutput
	logOutput = w
	logMu.Unlock()

	return func() {
		logMu.Lock()
		logOutput = previous
		logMu.Unlock()
	}
}

func decodeLogEntries(t *testing.T, buffer *bytes.Buffer) []map[string]any {
	t.Helper()

	lines := bytes.Split(bytes.TrimSpace(buffer.Bytes()), []byte("\n"))
	entries := make([]map[string]any, 0, len(lines))

	for _, line := range lines {
		if len(line) == 0 {
			continue
		}

		var entry map[string]any
		if err := json.Unmarshal(line, &entry); err != nil {
			t.Fatalf("failed to decode log entry: %v", err)
		}
		entries = append(entries, entry)
	}

	if len(entries) == 0 {
		t.Fatal("expected at least one log entry")
	}

	return entries
}

func decodeLogEntry(t *testing.T, buffer *bytes.Buffer) map[string]any {
	t.Helper()

	entries := decodeLogEntries(t, buffer)
	if len(entries) != 1 {
		t.Fatalf("expected exactly one log line, got %d", len(entries))
	}

	return entries[0]
}

func decodeJSONResponse[T any](t *testing.T, recorder *httptest.ResponseRecorder) T {
	t.Helper()

	var payload T
	if err := json.Unmarshal(recorder.Body.Bytes(), &payload); err != nil {
		t.Fatalf("failed to decode JSON response: %v", err)
	}

	return payload
}

func performRequest(handler http.Handler, method, path string) *httptest.ResponseRecorder {
	request := httptest.NewRequest(method, path, nil)
	request.RemoteAddr = "203.0.113.7:4321"
	request.Header.Set("User-Agent", "go-test")

	recorder := httptest.NewRecorder()
	handler.ServeHTTP(recorder, request)
	return recorder
}

func metricValue(metricsText, sampleName string, labels map[string]string) (float64, bool) {
	for _, line := range strings.Split(metricsText, "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		fields := strings.Fields(line)
		if len(fields) != 2 {
			continue
		}

		metricName, metricLabels := parseMetricSample(fields[0])
		if metricName != sampleName {
			continue
		}
		if !labelsMatch(metricLabels, labels) {
			continue
		}

		value, err := strconv.ParseFloat(fields[1], 64)
		if err != nil {
			return 0, false
		}
		return value, true
	}

	return 0, false
}

func parseMetricSample(sample string) (string, map[string]string) {
	openBrace := strings.Index(sample, "{")
	if openBrace == -1 {
		return sample, map[string]string{}
	}

	name := sample[:openBrace]
	labelText := strings.TrimSuffix(sample[openBrace+1:], "}")
	labels := map[string]string{}
	if labelText == "" {
		return name, labels
	}

	for _, part := range strings.Split(labelText, ",") {
		key, value, found := strings.Cut(part, "=")
		if !found {
			continue
		}
		labels[key] = strings.Trim(value, "\"")
	}

	return name, labels
}

func labelsMatch(actual map[string]string, expected map[string]string) bool {
	for key, value := range expected {
		if actual[key] != value {
			return false
		}
	}
	return true
}

func scrapeMetrics(t *testing.T) string {
	t.Helper()

	recorder := performRequest(http.HandlerFunc(metricsHandler), http.MethodGet, "/metrics")
	if recorder.Code != http.StatusOK {
		t.Fatalf("expected metrics status %d, got %d", http.StatusOK, recorder.Code)
	}

	return recorder.Body.String()
}

func TestIndexReturnsExpectedJSONStructureAndTypes(t *testing.T) {
	restore := captureLogOutput(io.Discard)
	defer restore()

	recorder := performRequest(http.HandlerFunc(router), http.MethodGet, "/")
	if recorder.Code != http.StatusOK {
		t.Fatalf("expected status %d, got %d", http.StatusOK, recorder.Code)
	}

	payload := decodeJSONResponse[RootResponse](t, recorder)
	if payload.Service.Name != serviceName {
		t.Fatalf("expected service name %q, got %q", serviceName, payload.Service.Name)
	}
	if payload.Service.Framework != serviceFramework {
		t.Fatalf("expected framework %q, got %q", serviceFramework, payload.Service.Framework)
	}
	if payload.Service.Version == "" {
		t.Fatal("expected non-empty version")
	}
	if payload.System.Hostname == "" {
		t.Fatal("expected hostname to be populated")
	}
	if payload.System.CPUCount < 1 {
		t.Fatalf("expected cpu_count >= 1, got %d", payload.System.CPUCount)
	}
	if payload.Runtime.Seconds < 0 {
		t.Fatalf("expected non-negative uptime, got %d", payload.Runtime.Seconds)
	}
	if payload.Request.ClientIP != "203.0.113.7" {
		t.Fatalf("expected client_ip %q, got %q", "203.0.113.7", payload.Request.ClientIP)
	}

	routeIndex := map[string]bool{}
	for _, endpoint := range payload.Endpoints {
		routeIndex[endpoint.Method+" "+endpoint.Path] = true
	}

	for _, route := range []string{
		http.MethodGet + " /",
		http.MethodGet + " /health",
		http.MethodGet + " /ready",
		http.MethodGet + " /metrics",
	} {
		if !routeIndex[route] {
			t.Fatalf("expected endpoint %q to be listed", route)
		}
	}
}

func TestHealthReturnsExpectedJSONStructureAndTypes(t *testing.T) {
	restore := captureLogOutput(io.Discard)
	defer restore()

	recorder := performRequest(http.HandlerFunc(router), http.MethodGet, "/health")
	if recorder.Code != http.StatusOK {
		t.Fatalf("expected status %d, got %d", http.StatusOK, recorder.Code)
	}

	payload := decodeJSONResponse[StatusResponse](t, recorder)
	if payload.Status != "healthy" {
		t.Fatalf("expected status %q, got %q", "healthy", payload.Status)
	}
	if payload.UptimeSeconds < 0 {
		t.Fatalf("expected non-negative uptime, got %d", payload.UptimeSeconds)
	}
	if payload.Timestamp == "" {
		t.Fatal("expected non-empty timestamp")
	}
}

func TestReadyReturnsExpectedJSONStructureAndTypes(t *testing.T) {
	restore := captureLogOutput(io.Discard)
	defer restore()

	recorder := performRequest(http.HandlerFunc(router), http.MethodGet, "/ready")
	if recorder.Code != http.StatusOK {
		t.Fatalf("expected status %d, got %d", http.StatusOK, recorder.Code)
	}

	payload := decodeJSONResponse[StatusResponse](t, recorder)
	if payload.Status != "ready" {
		t.Fatalf("expected status %q, got %q", "ready", payload.Status)
	}
	if payload.UptimeSeconds < 0 {
		t.Fatalf("expected non-negative uptime, got %d", payload.UptimeSeconds)
	}
	if payload.Timestamp == "" {
		t.Fatal("expected non-empty timestamp")
	}
}

func TestUnknownEndpointReturnsJSON404(t *testing.T) {
	restore := captureLogOutput(io.Discard)
	defer restore()

	recorder := performRequest(http.HandlerFunc(router), http.MethodGet, "/missing")
	if recorder.Code != http.StatusNotFound {
		t.Fatalf("expected status %d, got %d", http.StatusNotFound, recorder.Code)
	}

	payload := decodeJSONResponse[map[string]string](t, recorder)
	expected := map[string]string{
		"error":   "Not Found",
		"message": "Endpoint does not exist",
	}
	if payload["error"] != expected["error"] || payload["message"] != expected["message"] {
		t.Fatalf("expected %#v, got %#v", expected, payload)
	}
}

func TestNotFoundEmitsJSONWarningLog(t *testing.T) {
	var buffer bytes.Buffer
	restore := captureLogOutput(&buffer)
	defer restore()

	recorder := performRequest(http.HandlerFunc(router), http.MethodGet, "/missing")
	if recorder.Code != http.StatusNotFound {
		t.Fatalf("expected status %d, got %d", http.StatusNotFound, recorder.Code)
	}

	entry := decodeLogEntry(t, &buffer)
	if entry["level"] != "WARNING" {
		t.Fatalf("expected WARNING level, got %#v", entry["level"])
	}
	if entry["logger"] != serviceLoggerName {
		t.Fatalf("expected logger %q, got %#v", serviceLoggerName, entry["logger"])
	}
	if entry["message"] != "request returned not found" {
		t.Fatalf("expected message to be logged, got %#v", entry["message"])
	}
	if entry["status_code"] != float64(http.StatusNotFound) {
		t.Fatalf("expected status_code %d, got %#v", http.StatusNotFound, entry["status_code"])
	}
}

func TestRequestLoggingMiddlewareEmitsJSONAccessLog(t *testing.T) {
	var buffer bytes.Buffer
	restore := captureLogOutput(&buffer)
	defer restore()

	handler := requestLoggingMiddleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusCreated)
		_, _ = w.Write([]byte(`{"ok":true}`))
	}))

	request := httptest.NewRequest(http.MethodGet, "/health?full=1", nil)
	request.RemoteAddr = "203.0.113.10:4321"
	request.Header.Set("User-Agent", "go-test")

	recorder := httptest.NewRecorder()
	handler.ServeHTTP(recorder, request)

	if recorder.Code != http.StatusCreated {
		t.Fatalf("expected status %d, got %d", http.StatusCreated, recorder.Code)
	}

	entry := decodeLogEntry(t, &buffer)
	if entry["level"] != "INFO" {
		t.Fatalf("expected INFO level, got %#v", entry["level"])
	}
	if entry["logger"] != accessLoggerName {
		t.Fatalf("expected logger %q, got %#v", accessLoggerName, entry["logger"])
	}
	if entry["client_ip"] != "203.0.113.10" {
		t.Fatalf("expected client_ip to be logged, got %#v", entry["client_ip"])
	}
	if entry["method"] != http.MethodGet {
		t.Fatalf("expected method to be logged, got %#v", entry["method"])
	}
	if entry["path"] != "/health" {
		t.Fatalf("expected path to be logged, got %#v", entry["path"])
	}
	if entry["query"] != "?full=1" {
		t.Fatalf("expected query string to be logged, got %#v", entry["query"])
	}
	if entry["status_code"] != float64(http.StatusCreated) {
		t.Fatalf("expected status_code to be logged, got %#v", entry["status_code"])
	}
	if entry["response_bytes"] != "11" {
		t.Fatalf("expected response_bytes to be logged, got %#v", entry["response_bytes"])
	}
	if _, ok := entry["request_time_us"].(float64); !ok {
		t.Fatalf("expected request_time_us to be numeric, got %#v", entry["request_time_us"])
	}
	if entry["user_agent"] != "go-test" {
		t.Fatalf("expected user_agent to be logged, got %#v", entry["user_agent"])
	}
	if _, hasMessage := entry["message"]; hasMessage {
		t.Fatalf("access log should not include message, got %#v", entry["message"])
	}
}

func TestRecoverMiddlewareEmitsJSONPanicLog(t *testing.T) {
	var buffer bytes.Buffer
	restore := captureLogOutput(&buffer)
	defer restore()

	handler := recoverMiddleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		panic("boom")
	}))

	request := httptest.NewRequest(http.MethodGet, "/explode", nil)
	request.RemoteAddr = "203.0.113.20:8080"
	request.Header.Set("User-Agent", "go-test")

	recorder := httptest.NewRecorder()
	handler.ServeHTTP(recorder, request)

	if recorder.Code != http.StatusInternalServerError {
		t.Fatalf("expected status %d, got %d", http.StatusInternalServerError, recorder.Code)
	}

	entry := decodeLogEntry(t, &buffer)
	if entry["level"] != "ERROR" {
		t.Fatalf("expected ERROR level, got %#v", entry["level"])
	}
	if entry["logger"] != serviceLoggerName {
		t.Fatalf("expected logger %q, got %#v", serviceLoggerName, entry["logger"])
	}
	if entry["message"] != "request panic recovered" {
		t.Fatalf("expected panic message to be logged, got %#v", entry["message"])
	}
	if entry["error"] != "boom" {
		t.Fatalf("expected panic error to be logged, got %#v", entry["error"])
	}
	if entry["path"] != "/explode" {
		t.Fatalf("expected panic path to be logged, got %#v", entry["path"])
	}
	if entry["query"] != "" {
		t.Fatalf("expected empty query string, got %#v", entry["query"])
	}
	if entry["client_ip"] != "203.0.113.20" {
		t.Fatalf("expected client_ip to be logged, got %#v", entry["client_ip"])
	}
}

func TestMetricsEndpointExposesHTTPAndApplicationMetrics(t *testing.T) {
	restore := captureLogOutput(io.Discard)
	defer restore()

	handler := metricsMiddleware(http.HandlerFunc(router))

	performRequest(handler, http.MethodGet, "/")
	performRequest(handler, http.MethodGet, "/health")
	performRequest(handler, http.MethodGet, "/ready")
	performRequest(handler, http.MethodGet, "/does-not-exist")

	recorder := performRequest(handler, http.MethodGet, "/metrics")
	if recorder.Code != http.StatusOK {
		t.Fatalf("expected status %d, got %d", http.StatusOK, recorder.Code)
	}
	if !strings.HasPrefix(recorder.Header().Get("Content-Type"), "text/plain") {
		t.Fatalf("expected text/plain content type, got %q", recorder.Header().Get("Content-Type"))
	}

	metricsText := recorder.Body.String()
	for _, tc := range []struct {
		name   string
		labels map[string]string
	}{
		{name: "http_requests_total", labels: map[string]string{"method": "GET", "endpoint": "/", "status_code": "200"}},
		{name: "http_requests_total", labels: map[string]string{"method": "GET", "endpoint": "/health", "status_code": "200"}},
		{name: "http_requests_total", labels: map[string]string{"method": "GET", "endpoint": "/ready", "status_code": "200"}},
		{name: "http_requests_total", labels: map[string]string{"method": "GET", "endpoint": "unmatched", "status_code": "404"}},
		{name: "http_request_duration_seconds_count", labels: map[string]string{"method": "GET", "endpoint": "/", "status_code": "200"}},
		{name: "devops_info_endpoint_calls_total", labels: map[string]string{"endpoint": "/"}},
		{name: "devops_info_endpoint_calls_total", labels: map[string]string{"endpoint": "/ready"}},
		{name: "devops_info_system_info_duration_seconds_count", labels: map[string]string{}},
	} {
		value, ok := metricValue(metricsText, tc.name, tc.labels)
		if !ok || value < 1.0 {
			t.Fatalf("expected %s with labels %#v to be >= 1, got ok=%v value=%v", tc.name, tc.labels, ok, value)
		}
	}

	value, ok := metricValue(
		metricsText,
		"http_requests_in_progress",
		map[string]string{"method": "GET", "endpoint": "/"},
	)
	if !ok || value != 0.0 {
		t.Fatalf("expected in-progress gauge to be 0, got ok=%v value=%v", ok, value)
	}
}

func TestMetricsCountInternalServerErrorsWithStatusLabels(t *testing.T) {
	restore := captureLogOutput(io.Discard)
	defer restore()

	labels := map[string]string{"method": "GET", "endpoint": "/", "status_code": "500"}
	before, _ := metricValue(scrapeMetrics(t), "http_requests_total", labels)

	handler := metricsMiddleware(recoverMiddleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		panic("boom")
	})))
	recorder := performRequest(handler, http.MethodGet, "/")
	if recorder.Code != http.StatusInternalServerError {
		t.Fatalf("expected status %d, got %d", http.StatusInternalServerError, recorder.Code)
	}

	after, ok := metricValue(scrapeMetrics(t), "http_requests_total", labels)
	if !ok {
		t.Fatalf("expected %s with labels %#v to exist after panic request", "http_requests_total", labels)
	}
	if after != before+1.0 {
		t.Fatalf("expected counter to increase by 1, got before=%v after=%v", before, after)
	}
}
