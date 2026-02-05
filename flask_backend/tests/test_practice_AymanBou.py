def test_practice_test(test_client):
    """Test the practice endpoint"""
    response = test_client.get("/api/practice/test")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.get_json()
    assert data is not None, "Response JSON is None"
    assert "course" in data, "Missing 'course' key in response"
    assert data["course"] == "cosc 224", f"Expected 'cosc 224', got {data['course']}"