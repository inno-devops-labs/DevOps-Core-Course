package main

import (
	"encoding/json"
	"io"
	"log"
	"net/http"
	"net/http/httptest"
	"runtime"
	"strings"
	"testing"
	"time"
)

func init() {
	log.SetOutput(io.Discard)
}

func newTestHandler() http.Handler {
	rt := newRouter()
	rt.Handle(http.MethodGet, "/", "Root endpoint: returns service metadata and diagnostic information.", rootHandler(rt))
	rt.Handle(http.MethodGet, "/health", "Health check endpoint for monitoring and Kubernetes probes.", healthHandler)

	return recoverMiddleware(loggingMiddleware(rt))
}

func TestRootEndpoint_OK_JSON_Shape(t *testing.T) {
	h := newTestHandler()

	req := httptest.NewRequest(http.MethodGet, "http://example/", nil)
	req.Header.Set("User-Agent", "go-test")
	req.Header.Set("X-Forwarded-For", "1.2.3.4, 5.6.7.8")
	req.RemoteAddr = "9.9.9.9:12345"

	rr := httptest.NewRecorder()
	h.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("expected %d, got %d, body=%s", http.StatusOK, rr.Code, rr.Body.String())
	}
	if ct := rr.Header().Get("Content-Type"); !strings.Contains(ct, "application/json") {
		t.Fatalf("expected application/json content-type, got %q", ct)
	}

	var got RootResponse
	if err := json.Unmarshal(rr.Body.Bytes(), &got); err != nil {
		t.Fatalf("invalid json: %v, body=%s", err, rr.Body.String())
	}

	// Service
	if got.Service.Name != "devops-info-service" {
		t.Fatalf("service.name expected %q, got %q", "devops-info-service", got.Service.Name)
	}
	if got.Service.Framework != "Go net/http" {
		t.Fatalf("service.framework expected %q, got %q", "Go net/http", got.Service.Framework)
	}

	// Request (XFF more priority then RemoteAddr)
	if got.Request.ClientIP != "1.2.3.4" {
		t.Fatalf("request.client_ip expected %q, got %q", "1.2.3.4", got.Request.ClientIP)
	}
	if got.Request.Method != http.MethodGet {
		t.Fatalf("request.method expected %q, got %q", http.MethodGet, got.Request.Method)
	}
	if got.Request.Path != "/" {
		t.Fatalf("request.path expected %q, got %q", "/", got.Request.Path)
	}
	if got.Request.UserAgent != "go-test" {
		t.Fatalf("request.user_agent expected %q, got %q", "go-test", got.Request.UserAgent)
	}

	// System: key fields checker
	if got.System.Platform != runtime.GOOS {
		t.Fatalf("system.platform expected %q, got %q", runtime.GOOS, got.System.Platform)
	}
	if got.System.Architecture != runtime.GOARCH {
		t.Fatalf("system.architecture expected %q, got %q", runtime.GOARCH, got.System.Architecture)
	}
	if got.System.CPUCount <= 0 {
		t.Fatalf("system.cpu_count expected > 0, got %d", got.System.CPUCount)
	}
	if got.System.GoVersion == "" {
		t.Fatalf("system.go_version expected non-empty")
	}

	// Runtime
	if got.Runtime.Timezone != "UTC" {
		t.Fatalf("runtime.timezone expected %q, got %q", "UTC", got.Runtime.Timezone)
	}
	if got.Runtime.UptimeSeconds < 0 {
		t.Fatalf("runtime.uptime_seconds expected >= 0, got %d", got.Runtime.UptimeSeconds)
	}
	if got.Runtime.CurrentTime == "" {
		t.Fatalf("runtime.current_time expected non-empty")
	}

	if len(got.Endpoints) != 2 {
		t.Fatalf("expected 2 endpoints, got %d: %+v", len(got.Endpoints), got.Endpoints)
	}
	if got.Endpoints[0].Method != http.MethodGet || got.Endpoints[0].Path != "/" {
		t.Fatalf("endpoints[0] expected GET /, got %+v", got.Endpoints[0])
	}
	if got.Endpoints[1].Method != http.MethodGet || got.Endpoints[1].Path != "/health" {
		t.Fatalf("endpoints[1] expected GET /health, got %+v", got.Endpoints[1])
	}
}

func TestHealthEndpoint_OK(t *testing.T) {
	h := newTestHandler()

	req := httptest.NewRequest(http.MethodGet, "http://example/health", nil)
	rr := httptest.NewRecorder()
	h.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("expected %d, got %d, body=%s", http.StatusOK, rr.Code, rr.Body.String())
	}

	var got HealthResponse
	if err := json.Unmarshal(rr.Body.Bytes(), &got); err != nil {
		t.Fatalf("invalid json: %v, body=%s", err, rr.Body.String())
	}

	if got.Status != "healthy" {
		t.Fatalf("status expected %q, got %q", "healthy", got.Status)
	}
	if got.UptimeSeconds < 0 {
		t.Fatalf("uptime_seconds expected >= 0, got %d", got.UptimeSeconds)
	}
	if _, err := time.Parse(time.RFC3339, got.Timestamp); err != nil {
		t.Fatalf("timestamp is not RFC3339: %q err=%v", got.Timestamp, err)
	}
}

func TestNotFound_ReturnsJSON404(t *testing.T) {
	h := newTestHandler()

	req := httptest.NewRequest(http.MethodGet, "http://example/nope", nil)
	rr := httptest.NewRecorder()
	h.ServeHTTP(rr, req)

	if rr.Code != http.StatusNotFound {
		t.Fatalf("expected %d, got %d, body=%s", http.StatusNotFound, rr.Code, rr.Body.String())
	}

	var got ErrorResponse
	if err := json.Unmarshal(rr.Body.Bytes(), &got); err != nil {
		t.Fatalf("invalid json: %v, body=%s", err, rr.Body.String())
	}

	if got.Error != "Not Found" {
		t.Fatalf("error expected %q, got %q", "Not Found", got.Error)
	}
	if got.Message == "" {
		t.Fatalf("message expected non-empty")
	}
}

func TestMethodMismatch_TreatedAsNotFound(t *testing.T) {
	h := newTestHandler()

	req := httptest.NewRequest(http.MethodPost, "http://example/health", nil)
	rr := httptest.NewRecorder()
	h.ServeHTTP(rr, req)

	if rr.Code != http.StatusNotFound {
		t.Fatalf("expected %d, got %d, body=%s", http.StatusNotFound, rr.Code, rr.Body.String())
	}
}

func TestRecoverMiddleware_ReturnsJSON500OnPanic(t *testing.T) {
	panicHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		panic("boom")
	})

	h := recoverMiddleware(panicHandler)
	req := httptest.NewRequest(http.MethodGet, "http://example/", nil)
	rr := httptest.NewRecorder()
	h.ServeHTTP(rr, req)

	if rr.Code != http.StatusInternalServerError {
		t.Fatalf("expected %d, got %d, body=%s", http.StatusInternalServerError, rr.Code, rr.Body.String())
	}

	var got ErrorResponse
	if err := json.Unmarshal(rr.Body.Bytes(), &got); err != nil {
		t.Fatalf("invalid json: %v, body=%s", err, rr.Body.String())
	}
	if got.Error != "Internal Server Error" {
		t.Fatalf("error expected %q, got %q", "Internal Server Error", got.Error)
	}
}

func TestClientIP_UsesRemoteAddrWhenNoXFF(t *testing.T) {
	r := httptest.NewRequest(http.MethodGet, "http://example/", nil)
	r.RemoteAddr = "10.0.0.7:5555"

	if got := clientIP(r); got != "10.0.0.7" {
		t.Fatalf("expected %q, got %q", "10.0.0.7", got)
	}
}

func TestClientIP_FallsBackToRawRemoteAddrOnBadFormat(t *testing.T) {
	r := httptest.NewRequest(http.MethodGet, "http://example/", nil)
	r.RemoteAddr = "not-a-host-port"

	if got := clientIP(r); got != "not-a-host-port" {
		t.Fatalf("expected %q, got %q", "not-a-host-port", got)
	}
}

func TestRouterEndpoints_SortedByPathThenMethod(t *testing.T) {
	rt := newRouter()
	dummy := func(w http.ResponseWriter, r *http.Request) {}

	rt.Handle(http.MethodPost, "/same", "p", dummy)
	rt.Handle(http.MethodGet, "/same", "g", dummy)
	rt.Handle(http.MethodGet, "/zzz", "z", dummy)
	rt.Handle(http.MethodGet, "/aaa", "a", dummy)

	eps := rt.Endpoints()

	got := make([]string, 0, len(eps))
	for _, e := range eps {
		got = append(got, e.Method+" "+e.Path)
	}

	want := []string{
		"GET /aaa",
		"GET /same",
		"POST /same",
		"GET /zzz",
	}

	if len(got) != len(want) {
		t.Fatalf("len mismatch: got=%d want=%d", len(got), len(want))
	}
	for i := range want {
		if got[i] != want[i] {
			t.Fatalf("order mismatch at %d: got=%q want=%q\nall=%v", i, got[i], want[i], got)
		}
	}
}
