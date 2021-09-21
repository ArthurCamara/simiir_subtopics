from ifind.common.language_model import LanguageModel
from simiir.utils import lm_methods


class BaseTextClassifier(object):
    """ """

    def __init__(
        self,
        topic,
        search_context,
        stopword_file=[],
        background_file=[],
        full_background: bool = False,
    ):
        # Refactor; is this the best way to pass in details?
        self._stopword_file = stopword_file
        self._background_file = background_file
        self._topic = topic
        self._search_context = search_context
        self.doc_score = 0.0
        self.updating = False
        self.update_method = 1

        if self._background_file:
            self.read_in_background(self._background_file)
        # else:  # Construct a LM from a text input instead
        #     lines = [x for x in topic.content.split("\n") if len(x.strip()) > 0]
        #     if not full_background:
        #         # If we are not using the full background, only the first line, other than topic title, is considered.
        #         full_text = " ".join(lines[:2])
        #     else:
        #         full_text = " ".join(lines)
        #     document_term_counts = lm_methods.extract_term_dict_from_text(full_text, self._stopword_file)
        #     self.background_language_model = LanguageModel(term_dict=document_term_counts)

    def is_relevant(self, document):
        """
        Returns True if the given document is relevant.
        This is an abstract method; override this method with an inheriting text classifier.
        """
        return True

    def read_in_background(self, vocab_file):
        """
        Helper method to read in a file containing terms and construct a background language model.
        """
        vocab = {}
        f = open(vocab_file, "r")
        lines = f.readlines()
        try:
            tc = lines[0].split(",")[1]
        except IndexError:
            # This is probably a full text file. Create a nw vocab from this.
            full_text = " ".join(lines)
            document_term_counts = lm_methods.extract_term_dict_from_text(full_text, self._stopword_file)
            self.background_language_model = LanguageModel(term_dict=document_term_counts)
            f.close()
            return

        for line in lines:
            tc = line.split(",")
            vocab[tc[0]] = int(tc[1])

        f.close()
        self.background_language_model = LanguageModel(term_dict=vocab)

    def update_model(self, search_context):
        """
        Enables the model of relevance/topic to be updated, based on the search context
        The update model based on the documents etc in the search context (i.e. memory of the user)

        :param  search_context: search_contexts.search_context object
        :return: returns True is topic model is updated.
        """
        return False
