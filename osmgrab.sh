#!/bin/bash

grab_osm()
{
    HASH_ID=`echo "$1,$2,$3,$4" | md5sum | grep -Po "[^\ |\-]+"`
    echo "wget -O ./data/$HASH_ID.osm http://overpass-api.de/api/map?bbox=$1,$2,$3,$4"
    wget -O ./data/$HASH_ID.osm http://overpass-api.de/api/map?bbox=$1,$2,$3,$4
    return
}

grab_gps_ops()
{
	echo "wget -N -c ./data/gps-ops.txt http://www.celestrak.com/NORAD/elements/gps-ops.txt"
	wget -N -c ./data/gps-ops.txt http://www.celestrak.com/NORAD/elements/gps-ops.txt
  mv gps-ops.txt data/
	return
}

osm2obj()
{
    HASH_ID=`echo "$1,$2,$3,$4" | md5sum | grep -Po "[^\ |\-]+"`

    #java -Djava.library.path="osm2world/lib/jogl/linux-amd64" -Xmx2G -jar osm2world/OSM2World.jar -i `pwd`/data/$1,$2,$3,$4.osm -o `pwd`/data/$1,$2,$3,$4.obj

    echo "java -Djava.library.path=`pwd`/OSM2World/lp_solve/ux64 -Xmx2G -jar `pwd`/OSM2World/build/OSM2World.jar --config `pwd`/osm2world$5.properties -i `pwd`/data/$HASH_ID.osm -o `pwd`/data/$HASH_ID.obj"

    MISSING=($(java -Djava.library.path=`pwd`/OSM2World/lp_solve/ux64 \
               -Xmx2G -jar `pwd`/OSM2World/build/OSM2World.jar \
               --config `pwd`/osm2world$5.properties \
               -i `pwd`/data/$HASH_ID.osm \
               -o `pwd`/data/$HASH_ID.obj \
               2>&1 | grep "warning: missing SRTM tile" | grep -Po "[A-Z,0-9]+\.hgt"))

    if [[ $MISSING ]]
    then
        for hgt in "${MISSING[@]}"
        do
            wget -N -c -P data "http://dds.cr.usgs.gov/srtm/version2_1/SRTM3/Africa/$hgt.zip"
            wget -N -c -P data "http://dds.cr.usgs.gov/srtm/version2_1/SRTM3/Australia/$hgt.zip"
            wget -N -c -P data "http://dds.cr.usgs.gov/srtm/version2_1/SRTM3/Eurasia/$hgt.zip"
            wget -N -c -P data "http://dds.cr.usgs.gov/srtm/version2_1/SRTM3/Islands/$hgt.zip"
            wget -N -c -P data "http://dds.cr.usgs.gov/srtm/version2_1/SRTM3/North_America/$hgt.zip"
            wget -N -c -P data "http://dds.cr.usgs.gov/srtm/version2_1/SRTM3/South_America/$hgt.zip"
        done

        cd data
        unzip '*.zip'
        rm *.zip
        cd ..

        osm2obj $1 $2 $3 $4 $5
    fi

    echo "meshlabserver -i ./data/$HASH_ID.obj -o ./data/clean.obj"
    meshlabserver -i ./data/$HASH_ID.obj -o ./data/clean.obj
    echo "mv ./data/clean.obj ./data/$HASH_ID.obj"
    mv ./data/clean.obj ./data/$HASH_ID.obj

    return
}

ode()
{
    HASH_ID=`echo "$1,$2,$3,$4" | md5sum | grep -Po "[^\ |\-]+"`

    if [[ -z $5 ]]
    then
        X1=-200
        Y1=-200
        Z1=1
        X2=200
        Y2=200
        Z2=2
        RES=2
    else
        REGION=(`echo $5 | grep -Po "\-?[0-9]+(\.[0-9]*)?"`)
        X1=${REGION[0]}
        Y1=${REGION[1]}
        Z1=${REGION[2]}
        X2=${REGION[3]}
        Y2=${REGION[4]}
        Z2=${REGION[5]}

        RES=(`echo $6 | grep -Po "[0-9]+(\.[0-9]*)?"`)
    fi

    CENTER=(`cat data/$HASH_ID.meta | grep CENTER: | grep -Po "[^:]+$"`)
    ZOOM=(`cat data/$HASH_ID.meta | grep ZOOM: | grep -Po "[^:]+$"`)
    HEIGHT=(`cat data/$HASH_ID.meta | grep HEIGHT: | grep -Po "[^:]+$"`)
    WIDTH=(`cat data/$HASH_ID.meta | grep WIDTH: | grep -Po "[^:]+$"`)
    SCALE=(`cat data/$HASH_ID.meta | grep SCALE: | grep -Po "[^:]+$"`)

    echo "python ode/main.py --file  `pwd`/data/$HASH_ID.obj --image `pwd`/data/$HASH_ID.jpeg --image_params $WIDTH $HEIGHT $SCALE --ops "data/gps-ops.txt" --center ${CENTER[0]} ${CENTER[1]} ${CENTER[2]} --scanFrom $X1 $Y1 $Z1 --scanTo $X2 $Y2 $Z2 --scanInc  $RES --folder data/$HASH_ID --dpi 500 --mode 1 "

    python ode/main.py --file  `pwd`/data/$HASH_ID.obj \
                       --image `pwd`/data/$HASH_ID.jpeg --image_params $WIDTH $HEIGHT $SCALE \
                       --ops "data/gps-ops.txt" \
                       --center ${CENTER[0]} ${CENTER[1]} ${CENTER[2]} \
                       --scanFrom $X1 $Y1 $Z1 \
                       --scanTo   $X2 $Y2 $Z2 \
                       --scanInc  $RES \
                       --folder data/$HASH_ID \
                       --dpi 500 \
                       --mode 1

}

satellite()
{
    HASH_ID=`echo "$1,$2,$3,$4" | md5sum | grep -Po "[^\ |\-]+"`

    KEY=AvQ2ulKY-NHkFI0owgmdlViXv5LVO03L59Antb2NMnhAOoT7IfCvvsi8KpPw4Uzl
    FMT=jpeg
    WIDTH=$5
    HEIGHT=$6 #`bc <<< $WIDTH*\($4-$2\)/\($3-$1\)`

    if [[ -z $5 ]]
    then
        WIDTH=900
        HEIGHT=834
    fi

    echo "wget -N -c -O ./data/$HASH_ID.jpeg  http://dev.virtualearth.net/REST/v1/Imagery/Map/Aerial?mapArea=$2,$1,$4,$3\&format=$FMT\&ms=$WIDTH,$HEIGHT\&key=$KEY"
    wget -N -c -O ./data/$HASH_ID.jpeg  http://dev.virtualearth.net/REST/v1/Imagery/Map/Aerial?mapArea=$2,$1,$4,$3\&format=$FMT\&ms=$WIDTH,$HEIGHT\&key=$KEY
    echo "wget -N -c -O ./data/$HASH_ID.x  http://dev.virtualearth.net/REST/v1/Imagery/Map/Aerial?mapArea=$2,$1,$4,$3\&format=$FMT\&ms=$WIDTH,$HEIGHT\&key=$KEY"
    wget -N -c -O ./data/$HASH_ID.x  http://dev.virtualearth.net/REST/v1/Imagery/Map/Aerial?mapArea=$2,$1,$4,$3\&format=$FMT\&ms=$WIDTH,$HEIGHT\&key=$KEY\&mmd=1

    SEGMENTS=20
    echo "wget -N -c -O ./data/$HASH_ID.xx http://dev.virtualearth.net/REST/v1/Elevation/Bounds?bounds=$2,$1,$4,$3\&rows=$SEGMENTS\&cols=$SEGMENTS\&key=$KEY"
    wget -N -c -O ./data/$HASH_ID.xx http://dev.virtualearth.net/REST/v1/Elevation/Bounds?bounds=$2,$1,$4,$3\&rows=$SEGMENTS\&cols=$SEGMENTS\&key=$KEY


    CENTER=(`cat data/$HASH_ID.x | grep -Po "mapCenter\"\:\{[^\}]+" | grep -Po "\[[^\]]+" | grep -Po "\-?[0-9]+\.[0-9]+"`)
    ALTITUDE=(`cat data/$HASH_ID.xx | grep -Po "elevations\"\:\[[^\]]+" | grep -Po "[0-9]+" | sort | head -1`)
    ZOOM=(`cat data/$HASH_ID.x | grep -Po "zoom\"\:\"[^\"]+" | grep -Po "[0-9]+"`)
    HEIGHT=(`cat data/$HASH_ID.x | grep -Po "imageHeight\"\:\"[^\"]+" | grep -Po "[0-9]+"`)
    WIDTH=(`cat data/$HASH_ID.x | grep -Po "imageWidth\"\:\"[^\"]+" | grep -Po "[0-9]+"`)

    SCALE=`python -c "import math; print 156543.04 * abs(math.cos(${CENTER[0]} * math.pi / 180)) / (2 ** $ZOOM)"`

    echo "CENTER: ${CENTER[0]} ${CENTER[1]} $ALTITUDE" > data/$HASH_ID.meta
    echo "QUAD: $1 $2 $3 $4" >> data/$HASH_ID.meta
    echo "ZOOM: $ZOOM"       >> data/$HASH_ID.meta
    echo "HEIGHT: $HEIGHT"   >> data/$HASH_ID.meta
    echo "WIDTH: $WIDTH"     >> data/$HASH_ID.meta
    echo "SCALE: $SCALE"     >> data/$HASH_ID.meta
    echo "DATE: `date`"      >> data/$HASH_ID.meta

    rm data/$HASH_ID.x*
}

simp()
{
	cat ./data/$1.osm | perl -0 -pe 's|<$2.*?</$2>|$&=~/$3/?"":$&|gse' > ./data/xxx.osm
    mv ./data/xxx.osm ./data/$1.osm
}

simplify()
{
    HASH_ID=`echo "$1,$2,$3,$4" | md5sum | grep -Po "[^\ |\-]+"`

    #simp $HASH_ID way highway
    #simp $HASH_ID way railway
    #simp $HASH_ID node highway
    #simp $HASH_ID node railway

    #    cat ./data/$HASH_ID.osm | perl -0 -pe 's|<way.*?</way>|$&=~/highway/?"":$&|gse' > ./data/xxx.osm
    #mv ./data/xxx.osm ./data/$HASH_ID.osm

    #cat ./data/$HASH_ID.osm | perl -0 -pe 's|<way.*?</way>|$&=~/railway/?"":$&|gse' > ./data/xxx.osm
    #mv ./data/xxx.osm ./data/$HASH_ID.osm

    #cat ./data/$1,$2,$3,$4.osm | perl -0 -pe 's|<way.*?</way>|$&=~/train/?"":$&|gse' > ./data/xxx.osm
    #mv ./data/xxx.osm ./data/$1,$2,$3,$4.osm

    #cat ./data/$1,$2,$3,$4.osm | perl -0 -pe 's|<node.*?</node>|$&=~/highway/?"":$&|gse' > ./data/xxx.osm
    #mv ./data/xxx.osm ./data/$1,$2,$3,$4.osm

    #cat ./data/$1,$2,$3,$4.osm | perl -0 -pe 's|<node.*?</node>|$&=~/railway/?"":$&|gse' > ./data/xxx.osm
    #mv ./data/xxx.osm ./data/$1,$2,$3,$4.osm

    #cat ./data/$1,$2,$3,$4.osm | perl -0 -pe 's|<node.*?</node>|$&=~/train/?"":$&|gse' > ./data/xxx.osm
    #mv ./data/xxx.osm ./data/$1,$2,$3,$4.osm

    #cat ./data/$1,$2,$3,$4.osm | perl -0 -pe 's|<relation.*?</relation>|$&=~/road/?"":$&|gse' > ./data/xxx.osm
    #mv ./data/xxx.osm ./data/$1,$2,$3,$4.osm

    #cat ./data/$1,$2,$3,$4.osm | perl -0 -pe 's|<relation.*?</relation>|$&=~/route/?"":$&|gse' > ./data/xxx.osm
    #mv ./data/xxx.osm ./data/$1,$2,$3,$4.osm

    #cat ./data/$1,$2,$3,$4.osm | perl -0 -pe 's|<relation.*?</relation>|$&=~/roundtrip/?"":$&|gse' > ./data/xxx.osm
    #mv ./data/xxx.osm ./data/$1,$2,$3,$4.osm

    return
}

case "$1" in
    "--grab")
        grab_osm $2 $3 $4 $5
        ;;
    "--osm2obj")
        osm2obj $2 $3 $4 $5 $6
        ;;
    "--ode")
        ode $2 $3 $4 $5 $6 $7
        ;;
    "--gps-ops")
        grab_gps_ops
        ;;
    "--satellite")
       satellite $2 $3 $4 $5
       ;;
    "--test")
        grab_osm 13.36488 52.50682 13.38111 52.51274
        grab_gps_ops
        satellite 13.36488 52.50682 13.38111 52.51274
        simplify 13.36488 52.50682 13.38111 52.51274
        osm2obj 13.36488 52.50682 13.38111 52.51274
        ode 13.36488 52.50682 13.38111 52.51274
        ;;
    "--make")
        grab_osm $2 $3 $4 $5
        grab_gps_ops
        satellite $2 $3 $4 $5
        simplify $2 $3 $4 $5
        osm2obj $2 $3 $4 $5 $6
        ode $2 $3 $4 $5
        ;;
    "--install")
        git clone https://github.com/tordanik/OSM2World
        cd OSM2World
        ant jar
        cd ..
        sudo apt-get install libode1 libode-dev python-pyvtk meshlab
        sudo pip install PyODE
        git clone https://github.com/andre-dietrich/odeViz
        cd odeViz
        sudo python setup.py install
        sudo python setup.py install
        cd ..
        mkdir data
        ;;
    "--clean")
        cd data
        ls * | xargs rm -rf
        cd ..
    ;;
    "--simplify")
        simplify $2 $3 $4 $5
    ;;
    "--osm2world")
        java -Djava.library.path=`pwd`/OSM2World/lp_solve/ux64 -Xmx2G -jar `pwd`/OSM2World/build/OSM2World.jar
    ;;
    "--help" | "-h" | *)
        echo "--help                                 - print this help"
        echo "--install                              - install all required libs and tools"
        echo "--grab x1 y1 x2 y2                     - grab osm file"
        echo "--gps-ops                              - grab gps-ops file"
        echo "--satellite x1 y1 x2 y2 (width height) - grab the satellite image from bing"
        echo "--simplify x1 y1 x2 y2                 - delete not required tags from osm"
        echo "--osm2obj x1 y1 x2 y2 (SRMT)           - convert the osm to obj"
        echo "--ode x1 y1 x2 y2 region(xyz) resolution    - load the 3d model and the satellite image to odeViz and scans reagion"
        echo "--make x1 y1 x2 y2                     - perform grab, satellite, simplify, osm2obj, ode at once with default parameters"
        echo "--test                                 - performes a make for 13.36488 52.50682 13.38111 52.51274"
        echo "--clean                                - delete all content from data"
        echo "--osm2world                            - start the osm2world tool"
        ;;
esac
