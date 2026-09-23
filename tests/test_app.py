import copy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(copy.deepcopy(original_activities))


def test_get_activities_returns_activity_data():
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert expected_activity in payload
    assert {"description", "schedule", "max_participants", "participants"} <= payload[expected_activity].keys()


def test_signup_adds_participant():
    # Arrange
    activity_name = "Art Club"
    email = "new.student@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    assert email in activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant():
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_rejects_missing_activity():
    # Arrange
    activity_name = "Robotics Club"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": "student@mergington.edu"})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_requires_email():
    # Arrange
    activity_name = "Art Club"

    # Act
    response = client.post(f"/activities/{activity_name}/signup")

    # Assert
    assert response.status_code == 422


def test_signup_rejects_full_activity():
    # Arrange
    activity_name = "Art Club"
    activity = activities[activity_name]
    activity["participants"] = [
        f"student-{index}@mergington.edu"
        for index in range(activity["max_participants"])
    ]
    email = "student.new@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"
    assert email not in activity["participants"]


def test_unregister_removes_participant():
    # Arrange
    activity_name = "Art Club"
    email = "removable.student@mergington.edu"
    activities[activity_name]["participants"].append(email)

    # Act
    response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
    assert email not in activities[activity_name]["participants"]


def test_unregister_rejects_missing_participant():
    # Arrange
    activity_name = "Art Club"
    email = "missing.student@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_rejects_missing_activity():
    # Arrange
    activity_name = "Robotics Club"

    # Act
    response = client.delete(f"/activities/{activity_name}/signup", params={"email": "student@mergington.edu"})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_and_unregister_are_reflected_in_activity_list():
    # Arrange
    activity_name = "Art Club"
    email = "state.check@mergington.edu"

    # Act
    signup_response = client.post(
        f"/activities/{activity_name}/signup", params={"email": email}
    )
    signed_up_activities = client.get("/activities").json()
    unregister_response = client.delete(
        f"/activities/{activity_name}/signup", params={"email": email}
    )
    unregistered_activities = client.get("/activities").json()

    # Assert
    assert signup_response.status_code == 200
    assert email in signed_up_activities[activity_name]["participants"]
    assert unregister_response.status_code == 200
    assert email not in unregistered_activities[activity_name]["participants"]
