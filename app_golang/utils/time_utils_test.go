package utils

import (
	"testing"
	"time"
)

// TestGetCurrentTimeInMoscow checks if the time returned by GetCurrentTimeInMoscow is in the correct format
func TestGetCurrentTimeInMoscow(t *testing.T) {
	currentTime := GetCurrentTimeInMoscow()

	// Check if the returned time is in RFC3339 format
	_, err := time.Parse(time.RFC3339, currentTime)
	if err != nil {
		t.Errorf("Expected time in RFC3339 format, got %v", currentTime)
	}
}
