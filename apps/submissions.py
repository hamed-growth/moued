"""Expected failures of user submissions."""


class SubmissionRejected(Exception):
    def __init__(self, message, *, completed=False):
        super().__init__(message)
        self.completed = completed


class MissionTeamAccessDenied(SubmissionRejected):
    pass
