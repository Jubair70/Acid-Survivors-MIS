var days = ['Sun','Mon','Tue','Wed', 'Thu','Fri','Sat']; 

var Month = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
var week_period = ['W1','W2','W3','W4','W5','W6'];


function createChartSeries(type,jsonObj,container_name, chart_x_catag,legendShow){
    //console.log(JSON.stringify(jsonObj));
    var jsonArr = [];
    var arrLength = chart_x_catag.length;
    var tmpDataArr = [];
 /*  if(type==='column'){
        for(var i=0;i<arrLength;i++){
            tmpDataArr = Array.apply(null, Array(arrLength)).map(Number.prototype.valueOf,10);
            var keyGen = chart_x_catag[i].replace(/\s+/g, '_');
            tmpDataArr[i]= parseInt(jsonObj[keyGen]);
           jsonArr.push({
                name: chart_x_catag[i],
                data: tmpDataArr,

            });        
        };
   } else{*/
        for(var i=0;i<arrLength;i++){
            var keyGen = chart_x_catag[i].replace(/\s+/g, '_');
            var key = keyGen;
                tmpDataArr.push({
                    name: chart_x_catag[i],
                    y:parseInt(jsonObj[keyGen])
                });
                     
             };
             jsonArr.push({
                data: tmpDataArr,
                showInLegend: legendShow,
                colorByPoint: true,
             });
             tmpDataArr = [];
  // }
    return jsonArr;
}


function createWeeklyChartData(rawJson,data_id,container,param_data){
    jsonObj = rawJson; 
    var interval = param_data.int_time;
    var chartType = param_data.chart_type;
    var Title = 'Chart Data';
    var x_Axis = days;
    //console.log(JSON.stringify(rawJson));
    //console.log(data_id, rawJson,param_data.int_time);
    var processed_json = new Array(); 
    
    var currentDate = new Date();
    var series_val = [];
    
    if(jsonObj[0][data_id] == null){
        var x=document.getElementById(container);
        x.innerHTML = "No data to show for this time interval.."
       // alert(x.innerHTML);
    }else{
        var length = jsonObj[0][data_id].length;
        series_val.length = 0;
        switch (interval) {
            case 5:
            case 7:
                Title = 'Last 7 Days';
                series_val = Array.apply(null, Array(7)).map(Number.prototype.valueOf,0);    
            break;
            case 30:
                Title = 'Last 30 Days';
                x_Axis = [];
                var d = new Date();
                var x_catag = d.getDate() +' '+ Month[d.getMonth()];
                x_Axis.push(x_catag);
                for(var i=30;i>0;i=i-6){
                    d = new Date();
                    d.setDate(d.getDate()-i);  
                    x_catag = d.getDate()+' '+Month[d.getMonth()];
                    x_Axis.push(x_catag);  
                }
                
                series_val = Array.apply(null, Array(6)).map(Number.prototype.valueOf,0);
                break;
            case 60:
                Title = 'Last 60 Days';
                x_Axis = Month;
                series_val = Array.apply(null, Array(12)).map(Number.prototype.valueOf,0);
                break;
        }
        
        // Populate series
        for (i = 0; i < length; i++){
            var d = new Date(jsonObj[0][data_id][i]);
            //console.log(d.getWeekOfMonth()) ;
            if(interval == 7)
                series_val[d.getDay()]+= 1;
            if(interval == 30){

                series_val[d.getDay()]+= 1;
            }
                
            if(interval == 60)
                series_val[d.getMonth()]+= 1;
       
        }
        var processed_json = [];
        var jsondata = {}
        jsondata.name = container;
        jsondata.data = series_val;
        processed_json.push(jsondata);
        $("#"+container).empty();
        createChart(chartType,container,processed_json,Title,'Total No of Submission',x_Axis);
    }  
}

function createChart(type,container,processed_json,title,yAxis_title_text,xAxis_catag)
{    
     var options =   {
        chart: {
            type: type,
            renderTo: container
        },
        title: {
            text: title
        },
        xAxis: {
            categories: xAxis_catag
        },
         yAxis: {
                min: 0,
                title: {
                    text: yAxis_title_text

                }
            },
        plotOptions: {
            series: {
                dataLabels: {
                    enabled: true,
                    format: '{point.y:.1f}%'
                    
                }, point: {
                       events: {
                           click: function () {
                               alert('Category: ' + this.category + ', value: ' + this.y);
                           }
                       }
                   }
               },

               column: {
                stacking: 'normal',
                dataLabels: {
                    enabled: false,
                    color: (Highcharts.theme && Highcharts.theme.dataLabelsColor) || 'white',
                    style: {
                        textShadow: '0 0 3px black'
                    }
                }
            }
            },
            /*colors: [
                    '#ff0000',
                    '#00ff00',
                    '#0000ff'
                ],*/
            tooltip: {
                headerFormat: '<span style="font-size:10px">{point.key}: </span><table>',
                pointFormat: '<b>{point.y:.1f}%</b>',
                footerFormat: '',
                shared: true,
                useHTML: true
            },

        series: processed_json,
        /*[{
                
                name: container,
                data: processed_json,
                showInLegend: true,
                colorByPoint: true,
                
        }]*/

        exporting: {
            enabled: true
        },
    };
    chart = new Highcharts.Chart(options);
}

Date.prototype.getWeekOfMonth = function(exact) {
    var month = this.getMonth()
        , year = this.getFullYear()
        , firstWeekday = new Date(year, month, 1).getDay()
        , lastDateOfMonth = new Date(year, month + 1, 0).getDate()
        , offsetDate = this.getDate() + firstWeekday - 1
        , index = 1 // start index at 0 or 1, your choice
        , weeksInMonth = index + Math.ceil((lastDateOfMonth + firstWeekday - 7) / 7)
        , week = index + Math.floor(offsetDate / 7)
    ;
    if (exact || week < 2 + index) return week;
    return week === weeksInMonth ? index + 5 : week;
};


