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

PROV = Namespace("http://www.w3.org/ns/prov#")
BIBO = Namespace("http://purl.org/ontology/bibo/")
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")
VIVO = Namespace('http://vivoweb.org/ontology/core#')
VITRO = Namespace("http://vitro.mannlib.cornell.edu/ns/vitro/0.7#")
VITRO_PUB = Namespace("http://vitro.mannlib.cornell.edu/ns/vitro/public#")
OBO = Namespace("http://purl.obolibrary.org/obo/")
DCO = Namespace("http://info.deepcarbon.net/schema#")
CUB = Namespace(BASE_URL + "/")
FIS_LOCAL = Namespace("https://experts.colorado.edu/ontology/vivo-fis#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
NET_ID = Namespace("http://vivo.mydomain.edu/ns#")


get_pubs_query = load_file("queries/listPublications.rq")
describe_publication_query = load_file("queries/describePublication.rq")

# standard filters
non_empty_str = lambda s: True if s else False
has_label = lambda o: True if o.label() else False


def get_metadata(id):
    return {"index": {"_index": "fis", "_type": "publication", "_id": id}}


def get_pubid(pub_id):
    x= Maybe.of(pub_id).stream() \
        .flatmap(lambda p: p.objects(NET_ID.networkId)) \
        .filter(non_empty_str) \
        .one().value
    print("x:",x )

#    pubid = pub_id[pub_id.rfind('/pubid_') + 1:]
#    print("pubid:", pubid)
#    return pubid


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
    try:
        return sparql.query().convert()
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
    '''return Maybe.of(publication).stream() \
        .flatmap(lambda p: p.objects(DCO.inOrganization)) \
        .filter(has_label) \
        .map(lambda r: {"uri": str(r.identifier), "name": str(r.label())}).list()
    '''


def create_publication_doc(publication, endpoint):
    graph = describe_publication(endpoint=endpoint, publication=publication)

    pub = graph.resource(publication)
    print ("pub:", pub)

    try:
        name = pub.label()
    except AttributeError:
        print("missing name:", publication)
        return {}

    pubId = get_pubid(pub)
    doc = {"uri": publication, "name": name, "pubId": pubId}

    most_specific_type = get_most_specific_type(pub)
    if most_specific_type:
        doc.update({"mostSpecificType": most_specific_type})


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
    return list(chain.from_iterable(pool.map(process_publication, params)))


if __name__ == "__main__":

    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument('--threads', default=8, help='number of threads to use (default = 8)')
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
        publish(bulk=bulk_str, endpoint=args.es, rebuild=args.rebuild, mapping=args.mapping)
