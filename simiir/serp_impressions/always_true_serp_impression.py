from simiir.serp_impressions.base_serp_impression import BaseSERPImpression


class AlwaysTrueSERPImpression(BaseSERPImpression):
    """A class that will ALWAYS return true for serp impressions.
    Identical to SimpleSERPImpression, but without patch_judgements, since we don't have QRELS.
    """

    def __init__(self, search_context, host=None, port=None):
        super(AlwaysTrueSERPImpression, self).__init__(search_context=search_context, host=host, port=port)

    def is_serp_attractive(self):
        """
        Determines whether the SERP is attractive.
        As this is the SimpleSERPImpression, the SERP is always considered attractive.

        """

        return True
