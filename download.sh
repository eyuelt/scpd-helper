#!/bin/sh

if [[ -n $1 ]]
then
    while read line
    do
        if [[ $line =~ .*stanford.edu/videos/courses/.*\.mp4$ ]]
        then
            filename=$(echo $line | rev | sed s/\\/\.\*$// | rev)
            echo "Downloading video: '"$line"' and storing it in file '"$filename"'"
            curl -s $line > $filename &
        else
            echo "Invalid myvideosu link: "$line
        fi
    done < $1
else
    echo "Usage: "$0" [link_file]"
fi
