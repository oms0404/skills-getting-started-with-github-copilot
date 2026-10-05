import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def temporary_activity(monkeypatch):
    activity_name = "Pytest Test Activity"
    activity_details = {
        "description": "An activity used by API tests",
        "schedule": "Mondays, 3:00 PM - 4:00 PM",
        "max_participants": 3,
        "participants": ["existing@example.com"],
    }
    monkeypatch.setitem(activities, activity_name, activity_details)
    return activity_name, activity_details


def test_get_activities_includes_activity(client, temporary_activity):
    # Arrange
    activity_name, activity_details = temporary_activity

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()[activity_name] == activity_details


def test_signup_adds_participant(client, temporary_activity):
    # Arrange
    activity_name, activity_details = temporary_activity
    email = "new-student@example.com"

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
    assert activity_details["participants"] == [
        "existing@example.com",
        email,
    ]


def test_signup_rejects_duplicate_participant(client, temporary_activity):
    # Arrange
    activity_name, activity_details = temporary_activity
    email = "existing@example.com"
    original_participants = activity_details["participants"].copy()

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student is already signed up"}
    assert activity_details["participants"] == original_participants


def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "student@example.com"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_participant(client, temporary_activity):
    # Arrange
    activity_name, activity_details = temporary_activity
    email = "existing@example.com"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert activity_details["participants"] == []


def test_unregister_rejects_nonparticipant(client, temporary_activity):
    # Arrange
    activity_name, activity_details = temporary_activity
    email = "not-signed-up@example.com"
    original_participants = activity_details["participants"].copy()

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
    assert activity_details["participants"] == original_participants


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": "student@example.com"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}