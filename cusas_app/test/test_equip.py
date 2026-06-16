class FakeCursor:
    def __init__(self, row):
        self.row = row
        self.execute = None

    def execute(self, sql, params):
        self.execute = (sql, params)

    def fetchone(self):
        return self._row

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

    class FakeConnection:
        def __init__(self, row):
            self.row = row
            self.last_cursor = None

        def cursor(self):
            cursor = FakeCursor(self.row)
            self.last_cursor = cursor
            return cursor
