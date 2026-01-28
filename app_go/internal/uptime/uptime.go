package uptime

import (
	"fmt"
	"time"
)

var startTime = time.Now()

// Get returns uptime in seconds and human-readable format.
func Get() (seconds int64, human string) {
	delta := time.Since(startTime)
	seconds = int64(delta.Seconds())
	hours := seconds / 3600
	minutes := (seconds % 3600) / 60
	human = fmt.Sprintf("%d hours, %d minutes", hours, minutes)
	return
}
