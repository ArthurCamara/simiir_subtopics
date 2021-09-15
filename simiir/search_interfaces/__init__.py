import string


class Document(object):
    """
    Basic representation of a document -
        including a unique identifier (index ID), a title, document content (body),
        and an additional identifier (e.g. collection ID).
    Parameters title, content and the additional identifier are optional.
    """

    def __init__(self, id, title=None, content=None, doc_id=None, subtopic=None):
        """
        Instantiates an instance of the Document.
        """
        self.id = id
        self.title = title
        self.content = content
        self.doc_id = id
        self.judgment = -1
        self.subtopic = subtopic

        if self.doc_id:
            self.doc_id = doc_id

    def __str__(self):
        """
        Returns a string representation of a given instance of Document.
        """
        return "<Document ID: '{0}' Title: '{1}' Content: '{2}'".format(self.id, self.title, self.content)


class Topic(Document):
    """
    Extending from Document, provides the ability to read a topic title and description from a given input file.
    """

    def __init__(
        self,
        id,
        title=None,
        content=None,
        doc_id=None,
        qrels_filename=None,
        background_filename=None,
        subtopics_filename=None,
    ):
        super(Topic, self).__init__(id=id, title=title, content=content, doc_id=doc_id)
        self.qrels_filename = qrels_filename
        self.background_terms = {}
        self.subtopics = []

        if background_filename is not None:
            self._read_background(background_filename)
        if subtopics_filename is not None:
            self._read_subtopics(subtopics_filename)

    def _read_background(self, background_filename):
        """
        Populates the background_terms attribute.
        Returns a dictionary of <term, value> pairs.
        """
        f = open(background_filename, "r")

        for line in f:
            line = line.strip().split(",")

            term = line[0]
            score = float(line[1])

            self.background_terms[term] = score

        f.close()

    def _read_subtopics(self, subtopics_filename):
        """Populates the list of subtopics for this topic
        Returns a list with the string of the subtopics"""
        f = open(subtopics_filename)
        for line in f:
            line = line.strip()
            self.subtopics.append(line)
        f.close()

    def read_topic_from_file(self, topic_filename):
        """
        Attempts to open the given filename for reading and stores the contents within the given topic object.
        Assumes that the first line of the input file is the topic title,
            and remaining lines make up the topic description.
        """
        first_line = None
        topic_text = ""

        if topic_filename:
            f = open(topic_filename, "r")

            for line in f:
                if not first_line:
                    first_line = line.strip()
                topic_text = topic_text + " " + line

        self.title = first_line
        self.content = topic_text

    def get_topic_text(self):
        """
        Returns a string representing the topic's title and content (description).
        """
        return "{title} {content}".format(**self.__dict__)

    def get_topic_text_nopunctuation(self):
        """
        Returns a string representing the topic's title and content, with each term separated by a space.
        No punctuation is included, and all terms are lowercase.
        """
        topic_text = self.get_topic_text()

        # Remove punctuation from the string.
        topic_text = topic_text.translate(str.maketrans("", "", string.punctuation))
        # Remove any newline characters.
        topic_text = topic_text.replace("\n", " ").replace("\r", "")
        topic_text = topic_text.lower()  # Take everything to lowercase.

        return topic_text

    def __str__(self):
        """
        Returns a string representation of a given instance of Topic.
        """
        return "<Topic ID: '{0}' Title: '{1}' Content: '{2}'".format(self.id, self.title, self.content)
