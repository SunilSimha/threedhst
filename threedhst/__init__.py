"""
3DHST

Utilities for processing WFC3 Grism exposures
from the 3D-HST large program.

"""

__version__ = "$Rev$"
# $URL$
# $Author$
# $Date$

import utils
import shifts
import sex
import process_grism
import plotting
import gmap
import regions
import spec1d   

options = {}
currentRun = {}
currentRun['step'] = 'INIT'

def defaultOptions():
    """
defaultOptions()
    
    Set THREEDHST default options.
    
    To see the defaults, run
    
    >>> threedhst.defaultOptions()
    >>> threedhst.showOptions()
    """
    #### Delete all keywords and reset
    for key in options.keys():
        pop = options.popitem()
        
    options['DETECT_THRESH'] = 5.     ## Default 1.5
    options['ANALYSIS_THRESH']  = 5.  ## Default 1.5
    options['GRISM_NAME'] = 'G141'
    options['MAG_ZEROPOINT'] = 26.46
    
    # #### Image format for webpage
    # #options['IMAGE_FORMAT'] = 'png'
    # options['IMAGE_FORMAT'] = 'svgz'
    
    #### Config options
    options['CONFIG_FILE'] = 'WFC3.IR.G141.V1.0.conf'
    options['SKY_BACKGROUND'] = 'WFC3.IR.G141.sky.V1.0.fits'
    options['DRZRESOLA'] = '50' #'46.5'
    options['DRZSCALE'] = '0.128254'
    
    #### WCS alignment image
    options['ALIGN_IMAGE'] = None
    
    #### Add other bands to the fluxcube
    options['OTHER_BANDS'] = []
    
    #### For fluxcube, if these remain 'None', use files 
    #### created from the internal SExtractor run 
    #options['CATALOG_FILE'] = None
    #options['SEGMENTATION_MAP'] = None
    
    
defaultOptions()

def showOptions():
    """
    printOptions()
    
    Show the current THREEDHST option set.
    """
    for key in options.keys():
        print '%s = %s' %(key,str(options[key]))