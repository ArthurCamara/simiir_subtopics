from simiir.search_interfaces import Document
from simiir.search_interfaces.base_interface import BaseSearchInterface
from ifind.search.response import Response
import logging
import time
import redis
import pickle
import requests

log = logging.getLogger("simuser.search_interfaces.bing_interface")

BLOCKLIST = [
    "hawaiilibrary.net",
    "theinfolist.com",
    "peoplemaven.com",
    "wiki2.org",
    "zoo-hoo.com",
    "museumstuff.com",
    "answers.com",
    "oilfieldwiki.com",
    "wikimili.com",
    "winentrance.com",
    "Paralumnun.com",
    "wikinfo.org",
    "jambase.com",
    "newworldencyclopedia.org",
    "wikiwand.com",
    "medievalwarfare.info",
    "tripatlas.com",
    "alchetron.com",
    "wikivisually.com",
    "printfriendly.com",
    "afropedea.org",
    "conservapedia.com",
    "kids.kiddle.co",
    "thefreedictionary.com",
    "dictionary.sensagent.com",
    "artistopia.com",
    "academickids.com",
    "jewishvirtuallibrary.org",
    "classictvhits.com",
    "findwords.info",
    "pediapress.com",
    "memim.com",
    "i2osig.org",
    "absoluteastronomy.com",
    "wikishire.co.uk",
    "biographybase.com",
    "knowledgewiki.org",
    "en.turkcewiki.org",
    "gpedia.com",
    "heart-disease.health-cares.net",
    "sheppardsoftware.com",
    "wikimapia.org",
    "us.wow.com",
    "citizendium.org",
    "mondolatino.eu",
    "jiskha.com",
    "footballyears.net",
    "encyclopedia.thefreedictionary.com",
    "wp.wiki-wiki.ru",
    "wiki.phantis.com",
    "roadnow.com",
    "getwiki.net",
    "marspc.co.il",
    "self.gutenberg.org",
    "wikibin.org",
    "vacilando.org",
    "statemaster.com",
    "wikiwix.com",
    "daviddarling.info",
    "sciencedaily.com",
    "wikipedia.org",
    "wikimili.com",
    "wikiversity.org",
    "thefullwiki.org",
    "petrowiki.org",
    "wikizero.com",
    "wikidoc.org",
    "taggedwiki.zubiaga.org",
    "wiki.seg.org",
    "youtube.com",
    "everything.explained.today",
    "self.guttenberg.org",
]


# TODO CACHE RESULTS TO REDIS


class BingSearchInterface(BaseSearchInterface):
    """
    A search interface making use of the Bing REST API
    Params:
    """

    def __init__(self, private_key, n_results, search_url, blocklist=BLOCKLIST, redis_db=None, mkt="en-US"):
        super(BingSearchInterface, self).__init__()
        log.debug("Using BING API as a search backend")
        if redis_db:
            self.__redis_conn = redis.Redis(db=redis_db)
        blocklist_str = " -site:".join(blocklist)

        self.search_url = search_url
        self.query_template = "{}  -site:" + blocklist_str + "  -filetype:pdf"
        self.headers = {"Ocp-Apim-Subscription-Key": private_key}
        # Add query as q
        self.params = {"textDecorations": True, "textFormat": "HTML", "count": n_results, "mkt": mkt}

    def issue_query(self, query, top=100):
        """
        Allows one to issue a query to the underlying search engine. Takes an ifind Query object.
        """
        print("DEBUG TIME")
        query.top = top
        bing_response = self._send_bing_request(query)
        response = self._parse_bing_result(bing_response)

        self._last_query = query
        self._last_response = response
        return response

    def get_document(self, document_id):
        """
        Retrieves a Document object for the given document specified by parameter document_id.
        """
        # Doc stored on Redis as dictionary pickle object, with all fields.
        # TODO Check if page exists on cache. If not, retrieve it and return the textual context of it.

        # Can have id, title, content, doc_id, qrels_filename, background_terms, subtopics
        # Need to have: doc_id, content (clean), title
        doc = Document()
        fields = self.__reader.stored_fields(int(document_id))

        title = fields["title"]
        content = fields["content"]
        document_num = fields["docid"]
        document_date = fields["timedate"]
        document_source = fields["source"]

        document = Document(id=document_id, title=title, content=content)
        document.date = document_date
        document.doc_id = document_num
        document.source = document_source

        return document

    def _send_bing_request(self, query: Query):
        query_str = query.terms.strip().lower()
        self.params["q"] = self.query_template.format(query_str)
        response = requests.get(self.search_url, headers=self.headers, params=self.params)
        try:
            response.raise_for_status()
        except requests.HTTPError:  # Wait a second and try again
            time.sleep(1)
            response = requests.get(
                self.search_url,
                headers=self.headers,
                params=self.params,
                verify="/ssd/arthur/anaconda3/envs/simiir/lib/python2.7/site-packages/requests/cacert.pem",
            )
            response.raise_for_status()

        return response.json()

    def _parse_bing_result(self, query, bing_results):
        """Parses a bing results page into an iFind response
        Args:
            query: An iFind query object
            bing_results: An json dictionary with Bing results
        Returns:
            iFind results object"""

        response = Response(query.terms, query)

        rank_counter = 1

        for r in bing_results["webPages"]["value"]:
            response.add_result(title=r[u"Name"], url=r[u"url"], summary=r[u"snippet"], rank=rank_counter)
            rank_counter += 1

        return response
