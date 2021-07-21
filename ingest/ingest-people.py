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
import codecs
import time

# import EMAIL and PASSWORD variables for VIVO sparqlquery API, this is a link to a file for github purposes
# Also eventually can put more config info in here
from vivoapipw import *


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


get_people_query = load_file("queries/listPeople.rq")
describe_person_query = load_file("queries/describePerson.rq")
describe_award_query = load_file("queries/describeAward.rq")
describe_course_query = load_file("queries/describeCourses.rq")

# standard filters
non_empty_str = lambda s: True if s else False
has_label = lambda o: True if o.label() else False


def get_metadata(id):
    return {"index": {"_index": args.index, "_type": "person", "_id": id}}


def get_id(fis_id):
    #fis_id = fis_id[fis_id.rfind('/') + 1:]
    return fis_id

def select(endpoint, query):
    print("endpoint: ", endpoint)
#    print("EMAIL: ", EMAIL)
#    print("PASSWORD: ", PASSWORD)

    endpoint = endpoint
    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(query)
    sparql.setMethod("POST")
    sparql.addParameter("email", EMAIL)
    sparql.addParameter("password", PASSWORD)
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
        print("results: ", results)
        return results["results"]["bindings"]
    except Exception, e:
        try:
            print("Error trying sparql.query in select function. Will try again in 2 seconds")
            #print("Will try again after 1st exception: %s\n" % e)
            time.sleep(2)
            results = sparql.query().convert()
            print("results: ", results)
            return results["results"]["bindings"]
        except Exception, x:
            print("2nd try Error trying sparql.query in select function.")
            print("Second try failed: %s\n" % x)
            sys.exit(1)
        except RuntimeWarning:
            sys.exit(1)
    except RuntimeWarning:
         sys.exit(1)


def describe(endpoint, query):
    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(query)
    sparql.setMethod("POST")
    sparql.addParameter("email", EMAIL)
    sparql.addParameter("password", PASSWORD)
    try:
    #    print ("sparql query: ", sparql)
        results = sparql.query().convert()
    #    print ("Describe passed: ", query)
        return results
    #except RuntimeWarning:
    except Exception, e:
        try:
            print("Error trying sparql.query in describe function.")
            print("Will try again after 1st exception: %s\n" % e)
            time.sleep(2)
            results = sparql.query().convert()
            print("results: ", results)
            return results
        except Exception, f:
            print("Error trying sparql.query in describe function.")
            print "Couldn't do it a second time: %s\n" % f
            sys.exit(1)
            pass
        except RuntimeWarning:
            sys.exit(1)
            pass
    except RuntimeWarning:
        sys.exit(1)

def has_type(resource, type):
    try:
      for rtype in resource.objects(RDF.type):
          if str(rtype.identifier) == str(type):
              return True
      return False
    except:
      print ("ERROR has_type on type: ", type)
      return False


def get_people(endpoint):
    r = select(endpoint, get_people_query)
    return [rs["person"]["value"].encode('utf-8') for rs in r]


def describe_person(endpoint, person):
    q = describe_person_query.replace("?person", "<" + person + ">")
    return describe(endpoint, q)

def describe_award(endpoint, person):
    q = describe_award_query.replace("?person", "<" + person + ">")
    return describe(endpoint, q)

def describe_courses(endpoint, person):
    q = describe_course_query.replace("?person", "<" + person + ">")
    return describe(endpoint, q)


def get_fisid(person):
    return Maybe.of(person).stream() \
        .flatmap(lambda p: p.objects(FIS_LOCAL.fisId)) \
        .one().value

def get_researchOverview(person):
    return Maybe.of(person).stream() \
        .flatmap(lambda p: p.objects(VIVO.researchOverview)) \
        .one().value


def get_orcid(person):
    return Maybe.of(person).stream() \
        .flatmap(lambda p: p.objects(VIVO.orcidId)) \
        .map(lambda o: o.identifier) \
        .map(lambda o: o[o.rfind('/') + 1:]).one().value


def get_most_specific_type(person):
    return Maybe.of(person).stream() \
        .flatmap(lambda p: p.objects(VITRO.mostSpecificType)) \
        .map(lambda t: t.label()) \
        .filter(non_empty_str) \
        .one().value


def get_network_id(person):
    return Maybe.of(person).stream() \
        .flatmap(lambda p: p.objects(NET_ID.networkId)) \
        .filter(non_empty_str) \
        .one().value


def get_given_name(person):
    return Maybe.of(person).stream() \
        .flatmap(lambda p: p.objects(OBO.ARG_2000028)) \
        .flatmap(lambda v: v.objects(VCARD.hasName)) \
        .flatmap(lambda n: n.objects(VCARD.givenName)) \
        .filter(non_empty_str) \
        .one().value


def get_family_name(person):
    return Maybe.of(person).stream() \
        .flatmap(lambda p: p.objects(OBO.ARG_2000028)) \
        .flatmap(lambda v: v.objects(VCARD.hasName)) \
        .flatmap(lambda n: n.objects(VCARD.familyName)) \
        .filter(non_empty_str) \
        .one().value


def get_email(person):
    return Maybe.of(person).stream() \
        .flatmap(lambda p: p.objects(OBO.ARG_2000028)) \
        .flatmap(lambda v: v.objects(VCARD.hasEmail)) \
        .flatmap(lambda e: e.objects(VCARD.email)) \
        .filter(non_empty_str) \
        .one().value

def get_website(person):
    weblinks = []

    websites = Maybe.of(person).stream() \
        .flatmap(lambda p: p.objects(OBO.ARG_2000028)) \
        .flatmap(lambda v: v.objects(VCARD.hasURL)) \
        .filter(lambda o: has_type(o,VCARD.URL)).list()

    for website in websites:
        print("website", website )

        webname = Maybe.of(website).stream() \
           .filter(has_label) \
           .map(lambda t: str(t.label())) \
           .filter(non_empty_str) \
           .one().value[0]
        print("webname", webname)

        weburl = Maybe.of(website).stream() \
           .flatmap(lambda e: e.objects(VCARD.url)) \
           .map(lambda r: r.value) \
           .one().value
        print("weburl", weburl)

        if weburl:
           weblinks.append({"name": webname, "uri": weburl})

    return weblinks


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
            .flatmap(lambda r: r.objects(VIVO.relates)) \
            .filter(lambda o: has_type(o, FOAF.Organization)) \
            .filter(has_label) \
            .map(lambda o: {"uri": str(o.identifier), "name": o.label()}).one().value

        if organization:
            organizations.append(organization)
    return organizations
    '''return Maybe.of(person).stream() \
        .flatmap(lambda p: p.objects(DCO.inOrganization)) \
        .filter(has_label) \
        .map(lambda r: {"uri": str(r.identifier), "name": str(r.label())}).list()
    '''


def get_home_country(person):
    return Maybe.of(person).stream() \
        .flatmap(lambda p: p.objects(VIVO.geographicFocus)) \
        .filter(has_label) \
        .map(lambda r: {"uri": BASE_URL + '?uri=' + urllib.quote_plus(str(r.identifier)), "name": str(r.label().encode('utf-8'))}).list()

def get_affiliations(person):
    affiliations = []

    positions = Maybe.of(person).stream() \
        .flatmap(lambda per: per.objects(VIVO.relatedBy)) \
        .filter(lambda related: has_type(related, VIVO.Position)).list()

    for position in positions:
        organization = Maybe.of(position).stream() \
            .flatmap(lambda r: r.objects(VIVO.relates)) \
            .filter(lambda o: has_type(o, FOAF.Organization)) \
            .filter(has_label) \
            .map(lambda o: {"uri": str(o.identifier), "name": o.label()}) \
            .one().value

        if organization:
            affiliations.append({"position": str(position.label()), "org": organization})

    return affiliations


def get_courses(coursesgraph):
    courses = []

    print("In get_courses")

    instructors = Maybe.of(coursesgraph).stream() \
        .flatmap(lambda per: per.objects(OBO.RO_0000053)).list() 

#    print("got instructors: ", instructors)

    for instructor in instructors:
#        print("in instructor loop")
#        print("instructor: ", instructor)

        course = Maybe.of(instructor).stream() \
            .flatmap(lambda o: o.objects(OBO.BFO_0000054)) \
            .filter(has_label) \
            .map(lambda o: {"uri": str(o.identifier), "name": o.label()[0:o.label().find(" -")]}) \
            .one().value
        if course:
#            print("course exists: ", course)
            courses.append(course)

    return courses


def get_awards(awardgraph):
    awards = []

#    print("In get_awards")

    receipts = Maybe.of(awardgraph).stream() \
        .flatmap(lambda per: per.objects(VIVO.relatedBy)) \
        .filter(lambda related: has_type(related, VIVO.AwardReceipt)).list()

#    print("got award receipts")

    for receipt in receipts:
#        print("in award receipt loop")
#        print(receipt)

        award = Maybe.of(receipt).stream() \
            .flatmap(lambda r: r.objects(VIVO.relates)) \
            .filter(lambda o: has_type(o, VIVO.Award)) \
            .filter(has_label) \
            .map(lambda o: {"uri": o.identifier, "name": o.label()}) \
            .one().value

        awarddate = Maybe.of(receipt).stream() \
            .flatmap(lambda r: r.objects(VIVO.dateTimeValue)) \
            .flatmap(lambda d: d.objects(VIVO.dateTime)) \
            .one().value

        awardyear = str(awarddate)[:4]

#        print("Awarddate: ", awardyear)

        awardorg = Maybe.of(receipt).stream() \
            .flatmap(lambda r: r.objects(VIVO.relates)) \
            .filter(lambda o: has_type(o, VIVO.Award)) \
            .flatmap(lambda a: a.objects(VIVO.assignedBy)) \
            .map(lambda a: {"uri": str(a.identifier), "name": a.label()}) \
            .one().value
#        print("Awardorg: ", awardorg)


        if award:
#            print("award exists: ", award)
            awards.append({"award": award, "awardorg": awardorg, "awardyear": awardyear})
#            print("awards: ", awards)

    return awards


def get_thumbnail(person):

    return Maybe.of(person).stream() \
        .flatmap(lambda p: p.objects(VITRO_PUB.mainImage)) \
        .flatmap(lambda i: i.objects(VITRO_PUB.thumbnailImage)) \
        .flatmap(lambda t: t.objects(VITRO_PUB.downloadLocation)) \
        .map(lambda t: t.identifier) \
        .one().value


def create_person_doc(person, endpoint):
    logging.info('create_person_doc: %s', person)
    logging.debug('about to describe person: %s', person)
    graph = describe_person(endpoint=endpoint, person=person)
#    print("graph:", graph)
    sys.stdout.flush()
    logging.debug('about to create graph resource for : %s', person)
    try:
        per = graph.resource(person)
    except:
        print("Can't create graph for:", person)
        logging.info('failed to create graph for : %s', person)
        logging.info('graph is : %s', graph)
        return {}

    logging.debug('about to describe award: %s', person)
    grapha = describe_award(endpoint=endpoint, person=person)
#    print("grapha:", grapha)
    sys.stdout.flush()
    logging.debug('about to create award graph resource for : %s', person)
    try:
        award = grapha.resource(person)
    except:
        print("Can't create award graph for:", person)
        logging.info('failed to create award graph for : %s', person)
        logging.info('award graph is : %s', grapha)
        return {}

    logging.debug('about to describe courses: %s', person)
    graphc = describe_courses(endpoint=endpoint, person=person)
#    print("graphc:", graphc)
    sys.stdout.flush()
    logging.debug('about to create courses graph resource for : %s', person)
    try:
        coursesgraph = graphc.resource(person)
    except:
        print("Can't create courses graph for:", person)
        logging.info('failed to create courses graph for : %s', person)
        logging.info('courses graph is : %s', graphc)
        return {}


    logging.debug('check label: %s', person)
    try:
#        print("person has label:", per.label())
        name = per.label()
    except AttributeError:
        print("missing name:", person)
        return {}

    logging.debug('check fisid: %s', person)
    fis = get_fisid(per)
    doc = {"uri": person.replace(PRODURL, TARGETURL), "name": name, "fisId": fis}

    logging.debug('check orcid: %s', person)
    orcid = get_orcid(per)
    if orcid:
        doc.update({"orcid": orcid})

    researchOverview = get_researchOverview(per)
    if researchOverview:
        doc.update({"researchOverview": researchOverview})

    most_specific_type = get_most_specific_type(per)
    if most_specific_type:
        doc.update({"mostSpecificType": most_specific_type})

    given_name = get_given_name(per)
    if given_name:
        doc.update({"givenName": given_name})

    family_name = get_family_name(per)
    if family_name:
        doc.update({"familyName": family_name})

    email = get_email(per)
    if email:
        doc.update({"email": email})

    website = get_website(per)
    if website:
        doc.update({"website": website})

    research_areas = get_research_areas(per)
    if research_areas:
        doc.update({"researchArea": research_areas})

    home_country = get_home_country(per)
    if home_country:
        doc.update({"homeCountry": home_country})

    organizations = get_organizations(per)
    if organizations:
        doc.update({"organization": organizations})

    thumbnail = get_thumbnail(per)
    if thumbnail:
        thumbnail = thumbnail.replace("http://", "https://")
        thumbnail = thumbnail.replace(PRODURL, TARGETURL)
        doc.update({"thumbnail": thumbnail})

    affiliations = get_affiliations(per)
    if affiliations:
        doc.update({"affiliations": affiliations})

    awards = get_awards(award)
    if awards:
        doc.update({"awards": awards})
        doc.update({"awardreceived": "yes"})
 
#    print("coursesgraph: ", coursesgraph)
    courses = get_courses(coursesgraph)
    if courses:
        doc.update({"courses": courses})
        doc.update({"taughtcourse": "yes"})

    logging.debug('Person doc: %s', doc)
    #pdb.set_trace()
    return doc


def process_person(person):
    logging.info('Processing Person: %s', person)
    if person.find("fisid_") == -1:
       logging.info('INVALID PERSON: %s', person) 
       return []
    per = create_person_doc(person=person, endpoint=sparqlendpoint)
    es_id = per["fisId"] if "fisId" in per and per["fisId"] is not None else per["uri"]
    es_id = get_id(es_id)
    return [json.dumps(get_metadata(es_id)), json.dumps(per)]


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

    mapping_url = endpoint + "fis/person/_mapping"
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
    params = [person for person in get_people(endpoint=sparql)]
    return list(chain.from_iterable(pool.map(process_person, params)))


if __name__ == "__main__":

    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument('--threads', default=1, help='number of threads to use (default = 8)')
    parser.add_argument('--es', default="http://localhost:9200/", help="elasticsearch service URL")
    parser.add_argument('--publish', default=False, action="store_true", help="publish to elasticsearch?")
    parser.add_argument('--index', default='fis', help='name of index, needs to correlate with javascript library')
    parser.add_argument('--rebuild', default=False, action="store_true", help="rebuild elasticsearch index?")
    parser.add_argument('--mapping', default="mappings/person.json", help="publication elasticsearch mapping document")
    parser.add_argument('--sparql', default='http://localtomcathost:8780/vivo/api/sparqlQuery', help='local tomcat host and port for VIVO sparql query API endpoint')
    parser.add_argument('out', metavar='OUT', help='elasticsearch bulk ingest file')

    args = parser.parse_args()
    sparqlendpoint=args.sparql

    # generate bulk import document for publications
    records = generate(threads=int(args.threads), sparql=args.sparql)
    #records = open(args.out, "r").read().split('\n')
    #print records
    print "generated records"
    # save generated bulk import file so it can be backed up or reviewed if there are publish errors
    with open(args.out, "w") as bulk_file:
        bulk_file.write('\n'.join(records))
        bulk_file.write('\n')

    # publish the results to elasticsearch if "--publish" was specified on the command line
    if args.publish:
        bulk_str = '\n'.join(records)
        publish(bulk=bulk_str, endpoint=args.es, rebuild=args.rebuild, mapping=args.mapping)
