"""
DevOps Info Service
Веб-сервис для предоставления информации о системе и состоянии сервиса
"""

import os
import socket
import platform
import logging
from datetime import datetime, timezone, timedelta
from flask import Flask, jsonify, request

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Создание приложения Flask
app = Flask(__name__)

# Конфигурация
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Время запуска приложения
START_TIME = datetime.now(timezone.utc)


def get_system_info() -> dict:
    """
    Сбор информации о системе
    
    Returns:
        dict: Информация о системе
    """
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': platform.version(),
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count(),
        'python_version': platform.python_version()
    }


def get_uptime() -> dict:
    """
    Расчет времени работы приложения
    
    Returns:
        dict: Время работы в секундах и человекочитаемом формате
    """
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    
    # Преобразование в человекочитаемый формат
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    human_format = ""
    if hours > 0:
        human_format += f"{hours} hour{'s' if hours != 1 else ''}"
        if minutes > 0 or secs > 0:
            human_format += ", "
    if minutes > 0:
        human_format += f"{minutes} minute{'s' if minutes != 1 else ''}"
        if secs > 0:
            human_format += ", "
    if secs > 0 or (hours == 0 and minutes == 0):
        human_format += f"{secs} second{'s' if secs != 1 else ''}"
    
    return {
        'seconds': seconds,
        'human': human_format
    }


@app.route('/')
def index():
    """
    Основной эндпоинт - информация о сервисе и системе
    """
    logger.info(f"Request from {request.remote_addr} to main endpoint")
    
    return jsonify({
        'service': {
            'name': 'devops-info-service',
            'version': '1.0.0',
            'description': 'DevOps course info service',
            'framework': 'Flask',
            'environment': 'production' if not DEBUG else 'development'
        },
        'system': get_system_info(),
        'runtime': {
            'uptime_seconds': get_uptime()['seconds'],
            'uptime_human': get_uptime()['human'],
            'current_time': datetime.now(timezone.utc).isoformat(),
            'timezone': 'UTC',
            'start_time': START_TIME.isoformat()
        },
        'request': {
            'client_ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'Unknown'),
            'method': request.method,
            'path': request.path,
            'headers': dict(request.headers)
        },
        'endpoints': [
            {'path': '/', 'method': 'GET', 'description': 'Service information'},
            {'path': '/health', 'method': 'GET', 'description': 'Health check'}
        ]
    })


@app.route('/health')
def health():
    """
    Эндпоинт проверки состояния сервиса
    """
    logger.debug(f"Health check from {request.remote_addr}")
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': get_uptime()['seconds'],
        'service': 'devops-info-service',
        'version': '1.0.0'
    }), 200


@app.errorhandler(404)
def not_found(error):
    """
    Обработчик ошибки 404
    """
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested endpoint does not exist',
        'path': request.path,
        'available_endpoints': [
            {'path': '/', 'method': 'GET'},
            {'path': '/health', 'method': 'GET'}
        ]
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """
    Обработчик ошибки 500
    """
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), 500


@app.before_request
def log_request():
    """
    Логирование входящих запросов
    """
    logger.info(f"Incoming request: {request.method} {request.path} from {request.remote_addr}")


@app.after_request
def log_response(response):
    """
    Логирование исходящих ответов
    """
    logger.info(f"Response: {request.method} {request.path} - Status {response.status_code}")
    return response


if __name__ == '__main__':
    logger.info(f"Starting DevOps Info Service on {HOST}:{PORT}")
    logger.info(f"Debug mode: {DEBUG}")
    
    app.run(
        host=HOST,
        port=PORT,
        debug=DEBUG
    )