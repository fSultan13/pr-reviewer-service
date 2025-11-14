import random
import string
import uuid

from locust import HttpUser, between, task

TEAM_NAME = "backend-loadtest"
TEAM_MEMBERS = [
    {
        "user_id": f"u{i}",
        "username": f"User {i}",
        "is_active": True,
    }
    for i in range(1, 11)
]


class PRReviewerUser(HttpUser):
    """
    Модель "пользователя" для Locust.
    Он:
      - гарантирует, что есть команда и пользователи (/team/add)
      - создает PR (/pullRequest/create)
      - делает переназначения (/pullRequest/reassign)
      - мержит PR (/pullRequest/merge), в т.ч. проверяет идемпотентность
      - читает список PR'ов ревьювера (/users/getReview)
    """

    wait_time = between(0.2, 0.5)

    def on_start(self) -> None:
        """
        При старте каждого виртуального пользователя:
        - создаём (или убеждаемся, что уже есть) команду с пользователями.
        """
        self.author_ids = [m["user_id"] for m in TEAM_MEMBERS]

        self.prs: list[dict] = []

        with self.client.post(
            "/team/add",
            json={"team_name": TEAM_NAME, "members": TEAM_MEMBERS},
            catch_response=True,
        ) as resp:
            if resp.status_code in (201, 400):
                resp.success()
            else:
                resp.failure(
                    f"Unexpected status {resp.status_code} on /team/add: {resp.text}"
                )

    @staticmethod
    def _random_pr_name() -> str:
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
        return f"Load test PR {suffix}"

    def _choose_open_pr(self):
        candidates = [pr for pr in self.prs if pr["status"] == "OPEN"]
        return random.choice(candidates) if candidates else None

    def _choose_open_pr_with_reviewer(self):
        candidates = [
            pr for pr in self.prs if pr["status"] == "OPEN" and pr["reviewers"]
        ]
        return random.choice(candidates) if candidates else None

    def _choose_merged_pr(self):
        candidates = [pr for pr in self.prs if pr["status"] == "MERGED"]
        return random.choice(candidates) if candidates else None

    @task(3)
    def create_pull_request(self):
        """
        Создать PR и автоматически назначить ревьюеров.
        /pullRequest/create
        """
        pr_id = f"pr-{uuid.uuid4()}"
        author_id = random.choice(self.author_ids)

        payload = {
            "pull_request_id": pr_id,
            "pull_request_name": self._random_pr_name(),
            "author_id": author_id,
        }

        with self.client.post(
            "/pullRequest/create",
            json=payload,
            catch_response=True,
        ) as resp:
            if resp.status_code == 201:
                data = resp.json()["pr"]
                self.prs.append(
                    {
                        "id": data["pull_request_id"],
                        "reviewers": data.get("assigned_reviewers", []),
                        "status": data.get("status", "OPEN"),
                    }
                )
                resp.success()
            else:
                resp.failure(
                    f"Unexpected status {resp.status_code} on /pullRequest/create: {resp.text}"
                )

    @task(2)
    def reassign_reviewer(self):
        """
        Переназначить ревьювера у случайного открытого PR.
        /pullRequest/reassign
        """
        pr = self._choose_open_pr_with_reviewer()
        if not pr:
            return

        old_user_id = random.choice(pr["reviewers"])
        payload = {
            "pull_request_id": pr["id"],
            "old_user_id": old_user_id,
        }

        with self.client.post(
            "/pullRequest/reassign",
            json=payload,
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                new_reviewers = data["pr"]["assigned_reviewers"]
                pr["reviewers"] = new_reviewers
                resp.success()
            elif resp.status_code == 409:
                resp.success()
            else:
                resp.failure(
                    f"Unexpected status {resp.status_code} on /pullRequest/reassign: {resp.text}"
                )

    @task(2)
    def merge_pull_request(self):
        """
        Смёржить случайный открытый PR.
        /pullRequest/merge
        """
        pr = self._choose_open_pr()
        if not pr:
            return

        payload = {"pull_request_id": pr["id"]}

        with self.client.post(
            "/pullRequest/merge",
            json=payload,
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()["pr"]
                pr["status"] = data.get("status", "MERGED")
                resp.success()
            else:
                resp.failure(
                    f"Unexpected status {resp.status_code} on /pullRequest/merge: {resp.text}"
                )

    @task(1)
    def merge_idempotent_check(self):
        """
        Проверка идемпотентности: повторный /pullRequest/merge по уже MERGED PR.
        """
        pr = self._choose_merged_pr()
        if not pr:
            return

        payload = {"pull_request_id": pr["id"]}

        self.client.post("/pullRequest/merge", json=payload)

    @task(2)
    def get_user_review_prs(self):
        """
        Получить PR'ы, где пользователь назначен ревьювером.
        /users/getReview
        """
        user_id = random.choice(self.author_ids)
        self.client.get("/users/getReview", params={"user_id": user_id})

    @task(1)
    def bulk_deactivate_team_users_and_reassign(self):
        """
        Массовая деактивация части пользователей команды и безопасная
        переназначаемость открытых PR.
        /team/deactivateUsers
        """
        if len(self.author_ids) < 2:
            return

        user_ids = random.sample(self.author_ids, k=2)

        payload = {
            "team_name": TEAM_NAME,
            "user_ids": user_ids,
        }

        with self.client.post(
            "/team/deactivateUsers",
            json=payload,
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(
                    f"Unexpected status {resp.status_code} on /team/deactivateUsers: {resp.text}"
                )
