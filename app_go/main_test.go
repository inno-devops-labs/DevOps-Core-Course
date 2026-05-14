package main

import (
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
	"time"
)

func TestMainHandler(t *testing.T) {
	// Create a request to pass to our handler
	req, err := http.NewRequest("GET", "/", nil)
	if err != nil {
		t.Fatal(err)
	}

	// Create a ResponseRecorder to record the response
	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(mainHandler)

	// Serve the request
	handler.ServeHTTP(rr, req)

	// Check status code
	if status := rr.Code; status != http.StatusOK {
		t.Errorf("handler returned wrong status code: got %v want %v", status, http.StatusOK)
	}

	// Check content type
	contentType := rr.Header().Get("Content-Type")
	if contentType != "application/json" {
		t.Errorf("handler returned wrong content type: got %v want application/json", contentType)
	}

	// Check that response body contains expected fields
	body := rr.Body.String()
	expectedFields := []string{
		"service",
		"system",
		"runtime",
		"request",
		"endpoints",
		"devops-info-service",
		"1.0.0",
		"/init-file",
		"/metrics",
	}

	for _, field := range expectedFields {
		if !contains(body, field) {
			t.Errorf("response body does not contain expected field: %s", field)
		}
	}
}

func TestInitFileHandler(t *testing.T) {
	tmp := t.TempDir()
	path := tmp + "/index.html"
	expected := "downloaded by init"
	t.Setenv("INIT_FILE_PATH", path)

	if err := os.WriteFile(path, []byte(expected), 0644); err != nil {
		t.Fatal(err)
	}

	req, err := http.NewRequest("GET", "/init-file", nil)
	if err != nil {
		t.Fatal(err)
	}

	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(initFileHandler)
	handler.ServeHTTP(rr, req)

	if status := rr.Code; status != http.StatusOK {
		t.Errorf("handler returned wrong status code: got %v want %v", status, http.StatusOK)
	}

	if body := rr.Body.String(); body != expected {
		t.Errorf("handler returned wrong body: got %q want %q", body, expected)
	}
}

func TestMetricsHandler(t *testing.T) {
	req, err := http.NewRequest("GET", "/metrics", nil)
	if err != nil {
		t.Fatal(err)
	}

	rr := httptest.NewRecorder()
	mux := http.NewServeMux()
	registerHandlers(mux)

	mux.ServeHTTP(rr, req)

	if status := rr.Code; status != http.StatusOK {
		t.Errorf("handler returned wrong status code: got %v want %v", status, http.StatusOK)
	}

	body := rr.Body.String()
	if !contains(body, "go_gc_duration_seconds") && !contains(body, "go_goroutines") {
		t.Errorf("metrics response does not contain expected Go runtime metrics")
	}
}

func TestHealthHandler(t *testing.T) {
	req, err := http.NewRequest("GET", "/health", nil)
	if err != nil {
		t.Fatal(err)
	}

	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(healthHandler)

	handler.ServeHTTP(rr, req)

	// Check status code
	if status := rr.Code; status != http.StatusOK {
		t.Errorf("handler returned wrong status code: got %v want %v", status, http.StatusOK)
	}

	// Check content type
	contentType := rr.Header().Get("Content-Type")
	if contentType != "application/json" {
		t.Errorf("handler returned wrong content type: got %v want application/json", contentType)
	}

	// Check response body contains expected fields
	body := rr.Body.String()
	expectedFields := []string{
		"status",
		"healthy",
		"timestamp",
		"uptime_seconds",
	}

	for _, field := range expectedFields {
		if !contains(body, field) {
			t.Errorf("response body does not contain expected field: %s", field)
		}
	}
}

func TestNotFoundHandler(t *testing.T) {
	req, err := http.NewRequest("GET", "/nonexistent", nil)
	if err != nil {
		t.Fatal(err)
	}

	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(mainHandler) // mainHandler handles 404

	handler.ServeHTTP(rr, req)

	// Should return 404
	if status := rr.Code; status != http.StatusNotFound {
		t.Errorf("handler returned wrong status code: got %v want %v", status, http.StatusNotFound)
	}

	// Check error message
	body := rr.Body.String()
	if !contains(body, "Not Found") {
		t.Errorf("response body does not contain error message")
	}
}

func TestGetUptime(t *testing.T) {
	// Wait a bit to ensure uptime increases
	time.Sleep(100 * time.Millisecond)

	seconds1, human1 := getUptime()

	// Verify uptime is non-negative
	if seconds1 < 0 {
		t.Errorf("uptime seconds should be non-negative, got %d", seconds1)
	}

	// Verify human format contains expected text
	if human1 == "" {
		t.Errorf("uptime human format should not be empty")
	}

	// Wait and check again
	time.Sleep(100 * time.Millisecond)
	seconds2, human2 := getUptime()

	// Uptime should increase
	if seconds2 < seconds1 {
		t.Errorf("uptime should increase over time: got %d, previous %d", seconds2, seconds1)
	}

	// Human format should be different or same (depending on timing)
	if human2 == "" {
		t.Errorf("uptime human format should not be empty")
	}
}

func TestGetHostname(t *testing.T) {
	hostname := getHostname()
	if hostname == "" {
		t.Errorf("hostname should not be empty")
	}
}

// Helper function to check if string contains substring
func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(substr) == 0 ||
		(len(s) > len(substr) && containsHelper(s, substr)))
}

func containsHelper(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}
