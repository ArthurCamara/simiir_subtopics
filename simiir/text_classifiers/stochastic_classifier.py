__author__ = "arthur"
from simiir.text_classifiers.base_classifier import BaseTextClassifier
import logging
import random

log = logging.getLogger("lm_classifer.StochasticClassifier")


class StochasticClassifier(BaseTextClassifier):
    """ """

    def __init__(self, topic, search_context, stopword_file=[], background_file=[], prob=0.18):
        """ """
        super(StochasticClassifier, self).__init__(topic, search_context, stopword_file, background_file)
        self.prob = prob

    def is_relevant(self, document):
        """ """
        # Roll a die
        roll = random.random()
        return roll < self.prob
