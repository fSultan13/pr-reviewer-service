from uuid import uuid4

import pytest


@pytest.mark.e2e
@pytest.mark.anyio
async def test_full_pr_lifecycle(client, unique_suffix):
    team_name = f"backend-{unique_suffix}"
    u1 = f"{team_name}-u1"
    u2 = f"{team_name}-u2"
    u3 = f"{team_name}-u3"
    u4 = f"{team_name}-u4"

    team_payload = {
        "team_name": team_name,
        "members": [
            {"user_id": u1, "username": "Alice", "is_active": True},
            {"user_id": u2, "username": "Bob", "is_active": True},
            {"user_id": u3, "username": "Charlie", "is_active": True},
            {"user_id": u4, "username": "Dave", "is_active": True},
        ],
    }

    resp = await client.post("/team/add", json=team_payload)
    assert resp.status_code == 201, resp.text
    team = resp.json()["team"]
    assert team["team_name"] == team_name
    assert len(team["members"]) == 4

    pr_id = f"pr-{uuid4().hex[:8]}"
    create_payload = {
        "pull_request_id": pr_id,
        "pull_request_name": "e2e PR",
        "author_id": u1,
    }

    resp = await client.post("/pullRequest/create", json=create_payload)
    assert resp.status_code == 201, resp.text
    pr = resp.json()["pr"]

    assert pr["pull_request_id"] == pr_id
    assert pr["author_id"] == u1
    assert pr["status"] == "OPEN"

    reviewers = pr["assigned_reviewers"]
    assert 1 <= len(reviewers) <= 2
    assert u1 not in reviewers
    for r in reviewers:
        assert r in {u2, u3, u4}

    reviewer_to_check = reviewers[0]

    resp = await client.get("/users/getReview", params={"user_id": reviewer_to_check})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["user_id"] == reviewer_to_check
    assert any(p["pull_request_id"] == pr_id for p in body["pull_requests"])

    old_user_id = reviewers[0]
    reassign_payload = {
        "pull_request_id": pr_id,
        "old_user_id": old_user_id,
    }

    resp = await client.post("/pullRequest/reassign", json=reassign_payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    pr_after_reassign = body["pr"]
    replaced_by = body["replaced_by"]

    assert pr_after_reassign["pull_request_id"] == pr_id
    assert old_user_id not in pr_after_reassign["assigned_reviewers"]
    assert replaced_by in pr_after_reassign["assigned_reviewers"]
    assert pr_after_reassign["status"] == "OPEN"
    for r in pr_after_reassign["assigned_reviewers"]:
        assert r in {u2, u3, u4}
        assert r != u1

    resp1 = await client.post("/pullRequest/merge", json={"pull_request_id": pr_id})
    assert resp1.status_code == 200, resp1.text
    merged1 = resp1.json()["pr"]
    assert merged1["status"] == "MERGED"
    assert merged1["mergedAt"] is not None

    resp2 = await client.post("/pullRequest/merge", json={"pull_request_id": pr_id})
    assert resp2.status_code == 200, resp2.text
    merged2 = resp2.json()["pr"]
    assert merged2["status"] == "MERGED"
    assert merged2["mergedAt"] is not None
    assert merged2["assigned_reviewers"] == merged1["assigned_reviewers"]

    assigned_after_merge = merged2["assigned_reviewers"]
    assert assigned_after_merge
    resp = await client.post(
        "/pullRequest/reassign",
        json={"pull_request_id": pr_id, "old_user_id": assigned_after_merge[0]},
    )
    assert resp.status_code == 409, resp.text
    print(resp.json())
    err = resp.json()["error"]
    assert err["code"] == "PR_MERGED"


@pytest.mark.e2e
@pytest.mark.anyio
async def test_bulk_deactivate_team_users_and_reassign_e2e(client, unique_suffix):
    team_name = f"bulk-{unique_suffix}"
    u1 = f"{team_name}-u1"
    u2 = f"{team_name}-u2"
    u3 = f"{team_name}-u3"
    u4 = f"{team_name}-u4"

    team_payload = {
        "team_name": team_name,
        "members": [
            {"user_id": u1, "username": "Alice", "is_active": True},
            {"user_id": u2, "username": "Bob", "is_active": True},
            {"user_id": u3, "username": "Charlie", "is_active": True},
            {"user_id": u4, "username": "Dave", "is_active": True},
        ],
    }

    resp = await client.post("/team/add", json=team_payload)
    assert resp.status_code == 201, resp.text

    pr_id = f"pr-{uuid4().hex[:8]}"
    create_payload = {
        "pull_request_id": pr_id,
        "pull_request_name": "bulk deactivate PR",
        "author_id": u1,
    }

    resp = await client.post("/pullRequest/create", json=create_payload)
    assert resp.status_code == 201, resp.text
    pr = resp.json()["pr"]

    reviewers_before = pr["assigned_reviewers"]
    assert reviewers_before

    old_reviewer = reviewers_before[0]
    to_deactivate = list({old_reviewer, u4})

    resp = await client.post(
        "/team/deactivateUsers",
        json={"team_name": team_name, "user_ids": to_deactivate},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["team_name"] == team_name
    assert body["deactivated_users"] >= len(set(to_deactivate))

    resp = await client.get("/users/getReview", params={"user_id": old_reviewer})
    assert resp.status_code == 200, resp.text
    review_body = resp.json()
    assert all(p["pull_request_id"] != pr_id for p in review_body["pull_requests"])

    resp = await client.post("/pullRequest/merge", json={"pull_request_id": pr_id})
    assert resp.status_code == 200, resp.text
    merged = resp.json()["pr"]
    assert merged["status"] == "MERGED"
