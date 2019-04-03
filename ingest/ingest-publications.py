from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph, Namespace, RDF
import json
import requests
import multiprocessing
from itertools import chain
import functools
import argparse
import logging, sys
import urllib
import pdb   # Debugging purposes - comment out for production
import socket
import time
import os

# import EMAIL and PASSWORD variables for VIVO sparqlquery API, this is a link to a file for github purposes
# Also eventually can put more config info in here
from vivoapipw import *

g1 = Graph()

# This was used to create weblinks from facetview to VIVO. 
# TODO: parameterize the URL for the target link, this can accomodate all of our VIVO instances
SYSTEM_NAME = socket.gethostname()
if '-dev' in SYSTEM_NAME:
   BASE_URL = 'https://vivo-cub-dev.colorado.edu/individual'
else:
   BASE_URL = 'https://experts.colorado.edu/individual'

PROV = Namespace("http://www.w3.org/ns/prov#")
BIBO = Namespace("http://purl.org/ontology/bibo/")
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")
VIVO = Namespace('http://vivoweb.org/ontology/core#')
VITRO = Namespace("http://vitro.mannlib.cornell.edu/ns/vitro/0.7#")
VITRO_PUB = Namespace("http://vitro.mannlib.cornell.edu/ns/vitro/public#")
OBO = Namespace("http://purl.obolibrary.org/obo/")
CUB = Namespace(BASE_URL + "/")
FIS_LOCAL = Namespace("https://experts.colorado.edu/ontology/vivo-fis#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
FIS = Namespace("https://experts.colorado.edu/individual")
NET_ID = Namespace("http://vivo.mydomain.edu/ns#")
PUBS = Namespace("https://experts.colorado.edu/ontology/pubs#")

# standard filters
non_empty_str = lambda s: True if s else False
has_label = lambda o: True if o.label() else False

class Maybe:
    def __init__(self, v=None):
        self.value = v

    @staticmethod
    def nothing():
        return Maybe()

    @staticmethod
    def of(t):
        return Maybe(t)

    def reduce(self, action):
        return Maybe.of(functools.reduce(action, self.value)) if self.value else Maybe.nothing()

    def stream(self):
        return Maybe.of([self.value]) if self.value is not None else Maybe.nothing()

    def map(self, action):
        return Maybe.of(chain(map(action, self.value))) if self.value is not None else Maybe.nothing()

    def flatmap(self, action):
        return Maybe.of(chain.from_iterable(map(action, self.value))) if self.value is not None else Maybe.nothing()

    def andThen(self, action):
        return Maybe.of(action(self.value)) if self.value is not None else Maybe.nothing()

    def orElse(self, action):
        return Maybe.of(action()) if self.value is None else Maybe.of(self.value)

    def do(self, action):
        if self.value:
            action(self.value)
        return self

    def filter(self, action):
        return Maybe.of(filter(action, self.value)) if self.value is not None else Maybe.nothing()

    def followedBy(self, action):
        return self.andThen(lambda _: action)

    def one(self):
        try:
            return Maybe.of(next(self.value)) if self.value is not None else Maybe.nothing()
        except StopIteration:
            return Maybe.nothing()
        except TypeError:
            return self

    def list(self):
        return list(self.value) if self.value is not None else []

def get_altmetric_for_doi(ALTMETRIC_API_KEY, doi):
    if doi:
        query = ('http://api.altmetric.com/v1/doi/' + doi + '?key=' +
                 ALTMETRIC_API_KEY)

        try:
           r = requests.get(query)
           if r.status_code == 200:
             try:
                json = r.json()
                return json['score']
             except ValueError:
                logging.exception("Could not parse Altmetric response. ")
                return None
             except ValueError:
                logging.exception("Could not parse Altmetric response. ")
                return None
           elif r.status_code == 420:
              logging.info("Rate limit in effect!!!!")
              time.sleep(5)
           elif r.status_code == 403:
              logging.warn("Altmetric says you aren't authorized for this call.")
              return None
           else:
              logging.debug("No altmetric record or API error. ")
              return None
        except:
           logging.exception("Altmetric connection failure")
    else:
        return None

def get_orcid(person):
    return Maybe.of(person).stream() \
        .flatmap(lambda p: p.objects(VIVO.orcidId)) \
        .map(lambda o: o.identifier) \
        .map(lambda o: o[o.rfind('/') + 1:]).one().value


def get_research_areas(person):
    return Maybe.of(person).stream() \
        .flatmap(lambda p: p.objects(VIVO.hasResearchArea)) \
        .filter(has_label) \
        .map(lambda r: {"uri": str(r.identifier), "name": str(r.label())}).list()


def get_organizations(person):

    organizations = []

    positions = Maybe.of(person).stream() \
        .flatmap(lambda per: per.objects(VIVO.relatedBy)) \
        .filter(lambda related: has_type(related, VIVO.Position)).list()

    for position in positions:
        organization = Maybe.of(position).stream() \
            .flatmap(lambda r: r.subjects(VIVO.relatedBy)) \
            .filter(lambda o: has_type(o, FOAF.Organization)) \
            .filter(has_label) \
            .map(lambda o: {"uri": str(o.identifier), "name": str(o.label())}).one().value

        if organization:
            organizations.append(organization)
    return organizations


def get_metadata(id):
    return {"index": {"_index": args.index, "_type": "publication", "_id": id}}

def has_type(resource, type):
    for rtype in resource.objects(predicate=RDF.type):
        if str(rtype.identifier) == str(type):
            return True
    return False

def load_file(filepath):
    with open(filepath) as _file:
        return _file.read().replace('\n', " ")

def describe(sparqlendpoint, query):
    print("sparqlendpoint: ", sparqlendpoint)
    print("EMAIL: ", EMAIL)
    print("PASSWORD: ", PASSWORD)
    sparql = SPARQLWrapper(sparqlendpoint)
    sparql.setQuery(query)
    sparql.setMethod("POST")
    sparql.addParameter("email", EMAIL)
    sparql.addParameter("password", PASSWORD)
    logging.debug('logging - describe query: %s', query)
    try:
        results = sparql.query().convert()
        print("results: ", results)
        return results
    except EndPointInternalError:
        try:
            results = sparql.query().convert()
            print("results: ", results)
            return results
        except RuntimeWarning:
            pass
    except RuntimeWarning:
        pass

def create_publication_doc(pubgraph,publication):

    pub = g1.resource(publication)

    try:
        title = pubgraph.label(publication,"default title")
        logging.info('title: %s', title)
    except AttributeError:
        print("missing title:", publication)
        return {}

    pubId = publication[publication.rfind('/pubid_') + 7:]
    logging.info('pubid: %s', pubId)
    doc = {"uri": publication, "name": title, "pubId": pubId}

    doi = list(pub.objects(predicate=BIBO.doi))
    doi = doi[0].toPython() if doi else None
    ams = 0
    if doi:
        doc.update({"doi": doi})
        ams = get_altmetric_for_doi(ALTMETRIC_API_KEY, doi)
    doc.update({"amscore": ams})

    abstract = list(pub.objects(predicate=BIBO.abstract))
    abstract = abstract[0].encode('utf-8') if abstract else None
    if abstract:
        doc.update({"abstract": abstract})

    pageEnd = list(pub.objects(predicate=BIBO.pageEnd))
    pageEnd = pageEnd[0].encode('utf-8') if pageEnd else None
    if pageEnd:
        doc.update({"pageEnd": pageEnd})

    pageStart = list(pub.objects(predicate=BIBO.pageStart))
    pageStart = pageStart[0].encode('utf-8') if pageStart else None
    if pageStart:
        doc.update({"pageStart": pageStart})

    issue = list(pub.objects(predicate=BIBO.issue))
    issue = issue[0].encode('utf-8') if issue else None
    if issue:
        doc.update({"issue": issue})

    numPages = list(pub.objects(predicate=BIBO.numPages))
    numPages = numPages[0].encode('utf-8') if numPages else None
    if numPages:
        doc.update({"numPages": numPages})

    volume = list(pub.objects(predicate=BIBO.volume))
    volume = volume[0].encode('utf-8') if volume else None
    if volume:
        doc.update({"volume": volume})

    citedAuthors = list(pub.objects(predicate=PUBS.citedAuthors))
    citedAuthors = citedAuthors[0].encode('utf-8') if citedAuthors else None
    if citedAuthors:
        doc.update({"citedAuthors": citedAuthors})

    most_specific_type = list(pub.objects(VITRO.mostSpecificType))
    most_specific_type = most_specific_type[0].label().toPython() \
        if most_specific_type and most_specific_type[0].label() \
        else None
    if most_specific_type:
        doc.update({"mostSpecificType": most_specific_type})

    date_time_object = list(pub.objects(predicate=VIVO.dateTimeValue))
    date_time_object = date_time_object[0] if date_time_object else None
    if date_time_object is not None:
       date_time = list(date_time_object.objects(predicate=VIVO.dateTime))
       date_time = date_time[0] if date_time else None
       logging.debug("date: %s",str(date_time)[:10])
       logging.debug("year: %s",str(date_time)[:4])
       publication_date = str(date_time)[:10]
       publication_year = str(date_time)[:4]

       doc.update({"publicationDate": publication_date})
       doc.update({"publicationYear": publication_year})

    venue = list(pub.objects(VIVO.hasPublicationVenue))
    venue = venue[0] if venue else None
    if venue and venue.label():
        doc.update({"publishedIn": {"uri": str(venue.identifier), "name": venue.label().encode('utf8')}})
    elif venue:
        print("venue missing label:", str(venue.identifier))

    authors = []
    for s, p, o in pubgraph.triples((None, VIVO.relates, None)):
       for a, b, c in g1.triples((o, RDF.type, FOAF.Person)):
          gx = Graph()
          gx += g1.triples((a, None, None))
          name = (gx.label(a))
          obj = {"uri": a, "name": name}
          per = g1.resource(a)

          orcid = get_orcid(per)
          if orcid:
              obj.update({"orcid": orcid})

          organizations = get_organizations(per)
          if organizations:
            obj.update({"organization": organizations})

          research_areas = get_research_areas(per)
          if research_areas:
            obj.update({"researchArea": research_areas})

          authors.append(obj)

    doc.update({"authors": authors})

    logging.debug('Publication doc: %s', doc)
    #DEBUGS #pdb.set_trace()
    return doc

def process_publication(publication):
    pid = str(os.getpid())
    logfile = args.spooldir + '/log-' + pid
    idxfile = args.spooldir + '/idx-' + pid
    fidx=open(idxfile, 'a+')
    logging.info('Processing Publication: %s', publication)
    if publication.find("pubid_") == -1:
       logging.info('INVALID PUBLICATION: %s', publication) 
       return []
    pubgraph = Graph()
    pubgraph += g1.triples((publication, None, None))
    for o in pubgraph.objects(predicate=VIVO.relatedBy):
        pubgraph += g1.triples((o, None, None))
        pub = create_publication_doc(pubgraph=pubgraph, publication=publication)
        es_id = pub["pubId"] if "pubId" in pub and pub["pubId"] is not None else pub["uri"]
        logging.debug('es_id: %s', es_id)
    record = [json.dumps(get_metadata(es_id)), json.dumps(pub)]
    fidx.write('\n'.join(record) + "\n")
    return [json.dumps(get_metadata(es_id)), json.dumps(pub)]
    fidx.close()

def generate(threads):
    pool = multiprocessing.Pool(threads)
    params = [pub for pub in g1.subjects(RDF.type, BIBO.Document)]
    print("params: ", params)
    return list(chain.from_iterable(pool.map(process_publication, params)))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--threads', default=8, help='number of threads to use (default = 8)')
    parser.add_argument('--sparqlendpoint', default='http://localtomcathost:8780/vivo/api/sparqlQuery', help='local tomcat host and port for VIVO sparql query API endpoint')
    parser.add_argument('--spooldir', default='./spool', help='where to write files')
    parser.add_argument('--index', default='fis-pubs-setup', help='name of index, needs to correlate with javascript library')
    parser.add_argument('out', metavar='OUT', help='elasticsearch bulk ingest file')
    args = parser.parse_args()
    sparqlendpoint=args.sparqlendpoint

    get_orgs_query = load_file("queries/listOrgs.rq")
    get_subjects_query = load_file("queries/listSubjects.rq")
    get_author_query = load_file("queries/listAuthors.rq")
    get_pub_query = load_file("queries/listPubs.rq")

    g1 += describe(sparqlendpoint,get_orgs_query)
    g1 = g1 + describe(sparqlendpoint,get_subjects_query)
    g1 = g1 + describe(sparqlendpoint,get_author_query)
    g1 = g1 + describe(sparqlendpoint,get_pub_query)
    print("EMAIL: ", EMAIL)
    print("PASSWORD: ", PASSWORD)

    records = generate(threads=int(args.threads))
    print "generated records"
    with open(args.out, "w") as bulk_file:
      bulk_file.write('\n'.join(records))

