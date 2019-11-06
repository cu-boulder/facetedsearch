
<!DOCTYPE html>
<html lang="en">
    <head>

<meta charset="utf-8" />
<!-- Google Chrome Frame open source plug-in brings Google Chrome's open web technologies and speedy JavaScript engine to Internet Explorer-->
<meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">

<title>People | CU Experts | CU Boulder</title>



<!-- vitro base styles (application-wide) -->
<link rel="stylesheet" href="/css/vitro.css" />



<link rel="stylesheet" href="/css/edit.css" /><link rel="stylesheet" href="/themes/cu-boulder/css/screen.css" />

<script>
var i18nStrings = {
    allCapitalized: 'All',
};
</script>
<script type="text/javascript" src="/js/jquery.js"></script>
<script type="text/javascript" src="/js/vitroUtils.js"></script>

<!--[if lt IE 9]>
<script type="text/javascript" src="/js/html5.js"></script>
<![endif]-->

 

<!--[if lt IE 7]>
<link rel="stylesheet" href="/themes/cu-boulder/css/ie6.css" />
<![endif]-->

<!--[if IE 7]>
<link rel="stylesheet" href="/themes/cu-boulder/css/ie7.css" />
<![endif]-->

<!--[if (gte IE 6)&(lte IE 8)]>
<script type="text/javascript" src="/js/selectivizr.js"></script>
<![endif]-->



<div id="wrapper-content" role="main">        
    
    <!--[if lte IE 8]>
    <noscript>
        <p class="ie-alert">This site uses HTML elements that are not recognized by Internet Explorer 8 and below in the absence of JavaScript. As a result, the site will not be rendered appropriately. To correct this, please either enable JavaScript, upgrade to Internet Explorer 9, or use another browser. Here are the <a href="http://www.enable-javascript.com"  title="java script instructions">instructions for enabling JavaScript in your web browser</a>.</p>
    </noscript>
    <![endif]-->
        
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
                </div>

                <div class="person-body">
                <div class="thumbnail">
                    {{#if thumbnail}}
                      <a href="{{uri}}" target="_blank">
                       <img src="{{thumbnail}}">
                       </a>
                    {{else}}
                      <a href="{{uri}}" target="_blank">
                       <img src="https://vivo-cub-dev.colorado.edu/images/placeholders/thumbnail.jpg">
                       </a>
                    {{/if}}
                    <div class="caption">
                    <strong>
                    {{#if email}}
                       <div class="weblink">
                          <a href="mailto:{{email}}" class="fa fa-envelope-square fa-lg"></a>
                       </div>
                    {{/if}}
                    {{#if orcid}}
                       <div class="weblink">
                          <a href="{{orcidURL orcid}}" target="_blank" class="ai ai-orcid fa-lg"></a>
                       </div>
                    {{/if}}
                    </strong>
                    {{#if website}}
                      {{#listWebLinks website}}
                          <div class="weblink">
                             <a href="{{uri}}"` target="_blank" class="{{wclass}} fa-lg"></a>
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
                    <div><strong>Research Areas:</strong> {{#expand researchArea 9 uri }}<a href="{{uri}}" target="_blank">{{name}}</a>{{/expand}}</div>
                    {{/if}}

                    {{#if awards}}
                    <div><strong>Honors:</strong> {{#expand awards 10 uri }}<a href="{{award.uri}}" target="_blank">{{award.name}}</a>{{/expand}}</div>
                    {{/if}}

                    {{#if courses}}
                    <div><strong>Courses:</strong> {{#expand courses 5 uri }}<a href="{{uri}}" target="_blank">{{name}}</a>{{/expand}}</div>
                    {{/if}}

                    {{#if homeCountry}}
                    <div><strong>International Activities:</strong> {{#expand homeCountry 5 uri }}<a href="{{uri}}" target="_blank">{{name}}</a>{{/expand}}</div>
                    {{/if}}

                </div>
<!--
{{#if researchOverview}}
  <div class="dropdown">
/   <button 
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
*/
    </script>

    <script type="text/javascript">

        Handlebars.registerHelper('orcidURL', function(orcid) {
            return "http://orcid.org/"+orcid;
        });

        Handlebars.registerHelper('showMostSpecificType', function(mostSpecificType) {
            return (mostSpecificType && mostSpecificType != "Person");
        });

        Handlebars.registerHelper('listWebLinks', function(items, options) {
            var out = "";

            items.sort((a, b) => (a.name < b.name) ? 1 : -1);
            for(var i = 0; i < items.length; i++) {
               if (items[i].name == "Twitter") { items[i].wclass = "fa fa-twitter" }
               if (items[i].name == "LinkedIn") { items[i].wclass = "fa fa-linkedin" }
               if (items[i].name == "Webpage") { items[i].wclass = "fa fa-globe" }
               out += options.fn(items[i]);
            }
            return out;
        });



        Handlebars.registerHelper('expand', function(items, num, url, options) {
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
                    out += options.fn({uri: url, name: " ...more"})
                  } 
                  else {
                    out += options.fn(items[i]);
                  }
                }
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

        #facetview_filter_isDcoMember {
            display: none; !important;
            visibility: hidden;
        }

        #facetview_filter_group_isDcoMember {
            display: none; !important;
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
      class=btn "dropbtn">Help
      <i class="fa fa-caret-down"></i>
    </button>
    <div class="dropdown-content">
<h3> PEOPLE SEARCH </h3> Use the People Search bar directly below or the expandable Filters at left to explore Boulder faculty data. To limit search to exact terms use double quotes (" ").  Search also allows for wildcard searching by using the wildcard character (*). The filters on the left, such as Research Area, are  only searching the Research Area keywords. To search CU Experts without the filters in order to include all research fields, use the site search bar in the CU Experts page header. Filters default to 'and' logic. Toggle with the 'or' button if desired.
    </div>
  </div>
<div class="facet-view-simple">
</div>
</body>
</html>

        

</div> <!-- #wrapper-content -->


    </body>
</html>

