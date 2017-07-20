# dco-elasticsearch
DCO Faceted Search using ElasticSearch

## CUB specific notes
  only people and equipment are used and imported into elastic
  the ansible scripts in https://github.com/cu-boulder/fis_vivo_deployment are responsible for copying the correct html files into vivo
  vivo@prometheus crontab has the following 2 entries to ingest into elastic:
  00 03 * * * python /usr/local/vivo/experts-cub/vivo-cub/plugins/facetedsearch/ingest/ingest-people.py
15 03 * * * python /usr/local/vivo/experts-cub/vivo-cub/plugins/facetedsearch/ingest/ingest-equipment.py

## Overview

The DCO faceted search browsers are powered by [FacetView2](https://github.com/tetherless-world/facetview2) - a pure javascript frontend for ElasticSearch search indices that let you easily embed a faceted browse front end into any web page.

To configure a working faceted browser you need:
1. A running instance of ElasticSearch with a populated index
2. A webpage with references to facetview2 scripts and an embedded configuration

That's it!

You can find out more about ElasticSearch at [https://www.elastic.co/products/elasticsearch](https://www.elastic.co/products/elasticsearch)

### ElasticSearch Installation

Instructions for setting up a local instance of ElasticSearch are available at [https://www.elastic.co/guide/en/elasticsearch/reference/current/_installation.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/_installation.html)

Additionally, if you are on OSX you can install elasticsearch using homebrew with this command:

```
brew install elasticsearch
```

Finally, you can use the official docker image to start a containerized instance of ElasticSearch.  Instructions are available at [https://hub.docker.com/_/elasticsearch/](https://hub.docker.com/_/elasticsearch/).

### The Ingest Process

Currently we use python scripts to build and import batch documents into our ElasticSearch (ES) service.  The scripts can be scheduled or run manually and currently generate a batch of all documents for a given search type (e.g. publication, person, dataset, etc).  Our scripts do not currently support generating batches of only recently changed documents.  The ingest scripts query a DCO SPARQL endpoint and generate a ES batch file containing JSON documents for all entities to be indexed.

Ingest scripts are located in the ingest directory and follow the convention ingest-x.py where x the plural form of the 'type' of search document generated.

Currently a SELECT query is run to get a list of all URIs to build search documents for and a DESCRIBE query is run for each URI.  This means that for 1500 people, 1501 queries will be executed against the SPARQL endpoint.  This can cause performance problems with endpoints so please test against non-PRODUCTION endpoints and consider adding a LIMIT to the query used to generate the list of URIs to construct search documents for.

The ingest scripts will perform the import when the --publish command line parameter is specified.  You can change the elasticsearch URL the script imports to with the --es command line parameter.

!IMPORTANT! - if you are writing a new ingest script make sure the correct values for the ``_index`` and ``_type`` variables are specified at the top of the script.

To see the full list of commandline options available with the ingest script use -h.

Our current batch scripts take between 3-5 minutes each to run, generate 2-4MB batch files, and import into ES usually takes a couple seconds.

### Importing data into ElasticSearch

ElasticSearch (ES) is a search server based on Lucene. It provides a distributed, multitenant-capable full-text search engine with a RESTful web interface and schema-free JSON documents.  

ES is capable of indexing nested JSON documents.  This is a very useful feature as it makes it easy to build a JSON document containing nested objects that can be used to for search retrieval and faceting.

For example, the document:
```json
{
  "name": "John Doe",
  "network_id": "jdoe",
  "email": "jdoe@example.com",
  "interests": ["fishing","kayaking","golf"],
  "work": { "name": "Joe's Java", "position": "barista" }
}
```
would be returned on free-text queries for "barista" and would be associated with the value "barista" in a facet field "work.position".

Detailed documentation on all things ES is available at [https://www.elastic.co/guide/en/elasticsearch/guide/master/index.html](https://www.elastic.co/guide/en/elasticsearch/guide/master/index.html)

#### Bulk document import

ES supports bulk import of search documents via POST requests to /_bulk API endpoint.  The bulk file format is one search document per line preceded by a JSON document specifying the index, type, and id for the search document to be indexed.

```json
{ "index" : { "_index" : "test", "_type" : "type1", "_id" : "1" } }
{ "field1" : "foo" }
{ "index" : { "_index" : "test", "_type" : "type1", "_id" : "2" } }
{ "field1" : "bar" }
{ "index" : { "_index" : "test", "_type" : "type1", "_id" : "3" } }
{ "field1" : "baz" }
```

Probably the easiest way to look at a real-world example of a bulk import file would be to run one of the ingest scripts (don't specify --publish unless you want the index to be updated!) and then view the resulting file.  The ingest scripts are coded to always save the generated bulk import file to disk (unless an unrecoverable exception occurs).

Documentation on bulk import of ES documents is available at [https://www.elastic.co/guide/en/elasticsearch/reference/current/_batch_processing.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/_batch_processing.html).

#### Custom mapping import

ES will auto-generate a schema for an imported document if no mappings currently exist.  If a mapping already exists it will attempt to update the mapping with definitions for any fields from the imported document that did not exist in the current mapping.  If there is a conflict with an imported document and the current mapping the service will return an error message.

We have found it useful to customize mappings for values used in facets.  See the mapping JSON documents in ingest/mappings for examples.

Documentation on ES schemas and how a mapping can be customized are available at [https://www.elastic.co/blog/found-elasticsearch-mapping-introduction](https://www.elastic.co/blog/found-elasticsearch-mapping-introduction)

The ingest scripts will push a customized mapping during the publish phase if --mapping is specified with a path to the mapping file.

### Setting up the faceted browser

Embedding a faceted browser in a webpage is very simple.

Add the following code to your web page (paths will be different for some deployment environments):
```html
    <script type="text/javascript" src="facetview2/vendor/jquery/1.7.1/jquery-1.7.1.min.js"></script>
    <link rel="stylesheet" href="facetview2/vendor/bootstrap/css/bootstrap.min.css">
    <script type="text/javascript" src="facetview2/vendor/bootstrap/js/bootstrap.min.js"></script>
    <link rel="stylesheet" href="facetview2/vendor/jquery-ui-1.8.18.custom/jquery-ui-1.8.18.custom.css">
    <script type="text/javascript" src="facetview2/vendor/jquery-ui-1.8.18.custom/jquery-ui-1.8.18.custom.min.js"></script>
    <script type="text/javascript" src="facetview2/es.js"></script>
    <script type="text/javascript" src="facetview2/bootstrap2.facetview.theme.js"></script>
    <script type="text/javascript" src="facetview2/jquery.facetview2.js"></script>
    <link rel="stylesheet" href="facetview2/css/facetview.css">
    <link rel="stylesheet" href="browsers.css">
```

Then add a script somewhere to your page that actually calls and sets up the facetview on a particular page element: 
```js
<script type="text/javascript">
jQuery(document).ready(function($) {
  $('.facet-view-simple').facetview({
    search_url: 'http://localhost:9200/myindex/type/_search',
    facets: [
        {'field': 'publisher.exact', 'size': 100, 'order':'term', 'display': 'Publisher'},
        {'field': 'author.name.exact', 'display': 'author'},
        {'field': 'year.exact', 'display': 'year'}
    ],
  });
});
</script>
```

Then add a ``div`` with the HTML class referenced in the script to the HTML body.
```
</head>
    <body>
        <div class="facet-view-simple"></div>
    </body>
</html>
```

That should be it!

See the webpages in /html for examples of more complex facetview2 configurations and for how to use JS or templates to specify the HTML shown for result set entries.
