def test_public_app_settings_endpoint(client) -> None:
    response = client.get("/api/v1/app/settings")

    assert response.status_code == 200
    data = response.json()
    assert data["app_name"] == "Course Registration and Scheduling Platform"
    assert data["docs_url"] == "/docs"
    assert data["health_url"] == "/api/v1/health"
    assert data["dependency_health_url"] == "/api/v1/health/dependencies"
    assert "database_backend" in data
