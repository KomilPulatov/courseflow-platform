def test_professor_pages_are_served(client) -> None:
    routes = [
        "/professor",
        "/professor/sections",
        "/professor/sections/1",
        "/professor/sections/1/room-options",
        "/professor/timetable",
    ]

    for route in routes:
        response = client.get(route)
        assert response.status_code == 200
        assert "Inha University in Tashkent" in response.text
