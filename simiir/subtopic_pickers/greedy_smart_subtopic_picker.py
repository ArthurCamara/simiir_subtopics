from subtopic_pickers.base_subtopic_picker import BaseSubtopicPicker


class GreedySmartSubtopicPicker(BaseSubtopicPicker):
    """Will always the pick the subtopic with LOWER knowledge"""

    def __init__(self, search_context, seed=None, limit: float = 10.0):
        super(GreedySmartSubtopicPicker, self).__init__(search_context, limit)

    def pick(self):
        # Iterate over all subtopics, pick the minum
        if self.check_done():
            return False
        all_subtopics = self._search_context.get_subtopic_tracking()
        worst_subtopic = sorted(all_subtopics.items(), key=lambda x: x[1], reverse=True)[0]
        return worst_subtopic[0]
