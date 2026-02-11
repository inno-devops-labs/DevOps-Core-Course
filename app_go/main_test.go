package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
)

func setupRouter() *gin.Engine {
	gin.SetMode(gin.TestMode)
	r := gin.Default()

	r.GET("/", func(c *gin.Context) {
		s, human := uptime()
		service := map[string]string{
			"name":        getenv("SERVICE_NAME", "devops-info-service"),
			"version":     getenv("SERVICE_VERSION", "1.0.0"),
			"description": getenv("SERVICE_DESCRIPTION", "DevOps course info service"),
			"framework":   "gin",
		}
		system := map[string]interface{}{
			"hostname":         hostname(),
			"platform":         "linux",
			"platform_version": "test",
			"architecture":     "amd64",
			"cpu_count":        4,
			"go_version":       "go1.23",
		}
		runtimeInfo := map[string]interface{}{
			"uptime_seconds": s,
			"uptime_human":   human,
			"current_time":   "2024-01-28T12:00:00Z",
			"timezone":       "UTC",
		}
		requestInfo := map[string]interface{}{
			"client_ip":  c.ClientIP(),
			"user_agent": c.Request.UserAgent(),
			"method":     c.Request.Method,
			"path":       c.Request.URL.Path,
		}
		endpoints := []map[string]string{
			{"path": "/", "method": "GET", "description": "Service information"},
			{"path": "/health", "method": "GET", "description": "Health check"},
		}
		resp := map[string]interface{}{
			"service":   service,
			"system":    system,
			"runtime":   runtimeInfo,
			"request":   requestInfo,
			"endpoints": endpoints,
		}
		c.JSON(http.StatusOK, resp)
	})

	r.GET("/health", func(c *gin.Context) {
		s, _ := uptime()
		c.JSON(http.StatusOK, gin.H{
			"status":         "healthy",
			"timestamp":      "2024-01-28T12:00:00Z",
			"uptime_seconds": s,
		})
	})

	return r
}

func TestRootEndpoint(t *testing.T) {
	router := setupRouter()

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/", nil)
	router.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", w.Code)
	}

	var response map[string]interface{}
	if err := json.Unmarshal(w.Body.Bytes(), &response); err != nil {
		t.Errorf("Failed to parse JSON response: %v", err)
	}

	// Test required sections exist
	sections := []string{"service", "system", "runtime", "request", "endpoints"}
	for _, section := range sections {
		if _, exists := response[section]; !exists {
			t.Errorf("Response missing required section: %s", section)
		}
	}

	// Test service section
	service := response["service"].(map[string]interface{})
	if service["framework"] != "gin" {
		t.Errorf("Expected framework 'gin', got %v", service["framework"])
	}

	// Test endpoints section is a list
	endpoints := response["endpoints"].([]interface{})
	if len(endpoints) < 2 {
		t.Errorf("Expected at least 2 endpoints, got %d", len(endpoints))
	}
}

func TestHealthEndpoint(t *testing.T) {
	router := setupRouter()

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/health", nil)
	router.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", w.Code)
	}

	var response map[string]interface{}
	if err := json.Unmarshal(w.Body.Bytes(), &response); err != nil {
		t.Errorf("Failed to parse JSON response: %v", err)
	}

	// Test status field
	if response["status"] != "healthy" {
		t.Errorf("Expected status 'healthy', got %v", response["status"])
	}

	// Test required fields exist
	requiredFields := []string{"status", "timestamp", "uptime_seconds"}
	for _, field := range requiredFields {
		if _, exists := response[field]; !exists {
			t.Errorf("Health response missing required field: %s", field)
		}
	}
}

func TestNotFoundEndpoint(t *testing.T) {
	router := setupRouter()

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/nonexistent", nil)
	router.ServeHTTP(w, req)

	if w.Code != http.StatusNotFound {
		t.Errorf("Expected status 404, got %d", w.Code)
	}
}

func TestCustomUserAgent(t *testing.T) {
	router := setupRouter()

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/", nil)
	req.Header.Set("User-Agent", "TestBot/1.0")
	router.ServeHTTP(w, req)

	var response map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &response)

	request := response["request"].(map[string]interface{})
	if request["user_agent"] != "TestBot/1.0" {
		t.Errorf("Expected user agent 'TestBot/1.0', got %v", request["user_agent"])
	}
}

func TestRequestMethod(t *testing.T) {
	router := setupRouter()

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/", nil)
	router.ServeHTTP(w, req)

	var response map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &response)

	request := response["request"].(map[string]interface{})
	if request["method"] != "GET" {
		t.Errorf("Expected method 'GET', got %v", request["method"])
	}
}
