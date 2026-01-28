use actix_web::{web, App, HttpRequest, HttpServer, Responder, Result};
use serde::{Deserialize, Serialize};
use std::env;
use std::sync::Arc;
use std::time::SystemTime;
use chrono::{DateTime, Utc};
use sysinfo::System;

#[derive(Serialize, Deserialize)]
struct ServiceInfo {
    name: String,
    version: String,
    description: String,
    framework: String,
}

#[derive(Serialize, Deserialize)]
struct SystemInfo {
    hostname: String,
    platform: String,
    platform_version: String,
    architecture: String,
    cpu_count: usize,
    rust_version: String,
}

#[derive(Serialize, Deserialize)]
struct RuntimeInfo {
    uptime_seconds: u64,
    uptime_human: String,
    current_time: String,
    timezone: String,
}

#[derive(Serialize, Deserialize)]
struct RequestInfo {
    client_ip: String,
    user_agent: String,
    method: String,
    path: String,
}

#[derive(Serialize, Deserialize)]
struct EndpointInfo {
    path: String,
    method: String,
    description: String,
}

#[derive(Serialize, Deserialize)]
struct MainResponse {
    service: ServiceInfo,
    system: SystemInfo,
    runtime: RuntimeInfo,
    request: RequestInfo,
    endpoints: Vec<EndpointInfo>,
}

#[derive(Serialize, Deserialize)]
struct HealthResponse {
    status: String,
    timestamp: String,
    uptime_seconds: u64,
}

struct AppState {
    start_time: SystemTime,
}

fn get_uptime(start_time: SystemTime) -> (u64, String) {
    let duration = SystemTime::now()
        .duration_since(start_time)
        .unwrap_or_default();
    let seconds = duration.as_secs();
    let hours = seconds / 3600;
    let minutes = (seconds % 3600) / 60;

    let human = format!("{} hours, {} minutes", hours, minutes);
    (seconds, human)
}

fn get_system_info() -> SystemInfo {
    let sys = System::new_all();

    let hostname = System::host_name().unwrap_or_else(|| "unknown".to_string());
    let os_version = System::long_os_version().unwrap_or_else(|| "unknown".to_string());

    SystemInfo {
        hostname,
        platform: env::consts::OS.to_string(),
        platform_version: os_version,
        architecture: env::consts::ARCH.to_string(),
        cpu_count: sys.cpus().len(),
        rust_version: rustc_version_runtime::version().to_string(),
    }
}

fn get_service_info() -> ServiceInfo {
    ServiceInfo {
        name: "devops-info-service".to_string(),
        version: "1.0.0".to_string(),
        description: "DevOps course info service".to_string(),
        framework: "Actix-web".to_string(),
    }
}

fn get_runtime_info(start_time: SystemTime) -> RuntimeInfo {
    let (uptime_seconds, uptime_human) = get_uptime(start_time);
    let now: DateTime<Utc> = Utc::now();

    RuntimeInfo {
        uptime_seconds,
        uptime_human,
        current_time: now.to_rfc3339(),
        timezone: "UTC".to_string(),
    }
}

fn get_request_info(req: &HttpRequest) -> RequestInfo {
    let connection_info = req.connection_info();
    let client_ip = connection_info.realip_remote_addr()
        .unwrap_or("unknown")
        .to_string();

    let user_agent = req
        .headers()
        .get("user-agent")
        .and_then(|h| h.to_str().ok())
        .unwrap_or("unknown")
        .to_string();

    RequestInfo {
        client_ip,
        user_agent,
        method: req.method().to_string(),
        path: req.path().to_string(),
    }
}

fn get_endpoints() -> Vec<EndpointInfo> {
    vec![
        EndpointInfo {
            path: "/".to_string(),
            method: "GET".to_string(),
            description: "Service information".to_string(),
        },
        EndpointInfo {
            path: "/health".to_string(),
            method: "GET".to_string(),
            description: "Health check".to_string(),
        },
    ]
}

async fn index(data: web::Data<Arc<AppState>>, req: HttpRequest) -> Result<impl Responder> {
    let response = MainResponse {
        service: get_service_info(),
        system: get_system_info(),
        runtime: get_runtime_info(data.start_time),
        request: get_request_info(&req),
        endpoints: get_endpoints(),
    };

    Ok(web::Json(response))
}

async fn health(data: web::Data<Arc<AppState>>) -> Result<impl Responder> {
    let (uptime_seconds, _) = get_uptime(data.start_time);
    let now: DateTime<Utc> = Utc::now();

    let response = HealthResponse {
        status: "healthy".to_string(),
        timestamp: now.to_rfc3339(),
        uptime_seconds,
    };

    Ok(web::Json(response))
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    env_logger::init_from_env(env_logger::Env::new().default_filter_or("info"));

    let host = env::var("HOST").unwrap_or_else(|_| "0.0.0.0".to_string());
    let port = env::var("PORT").unwrap_or_else(|_| "8080".to_string());
    let bind_addr = format!("{}:{}", host, port);

    let app_state = Arc::new(AppState {
        start_time: SystemTime::now(),
    });

    log::info!("Application starting...");
    log::info!("Service: devops-info-service v1.0.0");
    log::info!("Listening on {}", bind_addr);

    HttpServer::new(move || {
        App::new()
            .app_data(web::Data::new(app_state.clone()))
            .route("/", web::get().to(index))
            .route("/health", web::get().to(health))
    })
    .bind(&bind_addr)?
    .run()
    .await
}
