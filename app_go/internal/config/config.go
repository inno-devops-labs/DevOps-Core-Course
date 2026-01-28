package config

import "os"

// Config holds application configuration.
type Config struct {
	Port string
}

// FromEnv reads configuration from environment variables with sensible defaults.
func FromEnv() Config {
	port := os.Getenv("PORT")
	if port == "" {
		port = "5002"
	}

	return Config{
		Port: port,
	}
}
