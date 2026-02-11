package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestMainHandler(t *testing.T) {
	req := httptest.NewRequest("GET", "/", nil)
	req.Header.Set("User-Agent", "TestClient/1.0")
	w := httptest.NewRecorder()

	mainHandler(w, req)

	resp := w.Result()
	if resp.StatusCode != http.StatusOK {
		t.Errorf("expected status 200, got %d", resp.StatusCode)
	}

	contentType := resp.Header.Get("Content-Type")
	if !strings.Contains(contentType, "application/json") {
		t.Errorf("expected JSON content type, got %s", contentType)
	}

	var info ServiceInfo
	if err := json.NewDecoder(resp.Body).Decode(&info); err != nil {
		t.Fatalf("failed to decode JSON: %v", err)
	}

	// Verify service info
	if info.Service.Name != "devops-info-service" {
		t.Errorf("expected service name 'devops-info-service', got %s", info.Service.Name)
	}
	if info.Service.Version != "1.0.0" {
		t.Errorf("expected version '1.0.0', got %s", info.Service.Version)
	}
	if info.Service.Framework != "Go net/http" {
		t.Errorf("expected framework 'Go net/http', got %s", info.Service.Framework)
	}

	// Verify system info
	if info.System.Hostname == "" {
		t.Error("expected non-empty hostname")
	}
	if info.System.Platform == "" {
		t.Error("expected non-empty platform")
	}
	if info.System.CPUCount <= 0 {
		t.Errorf("expected positive CPU count, got %d", info.System.CPUCount)
	}
	if info.System.GoVersion == "" {
		t.Error("expected non-empty Go version")
	}

	// Verify runtime info
	if info.Runtime.UptimeSeconds < 0 {
		t.Errorf("expected non-negative uptime, got %f", info.Runtime.UptimeSeconds)
	}
	if info.Runtime.Timezone != "UTC" {
		t.Errorf("expected timezone 'UTC', got %s", info.Runtime.Timezone)
	}

	// Verify request info
	if info.Request.Method != "GET" {
		t.Errorf("expected method GET, got %s", info.Request.Method)
	}
	if info.Request.Path != "/" {
		t.Errorf("expected path '/', got %s", info.Request.Path)
	}

	// Verify endpoints list
	if len(info.Endpoints) < 2 {
		t.Errorf("expected at least 2 endpoints, got %d", len(info.Endpoints))
	}
}

func TestHealthHandler(t *testing.T) {
	req := httptest.NewRequest("GET", "/health", nil)
	w := httptest.NewRecorder()

	healthHandler(w, req)

	resp := w.Result()
	if resp.StatusCode != http.StatusOK {
		t.Errorf("expected status 200, got %d", resp.StatusCode)
	}

	var health HealthResponse
	if err := json.NewDecoder(resp.Body).Decode(&health); err != nil {
		t.Fatalf("failed to decode JSON: %v", err)
	}

	if health.Status != "healthy" {
		t.Errorf("expected status 'healthy', got %s", health.Status)
	}
	if health.Timestamp == "" {
		t.Error("expected non-empty timestamp")
	}
	if health.UptimeSeconds < 0 {
		t.Errorf("expected non-negative uptime, got %f", health.UptimeSeconds)
	}
}

func TestFormatUptime(t *testing.T) {
	tests := []struct {
		seconds  float64
		contains []string
	}{
		{0, []string{"0 second"}},
		{1, []string{"1 second"}},
		{65, []string{"1 minute", "5 seconds"}},
		{3661, []string{"1 hour", "1 minute", "1 second"}},
		{7200, []string{"2 hours"}},
	}

	for _, tt := range tests {
		result := formatUptime(tt.seconds)
		for _, s := range tt.contains {
			if !strings.Contains(result, s) {
				t.Errorf("formatUptime(%f) = %q, expected to contain %q", tt.seconds, result, s)
			}
		}
	}
}

func TestGetClientIP(t *testing.T) {
	tests := []struct {
		name   string
		header string
		value  string
		want   string
	}{
		{"X-Forwarded-For", "X-Forwarded-For", "192.168.1.1", "192.168.1.1"},
		{"X-Real-Ip", "X-Real-Ip", "10.0.0.1", "10.0.0.1"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			req := httptest.NewRequest("GET", "/", nil)
			req.Header.Set(tt.header, tt.value)
			got := getClientIP(req)
			if got != tt.want {
				t.Errorf("getClientIP() = %q, want %q", got, tt.want)
			}
		})
	}
}
