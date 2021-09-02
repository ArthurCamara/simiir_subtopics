import abc


class BaseSubtopicPicker(object):
    """
    Base class for deciding what the next subtopic should be
    """

    def __init__(self, search_context):
        self._search_context = search_context
        self.all_subtopics = search_context.topic.subtopics

    @abc.abstractmethod
    def pick(self):
        """Abstract method for picking a subtopic.
        Needs to be implemented. Returns the string of a subtopic.:"""
        pass
