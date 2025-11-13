class TeamAlreadyExistsError(Exception):
    def __init__(self, team_name: str) -> None:
        self.team_name = team_name
        super().__init__(f"'{team_name}' already exists")


class NotFoundError(Exception):
    def __init__(self) -> None:
        super().__init__("resource not found")
