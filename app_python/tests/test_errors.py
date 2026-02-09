from fastapi import HTTPException

from app import app


def test_500_returns_custom_json(client_no_raise):
    @app.get("/__test_crash__")
    async def __test_crash__():
        raise RuntimeError("boom")

    try:
        r = client_no_raise.get("/__test_crash__")
        assert r.status_code == 500
        assert r.json() == {
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        }
    finally:
        app.router.routes = [
            route for route in app.router.routes
            if getattr(route, "path", None) != "/__test_crash__"
        ]


def test_http_exception_handler_404_custom_json(client):
    r = client.get("/this-endpoint-does-not-exist")

    assert r.status_code == 404
    assert r.json() == {
        "error": "Not Found",
        "message": "Endpoint does not exist",
    }


def test_http_exception_handler_non_404_returns_http_error_json(client):
    @app.get("/__test_http_418__")
    async def __test_http_418__():
        raise HTTPException(status_code=418, detail="I'm a teapot")

    try:
        r = client.get("/__test_http_418__")

        assert r.status_code == 418
        assert r.json() == {
            "error": "HTTP Error",
            "message": "I'm a teapot",
        }
    finally:
        app.router.routes = [
            route for route in app.router.routes
            if getattr(route, "path", None) != "/__test_http_418__"
        ]
