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
import csv
import pandas as pd

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

def get_unpaywall_for_doi(doi):
    if doi:
        query = ('http://api.unpaywall.org/v2/' + doi + '?email=elsborg@colorado.edu')
        try:
           r = requests.get(query)
           if r.status_code == 200:
             try:

                json = r.json()
#                return json['score']
                return json
             except ValueError:
                logging.exception("Could not parse Unpaywall response. ")
                return None
             except ValueError:
                logging.exception("Could not parse Unpaywall response. ")
                return None
           elif r.status_code == 420:
              logging.info("Unpaywall Rate limit in effect!!!!")
              time.sleep(5)
           elif r.status_code == 403:
              logging.warn("Unpaywall says you aren't authorized for this call.")
              return None
           else:
              logging.debug("No Unpaywall record or API error. ")
              return None
        except:
           logging.exception("Unpaywall connection failure")
    else:
        return None


def get_altmetric_for_doi(ALTMETRIC_API_KEY, doi):
    if doi:
        #DRE for news: query = ('http://api.altmetric.com/v1/fetch/doi/' + doi + '?key=' + ALTMETRIC_API_KEY + '&include_sources=news')
        query = ('http://api.altmetric.com/v1/fetch/doi/' + doi + '?key=' + ALTMETRIC_API_KEY)

        try:
           r = requests.get(query)
           if r.status_code == 200:
             try:

                json = r.json()
#                return json['score']
                return json
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

def get_email(person):
    return Maybe.of(person).stream() \
        .flatmap(lambda p: p.objects(OBO.ARG_2000028)) \
        .flatmap(lambda v: v.objects(VCARD.hasEmail)) \
        .flatmap(lambda e: e.objects(VCARD.email)) \
        .one().value


def get_orcid(person):
    return Maybe.of(person).stream() \
        .flatmap(lambda p: p.objects(VIVO.orcidId)) \
        .map(lambda o: o.identifier) \
        .map(lambda o: o[o.rfind('/') + 1:]).one().value

def get_fisid(person):
    return Maybe.of(person).stream() \
        .flatmap(lambda p: p.objects(FIS_LOCAL.fisId)) \
        .one().value


def get_research_areas(person):
    return Maybe.of(person).stream() \
        .flatmap(lambda p: p.objects(VIVO.hasResearchArea)) \
        .filter(has_label) \
        .map(lambda r: {"uri": r.identifier, "name": r.label()}).list()


def get_organizations(person):

    organizations = []
    affiliations = []

    positions = Maybe.of(person).stream() \
        .flatmap(lambda per: per.objects(VIVO.relatedBy)) \
        .filter(lambda related: has_type(related, VIVO.Position)).list()

    for position in positions:
        organization = Maybe.of(position).stream() \
            .flatmap(lambda r: r.subjects(VIVO.relatedBy)) \
            .filter(lambda o: has_type(o, FOAF.Organization)) \
            .filter(has_label) \
            .map(lambda o: {"uri": o.identifier, "name": o.label(), "id": o.identifier.split('_')[1]}).one().value

        if organization:
            organizations.append(organization)
            affiliations.append({"position": str(position.label()), "org": organization})
    return organizations, affiliations


def get_metadata(id):
    return {"index": {"_index": args.index, "_type": "publication", "_id": id}}

def has_type(resource, type):
    for rtype in resource.objects(predicate=RDF.type):
        if rtype.identifier == type:
            return True
    return False

def load_file(filepath):
    with open(filepath) as _file:
        return _file.read().replace('\n', " ")

def describe(sparqlendpoint, query):
    logging.info('sparqlendpoint: %s',  sparqlendpoint)
    sparql = SPARQLWrapper(sparqlendpoint)
    sparql.setQuery(query)
    sparql.setMethod("POST")
    sparql.addParameter("email", EMAIL)
    sparql.addParameter("password", PASSWORD)
    logging.debug('logging - describe query: %s', query)
    try:
        results = sparql.query().convert()
        return results
    except Exception as e:
        try:
            print("Error trying sparql.query in describe function.")
            print("Will try again after 1st exception: %s\n" % e)
            time.sleep(1)
            results = sparql.query().convert()
            print("results: ", results)
            return results
        except Exception as f:
            print("Error trying sparql.query in describe function.")
            print ("Couldn't do it a second time: %s\n" % f)
            sys.exit(1)
        except RuntimeWarning:
            sys.exit(1)
    except RuntimeWarning:
        sys.exit(1)

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

    x=json.dumps(doc)

    doi = list(pub.objects(predicate=BIBO.doi))
    doi = doi[0].toPython() if doi else None
    ams = 0
    if doi:
        doc.update({"doi": doi})
        j = get_altmetric_for_doi(ALTMETRIC_API_KEY, doi)
        try:
           j
        except NameError:
           logging.info('No altmetric results for doi %s', pubid)
        else:
           logging.debug('altmetric returned %s', doi)
           if isinstance(j, dict):
             if 'score' in j:
               ams = j['score']
               doc.update({"amscore": ams})
               if 'posts' in j:
                  if 'news' in j['posts']:
                     doc.update({"altmetricnews": j['posts']['news']})

        j = get_unpaywall_for_doi(doi)
        try:
           j
        except NameError:
           logging.info('No unpaywall results for doi %s', pubid)
        else:
           logging.debug('unpaywall returned %s', doi)
           if isinstance(j, dict):
             doc.update({"unpaywall": j})


    cuscholar = list(pub.objects(predicate=PUBS.cuscholar))
    cuscholar = cuscholar[0].toPython() if cuscholar else None
    if cuscholar:
        logging.debug('found cuscholar: %s', cuscholar)
        doc.update({"cuscholar": cuscholar})
        doc.update({"cuscholarexists": "CU Scholar"})

    abstract = list(pub.objects(predicate=BIBO.abstract))
    #abstract = abstract[0].encode('utf-8') if abstract else None
    abstract = abstract[0] if abstract else None
    if abstract:
        doc.update({"abstract": abstract})
        x=json.dumps(doc)

    pageEnd = list(pub.objects(predicate=BIBO.pageEnd))
    #pageEnd = pageEnd[0].encode('utf-8') if pageEnd else None
    pageEnd = pageEnd[0] if pageEnd else None
    if pageEnd:
        doc.update({"pageEnd": pageEnd})
        x=json.dumps(doc)

    pageStart = list(pub.objects(predicate=BIBO.pageStart))
    #pageStart = pageStart[0].encode('utf-8') if pageStart else None
    pageStart = pageStart[0] if pageStart else None
    if pageStart:
        doc.update({"pageStart": pageStart})
        x=json.dumps(doc)

    issue = list(pub.objects(predicate=BIBO.issue))
    #issue = issue[0].encode('utf-8') if issue else None
    issue = issue[0] if issue else None
    if issue:
        doc.update({"issue": issue})
        x=json.dumps(doc)

    numPages = list(pub.objects(predicate=BIBO.numPages))
    #numPages = numPages[0].encode('utf-8') if numPages else None
    numPages = numPages[0] if numPages else None
    if numPages:
        doc.update({"numPages": numPages})
        x=json.dumps(doc)

    volume = list(pub.objects(predicate=BIBO.volume))
    #volume = volume[0].encode('utf-8') if volume else None
    volume = volume[0] if volume else None
    if volume:
        doc.update({"volume": volume})
        x=json.dumps(doc)


    citedAuthors = list(pub.objects(predicate=PUBS.citedAuthors))
    #citedAuthors = citedAuthors[0].encode('utf-8') if citedAuthors else None
    citedAuthors = citedAuthors[0] if citedAuthors else None
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
        #doc.update({"publishedIn": {"uri": venue.identifier, "name": venue.label().encode('utf8')}})
        doc.update({"publishedIn": {"uri": venue.identifier, "name": venue.label()}})
    elif venue:
        logging.info('venue missing label: %s', venue.identifier)

    authors = []
    for s, p, o in pubgraph.triples((None, VIVO.relates, None)):
       for a, b, c in g1.triples((o, RDF.type, FOAF.Person)):
          gx = Graph()
          gx += g1.triples((a, None, None))
          name = (gx.label(a))
          obj = {"uri": a, "name": name}
          logging.debug('Getting person for: %s', name)
          per = g1.resource(a)
          logging.debug('Person is: %s', per)

# Improvements - reuse the person json object, should only have to look up each person once. 
#                reuse/query this object from the people index if possible.
          orcid = get_orcid(per)
          if orcid:
              obj.update({"orcid": orcid})

          email = get_email(per)
          if email:
             obj.update({"email": email})

          logging.debug('check fisid: %s', per)
          fis = get_fisid(per)
          obj.update({"fisId": fis})

          organizations, affiliations = get_organizations(per)
          if organizations:
            obj.update({"organization": organizations})
          if affiliations:
            logging.debug('From orgs Adding affiliations for: %s', per)
            obj.update({"affiliations": affiliations})

          research_areas = get_research_areas(per)
          if research_areas:
            obj.update({"researchArea": research_areas})

          authors.append(obj)

    doc.update({"authors": authors})

# Add external orgs for publication from CUBE csv file

    logging.info('Processing CSV for pubId: %s', pubId)
    pubdf=csvdf.loc[csvdf['ID'] == int(pubId)]
    if not pubdf.empty: 
       logging.debug('CSV found for pubId: %s', str(pubId))
       extorgs=[]
       puborgjson = json.loads(pubdf[['Organisation','Suborganisation', 'ISO_Country_Code','GRID_ID','GRID_Institution_Name','GRID_Institution_Link']].to_json(orient="index"))
       for key in puborgjson:
          extorgs.append(puborgjson[key])
       if extorgs:
          doc.update({"extOrgs": extorgs})

# End external orgs

# Add cube funding info for publications

    logging.info('Processing grants CSV for pubId: %s', pubId)
    pubgrantdf=grantcsvdf.loc[grantcsvdf['PUBID'] == int(pubId)]
    if not pubgrantdf.empty: 
       logging.debug('Grant found for pubId: %s', str(pubId))
       pubgrants=[]
       pubgrantjson = json.loads(pubgrantdf[['FUNDER_NAME','GRANT_ID']].to_json(orient="index"))
       for key in pubgrantjson:
          pubgrants.append(pubgrantjson[key])
       if pubgrants:
          doc.update({"pubGrants": pubgrants})

# End funding for publications

    logging.debug('Publication doc: %s', doc)
    return doc

def process_publication(publication):
    pid = str(os.getpid())
    logging.info('%s Processing Publication: %s', pid, publication)
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
    logging.debug('%s Pub Processed. Pub is: %s', pid, pub)
    pubdoc = json.dumps(pub)
    return [json.dumps(pub)]

def generate(threads):
    pool = multiprocessing.Pool(threads)
    params = [pub for pub in g1.subjects(RDF.type, BIBO.Document)]
    logging.info('params: %s', params)
    plist = list(chain.from_iterable(pool.map(process_publication, params)))
    return plist

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--threads', default=8, help='number of threads to use (default = 8)')
    parser.add_argument('--sparqlendpoint', default='http://localtomcathost:8780/vivo/api/sparqlQuery', help='local tomcat host and port for VIVO sparql query API endpoint')
    parser.add_argument('--spooldir', default='./spool', help='where to write files')
    parser.add_argument('--index', default='fis-pubs-setup', help='name of index, needs to correlate with javascript library')
    parser.add_argument('--chunk', default=4000, help='Number of records in each file, used for AWS uploads')
    parser.add_argument('out', metavar='OUT', help='elasticsearch bulk ingest file')
    args = parser.parse_args()
    sparqlendpoint=args.sparqlendpoint

    logfile=args.spooldir + '/ingest-pubs.log'
    logging.basicConfig(filename=logfile,level=logging.DEBUG)

    get_orgs_query = load_file("queries/listOrgs.rq")
    get_subjects_query = load_file("queries/listSubjects.rq")
    get_author_query = load_file("queries/listAuthors.rq")
    get_pub_query = load_file("queries/listPubs.rq")

    logging.info('Sparql Query for authors')
    g1 = g1 + describe(sparqlendpoint,get_author_query)
    logging.info('Sparql Query for orgs')
    g1 += describe(sparqlendpoint,get_orgs_query)
    logging.info('Sparql Query for subjects')
    g1 = g1 + describe(sparqlendpoint,get_subjects_query)
    logging.info('Sparql Query for publications')
    g1 = g1 + describe(sparqlendpoint,get_pub_query)

# Read csv file of external orgs for pubs
    logging.info('Reading external orgs csv')
    csvdf=pd.read_csv('external-publication-orgs.csv')

# Read csv file of external orgs for pubs
    logging.info('Reading grantinfo csv')
    grantcsvdf=pd.read_csv('cube-pub-funding.csv')

# section to create chunked files
    chunk = args.chunk
    numchunks = 0
    records = generate(threads=int(args.threads))
    rlen=len(records)
    pubrecords = []
    pubdoc={}
    for i in range(rlen):
        pubdata=json.loads(records[i])
        pubmetadata=get_metadata(pubdata["pubId"])
        #pubdoc.update({"pubmetadata:": pubmetadata})
        #pubdoc.update({"pubdata:": pubdata})
        pubrecords.append(json.dumps(pubmetadata))
        pubrecords.append(json.dumps(pubdata))
        numchunks += 1
        dochunk = numchunks % chunk
        if dochunk == 0:
            print("chunks: ", numchunks, " i: ", i)
            outfile=args.spooldir + '/' + args.out + str(numchunks)
            bulk_file=open(outfile, "w")
            bulk_file.write('\n'.join(pubrecords))
            pubrecords = []
            bulk_file.write('\n')
            bulk_file.close()
    print ("writing final file")
    print("chunks: ", numchunks, " i: ", i)
    outfile=args.spooldir + '/' + args.out + str(numchunks)
    bulk_file=open(outfile, "w")
    bulk_file.write('\n'.join(pubrecords))
    bulk_file.write('\n')
    bulk_file.close()
    print ("Done writing chunk files")

    print ("Writing full file")
    fulloutfile=args.spooldir + '/' + 'full-' + args.out
    with open(fulloutfile, "w") as bulk_file:
        bulk_file.write('\n'.join(records))
