class Timeline {
    constructor(container, minYr, maxYr, items) {
        this.container = document.getElementById(container);
        this.minYr = minYr;
        this.maxYr = maxYr;
        this.items = items;
        // console.log(this.container);
        // console.log(this.minYr);
        // console.log(this.maxYr);
        // console.log(this.items);
        this.drawTimeline();
        this.drawItems();
    }

    drawTimeline() {
        var html = [];
        for(var i = this.minYr; i <= this.maxYr; i++) {  // 1-len b/c want 18-65 instead of 0-64
            html.push("<section>" + i + "</section>");
        }
        this.container.classList.add("timesheet");
        this.container.classList.add("color-scheme-default");

        // this.container.class = "timesheet ";
        this.container.innerHTML = '<div class="scale scrollmenu">' + html.join("") + "</div>"
    }

    drawItems() {
        var html = [];
        for(var i = 0; i < this.items.length; i++) {
            var curItem = this.items[i];
            var yrWidth = 59;  // px
            var margin_left = yrWidth * (curItem.start - this.minYr);
            var width = margin_left + (yrWidth * (curItem.end - curItem.start));
            var ageSpan = (curItem.start != curItem.end) ? curItem.start + "-" + curItem.end : curItem.start;  // start and end may be same age 
            var text = curItem.text;
            var item = ['<span style="margin-left: ' + margin_left + "px; width: " + width + 'px;" class="bubble bubble-' + (curItem.color || "default"), '<span class="date">' + ageSpan + "</span> ", '<span class="label">' + text + "</span>"].join("");
            html.push("<li>" + item + "</li>")
        }

        // for (var html = [], widthMonth = this.container.querySelector(".scale section").offsetWidth, n = 0, m = this.data.length; m > n; n++) {
        //     var cur = this.data[n];
        //     console.log(cur.start);
        //     var yrWidth = 59;  // px
        //     var curYr = cur.start - 1900;
        //     var margin_left = yrWidth * (curYr - 18);
        //     var bubble = new TimesheetBubble(widthMonth, this.year.min, cur.start, cur.end);
        //     var line = ['<span style="margin-left: ' + margin_left + "px; width: " + 200 + 'px;" class="bubble bubble-' + (cur.type || "default") + '" data-duration="' + (cur.end ? Math.round((cur.end - cur.start) / 1e3 / 60 / 60 / 24 / 39) : "") + '"></span>', '<span class="date">' + bubble.getDateLabel() + "</span> ", '<span class="label">' + cur.label + "</span>"].join("");
        //     html.push("<li>" + line + "</li>")  // bubble.getStartOffset()  bubble.getWidth()
        // }
        // this.container.innerHTML += '<ul class="data">' + html.join("") + "</ul>"
    }
}

//     Timesheet.prototype.drawSections = function() {
//         for (var html = [], c = this.year.min; c <= this.year.max; c++) html.push("<section>" + (parseInt(c) - 1900) + "</section>");
//         this.container.className = "timesheet color-scheme-default", this.container.innerHTML = '<div class="scale">' + html.join("") + "</div>"
//     },
// }