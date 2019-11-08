<!DOCTYPE html>
<html>
<head lang="en">
    <meta charset="UTF-8">
    <title>People Browser</title>

    <script type="text/javascript" src="//cdnjs.cloudflare.com/ajax/libs/handlebars.js/4.0.1/handlebars.min.js"></script>

    <script type="text/javascript" src="/themes/cu-boulder/facetview2/vendor/jquery/1.7.1/jquery-1.7.1.min.js"></script>
    <link rel="stylesheet" href="/themes/cu-boulder/facetview2/vendor/bootstrap/css/bootstrap.min.css">
    <script type="text/javascript" src="/themes/cu-boulder/facetview2/vendor/bootstrap/js/bootstrap.min.js"></script>
    <link rel="stylesheet" href="/themes/cu-boulder/facetview2/vendor/jquery-ui-1.8.18.custom/jquery-ui-1.8.18.custom.css">
    <script type="text/javascript" src="/themes/cu-boulder/facetview2/vendor/jquery-ui-1.8.18.custom/jquery-ui-1.8.18.custom.min.js"></script>
    <!-- <script src="http://cdn.leafletjs.com/leaflet-0.7.5/leaflet.js"></script> -->

    <script type="text/javascript" src="/themes/cu-boulder/facetview2/es.js"></script>
    <script type="text/javascript" src="/themes/cu-boulder/facetview2/bootstrap2.facetview.theme.js"></script>
    <script type="text/javascript" src="/themes/cu-boulder/facetview2/jquery.facetview2.js"></script>

    <link rel="stylesheet" href="/themes/cu-boulder/facetview2/css/facetview.css">
    <link rel="stylesheet" href="/themes/cu-boulder/browsers.css">
    <!-- Add Font Awesome icon library -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
    <link rel="stylesheet" href="https://cdn.rawgit.com/jpswalsh/academicons/master/css/academicons.min.css">
    <!-- <link rel="stylesheet" href="http://cdn.leafletjs.com/leaflet-0.7.5/leaflet.css" /> -->

    <script id="person-template" type="text/x-handlebars-template">
        <tr>
            <td>
                <div class="person-body">
                <div class="thumbnail">
                    {{#if thumbnail}}
                      <a href="{{uri}}" target="_blank">
                       <img src="{{thumbnail}}">
                       </a>
                    {{else}}
                      <a href="{{uri}}" target="_blank">
                       <img src="/images/placeholders/thumbnail.jpg">
                       </a>
                    {{/if}}
                    <div class="caption">
                    <strong>
                    {{#if email}}
                       <div class="weblink">
                          <a href="mailto:{{email}}" title="Email" class="fa fa-envelope-square fa-lg"></a>
                       </div>
                    {{/if}}
                    {{#if orcid}}
                       <div class="weblink">
                          <a href="{{orcidURL orcid}}" target="_blank" title="ORCID" class="ai ai-orcid fa-lg"></a>
                       </div>
                    {{/if}}
                    </strong>
                    {{#if website}}
                      {{#listWebLinks website}}
                          <div class="weblink">
                             <a href="{{uri}}"` target="_blank" title="{{name}}" class="{{wclass}} fa-lg"></a>
                          </div>
                      {{/listWebLinks}}
                    {{/if}}
                    </strong>
                    </div>
                </div>
                <div class="person-info">
                   <div class="name"> <strong><h3> <a href="{{uri}}" target="_blank">{{name}}</a></h3></strong></div>

                    {{#if affiliations}}
                    {{#list affiliations}}{{position}} - <a href="{{org.uri}}">{{org.name}}</a>{{/list}}
                    {{/if}}

                    {{#if researchArea}}
                    <div><strong>Research Areas:</strong> {{#expand researchArea 9 uri "#research" }}<a href="{{uri}}" target="_blank">{{name}}</a>{{/expand}}</div>
                    {{/if}}

                    {{#if awards}}
                    <div><strong>Honors:</strong> {{#expand awards 10 uri "#background"}}<a href="{{award.uri}}" target="_blank">{{award.name}}</a>{{/expand}}</div>
                    {{/if}}

                    {{#if courses}}
                    <div><strong>Courses:</strong> {{#expand courses 5 uri "#teaching" }}<a href="{{uri}}" target="_blank">{{name}}</a>{{/expand}}</div>
                    {{/if}}

                    {{#if homeCountry}}
                    <div><strong>International Activities:</strong> {{#expand homeCountry 5 uri "#International_Activities"}}<a href="{{uri}}" target="_blank">{{name}}</a>{{/expand}}</div>
                    {{/if}}

                </div>
<!-- This is a prototype of a dropdown for researchOverview
{{#if researchOverview}}
  <div class="dropdown">
   <button 
      class="dropbtn">Research Overview
      <i class="fa fa-caret-down"></i>
    </button>
    <div class="dropdown-content">
        {{researchOverview}}
    </div>
  </div>
{{/if}}
-->
                </div>
            </td>
        </tr>
    </script>

    <script type="text/javascript">

        Handlebars.registerHelper('orcidURL', function(orcid) {
            return "http://orcid.org/"+orcid;
        });

        Handlebars.registerHelper('showMostSpecificType', function(mostSpecificType) {
            return (mostSpecificType && mostSpecificType != "Person");
        });

        Handlebars.registerHelper('expand', function(items, num, url, anchor, options) {
            var out = "";
            var z = items.length;
            var j = items.length - 1;
            var x = z;
            if(num < z) { x = num }
            var y = x - 1;
            for(var i = 0; i < x; i++) {
                if(i < y) {
                    out += options.fn(items[i]);
                    out += "; ";
                }
                else {
                  if(x < z) {
                    out += options.fn(items[i]);
                    out += options.fn({uri: url + anchor, name: " ...more"})
                  } 
                  else {
                    out += options.fn(items[i]);
                  }
                }
            }
            return out;
        });

        Handlebars.registerHelper('listWebLinks', function(items, options) {
            var out = "";

            items.sort(function(a, b) { 
               if (a.name < b.name) 
                 { return 1 }
               else { return -1}
            });
            for(var i = 0; i < items.length; i++) {
               if (items[i].name == "Twitter") { items[i].wclass = "fa fa-twitter" }
               if (items[i].name == "LinkedIn") { items[i].wclass = "fa fa-linkedin" }
               if (items[i].name == "Webpage") { items[i].wclass = "fa fa-globe" }
               out += options.fn(items[i]);
            }
            return out;
        });

        Handlebars.registerHelper('list', function(items, options) {
            var out = "<ul>";
            for(var i=0, l=items.length; i<l; i++) {
                out = out + "<li>" + options.fn(items[i]) + "</li>";
            }
            return out + "</ul>";
        });

        var source = $("#person-template").html();
        var template = Handlebars.compile(source);

    </script>

    <script type="text/javascript">
        jQuery(document).ready(function($) {
            $('.facet-view-simple').facetview({
                search_url: '/es/fis/person/_search',
                page_size: 10,
                sort: [
                    {"_score" : {"order" : "desc"}},
                    {"name.keyword" : {"order" : "asc"}}
                ],
                sharesave_link: true,
                search_button: true,
                default_freetext_fuzzify: false,
                default_facet_operator: "AND",
                default_facet_order: "count",
                default_facet_size: 15,
                facets: [
                    {'field': 'organization.name.keyword', 'display': 'Organization'},
                    {'field': 'researchArea.name.keyword', 'display': 'Research Area'},
                    {'field': 'homeCountry.name.keyword', 'display': 'International Activities'},
                    {'field': 'taughtcourse.keyword', 'display': 'Taught Course'},
                    {'field': 'awardreceived.keyword', 'display': 'Received Honor/Award'},
                ],
                search_sortby: [
                    {'display':'Name','field':'name.keyword'}
                ],
                render_result_record: function(options, record)
                {
                    return template(record).trim();
                },
                selected_filters_in_facet: true,
                show_filter_field : true,
                show_filter_logic: true
            });
        });
    </script>

    <style type="text/css">

        .facet-view-simple{
            width:100%;
            height:100%;
            margin:20px auto 0 auto;
        }

        .facetview_freetext.span4 {
           width: 290px;
           height: 10px;
        }

        legend {
            display: none;
        }

        #wrapper-content {
          padding-top: 0px;
        }

        input {
            -webkit-box-shadow: none;
            box-shadow: none;
        }

        .person-header {
            display: flex;
            vertical-align: top;
            clear: left;
            margin-left: 0 !important;
            max-width: 100%;
            justify-content: center;
        }

        .person-body {
            display: inline-block;
            vertical-align: top;
            clear: left;
            margin-left: 0 !important;
            max-width: 100%;
        }
        .person-info {
            display: inline-block;
            vertical-align: top;
            clear: left;
            margin-left: 0 !important;
            max-width: 80%;
        }

        .thumbnail {
            display: inline-block;
            width: 100px;
            box-shadow: none;
            border: none;
        }

        .name {
            box-shadow: none;
            border: none;
            margin-top: -12px;
            margin-bottom: -12px;
        }

        .weblink {
            display: inline-block;
            box-shadow: none;
            border: none;
            margin: 1px;
        }

       .weblink a {
            text-decoration: none;
        }
        .help {
            margin: 10px;
            border: 2px solid #c6ebc6;
            padding: 0 10px 10px;
        }

        .caption {
           margin-left: -10px;
           margin-right: -11px;
        }
.ul {
    margin: 0 0 4px 19px;
}
.navbar {
  overflow: hidden;
  background-color: #333;
  font-family: Arial, Helvetica, sans-serif;
}

.navbar a {
  float: left;
  font-size: 16px;
  color: white;
  text-align: center;
  padding: 14px 16px;
  text-decoration: none;
}

.dropdown {
  float: left;
  position: absolute;
  overflow: hidden;
  z-index: 5;
}

.dropdown .dropbtn {
  font-size: 14px;  
  outline: none;
  color: black;
  padding: 4px 6px;
  background-color: inherit;
  font-family: inherit;
  margin: 0;
  border-radious: 4px;
  
}

.navbar a:hover, .dropdown:hover .dropbtn {
  background-color: grey;
}

.dropdown-content {
  display: none;
  background-color: azure;
  min-width: 160px;
  box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2);
  z-index: 1;
  border: 1px solid;
  width: 600px;
  padding: 12px;
}

.dropdown-content a {
  float: none;
  color: black;
  text-decoration: none;
  display: block;
  text-align: left;
  background-color: azure;
  border: 1px solid;
  margin: 2px;
}


.dropdown-content a:hover {
  background-color: #ddd;
}

.dropdown:hover .dropdown-content {
  display: block;
}

 /* Style all font awesome icons */
.fa-twitter {
  background: #55ACEE;
  color: white;
}

.fa-linkedin {
  background: #007bb5;
  color: white;
}
.ai-orcid {
    background: white;
    color: #A6CE39;
}

    </style>

</head>
<body>
  <div class="dropdown">
    <button 
      class=btn "dropbtn">help
      <i class="fa fa-caret-down"></i>
    </button>
    <div class="dropdown-content">
      <b>SEARCH AND FILTER ON PEOPLE</b><br> The search term bar on the far right filters people whose data matches the term.  Encapsulate your term in  double quotes (" ") for exact matches. The filters on the left below, such as Research Area, are  only searching the Research Area keywords. The filters default to 'and' logic. Toggle with the 'or' button if desired. The filters and search term bar can be combined to help you narrow down the list of people you are interested in. To search all data in  CU Experts use the site search bar in the CU Experts page header. 
    </div>
  </div>
  <div class="facet-view-simple"> </div>
</body>
</html>

