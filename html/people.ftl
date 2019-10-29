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
    <!-- <link rel="stylesheet" href="http://cdn.leafletjs.com/leaflet-0.7.5/leaflet.css" /> -->

    <script id="person-template" type="text/x-handlebars-template">
        <tr>
            <td>
                <div class="thumbnail">
                    {{#if thumbnail}}<img src="{{thumbnail}}">{{/if}}
                    <div class="caption">
                        <h5><small>
                            {{#if dcoId}}
                            <a class="{{#if isDcoMember}}dco-logo{{/if}}" href="{{dcoId}}" target="_blank">{{name}}</a>
                            {{else}}
                            <a class="{{#if isDcoMember}}dco-logo{{/if}}" href="{{uri}}" target="_blank">{{name}}</a>
                            {{/if}}
                        </small></h5>
                    </div>
                </div>
                <div class="person-info">
                    {{#if (showMostSpecificType mostSpecificType)}}<div><em class="small">{{mostSpecificType}}</em></div>{{/if}}
                    {{#if email}}<div><strong>Email: </strong><a href="mailto:{{email}}">{{email}}</a></div>{{/if}}
                    {{#if orcid}}<div><strong>ORCID ID:</strong> <a href="{{orcidURL orcid}}" target="_blank">{{orcid}}</a></div>{{/if}}


                    {{#if organization}}
                    <div><strong>Organizations:</strong> {{#expand organization}}<a href="{{uri}}" target="_blank">{{name}}</a>{{/expand}}</div>
                    {{/if}}

                    {{#if affiliations}}
                    <div><strong>Affiliations:</strong></div>
                    {{#list affiliations}}{{position}} - <a href="{{org.uri}}">{{org.name}}</a>{{/list}}
                    {{/if}}

                    {{#if researchArea}}
                    <div><strong>Research Areas:</strong> {{#expand researchArea}}<a href="{{uri}}" target="_blank">{{name}}</a>{{/expand}}</div>
                    {{/if}}

                    {{#if homeCountry}}
                    <div><strong>International Activities:</strong> {{#expand homeCountry}}<a href="{{uri}}" target="_blank">{{name}}</a>{{/expand}}</div>
                    {{/if}}

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

        Handlebars.registerHelper('expand', function(items, options) {
            var out = "";
            var j = items.length - 1;
            for(var i = 0; i < items.length; i++) {
                out += options.fn(items[i]);
                if(i < j) {
                    out += "; ";
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
    </style>

</head>
<body>
<div class="facet-view-simple">
<div class="help"> <h3> PEOPLE SEARCH </h3> Use the People Search bar directly below or the expandable Filters at left to explore Boulder faculty data. People Search allows for wildcard * or exact search with " " double quotations. The research filter is only searching the Research Keywords, not the free-text keywords or research overview. To search VIVO without the filters in order to include all research fields, use the site search bar in the VIVO page header. Filters default to 'and' logic. Toggle with the 'or' button if desired.</div>
</body>
</html>
