from loggers import Actions


class SimulatedUser(object):
    """
    The simulated user. Stores references to all the required components, and contains the logical
        workflow for the simulation.
    """

    def __init__(self, configuration):
        self.__search_context = configuration.user.search_context
        self.__decision_maker = configuration.user.decision_maker
        self.__subtopic_picker = configuration.user.subtopics_picker
        self.__output_controller = configuration.output
        self.__logger = configuration.user.logger
        self.__document_classifier = configuration.user.document_classifier
        self.__snippet_classifier = configuration.user.snippet_classifier
        self.__query_generator = configuration.user.query_generator
        self.__serp_impression = configuration.user.serp_impression

        # Response from the previous action method - True or False? (did the user do or not do what they thought?)
        self.__action_value = None

    def decide_action(self):
        """
        This method is central to the whole simulation - it decides which action the user should perform next.
        The workflow implemented below is as follows. Steps with asterisks are DECISION POINTS.

        NEW:

        (0) User picks a subtopic
        (1)  User issues query
        (2)  User looks at the SERP
        (3*) If the SERP looks poor, goto (1) else goto (4)

        (4)  Examine a snippet
        (5*) If the snippet looks at least somewhat relevant, goto (6) else decide whether to goto (0) or (4)

        (6)  Examine document
        (7*) If the document looks to be relevant to the provided topic, goto (8), else decide whether to goto (0) or (4) # noqa: E501

        (8)  Mark the document
        (9*) Decide whether to goto (0) or (4)

        This method returns None.
        """

        def after_subtopic():
            self.__do_action(Actions.QUERY)

        def after_query():
            self.__do_action(Actions.SERP)

        def after_serp():
            # TODO: LOG LM HERE.
            if self.__action_value:
                self.__do_action(Actions.SNIPPET)
            else:
                self.__do_action(Actions.SUBTOPIC)

        def after_snippet():
            if self.__action_value:
                self.__do_action(Actions.DOC)
            else:
                self.__do_action(self.__do_decide())

        def after_assess_document():
            if self.__action_value:
                self.__do_action(Actions.MARK)
            else:
                self.__do_action(self.__do_decide())

        def after_mark():
            """
            This condition will always be True; we won't get here unless the document has been successfully marked!
            After the document has been marked, the user must decide whether (s)he wants to look at the subsequent snippet, or issue another query. # noqa: E501
            """

            self.__do_action(self.__do_decide())

        def after_none():
            """
            If no action has been supplied from before, then we must be at the start of the search session.
            Therefore, we begin by querying.
            """
            self.__do_action(Actions.SUBTOPIC)

        last_to_next_action_mapping = {
            Actions.SUBTOPIC: after_subtopic,
            Actions.QUERY: after_query,
            Actions.SERP: after_serp,
            Actions.SNIPPET: after_snippet,
            Actions.DOC: after_assess_document,
            Actions.MARK: after_mark,
            None: after_none,
        }

        last_action = self.__search_context.get_last_action()
        last_to_next_action_mapping[last_action]()

    def __do_action(self, action: str):
        """
        Selects the appropriate method to call to execute the requested action, then logs the interaction in the log and search context. # noqa: E501
        This method returns None.
        """
        action_mapping = {
            Actions.SUBTOPIC: self.__do_subtopic,
            Actions.QUERY: self.__do_query,
            Actions.SERP: self.__do_serp,
            Actions.SNIPPET: self.__do_snippet,
            Actions.DOC: self.__do_assess_document,
            Actions.MARK: self.__do_mark_document,
        }

        # Update the search context to reflect the most recent action.
        # Logging takes place within each method called (e.g. __do_query()) to reflect different values being passed.
        # This method prepares whatever is nedded BEFORE calling the actual step.
        self.__search_context.set_action(action)

        # Now call the appropriate method to perform the action.
        self.__action_value = action_mapping[action]()

    def __do_subtopic(self):
        """
        Called when the simulated user wants to pick another subtopic.
        This works by calling the search context for the next subtopic text, which in turns impacts on the user query
            behaviour, by influencing its LM
        """
        # Get a new subtopic
        new_subtopic = self.__subtopic_picker.pick()
        if new_subtopic is False:
            # If there is no new subtopic, we are done. And we end the simulation
            # Save LMs one more time
            self.__query_generator.update_model(self.__search_context)  # Update LM one last time
            self.__output_controller.log_language_model(self.__query_generator.background_language_model, "GLOBAL")
            for subtopic in self.__search_context.topic.subtopics:
                self.__output_controller.log_language_model(
                    self.__query_generator.subtopics_language_models[subtopic], subtopic
                )

            self.__logger.queries_exhausted()
            return False

        if new_subtopic not in self.__search_context._used_subtopics:
            self.__search_context._new_subtopic = True
        else:
            self.__search_context._new_subtopic = False

        # If the user changed the subtopic, keep track of it.
        if new_subtopic != self.__search_context._last_subtopic:
            self.__search_context._picked_subtopics.append(new_subtopic)
            self.__search_context._used_subtopics.add(new_subtopic)
        self.__search_context._last_subtopic = new_subtopic
        return True

    def __do_query(self) -> bool:
        """
        Called when the simulated user wishes to issue another query.
        This works by calling the search context for the subsequent query text, and is then issued to the search
            interface by the search context on behalf of the user.
        If no further queries are available, the logger is told of this - and the simulation will then stop
            at the next iteration.
        """
        # update the query generator with the latest search context.
        self.__query_generator.update_model(self.__search_context)
        # save all language models
        self.__output_controller.log_language_model(self.__query_generator.background_language_model, "GLOBAL")
        for subtopic in self.__search_context.topic.subtopics:
            try:
                self.__output_controller.log_language_model(
                    self.__query_generator.subtopics_language_models[subtopic], subtopic
                )
            except KeyError:  # LM still doesn't exist. Create it.
                self.__query_generator.init_lm_subtopic(subtopic, self.__search_context)
                self.__output_controller.log_language_model(
                    self.__query_generator.subtopics_language_models[subtopic], subtopic
                )

        # Get a query from the generator.
        query_text = self.__query_generator.get_next_query(self.__search_context)

        if query_text:
            # Can also supply page number and page lengths here.
            # This is where the query is ACTUALLY issued.
            self.__search_context.add_issued_query(query_text)
            self.__logger.log_action(Actions.QUERY, query=query_text)
            self.__output_controller.log_query(query_text)

            return True

        self.__output_controller.log_info(info_type="OUT_OF_QUERIES")
        # Tells the logger that there are no remaining queries; the logger will then stop the simulation.
        # self.__logger.queries_exhausted()
        return False

    def __do_serp(self):
        """
        Called when the simulated user wishes to examine a SERP - the "initial glance" - after issuing a query.
        If the SERP has no results, we continue with the next action - otherwise we will always go and look at said SERP. # noqa: E501
        """
        if self.__search_context.get_current_results_length() == 0:
            self.__logger.log_action(Actions.SERP, status="EMPTY_SERP")
            # No results present; return False (we don't continue with this SERP)
            return False

        # Code updates on 2017-09-28 for refactoring.
        # Simplified this portion -- the SERP impression component now only returns a True/False value.
        is_serp_attractive = self.__serp_impression.is_serp_attractive()
        # Update the search context.
        self.__search_context.add_serp_impression(is_serp_attractive)

        if is_serp_attractive:
            self.__logger.log_action(Actions.SERP, status="EXAMINE_SERP")
        else:
            self.__logger.log_action(Actions.SERP, status="IGNORE_SERP")

        return is_serp_attractive

    def __do_snippet(self):
        """
        Called when the user needs to make the decision whether to examine a snippet or not.
        The logic within this method supports previous observations of the same document, and whether the text within the snippet appears to be relevant. # noqa: E501
        """
        judgment = False
        snippet = self.__search_context.get_current_snippet()
        self.__search_context.increment_serp_position()

        if self.__search_context.get_document_observation_count(snippet) > 0:
            # This document has been previously seen; so we ignore it. But the higher the count, cumulated credibility could force us to examine it? # noqa: E501
            self.__logger.log_action(Actions.SNIPPET, status="SEEN_PREVIOUSLY", snippet=snippet)

        else:
            # This snippet has not been previously seen; check quality of snippet. Does it show some form of relevance?
            # If so, we return True - and if not, we return False, which moves the simulator to the next step.

            if self.__snippet_classifier.is_relevant(snippet):
                # snippet.judgment = 1
                self.__logger.log_action(Actions.SNIPPET, status="SNIPPET_RELEVANT", snippet=snippet)
                judgment = True
            else:
                snippet.judgment = 0
                self.__logger.log_action(Actions.SNIPPET, status="SNIPPET_NOT_RELEVANT", snippet=snippet)

        return judgment

    def __do_assess_document(self):
        """
        Called when a document is to be assessed.
        """
        judgment = False
        if self.__search_context.get_last_query():
            document = self.__search_context.get_current_document()
            self.__logger.log_action(Actions.DOC, status="EXAMINING_DOCUMENT", doc_id=document.id)

            if self.__document_classifier.is_relevant(document):
                document.judgment = 1
                # mark snippet as relevant, so their LM is also updated.
                snippet = self.__search_context.get_current_snippet()
                snippet.judgment = 1

                self.__logger.log_action(Actions.MARK, status="CONSIDERED_RELEVANT", doc_id=document.id)
                self.__search_context.add_relevant_document(document)
                judgment = True
                # Update tracking of subtopics
                self.__search_context.update_subtopics_tracker(document.id)
                self.__output_controller.log_subtopic_tracking(self.__search_context.get_subtopic_tracking())
            else:
                document.judgment = 0
                self.__search_context.add_irrelevant_document(document)
                self.__logger.log_action(Actions.MARK, status="CONSIDERED_NOT_RELEVANT", doc_id=document.id)
                judgment = False

            # Also update snippet classifier at the same time, since they BOTH got relevancy changed.
            self.__document_classifier.update_model(self.__search_context)
            self.__snippet_classifier.update_model(self.__search_context)

        return judgment

    def __do_mark_document(self):
        """
        The outcome of marking a document as relevant. At this stage, the user has decided that the document is relevant; hence True can be the only result. # noqa: E501
        """
        judgement_message = {0: "CONSIDERED_NOT_RELEVANT", 1: "CONSIDERED_RELEVANT"}

        document = self.__search_context.get_current_document()
        snippet = self.__search_context.get_current_snippet()
        snippet.judgment = 1

        self.__logger.log_action(Actions.MARK, status=judgement_message[document.judgment], doc_id=document.id)

        return True

    def __do_decide(self):
        """
        Method which returns whether a further snippet should be examined, the next query should be issued, or some other action. # noqa: E501
        This is the "decision making" logic - and is abstracted to the instantiated DecisionMaker instance to work this out. # noqa: E501
        """
        current_serp_length = self.__search_context.get_current_results_length()
        current_serp_position = self.__search_context.get_current_serp_position() + 1

        if current_serp_position > current_serp_length:
            # If this condition arises, we have reached the end of the SERP!
            # When SERP pagination is implemented, this condition will either result in moving to the next SERP page or query. # noqa: E501
            self.__output_controller.log_info(info_type="SERP_END_REACHED")
            return Actions.SUBTOPIC

        return self.__decision_maker.decide()
