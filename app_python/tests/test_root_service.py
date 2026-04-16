import pytest
from unittest.mock import Mock, patch
from fastapi import Request
from routes.root.service import RootService
from routes.root.schemas import SystemInfoResponse
from core.runtime import set_start_time


@pytest.fixture
def root_service():
    set_start_time()
    return RootService()


@pytest.fixture
def mock_request():
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"
    request.headers = {"user-agent": "test-agent"}
    request.method = "GET"
    request.url = Mock()
    request.url.path = "/"
    
    return request


def test_root_service_system_info_success(root_service, mock_request):
    with patch("routes.root.service.increment_visits"):
        result = root_service.system_info(mock_request)
    
    SystemInfoResponse(**result.model_dump())


def test_root_service_system_info_structure(root_service, mock_request):
    with patch("routes.root.service.increment_visits"):
        result = root_service.system_info(mock_request)

    assert len(SystemInfoResponse(**result.model_dump()).endpoints) >= 2

