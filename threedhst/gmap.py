"""
Convert Multidrizzle drz.fits (North up) to Google Maps tiles
"""

__version__ = "$Rev$"
# $URL$
# $Author$
# $Date$

import os
import numpy as np

# Specifies the size of the map (in pixels).
TILE_SIZE = 256
MAP_SIZE = [TILE_SIZE,TILE_SIZE]    
# This is the Maps API key for running on localhost:8080
MAP_KEY = 'ABQIAAAA1XbMiDxx_BTCY2_FkPh06RR20YmIEbERyaW5EQEiVNF0mpNGfBSRb' \
    '_rzgcy5bqzSaTV8cyi2Bgsx3g'

def makeGMapTiles(fitsimage=None):
    """
    This almost works.  Output coords don't seem to quite line up.
    """
    import pyfits
    import pywcs
    import fitsimage
    import numpy as np
    
    fitsimage = 'ib3721050_drz.fits'
    
    ### Read the FITS file
    fi = pyfits.open(fitsimage)
    head = fi[1].header
    data = fi[1].data
    #data = np.fliplr(fi[1].data)
    xsize = data.shape[1]
    ysize = data.shape[0]
    
    ### Image corners in Lat/Lon
    wcs = pywcs.WCS(head)
    llSE = radec2latlon(wcs.wcs_pix2sky([[wcs.naxis1,1]],1)[0])
    llNE = radec2latlon(wcs.wcs_pix2sky([[wcs.naxis1,wcs.naxis2]],1)[0])
    llSW = radec2latlon(wcs.wcs_pix2sky([[1,1]],1)[0])
    llNW = radec2latlon(wcs.wcs_pix2sky([[1,wcs.naxis2]],1)[0])
    llCenter = (llSW+llNE)/2.
    print llNE,llSW
    print llCenter
    
    lng_offset = 90
    
    makeMapHTML(llSW,llNE,lng_offset=lng_offset)
    
    llSW[1] += lng_offset-llCenter[1]
    llSE[1] += lng_offset-llCenter[1]
    llNW[1] += lng_offset-llCenter[1]
    llNE[1] += lng_offset-llCenter[1]
    llCenter[1] += lng_offset-llCenter[1]
    
    ### Get Google Map pixel/tile coordinates
    m = MercatorProjection()
    bounds = [llSW,llNE]
    view_size = [wcs.naxis1,wcs.naxis2]
    zoomLevel = m.CalculateBoundsZoomLevel(bounds, view_size)
    
    pixSW = m.FromLatLngToPixel(llSW,zoomLevel)
    pixSE = m.FromLatLngToPixel(llSE,zoomLevel)
    pixNW = m.FromLatLngToPixel(llNW,zoomLevel)
    pixNE = m.FromLatLngToPixel(llNE,zoomLevel)
    pixCenter = m.FromLatLngToPixel(llCenter,zoomLevel)
    
    ### Padding to make the output image size
    ### multiples of TILE_SIZE
    padL = (pixSW.tilex-np.floor(pixSW.tilex))*TILE_SIZE
    padR = (np.ceil(pixNE.tilex)-pixNE.tilex)*TILE_SIZE
    print padL,padR
    
    #padR = (pixNE.tilex-np.floor(pixNE.tilex))*TILE_SIZE
    #padL = (np.ceil(pixSW.tilex)-pixSW.tilex)*TILE_SIZE
    #print padL,padR
    
    ### Need to shift the image padding for the
    ### coords to come out right.  The expression 
    ### below works empirically for my test case, but not sure why.
    dd = (padL-padR)/2; padR+=dd; padL-=dd
    
    padT = (pixNE.tiley-np.floor(pixNE.tiley))*TILE_SIZE
    padB = (np.ceil(pixSW.tiley)-pixSW.tiley)*TILE_SIZE
    
    dx = pixNE.x-pixSW.x
    dy = pixSW.y-pixNE.y
    
    pixPerDeg = xsize/(llNE[1]-llSW[1])
    pixRatio = m.pixels_per_lon_degree[zoomLevel]/pixPerDeg
    
    data_copy = congrid(data,(dy,dx))
    
    #data_copy.resize((int(ysize*pixRatio),int(xsize*pixRatio)))
    #data_copy.resize((dy,dx))
    fullx = padL+padR+dx
    fully = padT+padB+dy
    full_image = np.zeros((fully,fullx))    
    full_image[padB:-padT, padL:-padR] = data_copy
    
    print pixRatio, dx/xsize, fullx/256., fully/256.
    
    NX = (padL+padR+dx)*1./TILE_SIZE
    NY = (padT+padB+dy)*1./TILE_SIZE
    
    tileX0 = int(pixSW.tilex)
    tileY0 = int(pixNE.tiley)
    
    for i in range(NX):
        for j in range(NY):
            #i,j = 0,0
            sub = full_image[fully-(j+1)*TILE_SIZE:fully-j*TILE_SIZE,
                             i*TILE_SIZE:(i+1)*TILE_SIZE]
            subim = data2image(sub)
            path = '/Users/gbrammer/Sites/map/ASTR/'
            outfile = path+'direct_%d_%d_%d.jpg' %(tileX0+i,
                            tileY0+j,zoomLevel)
            subim.save(outfile)
            #print outfile
            
    return None
    
def makeMapHTML(llSW, llNE, lng_offset=90):
    """
makeHTML(llSW, llNE, lng_offset=90)

    Make webpage container for holding the Google map.
    """
    
    center = (llSW+llNE)/2.
    
    web = """
    <html> 
    <head> 
        <meta http-equiv="content-type" content="text/html; charset=UTF-8"/> 
        <title>Google Maps</title> 
        <script src="http://maps.google.com/maps?file=api&amp;v=3&amp;key=ABQIAAAA1XbMiDxx_BTCY2_FkPh06RR20YmIEbERyaW5EQEiVNF0mpNGfBSRb_rzgcy5bqzSaTV8cyi2Bgsx3g" type="text/javascript"></script> 

        <script type="text/javascript"> 
    function initialize() {
        
        if (GBrowserIsCompatible()) {

          var map = new GMap2(document.getElementById("map"));
          map.addControl(new GScaleControl());
          // map.addControl(new GSmallMapControl());
          // map.addControl(new GMapTypeControl());
          var copyright = new GCopyright(1,
               new GLatLngBounds(new GLatLng(%f,%f),
                                 new GLatLng(%f,%f)),
                                 14, "3D-HST");
          var copyrightCollection = new GCopyrightCollection('Map Data:');
          copyrightCollection.addCopyright(copyright);

          CustomGetTileUrl=function(a,b){
              return "direct_"+a.x+"_"+a.y+"_"+b+".jpg"
          }
          var tilelayers = [new GTileLayer(copyrightCollection,14,14)];
          tilelayers[0].getTileUrl = CustomGetTileUrl;
          var custommap = new GMapType(tilelayers, 
                 new GMercatorProjection(15), "FITS");
          map.addMapType(custommap);
          map.setCenter(new GLatLng(%f,  %f), 14, custommap);
        }
    }
    function addObjectMarker(map,x,y,id) {
         var myIcon = new GIcon(G_DEFAULT_ICON);
         myIcon.iconSize = new GSize(40, 40);
         myIcon.iconAnchor = new GPoint(19.5, 19.5);

         myIcon.image = "circle.php?id="+id;
         markerOptions = { icon:myIcon };
         var point = new GLatLng(x,y);
         var marker = new GMarker(point, markerOptions)
         GEvent.addListener(marker, "click", function() {
             marker.openInfoWindowHtml("Marker <b>100</b>");
         });
         map.addOverlay(marker);
    }     
        </script>
        </head> 
      <body onload="initialize()" onunload="GUnload()"> 
        <div id="map" style="width: 300px; height: 300px"></div> 
      </body> 
    </html>
    """ %(llSW[0],llSW[1]-center[1]+lng_offset,
                  llNE[0],llNE[1]-center[1]+lng_offset,
                  center[0],lng_offset)
    
    outfile = '/Users/gbrammer/Sites/map/ASTR/map.html'
    fp = open(outfile,'w')
    fp.write(web)
    fp.close()
    print outfile
    
def makeCirclePNG(outfile=None):
    """
makeCirclePNG(outfile=None)
    
    Simple icon for overlay on Google Map.  Optionally includes
    an object label on top of a circle.
    
    Example:
    >>> makeCirclePNG(outfile='~/Sites/circle.php')
    
    Then point to 'http://localhost/~[user]/circle.php?id=100' in a web browser 
    (with web sharing and PHP enabled, if viewing locally)
    """
    
    PHPstring = """<?php
    $string = $_GET['id'];
    // Create a blank image.
    $image = imagecreatetruecolor(40, 40);
    // Make the background transparent
    $black = imagecolorallocate($im, 0, 0, 0);
    imagecolortransparent($image, $black);
    // Choose a color for the ellipse.
    $green = imagecolorallocate($image, 0, 255, 0);
    // Draw the ellipse.
    imageellipse($image, 19.5, 19.5, 10, 10, $green);
    // Add the ID number
    $px     = (imagesx($image) - 4.5 * strlen($string)) / 2;
    imagestring($image, 0, $px, 1.5, $string, $green);
    // Output the image.
    header("Content-type: image/png");
    imagepng($image);
    ?>
    """
    
    if outfile:
        fp = open(outfile,'w')
        fp.write(PHPstring)
        fp.close()
    else:
        print PHPstring


def data2image(data,zmin=-0.1,zmax=0.5):
    """
data2image(data,zmin=-0.1,zmax=0.5)
    
    Take a 2D data array and send it to a PIL Image 
    object after (linear) z-scaling.
    
    Parts taken from the `fitsimage` class in wcs2kml.
    
    """ 
    from PIL import Image
    import numpy as np
    # array sizes
    xsize = data.shape[1]
    ysize = data.shape[0]
    # copy of data
    fits_data = data*1.
    fits_data = np.where(fits_data > zmin, fits_data, zmin)
    fits_data = np.where(fits_data < zmax, fits_data, zmax)
    scaled_data = (fits_data - zmin) * (255.0 / (zmax - zmin)) + 0.5
    # convert to 8 bit unsigned int
    scaled_data = scaled_data.astype("B")
    # create the image
    image = Image.frombuffer("L", (xsize, ysize), scaled_data, "raw", "L", 0, 0)
    return image
    
def radec2latlon(radec):
    """
radec2latlon(radec)
    
    Convert R.A./Dec to Lat./Lon.
    
    """
    import numpy as np
    #latlon = np.zeros(2.)
    latlon = np.array([radec[1],360.-radec[0]])
    #latlon = np.array([radec[1],radec[0]])
    return latlon
    
def addPoly(radec,l0=0.):
    radec = np.array([189.2233,62.256869])
    l0 = 189.22169688
    ll = radec2latlon(radec)
    str = """
    var lat0 = %f;
    var lon0 = %f;
    var latOffset = 0.001;
    var lonOffset = 0.001;
    var polygon = new GPolygon([
      new GLatLng(lat0, lon0 - lonOffset),
      new GLatLng(lat0 + latOffset, lon0),
      new GLatLng(lat0, lon0 + lonOffset),
      new GLatLng(lat0 - latOffset, lon0),
      new GLatLng(lat0, lon0 - lonOffset)
    ], "#f33f00", 5, 1, "#ff0000", 0.2);
    map.addOverlay(polygon);""" %(ll[0],ll[1]-l0+90)
    
class Point():
    """
Stores a simple (x,y) point.  It is used for storing x/y pixels.
    
Attributes:
    x: An int for a x value.
    y: An int for a y value.
        
http://code.google.com/p/google-ajax-examples/source/browse/trunk/nonjslocalsearch/localSearch.py
    
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilex = x*1./TILE_SIZE
        self.tiley = y*1./TILE_SIZE
        
    def ToString(self):
        return '(%s, %s)' % (self.x, self.y)
    
    def Equals(self, other):
        if other is None :
            return false
        else:
            return (other.x == self.x and other.y == self.y)

class MercatorProjection():
  """
MercatorProjection

Calculates map zoom levels based on bounds or map points.

This class contains functions that are required for calculating the zoom  
level for a point or a group of points on a static map.  Usually the Maps API 
does the zoom for you when you specify a point, but not on static maps.

Attributes:
    pixels_per_lon_degree: A list for the number of pixels per longitude 
      degree for each zoom.
    pixels_per_lon_radian: A list for the number of pixels per longitude
      radian for each zoom.
    pixel_origo: List of number of x,y pixels per zoom.
    pixel_range: The range of pixels per zoom.
    pixels: Number of pixels per zoom.
    zoom_levels: A list of numbers representing each zoom level to test.
    
http://code.google.com/p/google-ajax-examples/source/browse/trunk/nonjslocalsearch/localSearch.py
    
  """
  def __init__(self, zoom_levels=18):
    self.pixels_per_lon_degree = []
    self.pixels_per_lon_radian = []
    self.pixel_origo = []
    self.pixel_range = []
    self.pixels = TILE_SIZE
    zoom_levels = range(0, zoom_levels)
    for z in zoom_levels:
      origin = self.pixels / 2
      self.pixels_per_lon_degree.append(self.pixels / 360)
      self.pixels_per_lon_radian.append(self.pixels / (2 * np.pi))
      self.pixel_origo.append(Point(origin, origin))
      self.pixel_range.append(self.pixels)
      self.pixels = self.pixels * 2
    
  def CalcWrapWidth(self, zoom):
    return self.pixel_range[zoom]
    
  def FromLatLngToPixel(self, lat_lng, zoom):
    """Given lat/lng and a zoom level, returns a Point instance.

    This method takes in a lat/lng and a _test_ zoom level and based on that it 
    calculates at what pixel this lat/lng would be on the map given the zoom 
    level.  This method is used by CalculateBoundsZoomLevel to see if this 
    _test_ zoom level will allow us to fit these bounds in our given map size.

    Args:
      lat_lng: A list of a lat/lng point [lat, lng]
      zoom: A list containing the width/height in pixels of the map.

    Returns:
      A Point instance in pixels.
    """
    o = self.pixel_origo[zoom]
    x = round(o.x + lat_lng[1] * self.pixels_per_lon_degree[zoom])
    siny = Bound(np.sin(DegreesToRadians(lat_lng[0])), 
        -0.9999, 0.9999)
    y = round(o.y + 0.5 * np.log((1 + siny) / 
        (1 - siny)) * -self.pixels_per_lon_radian[zoom])
    return Point(x, y)

  def CalculateBoundsZoomLevel(self, bounds, view_size):
    """Given lat/lng bounds, returns map zoom level.

    This method is used to take in a bounding box (southwest and northeast 
    bounds of the map view we want) and a map size and it will return us a zoom 
    level for our map.  We use this because if we take the bottom left and 
    upper right on the map we want to show, and calculate what pixels they 
    would be on the map for a given zoom level, then we can see how many pixels 
    it will take to display the map at this zoom level.  If our map size is 
    within this many pixels, then we have the right zoom level.

    Args:
      bounds: A list of length 2, each holding a list of length 2. It holds
        the southwest and northeast lat/lng bounds of a map.  It should look 
        like this: [[southwestLat, southwestLat], [northeastLat, northeastLng]]
      view_size: A list containing the width/height in pixels of the map.

    Returns:
      An int zoom level.
    """
    zmax = 18
    zmin = 0
    bottom_left = bounds[0]
    top_right = bounds[1]
    backwards_range = range(zmin, zmax)
    backwards_range.reverse()
    for z in backwards_range:
      bottom_left_pixel = self.FromLatLngToPixel(bottom_left, z)
      top_right_pixel = self.FromLatLngToPixel(top_right, z)
      if bottom_left_pixel.x > top_right_pixel.x :
        bottom_left_pixel.x -= self.CalcWrapWidth(z)
      if abs(top_right_pixel.x - bottom_left_pixel.x) <= view_size[0] \
          and abs(top_right_pixel.y - bottom_left_pixel.y) <= view_size[1] :
        return z
    return 0

def Bound(value, opt_min, opt_max):
    """
    Returns value if in min/max, otherwise returns the min/max.
    
  Args:
    value: The value in question.
    opt_min: The minimum the value can be.
    opt_max: The maximum the value can be.
    
  Returns:
    An int that is either the value passed in or the min or the max.
    
  http://code.google.com/p/google-ajax-examples/source/browse/trunk/nonjslocalsearch/localSearch.py
    """
    if opt_min is not None:
        value = max(value, opt_min)
    if opt_max is not None:
        value = min(value, opt_max)
    return value

def DegreesToRadians(deg):
    """
    http://code.google.com/p/google-ajax-examples/source/browse/trunk/nonjslocalsearch/localSearch.py
    """
    return deg * (np.pi / 180)

def congrid(a, newdims, method='linear', centre=False, minusone=False):
    '''Arbitrary resampling of source array to new dimension sizes.
    Currently only supports maintaining the same number of dimensions.
    To use 1-D arrays, first promote them to shape (x,1).
    
    Uses the same parameters and creates the same co-ordinate lookup points
    as IDL''s congrid routine, which apparently originally came from a VAX/VMS
    routine of the same name.

    method:
    neighbour - closest value from original data
    nearest and linear - uses n x 1-D interpolations using
                         scipy.interpolate.interp1d
    (see Numerical Recipes for validity of use of n 1-D interpolations)
    spline - uses ndimage.map_coordinates

    centre:
    True - interpolation points are at the centres of the bins
    False - points are at the front edge of the bin

    minusone:
    For example- inarray.shape = (i,j) & new dimensions = (x,y)
    False - inarray is resampled by factors of (i/x) * (j/y)
    True - inarray is resampled by(i-1)/(x-1) * (j-1)/(y-1)
    This prevents extrapolation one element beyond bounds of input array.
    '''
    import numpy as n
    import scipy.interpolate
    import scipy.ndimage
    
    if not a.dtype in [n.float64, n.float32]:
        a = n.cast[float](a)

    m1 = n.cast[int](minusone)
    ofs = n.cast[int](centre) * 0.5
    old = n.array( a.shape )
    ndims = len( a.shape )
    if len( newdims ) != ndims:
        print "[congrid] dimensions error. " \
              "This routine currently only support " \
              "rebinning to the same number of dimensions."
        return None
    newdims = n.asarray( newdims, dtype=float )
    dimlist = []

    if method == 'neighbour':
        for i in range( ndims ):
            base = n.indices(newdims)[i]
            dimlist.append( (old[i] - m1) / (newdims[i] - m1) \
                            * (base + ofs) - ofs )
        cd = n.array( dimlist ).round().astype(int)
        newa = a[list( cd )]
        return newa

    elif method in ['nearest','linear']:
        # calculate new dims
        for i in range( ndims ):
            base = n.arange( newdims[i] )
            dimlist.append( (old[i] - m1) / (newdims[i] - m1) \
                            * (base + ofs) - ofs )
        # specify old dims
        olddims = [n.arange(i, dtype = n.float) for i in list( a.shape )]

        # first interpolation - for ndims = any
        mint = scipy.interpolate.interp1d( olddims[-1], a, kind=method )
        newa = mint( dimlist[-1] )

        trorder = [ndims - 1] + range( ndims - 1 )
        for i in range( ndims - 2, -1, -1 ):
            newa = newa.transpose( trorder )

            mint = scipy.interpolate.interp1d( olddims[i], newa, kind=method )
            newa = mint( dimlist[i] )

        if ndims > 1:
            # need one more transpose to return to original dimensions
            newa = newa.transpose( trorder )

        return newa
    elif method in ['spline']:
        oslices = [ slice(0,j) for j in old ]
        oldcoords = n.ogrid[oslices]
        nslices = [ slice(0,j) for j in list(newdims) ]
        newcoords = n.mgrid[nslices]

        newcoords_dims = range(n.rank(newcoords))
        #make first index last
        newcoords_dims.append(newcoords_dims.pop(0))
        newcoords_tr = newcoords.transpose(newcoords_dims)
        # makes a view that affects newcoords

        newcoords_tr += ofs

        deltas = (n.asarray(old) - m1) / (newdims - m1)
        newcoords_tr *= deltas

        newcoords_tr -= ofs

        newa = scipy.ndimage.map_coordinates(a, newcoords)
        return newa
    else:
        print "Congrid error: Unrecognized interpolation type.\n", \
              "Currently only \'neighbour\', \'nearest\',\'linear\',", \
              "and \'spline\' are supported."
        return None