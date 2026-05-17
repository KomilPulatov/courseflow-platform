def test_app_utility_pages_are_served(client) -> None:
    routes = [
        "/app",
        "/app/health",
        "/app/settings",
        "/app/not-found",
    ]

    for route in routes:
        response = client.get(route)
        assert response.status_code == 200
        assert "Application Utility" in response.text
        assert 'id="root"' in response.text
