import cgi, sys, os
from lxml import etree
from collections import defaultdict
from urllib import urlopen

streets = [ 
    ('upper_street', (-0.10849,51.53161,-0.10047,51.54661)),
    ('oxford_street', (-0.15905,51.51284,-0.12966,51.51716)),
    ('brick_lane', (-0.07355,51.51593,-0.06829,51.5264)),
    ('regent_street', (-0.14397,51.50965,-0.13404,51.51775)),
    ('covent_garden', (-0.13145,51.50961,-0.11802,51.51761)),
]

special = ['place', 'railway', 'shop', 'amenity', 'tourism']

if not all(os.path.exists(s[0] + '.osm') for s in streets) or (len(sys.argv) > 1 and sys.argv[1] == '--download'):
    for street, bbox in streets:
        url = 'http://www.openstreetmap.org/api/0.6/map?bbox=' + ','.join(`i` for i in bbox)
        print 'getting:', url
        open(street + '.osm', 'w').write(urlopen(url).read())

def sort_by_name(things):
    def strip_the(s):
        return s[4:] if s.startswith('the ') else s
    return sorted(things, key=lambda i:strip_the(i['name'].lower()) if 'name' in i else None)

def thing_list(things):
    ret = ''
    span_open = False
    for t in things:
        node_id = t.pop('id') if 'id' in t else None
        if node_id:
            ret += '<span onclick="place_marker(%f, %f)">' % (t['lat'], t['lon'])
            span_open = True

        if 'name' in t:
            ret += '<b>' + cgi.escape(t['name'].encode('utf-8')) + '</b> '
        else:
            ret += '<i>unnamed</i> '
        done_street = False
        lines = []
        if 'addr:housenumber' in t and 'addr:street' in t:
            lines.append(t['addr:housenumber'] + ' ' + t['addr:street'])
            done_street = True
        if 'website' in t:
            if span_open:
                span_open = False
                ret += '</span>'
            website = t['website']
            if not website.startswith('http'):
                website = 'http://' + website
            lines.append('<a href="%s">website</a>' % website)
        if 'wikipedia' in t:
            if span_open:
                span_open = False
                ret += '</span>'
            wikipedia = t['wikipedia']
            if not wikipedia.startswith('http'):
                wikipedia = 'http://en.wikipedia.org/wiki/' + wikipedia.replace(' ', '_')
            lines.append('<a href="%s">wikipedia</a>' % wikipedia)
        for k, v in t.items():
            if k in ('id', 'lat', 'lon', 'name', 'website', 'wikipedia'):
                continue
            if k in ('addr:housenumber', 'addr:street') and done_street:
                continue
            lines.append(k + ': ' + cgi.escape(v.encode('utf-8')))
        ret += ', '.join(lines) + ' ' 
        if span_open:
            span_open = False
            ret+= '</span>'
        if node_id:
            ret += '<a href="http://www.openstreetmap.org/browse/node/' + node_id + '">osm</a>'
        ret += '<br>'
    return ret
 
for street, bbox in streets:
    print street
    street_name = ' '.join(s[0].upper() + s[1:].lower() for s in street.split('_'))

    tree = etree.parse(street + '.osm')
    root = tree.getroot()
    out = open(street + '.html', 'w')

    print >> out, '''<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" /> 
<title>Street guide</title>
<script src="http://www.openlayers.org/api/OpenLayers.js"></script>
<script src="http://www.openstreetmap.org/openlayers/OpenStreetMap.js"></script>
<script type="text/javascript">
var lat=%f;
var lon=%f;

var map; //complex object of type OpenLayers.Map

//Initialise the 'map' object
function init() {
    map = new OpenLayers.Map ("map", {
        controls:[
            new OpenLayers.Control.Navigation(),
            new OpenLayers.Control.PanZoomBar(),
            new OpenLayers.Control.LayerSwitcher(),
            new OpenLayers.Control.Attribution()],
        maxExtent: new OpenLayers.Bounds(-20037508.34,-20037508.34,20037508.34,20037508.34),
                    maxResolution: 156543.0399,
        numZoomLevels: 19,
        units: 'm',
        projection: new OpenLayers.Projection("EPSG:900913"),
        displayProjection: new OpenLayers.Projection("EPSG:4326")
    } );


    layerMapnik = new OpenLayers.Layer.OSM.Mapnik("Mapnik");
    map.addLayer(layerMapnik);
    layerTilesAtHome = new OpenLayers.Layer.OSM.Osmarender("Osmarender");
    map.addLayer(layerTilesAtHome);
    layerCycleMap = new OpenLayers.Layer.OSM.CycleMap("CycleMap");
    map.addLayer(layerCycleMap);
    layerMarkers = new OpenLayers.Layer.Markers("Markers");
    map.addLayer(layerMarkers);
    var lonLat = new OpenLayers.LonLat(lon, lat).transform(new OpenLayers.Projection("EPSG:4326"), map.getProjectionObject());
    map.setCenter (lonLat, 16);
}

function place_marker(mlat, mlon) {
    var lonLat = new OpenLayers.LonLat(mlon, mlat).transform(new OpenLayers.Projection("EPSG:4326"), map.getProjectionObject());
    map.setCenter (lonLat, 18);
    layerMarkers.clearMarkers();

    var size = new OpenLayers.Size(21,25);
    var offset = new OpenLayers.Pixel(-(size.w/2), -size.h);
    var icon = new OpenLayers.Icon('http://www.openstreetmap.org/openlayers/img/marker.png',size,offset);
    layerMarkers.addMarker(new OpenLayers.Marker(lonLat,icon));
}
</script>

</head>
<body onload="init();">
<div style="position:fixed;top:0px;left:0px;width:50%%;height:100%%;" id="map"></div>'
''' % (bbox[1] + (bbox[3] - bbox[1]) / 2, bbox[0] + (bbox[2] - bbox[0]) / 2)

    things = []
    for node_or_way in root:
        if node_or_way.tag not in ('way', 'node'):
            continue
        this = {}

        for e in node_or_way:
            if e.tag != 'tag' or e.attrib['k'] == 'created_by':
                continue
            this[e.attrib['k']] = e.attrib['v']
        if 'randomjunk_bot' in this:
            del this['randomjunk_bot']
        if 'website' not in this and 'url' in this:
            this['website'] = this.pop('url')
        if 'name' not in this and 'name:en' in this:
            this['name'] = this.pop('name:en')
        assert 'id' not in this

        if not this or this.get('highway') in ('crossing', 'traffic_signals', 'turning_circle', 'mini_roundabout'):
            continue
        if this.get('amenity') in ('car_sharing',):
            continue
        if this.get('barrier') == 'gate':
            continue
        for f in 'source', 'area', 'audio_file', 'addr:flats':
            if f in this:
                del this[f]
        if this.get('railway') in ('subway', 'rail') or this.get('traffic_calming') or this.get('enforcement'):
            continue
        if this.get('amenity') == 'parking' and this.get('access') == 'private':
            continue
        if this.get('tunnel') and not this.get('name'):
            continue
        if len(this) == 1 and 'addr:housenumber':
            continue
        if len(this) == 2 and 'building' in this and 'addr:housename' in this:
            continue
        if len(this) == 2 and 'building' in this and 'addr:street' in this:
            continue
        if len(this) == 3 and 'addr:housenumber' in this and 'building' in this and 'addr:street' in this:
            continue
        if len(this) == 4 and 'addr:postcode' in this and 'addr:housenumber' in this and 'building' in this and 'addr:street' in this:
            continue
        if node_or_way.tag == 'node':
            n = node_or_way.attrib
            this['id'] = n['id']
            this['lat'] = float(n['lat'])
            this['lon'] = float(n['lon'])

            if not ((bbox[1] < this['lat'] < bbox[3]) and (bbox[0] < this['lon'] < bbox[2])):
                continue
        elif 'highway' in this:
            continue
        things.append(this)

    tagwatch = defaultdict(lambda: defaultdict(int))

    has_name = 0
    poi = defaultdict(lambda: defaultdict(list))
    for t in things:
        for f in special:
            if f in t:
                poi[f][t[f]].append(t)
        if 'name' in t:
            has_name += 1
        for k, v in t.items():
            tagwatch[k][v] += 1

    print >> out, '<div style="overflow:auto;position:fixed;top:0px;left:50%;height:100%;">'
    print >> out, '<h1>%s</h1>' % street_name
    print >> out, "%d things found, %d have a name, %d don't have a name<br>" % (len(things), has_name, len(things) - has_name)

    for f in special:
        print >> out, '<h2>' + f[0].upper() + f[1:] + '</h2>'
        for k, v in sorted(poi[f].items(), key=lambda i: i[0]):
            print >> out, '<h3>' + k + '</h3>'
            print >> out, thing_list(sort_by_name(dict(b for b in a.items() if b[0] != f) for a in v))

    other = [i for i in things if not any(j in i for j in special)]
    print >> out, '<h2>With name</h2>'
    print >> out, thing_list(sort_by_name(i for i in other if 'name' in i))
    print >> out, '<h2>No name</h2>'
    print >> out, thing_list(i for i in other if 'name' not in i), '<p>'

    print >> out, 'Data is copyright OpenStreetMap and contributors License: <a href="http://creativecommons.org/licenses/by-sa/2.0/">Creative Commons BY-SA 2.0</a><br>'
    print >> out, '</div>'
    print >> out, '</body>\n</html>\n'
