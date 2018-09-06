#!/usr/bin/env python3
#
# See http://www.gdal.org/classVRTRasterBand.html#a155a54960c422941d3d5c2853c6c7cef
def histConvert(fname, outfmt= 'PDF', nbuckets=1000, percentiles=None):
  """
  This function was converted to Python 3 from Ahmed Fasih's Python 2 equivalent, 
  which can be found at the gist page 
  https://gist.github.com/fasiha/257337c756f3a8e8d088b24d75fe048e

  Given a filename, finds approximate percentile values and provides the
  gdal_translate invocation required to create an 8-bit file.
  Works by evaluating a histogram of the original raster with a large number of
  buckets between the raster minimum and maximum.
  N.B. This technique is very approximate and hasn't been checked for asymptotic
  convergence. 
  Optional arguments:
  - `percentiles`: list of percentiles, between 0 and 100 (inclusive).
  - `nbuckets`: the more buckets, the better percentile approximations you get.
  """
  import numpy as np
  from osgeo import gdal

  if percentiles is None:
      percentiles = [0.1, 99.9] 

  # Open source dataset
  src = gdal.Open(fname, gdal.GA_ReadOnly)
  band = src.GetRasterBand(1)

  # Use GDAL to find the min and max
  (lo, hi, avg, std) = band.GetStatistics(True, True)

  # Use GDAL to calculate a big histogram
  rawhist = band.GetHistogram(min=lo, max=hi, buckets=nbuckets)
  binEdges = np.linspace(lo, hi, nbuckets+1)

  # Probability mass function. Trapezoidal-integration of this should yield 1.0.
  pmf = rawhist / (np.sum(rawhist) * np.diff(binEdges[:2]))

  # Cumulative probability distribution. Starts at 0, ends at 1.0.
  distribution = np.cumsum(pmf) * np.diff(binEdges[:2])

  # Which histogram buckets are close to the percentiles requested?
  idxs = [np.sum(distribution < p / 100.0) for p in percentiles]

  # These:
  vals = [binEdges[i] for i in idxs]

  # Append 0 and 100% percentiles (min & max)
  percentiles = [0] + percentiles + [100]
  vals = [lo] + vals + [hi]

  # Print out gdal_translate command (what we came here for anyway)
  print("gdal_translate -ot Byte -of {fmt} -a_nodata 0 -scale {min} {max} 0 255 {fname} clipped-{fname}.{fmt.lower()}".format(min=vals[1], max=vals[-2], fname=fname, fmt = outfmt))

  if retVals:
      return (vals, percentiles)
  else: 
      return 0


def Parser():
    """Parse command line arguments using argparse."""
    import argparse

    p = argparse.ArgumentParser(
        description='Convert a GDAL-readable raster file to an image file (PNG, PDF)')

    # geom directory
    p.add_argument(
        '--filename', '-f', dest = 'filename', type = str,
        help='Convert a GDAL-readable file to a PDF or PNG',
        required = True)

    p.add_argument(
        '--outformat', '-of', dest = 'outformat', type = str,
        help='Format to convert raster',
        default = 'PDF')

    p.add_argument(
        '--nbuckets', '-n', dest = 'nbins',type = int,
        help='Number of bins',
        default = 1000)

    p.add_argument(
        '--percentiles', '-p', dest = 'percentiles', nargs = 2, type = float,
        help='Number of bins',
        default = None)

    return p


def cmdLineParse(parser, iargs = None):
    '''
    Command line parser.
    '''
    return parser.parse_args(args=iargs)


if __name__ == '__main__':

    inps = cmdLineParse(Parser())

    histConvert(inps.filename, inps.outformat, inps.nbins, inps.percentiles)
