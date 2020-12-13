
class AppFactory:
    def __init__(self):
        from app.main import app
        self.app = app
