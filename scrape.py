#!/usr/bin/env python
import re
import os
import sys
import json
import mechanize
import subprocess
from getpass import *
from datetime import datetime
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

"""

class SCPDScraper:

    def __init__(self, prefs_file='prefs.json'):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.prefs = self.getPrefs(prefs_file)
        self.browser = mechanize.Browser()
        self.browser.addheaders = [('User-agent', 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6; en-us) AppleWebKit/531.9 (KHTML, like Gecko) Version/4.0.3 Safari/531.9')]
        self.browser.set_handle_robots(False)
        self.cached_cookie = ''
        self.cached_slphash = ''

    def getPrefs(self, filename):
        prefs_file = self.script_dir + '/' + filename
        if os.path.exists(prefs_file):
            json_str = open(prefs_file).read()
            return json.loads(json_str)
        else:
            print "Preferences file not found"
            print prefs_file
            sys.exit(1)


    def convertToMp4(self, wmv_file, mp4_file):
        print "Converting " + wmv_file + " to " + mp4_file
        os.system('HandBrakeCLI -i %s -o %s' % (wmv_file, mp4_file))
        os.system('rm -f %s' % wmv_file)

    #TODO: why is course_name here?
    def download(self, video_link, course_name):
        output_name = re.search(r"[\w]+[0-9]+[\w]?/[0-9]+[^/]+",video_link).group(0).replace("/","_").lower()
        output_wmv = output_name + ".wmv"
        output_mp4 = output_name + ".mp4"
        
        if os.path.exists(output_wmv) or os.path.exists(output_mp4):
            print "Already downloaded " + output_name
        else:
            print "Downloading " + output_name
            os.system("mimms -c %s %s" % (video_link, output_wmv))
            if self.prefs["convert_to_mp4"]:
                self.convertToMp4(output_wmv, output_mp4)
            print "Finished downloading " + output_name

    def downloadAllVideosInFile(self, link_file_name, course_name):
        link_file = open(link_file_name, 'r')
        print "Downloading video streams."
        for line in link_file:
            video_link = line.strip()
            self.download(video_link, course_name)
        link_file.close()
        print "Done!"

    def getUrlParams(self, link):
        link = link.replace("%22" ,"'")
        args = re.findall("'[^']*'", link)
        args = [s[1:-1] for s in args]
        x = {}
        x["collGuid"] = args[0]
        x["courseName"] = args[1]
        x["coGuid"] = args[2]
        x["lectureName"] = args[3]
        x["lectureDesc"] = args[4]
        x["desiredAuthType"] = args[5]
        x["playerType"] = args[6]
        return x

    def getCookieStr(self):
        cookiestr = ''
        for c in self.browser._ua_handlers["_cookies"].cookiejar:
            cookiestr += c.name + '=' + c.value + ';'
        return cookiestr

    # slphash is some weird auth hash for silverlight
    def getSlpHash(self, x, curl_filename='slphash.curl'):
        cookie = self.getCookieStr()

        # if the cookie is the same, we shouldn't need to get another slphash
        if cookie == self.cached_cookie:
            return self.cached_slphash

        # send a curl to the server to get the slphash
        curl_script = self.script_dir + '/' + curl_filename
        slphash = subprocess.check_output(['bash', curl_script, cookie, x['collGuid'], x['coGuid'], x['desiredAuthType']])
        slphash = re.findall('"[^"]*"', slphash)[1][1:-1]

        self.cached_cookie = cookie
        self.cached_slphash = slphash
        return slphash

    def getUrlForLink(self, link):
        x = self.getUrlParams(link)
        slphash = self.getSlpHash(x);

        url = 'http://myvideosv.stanford.edu/player/slplayer.aspx?'
        url += 'coll={0}&course={1}&co={2}&lecture={3}'.format(x["collGuid"], x["courseName"], x["coGuid"], x["lectureName"])
        if x["lectureDesc"] == "problem session":
            url += '&lectureType=ps'
        url += '&authtype={0}&slp={1}{2}'.format(x["desiredAuthType"], slphash, x["playerType"])
        return url

    def writeLinksToFile(self, link_file_name):
        # Build up a list of lectures
        print "Loading video links."
        links = []
        for link in self.browser.links(text="WMP"):
            links.append(self.getUrlForLink(link.url))
        # So we download the oldest ones first.
        links.reverse()
        print "Found %d links, getting video streams." % (len(links))

        link_file = open(link_file_name, 'w')
        for link in links:
            response = self.browser.open(link)
            soup = BeautifulSoup(response.read())
            video = soup.find('object', id='WMPlayer')['data']
            video = re.sub("http","mms",video)
            video = video.replace(' ', '%20') # remove spaces, they break urls
            print video
            link_file.write(video + '\n')
        link_file.close()

    def goToCourseDir(self, video_dir, course_name):
        course_dir = video_dir + '/' + course_name
        if not os.path.exists(course_dir):
            os.mkdir(course_dir)
        os.chdir(course_dir)

    def processCourse(self, course_name):
        link_file_name = course_name.replace(' ', '') + '_links.txt'

        self.goToCourseDir(self.prefs["download_directory"], course_name)
        self.writeLinksToFile(link_file_name)
        self.downloadAllVideosInFile(link_file_name, course_name);

    def navigateToCoursePage(self, course_name):
        # Open the course page for the title you're looking for
        try:
            self.browser.follow_link(text=course_name)
        except:
            print "Link Navagation Error"
            sys.exit(1)

    def goToCourseListPage(self):
        course_list_page = 'https://myvideosu.stanford.edu/oce/currentquarter.aspx'
        self.browser.open(course_list_page)
        assert self.browser.viewing_html()

        while not self.browser.geturl() == course_list_page:
            try:
                self.browser.select_form(name="login")
                self.browser["username"] = self.prefs["stanford_id"]
                self.browser["password"] = getpass()
                response = self.browser.submit()
            except mechanize._mechanize.FormNotFoundError:
                print 'Error logging in'
                sys.exit(1);
            except Exception:
                pass

            # Handle two-factor auth
            try:
                self.browser.select_form(name="login")
                self.browser["otp"] = '' #So it will fail if we're not on OTP page (we want to prompt for pwd again)
                self.browser["otp"] = raw_input("OTP: ");
                response = self.browser.submit()
            except Exception:
                pass

    def downloadAllCourses(self, course_names):
        print "Logging in to myvideosu.stanford.edu..."
        self.goToCourseListPage()
        for course_name in course_names:
            self.navigateToCoursePage(course_name)
            print "Downloading '" + course_name + "'..."
            self.processCourse(course_name)
            self.goToCourseListPage();

    def updateLastRun(self, filename='.lastrun'):
        lastrun_file = open(self.script_dir + '/' + filename, 'w')
        lastrun_file.write(datetime.now().strftime('%m-%d-%Y %H:%M:%S'));

    def scrape(self):
        if os.path.exists(self.prefs["download_directory"]):
            self.downloadAllCourses(self.prefs["courses"])
            self.updateLastRun()
        else:
            print 'Download directory "' + self.prefs["download_directory"] + '" does not exist'
            sys.exit(1)


def main():
    if (len(sys.argv) < 1):
        #print "Usage: ./scrape.py [Stanford ID] 'Interactive Computer Graphics' 'Programming Abstractions' ..."
        print "Usage: ./scrape.py"
    else:
        scraper = SCPDScraper()
        scraper.scrape()
        
if __name__ == '__main__':
    main()
