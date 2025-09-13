# Logging

## Grafana

Grafana is a great tool for visualizing, analyzing, and exploring logs.

Right now, I mostly use it to get a nice log preview and as an interface for searching logs in Loki.

### Python container logs with `Grafana`:

![image](https://github.com/user-attachments/assets/ea9e255f-7686-49e3-92f4-15a9dc3594c5)

## Loki

Loki is a lightweight and efficient log storage and search engine. It stores logs from applications, indexes them, and makes searching fast.

## Promtail

Promtail is a log agent that grabs logs from different sources using a pull model. It collects logs based on a job list and then pushes them to a log storage system—Loki, in this case.

Since my apps don’t have specific log files, I just gather logs from all running Docker containers.
