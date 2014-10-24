#!/bin/bash

# $1 is url and $2 is destination path
start_download() {
    echo "Getting $2"
    tmpfilename="$2.tmp"
    curl -s $1 > $2
    mv $tmpfilename $2
    echo "Finished downloading $2"
}

if [[ -n $1 ]]
then
    while read line
    do
        if [[ $line =~ .*\.mp4$ ]]
        then
            filename=$(echo $line | rev | sed s/\\/\.\*$// | rev)
            if [[ -a $filename ]]
            then
                echo "This file already exists: $filename"
            else
                start_download $line $filename &
            fi
        else
            echo "Invalid link: "$line
        fi
    done < $1
    wait
else
    echo "Usage: "$0" [link_file]"
fi
