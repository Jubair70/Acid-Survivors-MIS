var days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
var series_val = [];

function createChart(container, title, chart_type, XaxisCatagory, YaxisCatagory, processed_json) {

    //chart.inverted = true;
    if (typeof chart_type === 'undefined') {
        chart_type = 'column';
    }


    var options = {
        chart: {
            type: chart_type,
            renderTo: container,
             zoomType: 'x',
            options3d: {
                enabled: true,
                alpha: 10,
                beta: 25,
                depth: 70
            }

        },
        title: {
            text: title
        },
        xAxis: {
            categories: XaxisCatagory
        },
        yAxis: {
            categories: YaxisCatagory,
            min: 0,
            max: 10,
            title: {
                text: 'Submission per day (No.)'

            },
            stackLabels: {
                enabled: true,
                style: {
                    fontWeight: 'bold',
                    color: (Highcharts.theme && Highcharts.theme.textColor) || 'gray'
                }
            }
        },
        plotOptions: {
            column: {
                depth: 25
            },
            series: {
                stacking: 'normal',
                dataLabels: {
                    enabled: false,
                    style: {
                        textShadow: '0 0 3px black'
                    }
                },
                point: {
                    events: {
                        click: function() {
                            alert('Category: ' + this.category + ', value: ' + this.y);
                        }
                    }
                }
            }

        },
        tooltip: {
            headerFormat: '<span style="font-size:10px">{point.key}</span><table>',
            pointFormat: '<tr><td style="color:{series.color};padding:0">{series.name}: </td>' +
                '<td style="padding:0"><b>{point.y:.1f} </b></td></tr>',
            footerFormat: '</table>',
            shared: true,
            useHTML: true
        },
        tooltip: {
            headerFormat: '<b>{point.x}</b><br/>',
            pointFormat: '{series.name}: {point.y}<br/>Total: {point.stackTotal}'
        },

        series: [{
            name: container,
            data: processed_json
        }, {
            name: container,
            data: processed_json,
        },
        {
            name: container,
            data: processed_json,
        },
        {
            name: container,
            data: processed_json,
        }]

        /* series:[{
            name: 'John',
            data: [5, 3, 4, 7, 2]
        }, {
            name: 'Jane',
            data: [2, 2, 3, 2, 1]
        }, {
            name: 'Joe',
            data: [3, 4, 4, 2, 5]
        }]*/

    };

    chart = new Highcharts.Chart(options);

}


function createTableRow(dataObj, submission, jsondata,data_type) {
    var title = 'Changing title';
    var type = 'column'; //area,spline, column, bar, pie(not fully)
    var xaxisCatagory = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    var xaxisCatagory2 = ['day1', 'day2', 'day3', 'day3'];
    console.log(jsondata);
    var jsonObj = JSON.parse(jsondata);

    var processed_json = new Array();

    series_val.length = 0;
    series_val = Array.apply(null, Array(7)).map(Number.prototype.valueOf, 0);
    // Populate series
    for (i = 0; i < jsonObj[dataObj].length; i++) {
        if(data_type==='date'){
            var d = new Date(jsonObj[dataObj][i]);    
            xaxisCatagory[d.getDay()] = jsonObj[dataObj][i];
            series_val[d.getDay()] += 1;
            console.log('date: ' + d);
        }else{
            xaxisCatagory[i] = jsonObj[dataObj][i];
            series_val[i] += 1;
        }

    }
    console.log(series_val);

    var table = $('#tg-xY4Sf');
    var spDataTableRow = $('<tr></tr>');
    var spTableRowData = $('<td class="tg-yw4l" id="' + dataObj + '" style="width:300px; min-width: 290px; height: 180px; margin: 0 auto"></td></td>');
    spDataTableRow.append(spTableRowData);
    table.append(spDataTableRow);
    createChart(dataObj, title, type, xaxisCatagory, null, series_val);
}