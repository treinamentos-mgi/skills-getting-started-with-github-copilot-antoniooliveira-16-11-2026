from src.app import activities


def test_root_redirects_to_static_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_all_activities_and_details(client):
    # Arrange
    expected_names = {
        "Chess Club",
        "Programming Class",
        "Gym Class",
        "Basketball Team",
        "Soccer Club",
        "Drama Club",
        "Art Club",
        "Debate Club",
        "Science Club",
    }
    expected_fields = {
        "description",
        "schedule",
        "max_participants",
        "participants",
    }

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert set(result) == expected_names
    assert all(set(activity) == expected_fields for activity in result.values())


def test_signup_adds_student_to_activity(client):
    # Arrange
    activity_name = "Basketball Team"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in activities[activity_name]["participants"]


def test_signup_returns_404_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_returns_400_for_duplicate_and_keeps_participants(client):
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]
    original_participants = activities[activity_name]["participants"].copy()

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert activities[activity_name]["participants"] == original_participants


def test_signup_supports_activity_names_with_spaces(client):
    # Arrange
    activity_name = "Chess Club"
    email = "new-player@mergington.edu"

    # Act
    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert email in activities[activity_name]["participants"]


def test_cancel_signup_removes_student(client):
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Cancelled signup for {email} in {activity_name}"
    }
    assert email not in activities[activity_name]["participants"]


def test_cancel_signup_returns_404_when_student_is_not_signed_up(client):
    # Arrange
    activity_name = "Chess Club"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": "not-signed-up@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_cancel_signup_returns_404_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_can_be_repeated_after_cancellation(client):
    # Arrange
    activity_name = "Basketball Team"
    email = "returning-student@mergington.edu"

    # Act
    signup_response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )
    cancel_response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )
    resubscribe_response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert signup_response.status_code == 200
    assert cancel_response.status_code == 200
    assert resubscribe_response.status_code == 200
    assert activities[activity_name]["participants"].count(email) == 1


def test_signup_currently_allows_more_than_max_participants(client):
    # Arrange
    activity_name = "Basketball Team"
    email = "overflow-student@mergington.edu"
    activity = activities[activity_name]
    activity["participants"] = [
        f"existing-{index}@mergington.edu"
        for index in range(activity["max_participants"])
    ]

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert len(activity["participants"]) == activity["max_participants"] + 1
    assert email in activity["participants"]
