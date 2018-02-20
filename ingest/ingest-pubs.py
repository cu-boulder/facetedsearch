__author__ = 'szednik'

from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Namespace, RDF
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


def load_file(filepath):
    with open(filepath) as _file:
        return _file.read().replace('\n', " ")


SYSTEM_NAME = socket.gethostname()
if '-dev' in SYSTEM_NAME:
   BASE_URL = 'https://vivo-cub-dev.colorado.edu/individual'
else:
   BASE_URL = 'https://experts.colorado.edu/individual'

ALTMETRIC_API_KEY = 'b7850a6cae053643e3f5f4514569a2ad'

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


get_pubs_query = load_file("queries/listPublications.rq")
describe_publication_query = load_file("queries/describePublication.rq")

# standard filters
non_empty_str = lambda s: True if s else False
has_label = lambda o: True if o.label() else False

def get_altmetric_for_doi(ALTMETRIC_API_KEY, doi):
    if doi:
        query = ('http://api.altmetric.com/v1/doi/' + doi + '?key=' +
                 ALTMETRIC_API_KEY)

        r = requests.get(query)
        if r.status_code == 200:
            try:
                json = r.json()
#                time.sleep(1)
                # print(json['score'])
                return json['score']
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
    else:
        return None



def get_metadata(id):
    return {"index": {"_index": "fis", "_type": "publication", "_id": id}}


def select(endpoint, query):
    endpoint = endpoint
    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    endpoint = endpoint
    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return results["results"]["bindings"]


def describe(endpoint, query):
    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(query)
    logging.debug('logging - describe query: %s', query)
    try:
        results = sparql.query().convert()
        print("results: ", results)
        return results
    except RuntimeWarning:
        pass


def has_type(resource, type):
    for rtype in resource.objects(RDF.type):
        if str(rtype.identifier) == str(type):
            return True
    return False


def get_pubs(endpoint):
    r = select(endpoint, get_pubs_query)
    return [rs["publication"]["value"].encode('utf-8') for rs in r]


def describe_publication(endpoint, publication):
    logging.debug('logging - will describe: %s', publication)
    q = describe_publication_query.replace("?publication", "<" + publication + ">")
    return describe(endpoint, q)


def get_most_specific_type(publication):
    return Maybe.of(publication).stream() \
        .flatmap(lambda p: p.objects(VITRO.mostSpecificType)) \
        .map(lambda t: t.label()) \
        .filter(non_empty_str) \
        .one().value


def get_network_id(publication):
    return Maybe.of(publication).stream() \
        .flatmap(lambda p: p.objects(NET_ID.networkId)) \
        .filter(non_empty_str) \
        .one().value


def get_given_name(publication):
    return Maybe.of(publication).stream() \
        .flatmap(lambda p: p.objects(OBO.ARG_2000028)) \
        .flatmap(lambda v: v.objects(VCARD.hasName)) \
        .flatmap(lambda n: n.objects(VCARD.givenName)) \
        .filter(non_empty_str) \
        .one().value


def get_email(publication):
    return Maybe.of(publication).stream() \
        .flatmap(lambda p: p.objects(OBO.ARG_2000028)) \
        .flatmap(lambda v: v.objects(VCARD.hasEmail)) \
        .flatmap(lambda e: e.objects(VCARD.email)) \
        .filter(non_empty_str) \
        .one().value


def get_research_areas(publication):
    return Maybe.of(publication).stream() \
        .flatmap(lambda p: p.objects(VIVO.hasResearchArea)) \
        .filter(has_label) \
        .map(lambda r: {"uri": str(r.identifier), "name": str(r.label())}).list()


def get_organizations(publication):

    organizations = []

    positions = Maybe.of(publication).stream() \
        .flatmap(lambda pub: pub.objects(VIVO.relatedBy)) \
        .filter(lambda related: has_type(related, VIVO.Position)).list()

    for position in positions:
        organization = Maybe.of(position).stream() \
            .flatmap(lambda r: r.objects(VIVO.relates)) \
            .filter(lambda o: has_type(o, FOAF.Organization)) \
            .filter(has_label) \
            .map(lambda o: {"uri": str(o.identifier), "name": str(o.label())}).one().value

        if organization:
            organizations.append(organization)
    return organizations


def create_publication_doc(publication, endpoint):
    graph = describe_publication(endpoint=endpoint, publication=publication)
    print("graph has %s statements." % len(graph))
#    for s, p, o in graph:
#        print((s, p, o))
#        title = graph.label(s,"s default")
#        print("subject label:", title)

    pub = graph.resource(publication)

    try:
        title = str(pub.label().encode('utf-8'))
        #title = graph.label(pub,"default")
        logging.info('title: %s', title)
    except AttributeError:
        print("missing title:", publication)
        return {}


#    pubId = get_pubid(pub)
    pubId = publication[publication.rfind('/pubid_') + 7:]
    logging.info('pubid: %s', pubId)
    doc = {"uri": publication, "name": title, "pubId": pubId}

    doi = list(pub.objects(BIBO.doi))
    doi = doi[0].toPython() if doi else None
    if doi:
        doc.update({"doi": doi})
        ams = get_altmetric_for_doi(ALTMETRIC_API_KEY, doi)
        doc.update({"amscore": ams})

    abstract = list(pub.objects(BIBO.abstract))
    #abstract = abstract[0].encode('utf-8').toPython() if abstract else None
    abstract = abstract[0].encode('utf-8') if abstract else None
    if abstract:
        doc.update({"abstract": abstract})

    most_specific_type = list(pub.objects(VITRO.mostSpecificType))
#    print("most specific type : ", most_specific_type)
    most_specific_type = most_specific_type[0].label().toPython() \
        if most_specific_type and most_specific_type[0].label() \
        else None
    if most_specific_type:
        doc.update({"mostSpecificType": most_specific_type})

    date_time_object = list(pub.objects(VIVO.dateTimeValue))
    date_time_object = date_time_object[0] if date_time_object else None
    if date_time_object is not None:
       date_time = list(date_time_object.objects(VIVO.dateTime))
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
        #doc.update({"publishedIn": {"uri": str(venue.identifier), "name": venue.label().toPython()}})
        doc.update({"publishedIn": {"uri": str(venue.identifier), "name": venue.label()}})
    elif venue:
        print("venue missing label:", str(venue.identifier))

    authors = []
    authorships = [faux for faux in pub.objects(VIVO.relatedBy) if has_type(faux, VIVO.Authorship)]
    for authorship in authorships:

        author = [person for person in authorship.objects(VIVO.relates) if has_type(person, FOAF.Person)][0]
        name = author.label().toPython() if author else None

        obj = {"uri": str(author.identifier), "name": name}

#        rank = list(authorship.objects(VIVO.rank))
#        rank = rank[0].toPython() if rank else None
#        if rank:
#            obj.update({"rank": rank})

        research_areas = [research_area.label().toPython() for research_area in author.objects(VIVO.hasResearchArea) if research_area.label()]
        print("research area: ", research_areas)

        if research_areas:
            obj.update({"researchArea": research_areas})

        authors.append(obj)

    try:
        authors = sorted(authors, key=lambda a: a["rank"]) if len(authors) > 1 else authors
    except KeyError:
        print("missing rank for one or more authors of:", publication)

    doc.update({"authors": authors})




    logging.debug('Publication doc: %s', doc)
    #pdb.set_trace()
    return doc


def process_publication(publication, endpoint='http://localhost:2020/ds/sparql'):
    logging.info('Processing Publication: %s', publication)
    if publication.find("pubid_") == -1:
       logging.info('INVALID PUBLICATION: %s', publication) 
       return []
    pub = create_publication_doc(publication=publication, endpoint=endpoint)
    es_id = pub["pubId"] if "pubId" in pub and pub["pubId"] is not None else pub["uri"]
    logging.debug('es_id: %s', es_id)
    #es_id = get_id(es_id)
    return [json.dumps(get_metadata(es_id)), json.dumps(pub)]


def publish(bulk, endpoint, rebuild, mapping):
    # if configured to rebuild_index
    # Delete and then re-create to publication index (via PUT request)

    index_url = endpoint+"fis"

    if rebuild:
        requests.delete(index_url)
        r = requests.put(index_url)
        if r.status_code != requests.codes.ok:
            print(r.url, r.status_code)
            r.raise_for_status()

    # push current publication document mapping

    mapping_url = endpoint + "fis/publication/_mapping"
    print "opening mapping"
    with open(mapping) as mapping_file:
        r = requests.put(mapping_url, data=mapping_file, verify=False)
        print "putting map file"
        if r.status_code != requests.codes.ok:
            print r.status_code, r.content
            # new mapping may be incompatible with previous
            # delete current mapping and re-push

            requests.delete(mapping_url, verify=False)
            print "failed. deleting..."
            r = requests.put(mapping_url, data=mapping_file, verify=False)
            print "re-putting map file"
            if r.status_code != requests.codes.ok:
                print(r.url, r.status_code)
                r.raise_for_status()

    print "mapped"
    # bulk import new publication documents
    bulk_import_url = endpoint + "_bulk"
    r = requests.post(bulk_import_url, data=bulk, verify=False)
    if r.status_code != requests.codes.ok:
        print(r.url, r.status_code)
        r.raise_for_status()
    print "Bulk Status: %s" % r.status_code

def generate(threads, sparql):
    pool = multiprocessing.Pool(threads)
    params = [pub for pub in get_pubs(endpoint=sparql)]
    print("params: ", params)
    return list(chain.from_iterable(pool.map(process_publication, params)))


if __name__ == "__main__":

    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--threads', default=6, help='number of threads to use (default = 6)')
    parser.add_argument('--es', default="http://localhost:9200/", help="elasticsearch service URL")
    parser.add_argument('--publish', default=False, action="store_true", help="publish to elasticsearch?")
    parser.add_argument('--rebuild', default=False, action="store_true", help="rebuild elasticsearch index?")
    parser.add_argument('--mapping', default="mappings/publication.json", help="publication elasticsearch mapping document")
    parser.add_argument('--sparql', default='http://localhost:2020/ds/sparql', help='sparql endpoint')
    parser.add_argument('out', metavar='OUT', help='elasticsearch bulk ingest file')

    args = parser.parse_args()

    # generate bulk import document for publications
    records = generate(threads=int(args.threads), sparql=args.sparql)
    #records = open(args.out, "r").read().split('\n')
    #print records
    print "generated records"
    # save generated bulk import file so it can be backed up or reviewed if there are publish errors
    with open(args.out, "w") as bulk_file:
        bulk_file.write('\n'.join(records))
    #DREwith open(args.out, "w") as bulk_file:
    #DRE    publish(bulk=bulk_str, endpoint=args.es, rebuild=args.rebuild, mapping=args.mapping)



