# GpsSatFi

A tool for calculating realistic GPS accuracy (dilution of precision) with the
help of 3D models, gathered from the community based [openstreetmap.org](https://www.openstreetmap.org).

    Authors: André Dietrich & Sebastian Zug
    Email: dietrich@ivs.cs.uni-magdeburg.de, zug@ivs.cs.uni-magdeburg.de
    Publication: to appear

## Installation

The project can be downloaded from [gitlab](http://gitlab.com) with `git` as
follows:
```bash
$ git clone --recursive https://gitlab.com/OvGU-ESS/GpsSatFi.git
```
Afterwards to build the additional submodules included, pleas run:
```bash
$ cd GpsSatFi
$ ./GpsSatFi.sh --make
```
If an error occurred, you can manually build them:
```bash
$ cd osm2world
$ ant jar
$ cd ..
$ cd odeViz
$ sudo python setup.py install  # propably, build has to be executed 2 times
$ cd ..
```
Additional dependencies that are not automatically installed:

* [`ephem`](http://rhodesmill.org/pyephem)
* [`mayavi2`](http://code.enthought.com/projects/mayavi)
* [`matplotlib`](http://matplotlib.org)
* [`meshlab`](http://meshlab.sourceforge.net)
* [`numpy`](http://www.numpy.org)
* [`vtk5`](http://www.vtk.org)

`ephem` needs to be installed via `pip`:
```bash
$ sudo pip install pyephem
```

All other packages can be downloaded from the standard Ubuntu repositories via:
```bash
$ sudo apt-get install mayavi2 python-matplotlib meshlab python-numpy python-vtk
```
... other missing packages should be reported by Python ;)

## Application

This module is intended to provide analysis data only in different formats.
Everything is handled with the help of the main script file
[`GpsSatFi.sh`](./GpsSatFi.sh). Run the following command to get an idea of the
appropriate usage:
```bash
$ ./GpsSatFi.sh --help
--clean CONFIGFILE              -   clean all config related files
--clean-all                     -   delete all downloaded files
--grab-norad                    -   download current norad files
--grab-meta                     -   download related metadata from bing
--grab-osm CONFIGFILE           -   download appropriate osm file
--kill CONFIGFILE               -   to appear
--make                          -   build additional packages
--osm2obj CONFIGFILE            -   convert osm file to obj
--parse CONFIGFILE              -   print config content
--scan CONFIGFILE               -   run batch analysis
--scan-interactive CONFIGFILE   -   interactive data exploration
```
As indicated by the appearance of `CONFIGFILE` above, all configuration is done
with the help of a single file. See the examples and comments in
[example-configuration.ini](./example-configuration.ini).

The following command executes the configured scan in batch processing mode and
stores the requested data in the requested formats at the specified output
folders.
```bash
$ ./GpsSatFi.sh --scan example-configuration.ini
```
Commonly `data/results` is therefore applied. Results are stored with the
following naming convention `ANALYSIS_TIMESTAMP.FORMAT`.

Although this project is optimized for batch processing, the following command
allows exploring the desired area manually.
```bash
$ ./GpsSatFi.sh --scan-interactive example-configuration.ini
```
Pressing the button `m` allows to switch between different analysis modes.

## Bing

To be able to download additional satellite images and meta information about
the area a Bing developer account is required. The registration and usage is
free of charge, but has to be renewed every three months. Please get your own
private BingMapsKey here: https://msdn.microsoft.com/de-de/library/ff428642.aspx

The generated key can then be set at the configuration file for parameter
`BING_KEY`.

## Extensions

The main analysis procedures are defined in file
[`ode/analyze.py`](ode/analyze.py). New analyze functions can be integrated and
made accessible to the scanner by extending the list in the last line of this
file with additional function pointers:

```python
FCT_LIST = [SatCount, DOPH_FAST, DOPP_FAST, DOPT_FAST, ... add here]
```
