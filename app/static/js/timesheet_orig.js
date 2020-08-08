! function() {
    "use strict";
    var Bubble = function(wMonth, min, start, end) {
        this.min = min, 
        this.start = start, 
        this.end = end
        this.widthMonth = wMonth
    };
    Bubble.prototype.formatMonth = function(num) {
        return num = parseInt(num, 10), num >= 10 ? num : "0" + num
    }, Bubble.prototype.getStartOffset = function() {
        return this.widthMonth / 12 * (12 * (this.start.getFullYear() - this.min) + this.start.getMonth())
    }, Bubble.prototype.getFullYears = function() {
        return (this.end && this.end.getFullYear() || this.start.getFullYear()) - this.start.getFullYear()
    }, Bubble.prototype.getMonths = function() {
        var fullYears = this.getFullYears(),
            months = 0;
        return this.end ? this.end.hasMonth ? (months += this.end.getMonth() + 1, months += 12 - (this.start.hasMonth ? this.start.getMonth() : 0), months += 12 * (fullYears - 1)) : (months += 12 - (this.start.hasMonth ? this.start.getMonth() : 0), months += 12 * (fullYears - 1 > 0 ? fullYears - 1 : 0)) : months += this.start.hasMonth ? 1 : 12, months
    }, Bubble.prototype.getWidth = function() {
        return this.widthMonth / 12 * this.getMonths()
    }, Bubble.prototype.getDateLabel = function() {
        return [(this.start.hasMonth ? this.formatMonth(this.start.getMonth() + 1) + "/" : "") + this.start.getFullYear(), this.end ? "-" + ((this.end.hasMonth ? this.formatMonth(this.end.getMonth() + 1) + "/" : "") + this.end.getFullYear()) : ""].join("")
    }, 
    window.TimesheetBubble = Bubble
}(),
function() {
    "use strict";
    var Timesheet = function(container, min, max, data) {
        this.data = [], this.year = {
            min: min,
            max: max
        }, this.parse(data || []), "undefined" != typeof document && (this.container = "string" == typeof container ? document.querySelector("#" + container) : container, this.drawSections(), this.insertData())
    };
    Timesheet.prototype.insertData = function() { 
        for (var html = [], widthMonth = this.container.querySelector(".scale section").offsetWidth, n = 0, m = this.data.length; m > n; n++) {
            var cur = this.data[n];
            console.log(cur.start);
            var yrWidth = 59;  // px
            var curYr = cur.start - 1900;
            var margin_left = yrWidth * (curYr - 18);
            var bubble = new TimesheetBubble(widthMonth, this.year.min, cur.start, cur.end);
            var line = ['<span style="margin-left: ' + margin_left + "px; width: " + 200 + 'px;" class="bubble bubble-' + (cur.type || "default") + '" data-duration="' + (cur.end ? Math.round((cur.end - cur.start) / 1e3 / 60 / 60 / 24 / 39) : "") + '"></span>', '<span class="date">' + bubble.getDateLabel() + "</span> ", '<span class="label">' + cur.label + "</span>"].join("");
            html.push("<li>" + line + "</li>")  // bubble.getStartOffset()  bubble.getWidth()
        }
        this.container.innerHTML += '<ul class="data">' + html.join("") + "</ul>"
    }, 
    Timesheet.prototype.drawSections = function() {
        for (var html = [], c = this.year.min; c <= this.year.max; c++) html.push("<section>" + (parseInt(c) - 1900) + "</section>");
        this.container.className = "timesheet color-scheme-default", this.container.innerHTML = '<div class="scale">' + html.join("") + "</div>"
    }, 
    Timesheet.prototype.parseDate = function(date) {
        return -1 === date.indexOf("/") ? (date = new Date(parseInt(date, 10), 0, 1), date.hasMonth = !1) : (date = date.split("/"), date = new Date(parseInt(date[1], 10), parseInt(date[0], 10) - 1, 1), date.hasMonth = !0), date
    }, 
    Timesheet.prototype.parse = function(data) {
        for (var n = 0, m = data.length; m > n; n++) {
            var beg = this.parseDate(data[n][0]),
                end = 4 === data[n].length ? this.parseDate(data[n][1]) : null,
                lbl = 4 === data[n].length ? data[n][2] : data[n][1],
                cat = data[n][3] || "default";
            beg.getFullYear() < this.year.min && (this.year.min = beg.getFullYear()), end && end.getFullYear() > this.year.max ? this.year.max = end.getFullYear() : beg.getFullYear() > this.year.max && (this.year.max = beg.getFullYear()), this.data.push({
                start: beg,
                end: end,
                label: lbl,
                type: cat
            })
        }
    }, 
    window.Timesheet = Timesheet
}();