package main

import (
	"testing"
	"time"
)

// Tests verify runtime calculations, uptime formatting, and time format validation.
func TestGetRuntime(t *testing.T) {
	// Reset startTime for testing
	originalStartTime := startTime
	startTime = time.Now().Add(-5 * time.Second)
	defer func() { startTime = originalStartTime }()

	runtime := getRuntime()

	// Check uptime is approximately 5 seconds (allow 1 second tolerance)
	if runtime.UptimeSeconds < 4 || runtime.UptimeSeconds > 6 {
		t.Errorf("Expected uptime around 5 seconds, got %d", runtime.UptimeSeconds)
	}

	// Check timezone
	if runtime.Timezone != "UTC" {
		t.Errorf("Expected timezone 'UTC', got '%s'", runtime.Timezone)
	}

	// Check uptime human format
	if runtime.UptimeHuman == "" {
		t.Error("UptimeHuman should not be empty")
	}
}

func TestFormatUptime(t *testing.T) {
	tests := []struct {
		hours   int64
		minutes int64
		want    string
	}{
		{0, 0, "0 hours, 0 minutes"},
		{1, 30, "1 hours, 30 minutes"},
		{24, 0, "24 hours, 0 minutes"},
	}

	for _, tt := range tests {
		got := formatUptime(tt.hours, tt.minutes)
		if got != tt.want {
			t.Errorf("formatUptime(%d, %d) = %s, want %s", tt.hours, tt.minutes, got, tt.want)
		}
	}
}

func TestGetRuntimeCurrentTime(t *testing.T) {
	originalStartTime := startTime
	startTime = time.Now().Add(-10 * time.Minute)
	defer func() { startTime = originalStartTime }()

	runtime := getRuntime()

	// Verify current time is in RFC3339 format
	if runtime.CurrentTime == "" {
		t.Error("CurrentTime should not be empty")
	}

	// Try to parse the time to verify format
	_, err := time.Parse(time.RFC3339, runtime.CurrentTime)
	if err != nil {
		t.Errorf("CurrentTime should be in RFC3339 format, got error: %v", err)
	}
}
