grab_norad()
{
  echo "============================================================"
  echo "NORAD DOWNLOAD"
  echo "============================================================"
  echo "wget -N -c ./data/gps-ops.txt http://www.celestrak.com/NORAD/elements/gps-ops.txt"
  wget -N -c . http://www.celestrak.com/NORAD/elements/gps-ops.txt

  wget -N -c . http://www.celestrak.com/NORAD/elements/
  NORAD_DATE=`grep "Data Updated: " ./index.html | grep -Po "20.*?\ .*?\ .*?\ "`
  IFS=' ' read -a array <<< "$NORAD_DATE"
  #NORAD_DATE=`date -d "${array[2]} ${array[1]} ${array[0]} ${array[3]} ${array[4]}" +"%s"`

  rm index.html

  NORAD_DATE="${array[2]}_${array[1]}_${array[0]}"
  mv gps-ops.txt data/gps-ops/"$NORAD_DATE".txt
}

parse()
{
  CONFIGFILE=$1

  eval $(sed '/:/!d;/^ *#/d;s/:/ /;' < "$CONFIGFILE" | while read -r key val
  do
    #verify here
    #...
    str="$key='$val'"
    echo "$str"
  done)
}

parse_config()
{
  CONFIGFILE=$1

  parse $CONFIGFILE

  echo "============================================================"
  echo "PARSING CONFIGURATION FILE: $CONFIGFILE"
  echo "============================================================"
  GPS_FROM=(`echo $GPS_FROM | grep -Po "\-?[0-9]+(\.[0-9]*)?"`)
  GPS_FROM1=${GPS_FROM[0]}
  GPS_FROM2=${GPS_FROM[1]}
  echo "GPS coord. from: $GPS_FROM1 $GPS_FROM2"
  GPS_TO=(`echo $GPS_TO | grep -Po "\-?[0-9]+(\.[0-9]*)?"`)
  GPS_TO1=${GPS_TO[0]}
  GPS_TO2=${GPS_TO[1]}
  echo "GPS coord. to:   $GPS_TO1 $GPS_TO2"
  echo "------------------------------------------------------------"
  HASH_ID=`echo "$GPS_FROM1,$GPS_FROM2,$GPS_TO1,$GPS_TO2" | md5sum | grep -Po "[^\ |\-]+"`
  echo "generated hash for terrain: $HASH_ID"
  echo "------------------------------------------------------------"
  echo "scan location from: $SCAN_LOCATION_FROM"
  echo "scan location to:   $SCAN_LOCATION_TO"
  echo "scan location increment (m): $SCAN_LOCATION_INC"
  echo "------------------------------------------------------------"
  SCAN_TIME_START=`date -d "$SCAN_TIME_START" +"%s"`
  SCAN_TIME_STOP=`date -d "$SCAN_TIME_STOP" +"%s"`
  echo "scan time start (unix): $SCAN_TIME_START"
  echo "scan time stop (unix):  $SCAN_TIME_STOP"
  echo "scan time increment (sec):      $SCAN_TIME_INC"
  echo "------------------------------------------------------------"
  echo "gps-ops: $OPS"
  echo "------------------------------------------------------------"
  if [ -z "$OSM_MODE" ]
  then
    OSM_MODE="DEFAULT"
  fi
  echo "osm mode: $OSM_MODE"
  echo "------------------------------------------------------------"
  echo "bing-key: $BING_KEY"
  echo "------------------------------------------------------------"
  echo "image-format: $IMG_FORMAT"
  echo "image-width:  $IMG_WIDTH"
  echo "image-height: $IMG_HEIGHT"
  echo "------------------------------------------------------------"
  echo "number of processes: $NUMBER_OF_PROCESSES"
  mkdir $OUTPUT_FOLDER
  echo "output folder: $OUTPUT_FOLDER"
  echo "output: $OUTPUT"
  echo "dpi: $DPI"

}

parse_meta()
{
  METAFILE="./data/tmp/$HASH_ID.meta"

  parse $METAFILE

  echo "============================================================"
  echo "PARSING META FILE: $METAFILE"
  echo "============================================================"
  echo "GPS center:  $CENTER"
  echo "image scale: $SCALE"
  echo "image zoom:  $ZOOM"
}

grab_osm()
{
  echo "============================================================"
  echo "OSM-GRAB"
  echo "============================================================"
  if [ -a "./data/tmp/$HASH_ID.osm" ]
  then
    echo "skipping, file already exists ..."
    echo "./data/tmp/$HASH_ID.osm"
  else
    echo "wget -N -c -O ./data/tmp/$HASH_ID.osm http://overpass-api.de/api/map?bbox=$GPS_FROM1,$GPS_FROM2,$GPS_TO1,$GPS_TO2"
    wget -N -c -O ./data/tmp/$HASH_ID.osm http://overpass-api.de/api/map?bbox=$GPS_FROM1,$GPS_FROM2,$GPS_TO1,$GPS_TO2
  fi
  #return
}

osm2obj()
{
  echo "============================================================"
  echo "OSM TO OBJECT"
  echo "============================================================"
  if [ -a "./data/tmp/$HASH_ID.obj" ]
  then
    echo "skipping, file already exists ..."
    echo "./data/tmp/$HASH_ID.obj"
  else

    echo "java -Djava.library.path=`pwd`/osm2world/lp_solve/ux64 -Xmx2G -jar `pwd`/osm2world/build/OSM2World.jar --config `pwd`data/osm2world/$OSM_MODE.properties -i `pwd`/data/$HASH_ID.osm -o `pwd`/data/$HASH_ID.obj"

    MISSING=($(java -Djava.library.path=`pwd`/osm2world/lp_solve/ux64 \
               -Xmx2G -jar `pwd`/osm2world/build/OSM2World.jar \
               --config `pwd`data/osm2world/$OSM_MODE.properties \
               -i `pwd`/data/tmp/$HASH_ID.osm \
               -o `pwd`/data/tmp/$HASH_ID.obj \
               2>&1 | grep "warning: missing SRTM tile" | grep -Po "[A-Z,0-9]+\.hgt"))

    if [[ $MISSING ]]
    then
        for hgt in "${MISSING[@]}"
        do
            wget -N -c -P data/tmp "http://dds.cr.usgs.gov/srtm/version2_1/SRTM3/Africa/$hgt.zip"
            wget -N -c -P data/tmp "http://dds.cr.usgs.gov/srtm/version2_1/SRTM3/Australia/$hgt.zip"
            wget -N -c -P data/tmp "http://dds.cr.usgs.gov/srtm/version2_1/SRTM3/Eurasia/$hgt.zip"
            wget -N -c -P data/tmp "http://dds.cr.usgs.gov/srtm/version2_1/SRTM3/Islands/$hgt.zip"
            wget -N -c -P data/tmp "http://dds.cr.usgs.gov/srtm/version2_1/SRTM3/North_America/$hgt.zip"
            wget -N -c -P data/tmp "http://dds.cr.usgs.gov/srtm/version2_1/SRTM3/South_America/$hgt.zip"
        done

        cd data/tmp
        unzip '*.zip'
        rm *.zip
        cd ..

        osm2obj
    fi

    echo "meshlabserver -i ./data/tmp/$HASH_ID.obj -o ./data/tmp/clean.obj"
    meshlabserver -i ./data/tmp/$HASH_ID.obj -o ./data/tmp/clean.obj
    echo "mv ./data/tmp/clean.obj ./data/tmp/$HASH_ID.obj"
    mv ./data/tmp/clean.obj ./data/tmp/$HASH_ID.obj
  fi
}

grab_meta()
{
  if [ -z "$BING_KEY" ]
  then
    KEY=$BING_KEY
  else
    KEY=AvQ2ulKY-NHkFI0owgmdlViXv5LVO03L59Antb2NMnhAOoT7IfCvvsi8KpPw4Uzl
  fi

  echo "============================================================"
  echo "GRABBING SATTELITE IMAGE FROM BING"
  echo "============================================================"
  if [ -a "./data/tmp/$HASH_ID.jpeg" ]
  then
    echo "skipping, file already exists ..."
    echo "./data/tmp/$HASH_ID.jpeg"
  else
    #echo "wget -N -c -O ./data/$HASH_ID.jpeg  http://dev.virtualearth.net/REST/v1/Imagery/Map/Aerial?mapArea=$2,$1,$4,$3\&format=$FMT\&ms=$WIDTH,$HEIGHT\&key=$KEY"
    wget -N -c -O ./data/tmp/$HASH_ID.$IMG_FORMAT  http://dev.virtualearth.net/REST/v1/Imagery/Map/Aerial?mapArea=$GPS_FROM2,$GPS_FROM1,$GPS_TO2,$GPS_TO1\&format=$IMG_FORMAT\&ms=$IMG_WIDTH,$IMG_HEIGHT\&key=$KEY

    echo "============================================================"
    echo "GRABBING META DATA FROM BING"
    echo "============================================================"
    #echo "wget -N -c -O ./data/$HASH_ID.x  http://dev.virtualearth.net/REST/v1/Imagery/Map/Aerial?mapArea=$2,$1,$4,$3\&format=$FMT\&ms=$WIDTH,$HEIGHT\&key=$KEY"
    wget -N -c -O ./data/tmp/$HASH_ID.x  http://dev.virtualearth.net/REST/v1/Imagery/Map/Aerial?mapArea=$GPS_FROM2,$GPS_FROM1,$GPS_TO2,$GPS_TO1\&format=$IMG_FORMAT\&ms=$IMG_WIDTH,$IMG_HEIGHT\&key=$KEY\&mmd=1

    SEGMENTS=20
    #echo "wget -N -c -O ./data/$HASH_ID.xx http://dev.virtualearth.net/REST/v1/Elevation/Bounds?bounds=$2,$1,$4,$3\&rows=$SEGMENTS\&cols=$SEGMENTS\&key=$KEY"
    wget -N -c -O ./data/tmp/$HASH_ID.xx http://dev.virtualearth.net/REST/v1/Elevation/Bounds?bounds=$GPS_FROM2,$GPS_FROM1,$GPS_TO2,$GPS_TO1\&rows=$SEGMENTS\&cols=$SEGMENTS\&key=$KEY

    CENTER=(`cat data/tmp/$HASH_ID.x | grep -Po "mapCenter\"\:\{[^\}]+" | grep -Po "\[[^\]]+" | grep -Po "\-?[0-9]+\.[0-9]+"`)
    ALTITUDE=(`cat data/tmp/$HASH_ID.xx | grep -Po "elevations\"\:\[[^\]]+" | grep -Po "[0-9]+" | sort | head -1`)
    ZOOM=(`cat data/tmp/$HASH_ID.x | grep -Po "zoom\"\:\"[^\"]+" | grep -Po "[0-9]+"`)
    HEIGHT=(`cat data/tmp/$HASH_ID.x | grep -Po "imageHeight\"\:\"[^\"]+" | grep -Po "[0-9]+"`)
    WIDTH=(`cat data/tmp/$HASH_ID.x | grep -Po "imageWidth\"\:\"[^\"]+" | grep -Po "[0-9]+"`)

    # Formula: https://msdn.microsoft.com/en-us/library/aa940990.aspx
    SCALE=`python -c "import math; print 156543.04 * abs(math.cos(${CENTER[0]} * math.pi / 180)) / (2 ** $ZOOM)"`

    echo "#QUAD: $GPS_FROM1,$GPS_FROM2,$GPS_TO1,$GPS_TO2" >> data/tmp/$HASH_ID.meta
    echo "#IMG_FORMAT: $IMG_FORMAT" >> data/tmp/$HASH_ID.meta
    echo "#IMG_HEIGHT: $HEIGHT"     >> data/tmp/$HASH_ID.meta
    echo "#IMG_WIDTH: $WIDTH"       >> data/tmp/$HASH_ID.meta
    echo "DATE: `date`"             >> data/tmp/$HASH_ID.meta
    echo "CENTER: ${CENTER[0]} ${CENTER[1]} $ALTITUDE" > data/tmp/$HASH_ID.meta
    echo "ZOOM: $ZOOM"              >> data/tmp/$HASH_ID.meta
    echo "SCALE: $SCALE"            >> data/tmp/$HASH_ID.meta

    rm data/tmp/$HASH_ID.x*
  fi
}

analyse()
{
  for i in $(seq 1 1 $NUMBER_OF_PROCESSES)
  do
    python ode/scanner.py \
        --file  `pwd`/data/tmp/$HASH_ID.obj \
        --image `pwd`/data/tmp/$HASH_ID.$IMG_FORMAT \
        --image_params $IMG_WIDTH $IMG_HEIGHT $SCALE \
        --ops $OPS \
        --time `expr $SCAN_TIME_START + $i \* $SCAN_TIME_INC` $SCAN_TIME_STOP `expr $SCAN_TIME_INC \* $NUMBER_OF_PROCESSES` \
        --center   $CENTER \
        --scanFrom $SCAN_LOCATION_FROM \
        --scanTo   $SCAN_LOCATION_TO \
        --scanInc  $SCAN_LOCATION_INC \
        --folder   $OUTPUT_FOLDER \
        --dpi $DPI \
        --output "$OUTPUT" &
  done
}

analyse-interactive()
{
  python ode/scanner.py \
    --file  `pwd`/data/tmp/$HASH_ID.obj \
    --image `pwd`/data/tmp/$HASH_ID.$IMG_FORMAT \
    --image_params $IMG_WIDTH $IMG_HEIGHT $SCALE \
    --ops $OPS \
    --time $SCAN_TIME_START $SCAN_TIME_STOP $SCAN_TIME_INC \
    --center   $CENTER \
    --scanFrom $SCAN_LOCATION_FROM \
    --scanTo   $SCAN_LOCATION_TO \
    --scanInc  $SCAN_LOCATION_INC \
    --folder   $OUTPUT_FOLDER \
    --dpi $DPI \
    --output "$OUTPUT" \
    --interactive
}

case "$1" in
  "--grab-norad")
    grab_norad
  ;;
  "--scan")
    parse_config $2
    grab_osm
    osm2obj
    grab_meta
    parse_meta
    analyse
  ;;

  "--scan-interactive")
    parse_config $2
    grab_osm
    osm2obj
    grab_meta
    parse_meta
    analyse-interactive
  ;;

  "--osm2obj")
    parse_config $2
    osm2obj
  ;;
  "--clean-all")
    cd data/tmp
    ls *.* | xargs rm -rf
    cd -
  ;;
  "--clean")
    parse_config $2
    rm data/tmp/$HASH_ID*
    rm -rf $OUTPUT_FOLDER
  ;;
  "--make")
    cd osm2world
    ant jar
    cd ..
    grab_norad
    cd odeViz
    sudo python setup.py install
    cd ..
  ;;
  "--grab-osm")
    parse_config $2
    grab_osm
  ;;
  "--grab-meta")
    parse_config $2
    grab_meta
  ;;
  "--kill")
    #cd todo
  ;;
  *)
    echo "help"
    echo ""
    echo "--clean CONFIGFILE              -   clean all config related files"
    echo "--clean-all                     -   delete all downloaded files"
    echo "--grab-norad                    -   download current norad files"
    echo "--grab-meta                     -   download related metadata from bing"
    echo "--grab-osm CONFIGFILE           -   download appropriate osm file"
    echo "--kill CONFIGFILE               -   to appear"
    echo "--make                          -   build additional packages"
    echo "--osm2obj CONFIGFILE            -   convert osm file to obj"
    echo "--parse CONFIGFILE              -   print config content"
    echo "--scan CONFIGFILE               -   run batch analysis"
    echo "--scan-interactive CONFIGFILE   -   interactive data exploration"
  ;;

esac
