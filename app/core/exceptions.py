class TeamAlreadyExistsError(Exception):
    def __init__(self, team_name: str) -> None:
        self.team_name = team_name
        super().__init__(f"Team '{team_name}' already exists")


class TeamNotFoundError(Exception):
    def __init__(self, team_name: str) -> None:
        self.team_name = team_name
        super().__init__(f"Team '{team_name}' not found")
