from deckflix_app.importer.models import ImportJob


class ImportQueue:
    def __init__(self):
        self.jobs: list[ImportJob] = []

    def add(self, job: ImportJob):
        self.jobs.append(job)

    def pending(self):
        return [j for j in self.jobs if not j.completed]

    def completed(self):
        return [j for j in self.jobs if j.completed]
