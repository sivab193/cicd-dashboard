// An outbound-only agent. No HTTP listener, arbitrary shell, or arbitrary paths.
package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
	"time"
)

type Service struct {
	File    string `json:"file"`
	Service string `json:"service"`
}
type Config struct {
	URL      string             `json:"url"`
	ID       string             `json:"id"`
	Token    string             `json:"token"`
	Services map[string]Service `json:"services"`
}
type Task struct {
	ID      string `json:"id"`
	Action  string `json:"action"`
	Service string `json:"service"`
	Image   string `json:"image"`
}

var client = &http.Client{Timeout: 20 * time.Second}
var previousCPUIdle, previousCPUTotal uint64

func request(c Config, method, path string, body any, result any) error {
	b, err := json.Marshal(body)
	if err != nil {
		return err
	}
	req, err := http.NewRequest(method, strings.TrimRight(c.URL, "/")+path, bytes.NewReader(b))
	if err != nil {
		return err
	}
	req.Header.Set("Authorization", "Bearer "+c.Token)
	req.Header.Set("X-Agent-ID", c.ID)
	req.Header.Set("Content-Type", "application/json")
	res, err := client.Do(req)
	if err != nil {
		return err
	}
	defer res.Body.Close()
	if res.StatusCode >= 300 {
		return fmt.Errorf("API returned %d", res.StatusCode)
	}
	if result != nil {
		return json.NewDecoder(io.LimitReader(res.Body, 1<<20)).Decode(result)
	}
	return nil
}
func execute(c Config, t Task) error {
	s, ok := c.Services[t.Service]
	if !ok {
		return fmt.Errorf("service not allowlisted")
	}
	if !filepath.IsAbs(s.File) || s.Service == "" || strings.HasPrefix(s.Service, "-") {
		return fmt.Errorf("invalid allowlist entry")
	}
	args := []string{"compose", "-f", s.File}
	switch t.Action {
	case "restart":
		args = append(args, "restart", s.Service)
	case "stop":
		args = append(args, "stop", s.Service)
	case "deploy", "redeploy", "rollback":
		if t.Action == "rollback" && t.Image == "" {
			return fmt.Errorf("rollback requires image digest")
		}
		args = append(args, "up", "-d", "--pull", "always", "--no-deps", s.Service)
	default:
		return fmt.Errorf("task type not permitted")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
	defer cancel()
	cmd := exec.CommandContext(ctx, "docker", args...)
	cmd.Env = os.Environ()
	if t.Image != "" {
		if !strings.Contains(t.Image, "@sha256:") {
			return fmt.Errorf("pinned image digest required")
		}
		cmd.Env = append(cmd.Env, "CICD_IMAGE="+t.Image)
	}
	cmd.Stdout = io.Discard
	cmd.Stderr = io.Discard
	return cmd.Run()
}

func cpuPercent() float64 {
	file, err := os.Open("/proc/stat")
	if err != nil {
		return 0
	}
	defer file.Close()
	line, _ := bufio.NewReader(file).ReadString('\n')
	fields := strings.Fields(line)
	if len(fields) < 5 || fields[0] != "cpu" {
		return 0
	}
	var total uint64
	values := make([]uint64, 0, len(fields)-1)
	for _, field := range fields[1:] {
		value, err := strconv.ParseUint(field, 10, 64)
		if err != nil {
			return 0
		}
		values = append(values, value)
		total += value
	}
	idle := values[3]
	if len(values) > 4 {
		idle += values[4]
	}
	if previousCPUTotal == 0 || total <= previousCPUTotal {
		previousCPUIdle, previousCPUTotal = idle, total
		return 0
	}
	deltaTotal := total - previousCPUTotal
	deltaIdle := idle - previousCPUIdle
	previousCPUIdle, previousCPUTotal = idle, total
	return 100 * (1 - float64(deltaIdle)/float64(deltaTotal))
}

func memoryPercent() float64 {
	file, err := os.Open("/proc/meminfo")
	if err != nil {
		return 0
	}
	defer file.Close()
	var total, available float64
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		fields := strings.Fields(scanner.Text())
		if len(fields) < 2 {
			continue
		}
		value, _ := strconv.ParseFloat(fields[1], 64)
		switch fields[0] {
		case "MemTotal:":
			total = value
		case "MemAvailable:":
			available = value
		}
	}
	if total == 0 {
		return 0
	}
	return 100 * (total - available) / total
}

func diskPercent() float64 {
	var stats syscall.Statfs_t
	if err := syscall.Statfs("/", &stats); err != nil || stats.Blocks == 0 {
		return 0
	}
	return 100 * (1 - float64(stats.Bavail)/float64(stats.Blocks))
}

func metrics(c Config) map[string]any {
	services := []map[string]any{}
	for name, s := range c.Services {
		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		out, err := exec.CommandContext(ctx, "docker", "compose", "-f", s.File, "ps", "--format", "json", s.Service).Output()
		cancel()
		state := "unknown"
		image := ""
		if err == nil {
			var v map[string]any
			if json.Unmarshal(out, &v) == nil {
				if v["State"] == "running" {
					state = "healthy"
				} else {
					state = "stopped"
				}
				image, _ = v["Image"].(string)
			}
		}
		services = append(services, map[string]any{"name": name, "status": state, "image": image})
	}
	return map[string]any{
		"version":  "1.0.0",
		"services": services,
		"cpu":      cpuPercent(),
		"ram":      memoryPercent(),
		"disk":     diskPercent(),
	}
}
func main() {
	path := os.Getenv("CICD_AGENT_CONFIG")
	if path == "" {
		path = "agent.json"
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		log.Fatal(err)
	}
	var c Config
	if err = json.Unmarshal(raw, &c); err != nil {
		log.Fatal(err)
	}
	u, err := url.Parse(c.URL)
	if err != nil || u.Scheme != "https" {
		log.Fatal("agent requires HTTPS control-plane URL")
	}
	if c.ID == "" || c.Token == "" {
		log.Fatal("agent identity required")
	}
	for {
		if err = request(c, "POST", "/api/agent/heartbeat", metrics(c), nil); err != nil {
			log.Printf("heartbeat failed: %v", err)
		}
		var tasks []Task
		if err = request(c, "GET", "/api/agent/tasks", nil, &tasks); err == nil {
			for _, t := range tasks {
				err = execute(c, t)
				if err != nil {
					log.Printf("task %s failed", t.ID)
				}
				for attempt := 1; attempt <= 5; attempt++ {
					e := request(c, "POST", "/api/agent/tasks/"+t.ID+"/result", map[string]any{"success": err == nil}, nil)
					if e == nil {
						break
					}
					log.Printf("result delivery attempt %d failed: %v", attempt, e)
					time.Sleep(time.Duration(attempt) * 2 * time.Second)
				}
			}
		}
		time.Sleep(15 * time.Second)
	}
}
