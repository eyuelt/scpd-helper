#!/usr/bin/env python
import re
import os
import sys
import json
from getpass import *
from datetime import datetime
from mechanize import Browser
from BeautifulSoup import BeautifulSoup

"""

This program downloads scpd videos for a given class in the order
that they happened as a wmv, then converts them to a mp4. Each time 
the script is run, it will update to download all of the undownloaded
videos. 

This script is modified from the one by Jeremy Keeshin (https://github.com/jkeesh),
which itself was modified from the one by Ben Newhouse (https://github.com/newhouseb).

Unfortunately, there are lots of dependencies to get it up and running
1. Handbrake CLI, for converting to mp4: http://handbrake.fr/downloads2.php
2. BeautifulSoup for parsing: http://www.crummy.com/software/BeautifulSoup/
3. Mechanize for emulating a browser, http://wwwsearch.sourceforge.net/mechanize/

Usage: python scrape.py [Stanford ID] "Interactive Computer Graphics"

The way I use it is to keep a folder of videos, and once I have watched them, move them
into a subfolder called watched. So it also wont redownload files that are in a subfolder
called watched.


"""

def convertToMp4(wmv_file, mp4_file):
    print "Converting " + wmv_file + " to " + mp4_file
    os.system('HandBrakeCLI -i %s -o %s' % (wmv_file, mp4_file))
    os.system('rm -f %s' % wmv_file)

def download(video_link, courseName):
    output_name = re.search(r"[a-z]+[0-9]+[a-z]?/[0-9]+",video_link).group(0).replace("/","_")
    output_wmv = output_name + ".wmv"
    output_mp4 = output_name + ".mp4"
    
    if os.path.exists(output_wmv) or os.path.exists(output_mp4):
        print "Already downloaded " + output_name
    else:
        print "Downloading " + output_name
        os.system("mimms -c %s %s" % (video_link, output_wmv))
        # convertToMp4(output_wmv, output_mp4)
        print "Finished downloading " + output_name

def downloadAllVideosInFile(link_file_name, courseName):
    link_file = open(link_file_name, 'r')
    print "Downloading video streams."
    for line in link_file:
        video_link = line.strip()
        download(video_link, courseName)
    link_file.close()
    print "Done!"

def writeLinksToFile(browser, link_file_name):
    # Build up a list of lectures
    print "Loading video links."
    links = []
    for link in browser.links(text="WMP"):
        links.append(re.search(r"'(.*)'",link.url).group(1))
    # So we download the oldest ones first.
    links.reverse()
    print "Found %d links, getting video streams." % (len(links))

    link_file = open(link_file_name, 'w')
    for link in links:
        response = browser.open(link)
        soup = BeautifulSoup(response.read())
        video = soup.find('object', id='WMPlayer')['data']
        video = re.sub("http","mms",video)
        video = video.replace(' ', '%20') # remove spaces, they break urls
        print video
        link_file.write(video + '\n')
    link_file.close()

def loginAndGoToCoursePage(browser, username, password, courseName):
    browser.addheaders = [('User-agent', 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6; en-us) AppleWebKit/531.9 (KHTML, like Gecko) Version/4.0.3 Safari/531.9')]
    browser.set_handle_robots(False)
    browser.open("https://myvideosu.stanford.edu/oce/currentquarter.aspx")
    assert browser.viewing_html()
    browser.select_form(name="login")
    browser["username"] = username
    browser["password"] = password
    response = browser.submit()

    # Handle two-factor auth
    try:
        browser.select_form(name="login")
        browser["otp"] = raw_input("OTP: ");
        response = browser.submit()
    except:
        pass

    # Open the course page for the title you're looking for
    print "Logging in to myvideosu.stanford.edu..."
    try:
        response = browser.follow_link(text=courseName)
    except:
        print "Login Error: username, otp, password, or courseName likely malformed"
        sys.exit(1)
    #print response.read()
    print "Logged in, going to course link."

def goToCourseDir(video_dir, courseName):
    courseDir = video_dir + '/' + courseName
    if not os.path.exists(courseDir):
        os.mkdir(courseDir)
    os.chdir(courseDir)

def processCourse(prefs, courseName, password):
    br = Browser()
    link_file_name = courseName.replace(' ', '') + '_links.txt'

    goToCourseDir(prefs["download_directory"], courseName)
    loginAndGoToCoursePage(br, prefs["stanford_id"], password, courseName)
    writeLinksToFile(br, link_file_name)
    downloadAllVideosInFile(link_file_name, courseName);

def downloadAllCourses(prefs, courseNames):
    password = getpass()
    for courseName in courseNames:
        print "Downloading '" + courseName + "'..."
        processCourse(prefs, courseName, password)

def updateLastRun(script_dir, filename='.lastrun'):
    file = open(script_dir + '/' + filename, 'w')
    file.write(datetime.now().strftime('%m-%d-%Y %H:%M:%S'));

def getPrefs(script_dir, filename='prefs.json'):
    prefs_file = script_dir + '/' + filename
    if os.path.exists(prefs_file):
        json_str = open(prefs_file).read()
        return json.loads(json_str)
    else:
        print "Preferences file not found"
        print prefs_file
        sys.exit(1)

def main():
    if (len(sys.argv) < 1):
        #print "Usage: ./scrape.py [Stanford ID] 'Interactive Computer Graphics' 'Programming Abstractions' ..."
        print "Usage: ./scrape.py"
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        prefs = getPrefs(script_dir)
        if os.path.exists(prefs["download_directory"]):
            downloadAllCourses(prefs, prefs["courses"])
        else:
            print 'Download directory "' + prefs["download_directory"] + '" does not exist'
            sys.exit(1)
        updateLastRun(script_dir)

if __name__ == '__main__':
    main();
