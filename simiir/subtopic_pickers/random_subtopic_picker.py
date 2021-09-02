import random

from subtopic_pickers.base_subtopic_picker import BaseSubtopicPicker


class RandomSubtopicPicker(BaseSubtopicPicker):
    """Chaotic user. Randomly pick a subtopic for every iteration"""

    def __init__(self, search_context, seed=42):
        super(RandomSubtopicPicker, self).__init__(search_context)
        self.seed = seed
        random.seed(self.seed)

    def pick(self):
        # FIX THIS TO ACTUALLY WORK. I'm not sure where the subtopics are in the search context.
        return random.choice(self._search_context.topic.subtopics)