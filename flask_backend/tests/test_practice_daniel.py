import json


def test_practice_endpoint(test_client):
    """
    GIVEN GET /practice/test
    WHEN the practice endpoint is called
    THEN it should return status 200, a non-null response, and course value 'cosc 224'
    """
    # Make GET request to the practice endpoint
    response = test_client.get("/practice/test")

    print("\n" + "="*50)
    print(f"Status Code: {response.status_code}")
    print(f"Response JSON: {response.json}")
    print(f"Full Data: {response.get_json()}")
    print("="*50 + "\n")
    
    # Assert status code is 200
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    # Assert response is not null
    assert response.json is not None, "Response JSON should not be null"
    
    # Assert the course key exists and has the correct value
    assert "course" in response.json, "Response should contain 'course' key"
    assert response.json["course"] == "cosc 224", f"Expected 'cosc 224', got {response.json['course']}"
