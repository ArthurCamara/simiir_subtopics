import abc
from search_contexts.search_context import SearchContext


class BaseSubtopicPicker(object):
    """
    Base class for deciding what the next subtopic should be
    """

    def __init__(self, search_context: SearchContext, limit: float = 10.0):
        self._search_context = search_context
        self.all_subtopics = search_context.topic.subtopics
        self.limit = limit

    @abc.abstractmethod
    def pick(self):
        """Abstract method for picking a subtopic.
        Needs to be implemented. Returns the string of a subtopic.:"""
        pass

    def check_done(self):
        """Check if we have already covered all of the subtopics necessary"""
        for s in self._search_context.topic.subtopics:
            if self._search_context.get_state_of_subtopic(s) < self.limit:
                return False
        return True
