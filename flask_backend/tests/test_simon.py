def test_practice_test_endpoint(test_client):
    response = test_client.get("/practice/test")

    assert response.status_code == 200
    assert response is not None

    data = response.get_json()
    assert data is not None
    assert "course" in data
    assert data["course"] == "cosc 224"
