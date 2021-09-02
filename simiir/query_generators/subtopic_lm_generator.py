from ifind.common.language_model import LanguageModel
from ifind.common.smoothed_language_model import SmoothedLanguageModel
from ifind.common.query_generation import SingleQueryGeneration
from simiir.utils import lm_methods
from simiir.query_generators.base_generator import BaseQueryGenerator
from bs4 import BeautifulSoup


class SubtopicLMGenerator(BaseQueryGenerator):
    """
    This classs implement one LM query generator for each subtopic.
    It will generate 3-terms queries every time, EXCEPT if it is the first time a subtopic has been picked.
    In  this case, the query will be subtopic title.
    This is based on the tri_term_generator.
    """

    def __init__(self, stopword_file, background_file=[]):
        super(SubtopicLMGenerator, self).__init__(
            stopword_file, background_file=background_file, allow_similar=True)
        # As an extra, we also have one LM for each subtopic. They are initialized as the full background LM.
        self.subtopics_language_models = dict()

    def generate_query_list(self, search_context):
        """If the user is in a new subtopic, the query is only the topic title + subtopic title.
        Otherwise, use QS3 to generate a list of queries."""
        # If it's a new subtopic, a single query is returned.
        if search_context._new_subtopic:
            return [[search_context.topic.title + " " + search_context._last_subtopic]]
        return self._generate_query_list_single_subtopic(search_context, search_context._last_subtopic)

    def update_model(self, search_context):
        """Update background and subtopic language model after a query"""
        if not self.updating:
            return False
        snippet_text = self._get_snip_text(search_context)
        snippet_text = self._check_terms(snippet_text)

        if snippet_text:
            topic_text = search_context.topic.get_topic_text()
            subtopic_text = search_context.get_subtopic()

            all_text = '{0} {1} {2}'.format(
                topic_text, subtopic_text, snippet_text)

            term_counts = lm_methods.extract_term_dict_from_text(
                all_text, self._stopword_file)
            language_model = LanguageModel(term_dict=term_counts)

            self.topic_lang_model = language_model
            if self.background_language_model:

                smoothed_subtopic_language_model = SmoothedLanguageModel(
                    language_model, self.subtopics_language_models[subtopic_text])

                smoothed_topic_language_model = SmoothedLanguageModel(
                    language_model, self.background_language_model)

                self.topic_lang_model = smoothed_topic_language_model

                self.subtopics_language_models[subtopic_text] = smoothed_subtopic_language_model

                return True
            return False

    def _get_snip_text(self, search_context):
        document_list = search_context.get_all_examined_snippets()

        # iterate through document_list, pull out relevant snippets / text
        rel_text_list = []
        snippet_text = ''
        for doc in document_list:
            if doc.judgment > 0:
                rel_text_list.append('{0} {1}'.format(doc.title, doc.content))

        if rel_text_list:
            snippet_text = ' '.join(rel_text_list)

        snippet_soup = BeautifulSoup(snippet_text, 'html.parser')

        return snippet_soup.get_text()

    def _check_terms(self, text):
        if self.background_language_model is None:
            return text

        term_list = text.split()
        checked_term_list = []
        for term in term_list:
            if self.background_language_model.get_num_occurrences(term) > 0:
                checked_term_list.append(term)

        return ' '.join(checked_term_list)

    def _generate_topic_language_model(self, search_context, subtopic):
        # if no subtopic, pick from the standart language model.
        if subtopic is None:
            return self.background_language_model

        # Initialize language model for subtopic
        if subtopic not in self.subtopics_language_models:
            topic = search_context.topic
            topic_text = "{0} {1} {2}".format(
                topic.title, subtopic, topic.content)
            document_term_counts = lm_methods.extract_term_dict_from_text(
                topic_text, self._stopword_file)

            subtopic_language_model = LanguageModel(
                term_dict=document_term_counts)
            self.subtopics_language_models[subtopic] = subtopic_language_model

        return self.subtopics_language_models[subtopic]

    def _generate_query_list_single_subtopic(self, search_context, subtopic):
        """
        Copy of tri_term_generator.generate_query_list
        """
        self.__description_cutoff = 0

        topic = search_context.topic
        topic_title = topic.title
        topic_description = topic.content
        subtopic_language_model = self._generate_topic_language_model(
            search_context, subtopic)

        # Generate a series of query terms from the titles (topic and subtopic), and then rank the generated terms.
        title_generator = SingleQueryGeneration(
            minlen=3, stopwordfile=self._stopword_file)
        title_query_list = title_generator.extract_queries_from_text(
            topic_title + " " + subtopic)

        title_query_list = self._rank_terms(
            title_query_list, topic_language_model=subtopic_language_model)

        # Produce the two-term query "stem"
        title_query_list = self.__get_title_combinations(
            subtopic_language_model, title_query_list)

        # Perform the same steps, but from the description of the topic.
        description_generator = SingleQueryGeneration(
            minlen=3, stopwordfile=self._stopword_file)
        description_query_list = description_generator.extract_queries_from_text(
            topic_description)

        description_query_list = self._rank_terms(
            description_query_list, topic_language_model=subtopic_language_model)

        generated_permutations = self.__generate_permutations(
            subtopic_language_model, title_query_list, description_query_list)

        return generated_permutations

    def _rank_terms(self, terms, **kwargs):
        """
        Ranks terms according to their discriminatory power.
        """
        return lm_methods.rank_terms(terms, **kwargs)

    def __get_title_combinations(self, topic_language_model, title_query_list):
        """
        Returns a list of two-term ranked queries, extracted from the topic title.
        If the title consists of one term...surely not!!
        """
        count = 0
        prev_term = None
        windows = []

        # One term only, no need to do sliding windows.
        if len(title_query_list) == 1:
            return title_query_list

        for term in title_query_list:
            if count == 0:
                prev_term = term[0]
                count = count + 1
                continue
            else:
                count = 0
                windows.append('{0} {1}'.format(prev_term, term[0]))

        return self._rank_terms(windows, topic_language_model=topic_language_model)

    def __generate_permutations(self, topic_language_model, title_query_list, description_query_list):
        """
        Returns a list of ranked permutations for each title term.
        Queries are ranked for each title term - this ensures that the sequence of w1 w2 > w1 w3 is not broken.
        """
        return_terms = []
        observed_stems = []

        # Hack - this should be an instance variable or something that can be shared between the title and description parts.
        for terms in title_query_list:
            for term in terms[0].split():
                stemmed_term = self._stem_term(term)

                if stemmed_term not in observed_stems:
                    observed_stems.append(stemmed_term)

        if len(observed_stems) == 1:
            get_terms = 2  # Indicate that we need to pull out two terms to compensate
        else:
            get_terms = 1  # Our pivot is of length 2; just get one term.

        for title_term in title_query_list:
            title_terms = []
            cutoff_counter = 0

            description_two = []

            for description_term in description_query_list:
                if self.__description_cutoff > 0 and cutoff_counter == self.__description_cutoff:
                    break

                stemmed_term = self._stem_term(description_term[0])
                if stemmed_term in observed_stems:
                    continue

                observed_stems.append(stemmed_term)

                if get_terms == 2:
                    if len(description_two) == 2:
                        title_terms.append('{0} {1} {2}'.format(
                            title_term[0], description_two[0], description_two[1]))
                        description_two = [description_term[0]]
                    else:
                        description_two.append(description_term[0])
                else:
                    title_terms.append('{0} {1}'.format(
                        title_term[0], description_term[0]))

                cutoff_counter = cutoff_counter + 1

            title_terms = self._rank_terms(
                title_terms, topic_language_model=topic_language_model)
            return_terms = return_terms + title_terms

        return return_terms
