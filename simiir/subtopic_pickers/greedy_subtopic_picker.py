from subtopic_pickers.base_subtopic_picker import BaseSubtopicPicker


class GreedySubtopicPicker(BaseSubtopicPicker):
    """will pick one subtopic only AFTER it's done with the previous one."""

    def __init__(self, search_context, seed=None, limit: float = 10.0):
        super(GreedySubtopicPicker, self).__init__(search_context, limit)

    def pick(self):
        # Check if it's done with current subtopic
        current_subtopic = self._search_context.get_subtopic()
        if current_subtopic is None:
            return self._search_context.topic.subtopics[0]
        if self._search_context.get_state_of_subtopic(current_subtopic) > self.limit:
            # Get current subtopic index. Could also be stored.
            curr_index = self._search_context.topic.subtopics.index(current_subtopic)
            # It's also possible that we are already done, even without reaching all subtopics. In this case, finish it!
            if self.check_done():
                return False
            curr_index += 1
            try:
                return self._search_context.topic.subtopics[curr_index]
            except IndexError:  # Out of subtopics. We are DONE.
                return False
        return current_subtopic
