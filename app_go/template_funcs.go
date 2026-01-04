package main

import (
	"html/template"
)

func init() {
	// Add custom template functions
	templates = template.Must(template.New("").Funcs(template.FuncMap{
		"sub": func(a, b int) int {
			return a - b
		},
		"iterate": func(count int) []int {
			var i int
			var Items []int
			for i = 0; i < count; i++ {
				Items = append(Items, i)
			}
			return Items
		},
	}).ParseGlob("templates/*.html"))
}
