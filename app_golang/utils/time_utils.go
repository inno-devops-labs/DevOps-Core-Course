package utils

import (
	"time"
)

// GetCurrentTimeInMoscow returns the current time in Moscow formatted as a string
func GetCurrentTimeInMoscow() string {
	loc, err := time.LoadLocation("Europe/Moscow")
	if err != nil {
		return "Error loading Moscow time zone"
	}
	return time.Now().In(loc).Format(time.RFC3339)
}
