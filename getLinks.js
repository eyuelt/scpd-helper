console.log("✋ Don't run this script. See comment in source.");
if (process) process.exit();

/* Usage:
 * ------
 * 1. Go to the course page for the course you want to download.
 * 2. Copy the function below and paste it into the browser console.
 * 3. The links to all of the lectures will be displayed in an alert.
 */

(function() {
    var coursesBox = $('#course-sessions');
    var scope = angular.element(coursesBox).scope();
    var weeks = scope.courseDetail.CourseWeek;
    var lectures = weeks.reduce(function(lectures, week) {
        lectures = lectures.concat(week.Lectures);
        return lectures;
    }, []);
    lectures = lectures.reduce(function(lectures, lecture) {
        var lec = {};
        lec.date = lecture.LectureDate;
        lec.url = lecture.HiVideoDownloadUrl;
        lectures.push(lec);
        return lectures;
    }, []);
    var links = lectures.reduce(function(str, lecture) {
        if (!lecture.url) return str;
        return str + lecture.url + "\n";
    }, "");
    console.log(lectures);
    alert(links);
})();
