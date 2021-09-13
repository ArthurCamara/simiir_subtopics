from typing import Dict, List
from requests.sessions import HTTPAdapter
from simiir.search_interfaces import Document
from simiir.search_interfaces.base_interface import BaseSearchInterface
from ifind.search.response import Response
from ifind.search.query import Query
import logging
import time
import redis
import requests
import pickle
import justext
import lxml

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
        private_key: A string with the BING API key.
        n_results: Integer with may results to return at each interaction.
        search_url: BING API endpoint URL.
        blocklist: List with urls that should NOT be returned by BING. Generally, a copy of wikipedia.
        redis_db: Optional. If used, the ID of a redis DB to be used to cache results. redis_db+1 will store SERPS
        mkt: Optional. A string with what market to use for the bing api. Defaults to en-US.
    """

    def __init__(
        self,
        private_key: str,
        n_results: int,
        search_url: str,
        blocklist: List[str] = BLOCKLIST,
        redis_db: int = None,
        mkt: str = "en-US",
    ):
        super(BingSearchInterface, self).__init__()
        log.debug("Using BING API as a search backend")
        if redis_db:
            self.__redis_page_cache = redis.Redis(db=redis_db)
            self.__redis_SERP_cache = redis.Redis(db=redis_db + 1)
            self.__redis_in_use = True
        else:
            self.__redis_in_use = False

        blocklist_str = " -site:".join(blocklist)

        self.search_url = search_url
        self.query_template = "{}  -site:" + blocklist_str + "  -filetype:pdf"
        self.headers = {"Ocp-Apim-Subscription-Key": private_key}
        # Add query as q
        self.params = {"textDecorations": True, "textFormat": "HTML", "count": n_results, "mkt": mkt}
        self._doc_titles = {}

    def issue_query(self, query: Query, top: int = 100) -> Response:
        """
        Allows one to issue a query to the underlying search engine. Takes an ifind Query object.
        """

        query.top = top
        bing_response = self._send_bing_request(query)
        response = self._parse_bing_result(query, bing_response)

        self._last_query = query
        self._last_response = response
        return response

    def get_document(self, document_id: str) -> Document:
        """
        Retrieves a Document object for the given document specified by parameter document_id.
        args:
            document_id: String with document URL
        Returns:
            An ifind Document object
        """

        title = self._doc_titles[document_id]
        content = self._fetch_web_page_contents(document_id)

        document = Document(id=document_id, title=title, content=content)

        return document

    def _send_bing_request(self, query: Query) -> Dict:
        """Sends a request to the Bing API and returns a dictionary with the parsed JSON response
        Args:
            query: A Query object with the query terms
        Returns:
            A Dictionary with the parsed JSON results
        """
        query_str = query.terms.strip().lower()

        if self.__redis_in_use and query_str in self.__redis_SERP_cache:
            return pickle.loads(self.__redis_SERP_cache.get(query_str))

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
            )
            response.raise_for_status()

        # Store SERP in REDIS
        if self.__redis_in_use:
            self.__redis_SERP_cache.set(query_str, pickle.dumps(response.json()))
        return response.json()

    def _parse_bing_result(self, query: Query, bing_results: Dict) -> Response:
        """Parses a bing results page into an iFind response
        Args:
            query: An iFind Query object
            bing_results: An JSON dictionary with Bing results
        Returns:
            iFind Response object"""

        response = Response(query.terms, query)

        rank_counter = 1

        for r in bing_results["webPages"]["value"]:
            self._doc_titles[r"url"] = r["name"]
            response.add_result(title=r["name"], url=r["url"], summary=r["snippet"], rank=rank_counter)
            rank_counter += 1

        return response

    def _fetch_web_page_contents(self, url: str) -> str:
        """Fetches a webpage, given its url. May return an empty page if the page can't be reached for some reason.
        If the page already exists in the local redis cache, will return it instead.
        Args:
            url: A string with the page url to be fetched
        """
        if self.__redis_in_use and self.__redis_page_cache.exists(url):
            return self.__redis_page_cache.get(url)
        s = requests.Session()
        s.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9"  # noqa: E501
            }
        )
        adapter = HTTPAdapter(max_retries=0)
        s.mount("https://", adapter)
        s.mount("http://", adapter)
        try:
            page_content = s.get(url, verify=False, timeout=5).text
        except (requests.ConnectionError, requests.exceptions.TooManyRedirects, requests.exceptions.ReadTimeout):
            log.warn("Could not fetch page {}".format(url))
            return ""

        page_content = " ".join(self.__clean_page(page_content[1]))
        if self.__redis_in_use:
            self.__redis_page_cache.set(url, page_content)
        return page_content

    def __clean_page(self, html_content):
        # Return a clean page using justext.
        try:
            paragraphs = [
                x.text for x in justext.justext(html_content, justext.get_stoplist("English")) if not x.is_boilerplate
            ]
        except lxml.etree.ParserError:
            paragraphs = [""]
        total_text_len = sum([len(x.split()) for x in paragraphs])
        if total_text_len == 0:
            return (0, [])
        return (total_text_len, paragraphs)
