from uuid import uuid4

import pytest


@pytest.mark.e2e
@pytest.mark.anyio
async def test_inactive_user_not_assigned_to_new_pr(client, unique_suffix):
    team_name = f"backend-inactive-{unique_suffix}"
    u1 = f"{team_name}-u1"
    u2 = f"{team_name}-u2"
    u3 = f"{team_name}-u3"

    team_payload = {
        "team_name": team_name,
        "members": [
            {"user_id": u1, "username": "Author", "is_active": True},
            {"user_id": u2, "username": "WillBeInactive", "is_active": True},
            {"user_id": u3, "username": "ActiveReviewer", "is_active": True},
        ],
    }
    resp = await client.post("/team/add", json=team_payload)
    assert resp.status_code == 201, resp.text

    resp = await client.post(
        "/users/setIsActive",
        json={"user_id": u2, "is_active": False},
    )
    assert resp.status_code == 200, resp.text
    user = resp.json()["user"]
    assert user["user_id"] == u2
    assert user["is_active"] is False

    pr_id = f"pr-{uuid4().hex[:8]}"
    resp = await client.post(
        "/pullRequest/create",
        json={
            "pull_request_id": pr_id,
            "pull_request_name": "PR with inactive user in team",
            "author_id": u1,
        },
    )
    assert resp.status_code == 201, resp.text
    pr = resp.json()["pr"]

    reviewers = pr["assigned_reviewers"]

    assert u1 not in reviewers
    assert u2 not in reviewers
    for r in reviewers:
        assert r in {u3}
    assert len(reviewers) <= 1


@pytest.mark.e2e
@pytest.mark.anyio
async def test_team_and_user_not_found_errors(client, unique_suffix):
    nonexistent_team = f"no-team-{unique_suffix}"
    resp = await client.get("/team/get", params={"team_name": nonexistent_team})
    assert resp.status_code == 404, resp.text
    err = resp.json()["error"]
    assert err["code"] == "NOT_FOUND"

    nonexistent_user = f"user-{unique_suffix}"
    resp = await client.post(
        "/users/setIsActive",
        json={"user_id": nonexistent_user, "is_active": True},
    )
    assert resp.status_code == 404, resp.text
    err2 = resp.json()["error"]
    assert err2["code"] == "NOT_FOUND"
