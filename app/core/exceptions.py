class AlreadyExistsError(Exception):
    def __init__(self) -> None:
        super().__init__("'already exists")


class NotFoundError(Exception):
    def __init__(self) -> None:
        super().__init__("resource not found")


class PullRequestMergedError(Exception):
    def __init__(self) -> None:
        super().__init__("cannot reassign on merged PR")


class ReviewerNotAssignedError(Exception):
    def __init__(self) -> None:
        super().__init__("the user is not a reviewer")


class NoReplacementCandidateError(Exception):
    def __init__(self) -> None:
        super().__init__("no replacement candidate")
