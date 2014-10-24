# SCPD Helper

Get the links to a course's lecture videos and then download them all in parallel.

Usage:
------
1. Login to the SCPD website in your browser and go to the course page for the course you want to download.
2. Copy the function in `getLinks.js` and run it in the javascript console in your browser.
3. An alert will pop up with the links for all of the course videos. Copy-paste this text into a textfile.
4. Run `./download.sh [textfile]`.

*Note: Since these videos are 720p and about an hour long, each lecture can be around 1GB in size. To get the 540p version instead, simply modify the function in `getLinks.js` by replacing `HiVideoDownloadUrl` with `LowVideoDownloadUrl`.*
