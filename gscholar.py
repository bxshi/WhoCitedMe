#!/usr/bin/env python3

import hashlib
import json
import itertools
from time import sleep

from selenium import webdriver
from selenium.common import exceptions

GSCHOLAR_URL = "https://scholar.google.com/citations?user=BINSaTEAAAAJ"
SLEEP_SEC = 2  # Change this to a larger number if your Internet connection is slow.


def extract_paper_divs(d):
    """ Extract paper divs from a person's google scholar page
    :param d: Selenium driver object with a person's google scholar page opened.
    :return: A list of divs containing publications.
    """
    return d.find_elements_by_css_selector("tr.gsc_a_tr")


def extract_papers():
    # Start headless browser
    driver = webdriver.Chrome()
    driver.get(GSCHOLAR_URL)

    # Expand GScholar to show all papers (TODO: check if clicking once is sufficient).
    try:
        show_more_btn = driver.find_element_by_xpath('//span[text()="Show more"]')
        show_more_btn.click()
        print("Sleep %d seconds to wait for loading..." % SLEEP_SEC)
        sleep(SLEEP_SEC)
    except exceptions.NoSuchElementException as err:
        print("Can not locate SHOW_MORE button.")

    papers = [Paper(x) for x in extract_paper_divs(driver)]
    print("Load %d papers from profile." % len(papers))
    driver.close()
    return papers


class CitationObject(object):
    """Comparable class based on citation count.
    """

    def __gt__(self, other):
        return self.citation > other.citation

    def __ge__(self, other):
        return self.citation >= other.citation

    def __lt__(self, other):
        return self.citation < other.citation

    def __le__(self, other):
        return self.citation <= other.citation

    def __eq__(self, other):
        return self == other

    def to_json(self):
        raise NotImplementedError('toJSON is not implemented.')

    def __hash__(self):
        return int(hashlib.md5(json.dumps(self.to_json()).encode()).hexdigest(), 16)


class Author(CitationObject):
    def __init__(self, author_elem):
        author_profile = author_elem.find_element_by_css_selector("#gsc_prf")
        self.name = author_profile.find_element_by_css_selector("#gsc_prf_in").text
        self.affiliation = author_profile.find_element_by_css_selector("div.gsc_prf_il").text
        self.citation = int(author_elem.find_element_by_css_selector("td.gsc_rsb_std").text)

    def __str__(self):
        return json.dumps(self.to_json(), indent=2, sort_keys=False)

    def __eq__(self, other):
        return all([x == y for (x, y) in zip([self.name, self.affiliation, self.citation],
                                             [other.name, other.affiliation, other.citation])])

    def __hash__(self):
        return int(hashlib.md5(json.dumps(self.to_json()).encode()).hexdigest(), 16)

    def to_json(self):
        return {"name": self.name,
                "affiliation": self.affiliation,
                "citation": self.citation}


class Citation(CitationObject):
    def __init__(self, citation_elem):
        self.title = citation_elem.find_element_by_css_selector("h3.gs_rt").text
        self.info = citation_elem.find_element_by_css_selector("div.gs_a").text
        citation_count_str = citation_elem.find_elements_by_css_selector("div.gs_fl a")[2].text
        if citation_count_str.startswith("Cited by"):
            self.citation = int(citation_count_str.replace("Cited by ", ""))
        else:
            self.citation = 0

        authors = citation_elem.find_elements_by_css_selector("div.gs_a a")
        d = webdriver.Chrome()
        d.maximize_window()
        self.authors = []
        for author in authors:
            sleep(SLEEP_SEC)
            d.get(author.get_attribute("href"))
            self.authors.append(Author(d))
        d.close()
        self.authors = sorted(self.authors, reverse=True)

    def __str__(self):
        return json.dumps(self.to_json(),
                          indent=2, sort_keys=False)

    def __eq__(self, other):
        return all([x == y for (x, y) in zip([self.title, self.info, self.citation],
                                             [other.title, other.info, other.citation])])

    def __hash__(self):
        return int(hashlib.md5(json.dumps(self.to_json()).encode()).hexdigest(), 16)

    def to_json(self):
        return {"title": self.title,
                "info": self.info,
                "citation": self.citation,
                "authors": [x.to_json() for x in self.authors]}


class Paper(CitationObject):
    citation_details = []

    def __init__(self, d):
        self.title = d.find_element_by_css_selector(".gsc_a_at").text
        self.authors, self.venue = [_.text for _ in d.find_elements_by_css_selector(".gsc_a_t .gs_gray")]
        try:
            self.citation = int(d.find_element_by_css_selector(".gsc_a_c").text)
        except ValueError:
            self.citation = 0
        self.citation_url = d.find_element_by_css_selector(".gsc_a_c a").get_attribute("href")
        self.year = d.find_element_by_css_selector(".gsc_a_y").text
        self.citation_details = []

    def parse_citations(self):
        if not self.citation_url:
            return
        d = webdriver.Chrome()
        d.get(self.citation_url)
        citation_elems = d.find_elements_by_css_selector("div.gs_ri")
        self.citation_details = [Citation(citation_elem) for citation_elem in citation_elems]

        # check next page
        try:
            next_btn = d.find_element_by_xpath('//button[@aria-label="Next"]')
            while next_btn.is_enabled():
                sleep(SLEEP_SEC)
                next_btn.click()
                citation_elems = d.find_elements_by_css_selector("div.gs_ri")
                self.citation_details.extend([Citation(x) for x in citation_elems])
                next_btn = d.find_element_by_xpath('//button[@aria-label="Next"]')
        except exceptions.NoSuchElementException:
            pass
        d.close()

        self.citation_details = sorted(self.citation_details, reverse=True)

    def sorted_citation_authors(self):
        unique_authors = list(set(itertools.chain(*[itertools.chain(x.authors) for x in self.citation_details])))
        return sorted(unique_authors, reverse=True)

    def __str__(self):
        return json.dumps(self.to_json(), indent=2, sort_keys=False)

    def to_json(self):
        return {'title': self.title,
                'authors': self.authors,
                'citation': self.citation,
                'year': self.year,
                'citation_details': [x.to_json() for x in self.citation_details]}


def sort_citation_objects(authors):
    """Sort all authors based on citation count.
    :param authors: A list of author lists.
    :return: A list of authors sorted in descending order.
    """
    authors = set(itertools.chain(*[x if isinstance(x, CitationObject) else itertools.chain(x) for x in authors]))
    return sorted(authors, reverse=True)


if __name__ == '__main__':
    papers = extract_papers()

    for paper_id, paper in enumerate(papers):
        paper.parse_citations()
        with open("paper_%d.json" % paper_id, 'w') as fout:
            fout.write(json.dumps(paper.to_json(), indent=2))
    sorted_authors = [_.to_json() for _ in sort_citation_objects([x.sorted_citation_authors() for x in papers])]
    with open("sorted_citation_authors.json", 'w') as fout:
        fout.write(json.dumps(sorted_authors, indent=2))
    sorted_citations = [_.to_json() for _ in sort_citation_objects([x.citation_details for x in papers])]
    with open("sorted_citations.json", 'w') as fout:
        fout.write(json.dumps(sorted_citations, indent=2))
