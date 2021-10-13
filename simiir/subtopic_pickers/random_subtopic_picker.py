import random
from subtopic_pickers.base_subtopic_picker import BaseSubtopicPicker


class RandomSubtopicPicker(BaseSubtopicPicker):
    """Chaotic user. Randomly pick a subtopic for every iteration"""

    def __init__(self, search_context, seed=None, limit=10):
        super(RandomSubtopicPicker, self).__init__(search_context, limit)
        if seed:
            self.seed = seed
            random.seed(self.seed)

    def pick(self):
        """Randomly picks one subtopic"""
        # Check if we are done
        if not self.check_done():
            return random.choice(self._search_context.topic.subtopics)
        return False
