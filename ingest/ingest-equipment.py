__author__ = 'szednik'

from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Namespace, RDF
import json
import requests
import multiprocessing
from itertools import chain
import functools
import argparse


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


PROV = Namespace("http://www.w3.org/ns/prov#")
BIBO = Namespace("http://purl.org/ontology/bibo/")
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")
VIVO = Namespace('http://vivoweb.org/ontology/core#')
VITRO = Namespace("http://vitro.mannlib.cornell.edu/ns/vitro/0.7#")
VITRO_PUB = Namespace("http://vitro.mannlib.cornell.edu/ns/vitro/public#")
OBO = Namespace("http://purl.obolibrary.org/obo/")
DCO = Namespace("http://info.deepcarbon.net/schema#")
CUB = Namespace("https://experts.colorado.edu/individual/")
FIS_LOCAL = Namespace("https://experts.colorado.edu/ontology/vivo-fis#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
NET_ID = Namespace("http://vivo.mydomain.edu/ns#")
EQUIP = Namespace("https://experts.colorado.edu/ontology/equipment#")

get_equipment_query = load_file("queries/listEquipment.rq")
describe_equipment_query = load_file("queries/describeEquipment.rq")

# standard filters
non_empty_str = lambda s: True if s else False
has_label = lambda o: True if o.label() else False


def get_metadata(id):
    return {"index": {"_index": "fis", "_type": "equipment", "_id": id}}

def get_id(equip_id):
    return equip_id

def select(endpoint, query):
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

def get_equipment(endpoint):
    r = select(endpoint, get_equipment_query)
    return [rs["equipment"]["value"] for rs in r]

def describe_equipment(endpoint, equipment):
    q = describe_equipment_query.replace("?equipment", "<" + equipment + ">")
    return describe(endpoint, q)

def get_equipid(equipment):
    return Maybe.of(equipment).stream() \
        .flatmap(lambda p: p.objects(EQUIP.equipId)) \
        .one().value

def get_type(equipment):
    return Maybe.of(equipment).stream() \
           .flatmap(lambda p: p.objects(RDF.type)) \
           .filter(has_label) \
           .map(lambda r: {"name": str(r.label())}).one().value

def get_email(equipment):
    return Maybe.of(equipment).stream() \
        .flatmap(lambda p: p.objects(EQUIP.email)) \
        .one().value

def get_lab(equipment):
    return Maybe.of(equipment).stream() \
        .flatmap(lambda p: p.objects(EQUIP.lab)) \
        .one().value

def get_url(equipment):
    return Maybe.of(equipment).stream() \
        .flatmap(lambda p: p.objects(EQUIP.url)) \
        .one().value

def get_sector_id(equipment):
    return Maybe.of(equipment).stream() \
        .flatmap(lambda p: p.objects(FIS_LOCAL.hasSector)) \
        .filter(has_label) \
        .map(lambda r: {"uri": str(r.identifier), "name": str(r.label())}).list()

def get_research_areas(person):
    return Maybe.of(person).stream() \
        .flatmap(lambda p: p.objects(VIVO.hasResearchArea)) \
        .filter(has_label) \
        .map(lambda r: {"uri": str(r.identifier), "name": str(r.label())}).list()


def get_organization(equipment):

    organization = Maybe.of(equipment).stream() \
            .flatmap(lambda r: r.objects(EQUIP.department)) \
            .filter(lambda o: has_type(o, FOAF.Organization)) \
            .filter(has_label) \
            .map(lambda o: {"uri": str(o.identifier), "name": str(o.label())}).one().value

    return organization

def get_available_to(equipment):
   
    ''' This works a little differently than the rest of the 
        functions because it splits a single value into multiple
    '''
    vals = Maybe.of(equipment).stream() \
        .flatmap(lambda p: p.objects(EQUIP.internalUse)) \
        .one().value
    if vals:
        vals = [{"name": x.strip()} for x in vals.split(',')]
    return vals

def get_maintype(equipment):

    return Maybe.of(equipment).stream() \
        .flatmap(lambda p: p.objects(EQUIP.type)) \
        .one().value

def get_subtype(equipment):

    return Maybe.of(equipment).stream() \
        .flatmap(lambda p: p.objects(EQUIP.subtype)) \
        .one().value

def get_tests(equipment):

    return Maybe.of(equipment).stream() \
        .flatmap(lambda p: p.objects(EQUIP.testsAvailable)) \
        .map(lambda r: {"name": str(r)}).list()

    '''return Maybe.of(equipment).stream() \
        .flatmap(lambda p: p.objects(EQUIP.testsAvailable)) \
        .one().value'''

def get_analysis(equipment):

    return Maybe.of(equipment).stream() \
        .flatmap(lambda p: p.objects(EQUIP.analysis)) \
        .one().value

def create_equipment_doc(equipment, endpoint):
    graph = describe_equipment(endpoint=endpoint, equipment=equipment)

    eq = graph.resource(equipment)

    try:
        name = eq.label()
    except AttributeError:
        print("missing name:", eq)
        return {}

    eqid = get_equipid(eq)
    doc = {"uri": equipment, "name": name, "equipId": eqid}

    email = get_email(eq)
    if email:
        doc.update({"email": email})

    lab = get_lab(eq)
    if lab:
        doc.update({"lab": lab})

    url = get_url(eq)
    if url:
        doc.update({"url": url})

    sector_id = get_sector_id(eq)
    if sector_id:
        doc.update({"sector_id": sector_id})

    research_areas = get_research_areas(eq)
    if research_areas:
        doc.update({"researchArea": research_areas})

    organization = get_organization(eq)
    if organization:
        doc.update({"organization": organization})

    eqtype = get_type(eq)
    if eqtype:
        doc.update({"eqtype": eqtype})

    available_to = get_available_to(eq)
    if available_to:
        doc.update({"available_to": available_to})

    main_type = get_maintype(eq)
    if main_type:
        doc.update({"main_type": main_type})

    subtype = get_subtype(eq)
    if subtype:
        doc.update({"subtype": subtype})

    tests = get_tests(eq)
    if tests:
        doc.update({"tests": tests})

    analysis = get_analysis(eq)
    if analysis:
        doc.update({"analysis": analysis})

    return doc


def process_equipment(equipment, endpoint='http://localhost:2020/ds/sparql'):
    eq = create_equipment_doc(equipment=equipment, endpoint=endpoint)
    es_id = eq["equipId"] if "equipId" in eq and eq["equipId"] is not None else eq["uri"]
    es_id = get_id(es_id)
    return [json.dumps(get_metadata(es_id)), json.dumps(eq)]


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

    mapping_url = endpoint + "fis/equipment/_mapping"
    with open(mapping) as mapping_file:
        r = requests.put(mapping_url, data=mapping_file, verify=False)
        if r.status_code != requests.codes.ok:
            print r.status_code
            # new mapping may be incompatible with previous
            # delete current mapping and re-push

            requests.delete(mapping_url, verify=False)
            print "failed. deleting..."
            r = requests.put(mapping_url, data=mapping_file, verify=False)
            print "re-putting map file"
            if r.status_code != requests.codes.ok:
                print(r.url, r.status_code)
                r.raise_for_status()

    # bulk import new publication documents
    bulk_import_url = endpoint + "_bulk"
    r = requests.post(bulk_import_url, data=bulk, verify=False)
    if r.status_code != requests.codes.ok:
        print(r.url, r.status_code)
        r.raise_for_status()
    print "Bulk Status: %s" % r.status_code

def generate(threads, sparql):
    pool = multiprocessing.Pool(threads)
    params = [equip for equip in get_equipment(endpoint=sparql)]
    return list(chain.from_iterable(pool.map(process_equipment, params)))


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--threads', default=8, help='number of threads to use (default = 8)')
    parser.add_argument('--es', default="http://localhost:9200/", help="elasticsearch service URL")
    parser.add_argument('--publish', default=False, action="store_true", help="publish to elasticsearch?")
    parser.add_argument('--rebuild', default=False, action="store_true", help="rebuild elasticsearch index?")
    parser.add_argument('--mapping', default="mappings/equipment.json", help="publication elasticsearch mapping document")
    parser.add_argument('--sparql', default='http://localhost:2020/ds/sparql', help='sparql endpoint')
    parser.add_argument('out', metavar='OUT', help='elasticsearch bulk ingest file')

    args = parser.parse_args()

    # generate bulk import document for publications
    records = generate(threads=int(args.threads), sparql=args.sparql)

    # save generated bulk import file so it can be backed up or reviewed if there are publish errors
    with open(args.out, "w") as bulk_file:
        bulk_file.write('\n'.join(records))

    # publish the results to elasticsearch if "--publish" was specified on the command line
    if args.publish:
        bulk_str = '\n'.join(records)
        publish(bulk=bulk_str, endpoint=args.es, rebuild=args.rebuild, mapping=args.mapping)
