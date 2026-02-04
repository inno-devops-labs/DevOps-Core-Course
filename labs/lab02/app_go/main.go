package main

import (
	"log"
	"net/http"
	"os"
	"runtime"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
)

var startTime = time.Now().UTC()

func uptime() (int64, string) {
	secs := int64(time.Since(startTime).Seconds())
	h := secs / 3600
	m := (secs % 3600) / 60
	return secs, strconv.FormatInt(h, 10) + " hours, " + strconv.FormatInt(m, 10) + " minutes"
}

func main() {
	gin.SetMode(gin.ReleaseMode)
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
			"platform":         runtime.GOOS,
			"platform_version": runtime.Version(),
			"architecture":     runtime.GOARCH,
			"cpu_count":        runtime.NumCPU(),
			"go_version":       runtime.Version(),
		}
		runtimeInfo := map[string]interface{}{
			"uptime_seconds": s,
			"uptime_human":   human,
			"current_time":   time.Now().UTC().Format(time.RFC3339),
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
			"timestamp":      time.Now().UTC().Format(time.RFC3339),
			"uptime_seconds": s,
		})
	})

	host := getenv("HOST", "0.0.0.0")
	port := getenv("PORT", "8080")
	addr := host + ":" + port
	log.Printf("starting devops-info-service on %s", addr)
	if err := r.Run(addr); err != nil {
		log.Fatalf("server failed: %v", err)
	}
}

func getenv(k, d string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return d
}

func hostname() string {
	h, err := os.Hostname()
	if err != nil {
		return "unknown"
	}
	return h
}
