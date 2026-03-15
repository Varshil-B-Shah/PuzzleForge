# Minimal stub — full implementation in Task 10
class AnnotationList:
    def __init__(self):
        self._entries = []

    def add_annotation(self, move_number, player_uci, ai_uci, observation):
        pass

    def should_compress(self, move_number):
        return False

    def compress(self):
        pass

    def get_context_string(self):
        return ""
