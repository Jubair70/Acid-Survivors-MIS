


/***
 * Dropdown ELEMENT CREATE
 * @param element  --New created element id field
 * @param parent_div_id  -- parent div of new elements
 * @param control_name   -- name field of control
 * @param control_label -- visible label
 * @param jsondata  --json having id and name
 *
 * @author persia
 */
function dropdownControlCreate(element,parent_div_id,control_name, control_label, has_cascaded_element,jsondata, appearance) {
    var col_md=12;
    if('col_md'  in appearance)
            col_md=appearance['col_md'];
    var wrapper_class=""
    if('wrapper_class'  in appearance)
            wrapper_class=appearance['wrapper_class'];
    var start_wrapper='<div class ="  "> <div class ="col-md-'+col_md+' '+wrapper_class+' " >';
    var end_wrapper = '</div></div>';
    var label='<label>'+control_label+'</label>';
    var dropdown_html=start_wrapper+label+'<select style="width:100%" id="'+element+'" name="'+control_name+'" class="form-control" onchange="'+has_cascaded_element+'"> <option value="">Select</option>';
    if(jsondata){
        for (var i = 0; i < jsondata.length; i++) {
            dropdown_html += '<option value="'+jsondata[i].id+'">'+jsondata[i].name+'</option>';
        }
    }
    dropdown_html+='</select>'+end_wrapper;
    $("#"+parent_div_id).append(dropdown_html);
} //END of checkboxControlCreate



/***
 * Button (Submit Type) CREATE
 * @param element  --New created element id field
 * @param parent_div_id  -- parent div of new elements
 * @param control_label -- visible label
 *
 * @author persia
 */
function buttonControlCreate(element,parent_div_id, control_label) {
    var start_wrapper='<div class="mp_submit" ><div class ="col-md-4" >  ';
    var end_wrapper = '</div></div>';
    var button_html=start_wrapper+'<input id="'+element+'" type="submit" class="btn btn-primary"  value="'+control_label+'"     >'+end_wrapper;
    $("#"+parent_div_id).append(button_html);
} //END of checkboxControlCreate





/***
 * Multiple Select ELEMENT CREATE
 * @param element  --New created element id field
 * @param parent_div_id  -- parent div of new elements
 * @param control_name   -- name field of control
 * @param control_label -- visible label
 * @param jsondata  --json having id and name
 *
 * @author persia
 */
function multipleSelectControlCreate(element,parent_div_id,control_name, control_label,has_cascaded_element, jsondata,appearance) {
    if(jsondata==null){
        console.log(control_label+" element cannot be created -mpower");
        return;
    }
    var col_md=12;
    if('col_md'  in appearance)
            col_md=appearance['col_md'];
    var wrapper_class=""
    if('wrapper_class'  in appearance)
            wrapper_class=appearance['wrapper_class'];
    var start_wrapper='<div class ="  "> <div class ="col-md-'+col_md+' '+wrapper_class+'" >';
    var end_wrapper = '</div></div>';
    var label='<label class="control-label">'+control_label+'</label> <div  >';
    var multiple_select_html=start_wrapper+label+'<select multiple="multiple"   onchange="'+has_cascaded_element+'" id="'+element+'" name="'+control_name+'" class="form-control">';
    for (var i = 0; i < jsondata.length; i++) {
        multiple_select_html += '<option value="'+jsondata[i].id+'">'+jsondata[i].name+'</option>';
    }
    multiple_select_html+='</select></div>'+end_wrapper;
    $("#"+parent_div_id).append(multiple_select_html);

    handleMultipleSelect(element);
} //END of multipleSelectControlCreate



/***
 * CHECKBOX ELEMENT CREATE
 * @param element  --New created element class field
 * @param parent_div_id  -- parent div of new elements
 * @param control_name   -- name field of control
 * @param control_label -- visible label
 * @param jsondata  --json having id and name
 *
 * @author persia
 */
function checkboxControlCreate(element,parent_div_id,control_name, control_label, jsondata) {
    var start_wrapper='<div class ="controls  "> <div class ="form-group" >';
    var end_wrapper = '</div></div>';
    var label='<label>'+control_label+'</label>';
    var checkbox_html=start_wrapper+label+'<div class="checkbox-list">';
    for (var i = 0; i < jsondata.length; i++) {
        checkbox_html += '<label><input class="'+element+'" type="checkbox" name="'+control_name+'" value="'+jsondata[i].id+'">'+jsondata[i].name+'</label>';
    }
    checkbox_html+='</div>'+end_wrapper;
    $("#"+parent_div_id).append(checkbox_html);
} //END of checkboxControlCreate





/***
 * Radio button ELEMENT CREATE
 * @param element  --New created element class field
 * @param parent_div_id  -- parent div of new elements
 * @param control_name   -- name field of control
 * @param control_label -- visible label
 * @param jsondata  --json having id and name
 *
 * @author persia
 */
function radioControlCreate(element,parent_div_id,control_name, control_label, jsondata) {
    var start_wrapper='<div class ="controls  "> <div class ="form-group" >';
    var end_wrapper = '</div></div>';
    var label='<label>'+control_label+'</label>';
    var radio_html=start_wrapper+label+'<div class="checkbox-list">';
    for (var i = 0; i < jsondata.length; i++) {
        radio_html += '<label><input class="'+element+'" type="radio" name="'+control_name+'" value="'+jsondata[i].id+'">'+jsondata[i].name+'</label>';
    }
    radio_html+='</div>'+end_wrapper;
    $("#"+parent_div_id).append(radio_html);
} //END of radioControlCreate




/***
 * Date Field CREATE
 * @param element  --New created element class field
 * @param parent_div_id  -- parent div of new elements
 * @param control_name   -- name field of control
 * @param control_label -- visible label
 * @param initialdate  --initial date
 *
 * @author persia
 */
function dateControlCreate(element,parent_div_id,control_name, control_label, appearance_json, initialdate) {

    var start_wrapper='<div class ="controls  "> <div class ="col-md-12" > ';
    var end_wrapper = '</div></div>';
    var label='<label>'+control_label+'</label>';
    var date_input_html=start_wrapper+label+'<div class="input-group input-medium date date-picker" >';
    date_input_html +='<input type="text" id="'+element+'" name="'+control_name+'" class="form-control"   readonly /> ';
    date_input_html+='<span class="input-group-btn"></span><button class="btn default" type="button"><i class="fa fa-calendar"></i></button> </span>'+end_wrapper;
    $("#"+parent_div_id).append(date_input_html);
    handleDatePickers(appearance_json);
} //END of radioControlCreate



/***
 * TEXT Input Field CREATE
 * @param element  --New created element class field
 * @param parent_div_id  -- parent div of new elements
 * @param control_name   -- name field of control
 * @param control_label -- visible label
 * @param initialvalue  --initial value
 *
 * @author persia
 */
function textinputControlCreate(element,parent_div_id,control_name, control_label, initialvalue) {
    var start_wrapper='<div class ="controls  "> <div class ="form-group" > ';
    var end_wrapper = '</div></div>';
    var label='<label>'+control_label+'</label>';
    var text_input_html=start_wrapper+label;
    text_input_html +='<input type="text" id="'+element+'" name="'+control_name+'" class="form-control" value="'+initialvalue+'" /> '+end_wrapper;
    $("#"+parent_div_id).append(text_input_html);
    //handleDatePickers();
} //END of textinputControlCreate





/**
 * Bootstrap Datepicker Function
 * @param element
 *
 * @persia
 */
var handleDatePickers = function (appearance_json) {
        //rtl: App.isRTL(),
        appearance_json["autoclose"]=true;
        if (jQuery().datepicker) {
            $('.date-picker').datepicker(appearance_json);
            $('body').removeClass("modal-open"); // fix bug when inline picker is used in modal
        }
 } // End of handleDatePickers


/**
 * Bootstrap Multiple Select Function
 * @param element
 *
 * @persia
 */
var handleMultipleSelect = function (element) {
        $("#"+element).multiselect({
            enableFiltering: true,
            //filterBehavior: 'value',
            maxHeight: 200,
            numberDisplayed: 1,
            includeSelectAllOption: true,
            buttonWidth: '100%'
        });
 } // End of handleDatePickers


function onChangeElement(control_id,changed_val) {
    $.ajax({
        type: 'POST',
        url: '/dashboard/on_change_element/',
        data: {'control_id': control_id , 'changed_val':changed_val},
        beforeSend: function() {
        },
        success: function(data) {
            $('#'+data.element).find('option').remove();//.append('<option value="">Select</option>);
            dropdown_html='<option value="">Select</option>' ;
            jsondata=JSON.parse(data.jsondata);
            if(jsondata){
                for (var i = 0; i < jsondata.length; i++) {
                    dropdown_html += '<option value="'+jsondata[i].id+'">'+jsondata[i].name+'</option>';
                }
             }
             $('#'+data.element).append(dropdown_html);
        },
        error: function(data) {
        }
    });
} //END of onChangeElement


function onChangeMultipleSelect(control_id,changed_val) {

     $.ajaxSetup({
    beforeSend: function(xhr, settings) {
            function getCookie(name) {
                var cookieValue = null;
                if (document.cookie && document.cookie != '') {
                    var cookies = document.cookie.split(';');
                    for (var i = 0; i < cookies.length; i++) {
                        var cookie = jQuery.trim(cookies[i]);
                        // Does this cookie string begin with the name we want?
                        if (cookie.substring(0, name.length + 1) == (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }
            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        }
    });


    $.ajax({
        type: 'POST',
        url: '/dashboard/on_change_multiple_select/',
        data: {'control_id': control_id , 'changed_val':changed_val},
        beforeSend: function() {
        },
        success: function(data) {
            //$('#'+data.element).multiselect('destroy');
            jsondata=JSON.parse(data.jsondata);
            console.log("DELETED");
            $('#'+data.element +"  option").remove();
            var multiple_select_html=''//'<option value="">Select</option>' ;
            if(jsondata){
                for (var i = 0; i < jsondata.length; i++) {
                    multiple_select_html += '<option value="'+jsondata[i].id+'">'+jsondata[i].name+'</option>';
                }
             }
            $('#'+data.element).append(multiple_select_html);
            //$('#'+data.element).multiselect('refresh');
            $('#'+data.element).multiselect('rebuild');
            //handleMultipleSelect(data.element);

        },
        error: function(data) {
        }
    });
} //END of onChangeElement







/**
* Asynchronous request For Chart generation
* @author persia
**/
function mpowerRequestForChart(post_url, element, chart_object, filtering) {

    $.ajaxSetup({
    beforeSend: function(xhr, settings) {
            function getCookie(name) {
                var cookieValue = null;
                if (document.cookie && document.cookie != '') {
                    var cookies = document.cookie.split(';');
                    for (var i = 0; i < cookies.length; i++) {
                        var cookie = jQuery.trim(cookies[i]);
                        // Does this cookie string begin with the name we want?
                        if (cookie.substring(0, name.length + 1) == (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }
            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        }
    });


    $.ajax({
        type: 'POST',
        url: post_url,
        data: filtering,
        beforeSend: function() {
            $(element).html("Please Wait...loading....");
        },
        success: function(data) {
            chart_object['dataset'] = data;
            mPowerChartGeneration(chart_object);
        },
        error: function(data) {
            $(element).html("Error occurred! Please reload.");
        }
    });
} // END of mpowerRequestForChart


/**
 * Chart Generation Function
 * @author persia
 * @param obj -> containing all properties including dataset
 */
function mPowerChartGeneration(obj) {

        //All Variable Declaration
        var divId,chartType,stackLabelEnabled,plotColumnDatalabelEnabled,stackLabelEnabled,chart_title,colorByPoint,colors,stacking,new_yAxis,legend_enabled,dataLabel,tooltip_text;

        var yAxis1_title,yAxis2_title;
        //**Exploring Chart Properties from object**

	

        //Mandatory properties
        dataset = obj['dataset'];
        divId=obj['element'];
        chartType=obj['chartType'];

        //Optional properties
        if('title'  in obj)
            chart_title=obj['title'];
        else chart_title=false;

        if('stackLabelEnabled'  in obj)
            stackLabelEnabled=obj['stackLabelEnabled'];
        else stackLabelEnabled=false;

        if('plotColumnDatalabelEnabled'  in obj)
            plotColumnDatalabelEnabled=obj['plotColumnDatalabelEnabled'];
        else plotColumnDatalabelEnabled=false;

        if('stackLabelEnabled'  in obj)
            chartType=obj['stackLabelEnabled'];
        else stackLabelEnabled=false;

        if('colorByPoint'  in obj)
            colorByPoint=obj['colorByPoint'];
        else colorByPoint=false;


        if('legend_enabled'  in obj)
            legend_enabled=obj['legend_enabled'];
        else legend_enabled=true;

        if('yAxis1_title'  in obj)
            yAxis1_title=obj['yAxis1_title'];
        else yAxis1_title="";


        if('yAxis2_title'  in obj)
            yAxis2_title=obj['yAxis2_title'];
        else yAxis2_title="";

        if('colors'  in obj)
            colors=obj['colors'];
        else colors=['#058DC7', '#50B432', '#ED561B', '#DDDF00', '#24CBE5', '#64E572',
                     '#FF9655', '#FFF263', '#6AF9C4'];


        if('stacking'  in obj)
            stacking=obj['stacking'];
        else stacking=null;

        if('yAxis'  in obj)
            new_yAxis=obj['yAxis'];
        else new_yAxis=null;

	if('dataLabel'  in obj)
            dataLabel=obj['dataLabel'];
        else dataLabel=false;




        /**************Customized HighCharts Theme**************/
        Highcharts.theme = {
            colors: colors,
            chart: {
                backgroundColor: {
                    linearGradient: [0, 0, 500, 500],
                    stops: [
                        [0, 'rgb(255, 255, 255)'],
                        [1, 'rgb(240, 240, 255)']
                    ]
                },
            },
            title: {
                style: {
                    color: '#000',
                    font: 'bold 16px "Trebuchet MS", Verdana, sans-serif'
                }
            },
            subtitle: {
                style: {
                    color: '#666666',
                    font: 'bold 12px "Trebuchet MS", Verdana, sans-serif'
                }
            },

            legend: {
                itemStyle: {
                    font: '9pt Trebuchet MS, Verdana, sans-serif',
                    color: 'black'
                },
                itemHoverStyle:{
                    color: 'gray'
                }
            },
            responsive: {
                rules: [{
                    condition: {
                        //maxWidth: 500
                    },
                    chartOptions: {
                        legend: {
                            align: 'center',
                            verticalAlign: 'bottom',
                            layout: 'horizontal'
                        },
                        yAxis: {
                            labels: {
                                align: 'left',
                                x: 0,
                                y: -5
                            },
                            title: {
                                text: null
                            }
                        },
                        subtitle: {
                            text: null
                        },
                        credits: {
                            enabled: false
                        }
                    }
                }]
            }
        };

        /*Highcharts.setOptions({
            chart: {
                backgroundColor: {
                    linearGradient: [0, 0, 500, 500],
                    stops: [
                        [0, 'rgb(255, 255, 255)'],
                        [1, 'rgb(240, 240, 255)']
                        ]
                },
                borderWidth: 2,
                plotBackgroundColor: 'rgba(255, 255, 255, .9)',
                plotShadow: true,
                plotBorderWidth: 1
            }
        });*/

        Highcharts.setOptions(Highcharts.theme);
        var chart = {
            type: chartType
        };
        var title = {
            text: chart_title,
        };


        var subtitle = {
            text: ' ',
        };
        var xAxis = {
            categories: dataset.categories,
            title: {
                enabled: false
            }
        };
        var yAxis = [{
            allowDecimals: true,
            min: 0,
            title: {
                text: yAxis1_title
            },

            stackLabels: {
                enabled: stackLabelEnabled,
                style: {
                    fontWeight: 'bold',
                    color: (Highcharts.theme && Highcharts.theme.textColor) || 'gray'
                }

            }
        },
        {
            allowDecimals: true,
            min: 0,
            title: {
                text: yAxis2_title
            },
            stackLabels: {
                enabled: stackLabelEnabled,
                style: {
                    fontWeight: 'bold',
                    color: (Highcharts.theme && Highcharts.theme.textColor) || 'gray'
                }
            },
            opposite: true
        }];

        var legend = {
            layout: 'vertical',
            align: 'right',
            verticalAlign: 'middle',
            enabled: legend_enabled
        };

	//Tooltip Options
	if(chartType=='area'){
		tooltip_text='<span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> ';
	    	
        }
	else if(stacking=='percent'){
		tooltip_text='<span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> ({point.percentage:.0f}%)<br/>';
	}
	else{
		tooltip_text='<span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> ';
	}

        var tooltip = {
            // pointFormat: '{series.name}: <b>{point.y:.1f}%</b>'
            //pointFormat: '<b>{point.y}</b>'
             pointFormat: tooltip_text
             
        };

        var series = dataset.seriesdata


        /****** Setting plotOptions according to chart type******/
        var plotOptions={}
        if(chartType=='bar'){
            plotOptions = {
                bar: {
                    allowPointSelect: true,
                    showInLegend: true,
                    stacking: stacking,
                    /*dataLabels: {
                        enabled: plotColumnDatalabelEnabled,
                        color: (Highcharts.theme && Highcharts.theme.dataLabelsColor) || 'white'
                    },*/
                    colorByPoint: colorByPoint,
		dataLabels: {
				enabled: dataLabel
			    }
                }
            };
        }
        else if(chartType=='column'){
            plotOptions = {
                column: {
                    allowPointSelect: true,
                    showInLegend: true,
                    stacking: stacking,
                    /*dataLabels: {
                        enabled: plotColumnDatalabelEnabled,
                        color: (Highcharts.theme && Highcharts.theme.dataLabelsColor) || 'white'
                    },*/
                    colorByPoint: colorByPoint,
			dataLabels: {
				enabled: dataLabel,
                    formatter:function() {
				    if(this.percentage==null)
				        return this.y;
                      return Math.round(this.percentage)   + '%';
                    }
			    }
                }

            };
        }
        else if(chartType=='area'){
            plotOptions = {
                area: {
                    stacking: stacking,
                    allowPointSelect: true,
                    showInLegend: true, 
			dataLabels: {
				enabled: dataLabel
			    }
                    /*dataLabels: {
                        enabled: plotColumnDatalabelEnabled,
                        color: (Highcharts.theme && Highcharts.theme.dataLabelsColor) || 'white'
                    },*/
                }

            };
        }

        var credits = {

            enabled: false
        }


        var exporting = {
            buttons: {
                contextButton: {
                    enabled: true
                }
            }
        }

        var json = {};
        json.chart = chart;
        json.title = title;
        json.subtitle = subtitle;
        json.xAxis = xAxis;
        json.yAxis = yAxis;
        json.legend = legend;
        json.tooltip = tooltip;
        json.series = series;
        json.plotOptions = plotOptions;
        json.credits = credits;
        json.exporting = exporting;
        //json.responsive=responsiveness;
        $('#' + divId).highcharts(json);

}


/**
* Asynchronous request For Table generation
* @author persia
**/
function mpowerRequestForTable(post_url, element, chart_object,filtering) {

    var grouping=true,collapsed;
    if('grouping'  in chart_object)
            grouping=chart_object['grouping'];
        else grouping=false;

    if('collapsed'  in chart_object)
            collapsed=chart_object['collapsed'];
        else collapsed=false;

    $.ajaxSetup({
    beforeSend: function(xhr, settings) {
            function getCookie(name) {
                var cookieValue = null;
                if (document.cookie && document.cookie != '') {
                    var cookies = document.cookie.split(';');
                    for (var i = 0; i < cookies.length; i++) {
                        var cookie = jQuery.trim(cookies[i]);
                        // Does this cookie string begin with the name we want?
                        if (cookie.substring(0, name.length + 1) == (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }
            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        }
    });


    $.ajax({
        type: 'POST',
        url: post_url,
        data: filtering,
        beforeSend: function() {
            $(element).html("Please Wait...loading....");
        },
        success: function(dataset) {
            console.log("collapsed "+collapsed);
            if(grouping)
                initGroupedDataTable(element, dataset.data, dataset.col_name,chart_object);
            else if(collapsed)
                initCollapsedDataTable(element, dataset.data, dataset.col_name,chart_object);
            else initDataTable(element, dataset.data, dataset.col_name,chart_object);

            $('#'+element).show();
        },
        error: function(data) {
            $(element).html("Error occurred! Please reload.");
        }
    });
} // END of mpowerRequestForTable






/**
* Asynchronous request For Map generation
* @author persia
**/
function mpowerRequestForMap(post_url, element,chart_object, filtering) {
    console.log(post_url+"    "+element +"    "+chart_object);
    $.ajaxSetup({
    beforeSend: function(xhr, settings) {
            function getCookie(name) {
                var cookieValue = null;
                if (document.cookie && document.cookie != '') {
                    var cookies = document.cookie.split(';');
                    for (var i = 0; i < cookies.length; i++) {
                        var cookie = jQuery.trim(cookies[i]);
                        // Does this cookie string begin with the name we want?
                        if (cookie.substring(0, name.length + 1) == (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }
            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        }
    });

    $.ajax({
        type: 'POST',
        url: post_url,
        data: filtering,
        beforeSend: function() {
            $(element).html("Please Wait...loading....");
        },
        success: function(dataset) {
            dataset=JSON.parse(dataset);
            console.log("dataset "+dataset);
            chart_object['dataset'] = dataset;
            chart_object['element'] = element;
            mPowerMapGeneration(chart_object);
        },
        error: function(data) {
            $(element).html("Error occurred! Please reload.");
        }
    });
} // END of mpowerRequestForMap






/**
 * MAP Generation Function
 * @author persia
 * @param obj -> containing all properties including dataset
 */
function mPowerMapGeneration(obj) {

    //All Variable Declaration
    var divId,clustering;

    //**Exploring MAP Properties from object**

    //Mandatory properties
    dataset = obj['dataset'];
    divId = obj['element'];


    if('clustering'  in obj)
            clustering=obj['clustering'];
        else clustering=false;

    color_ranges=[['Excellent', '#0000bb'], ['Good', '#00bb00'], ['Medium', '#bbbb00'], ['Bad', '#bb0000'] ];
    try{
        //SETTING DATA
       var geoJson = dataset;
        mapboxgl.accessToken = 'pk.eyJ1IjoiaWJ0YXNoYW0iLCJhIjoiY2lmejE0eGswNWpudXU3bHhoMXJ2Zm5weiJ9.5KD2N8Y7YiKI3DfdMZwodQ';
        var map = new mapboxgl.Map({
            container: divId,
            style: 'mapbox://styles/mapbox/streets-v8',
            center: [89.890137,22.521279], //khulna 22.8456° N, 89.5403° E
            zoom: 8
        });



        map.on('load', function(){
            // Add a new source from our GeoJSON data and set the
            // 'cluster' option to true.
            map.addSource("earthquakes", {
                type: "geojson",
                // Point to GeoJSON data.
                data: geoJson, //"/geodata.geojson",
                cluster: clustering
                //clusterMaxZoom: 14, // Max zoom to cluster points on
                //clusterRadius: 50 // Radius of each cluster when clustering points (defaults to 50)

            });

            map.addLayer({
                'id': 'population',
                'type': 'circle',
                "source": "earthquakes",
                'source-layer': 'sf2010',
                'paint': {
                    // make circles larger as the user zooms from z12 to z22
                    'circle-radius': {
                        'base': 4,
                        'stops': [[12, 5], [22, 180]]
                    },
                    // color circles by ethnicity, using data-driven styles
                    'circle-color': {
                        property: 'title',
                        type: 'categorical',
                        stops:  color_ranges
                    },
                    'circle-opacity': 0.8
                 }
            });



            if(clustering==true){
                // Display the earthquake data in three layers, each filtered to a range of
                // count values. Each range gets a different fill color.
                var layers = [
                    [150, '#f28cb1'],
                    [20, '#f1f075'],
                    [0, '#51bbd6']
                ];

                layers.forEach(function (layer, i) {
                    map.addLayer({
                        "id": "cluster-" + i,
                        "type": "circle",
                        "source": "earthquakes",
                        "paint": {
                            "circle-color": layer[1],
                            "circle-radius": 18
                        },
                        "filter": i == 0 ?
                            [">=", "point_count", layer[0]] :
                            ["all",
                                [">=", "point_count", layer[0]],
                                ["<", "point_count", layers[i - 1][0]]]
                    });
                });

                // Add a layer for the clusters' count labels
                map.addLayer({
                    "id": "cluster-count",
                    "type": "symbol",
                    "source": "earthquakes",
                    "layout": {
                        "text-field": "{point_count}",
                        "text-font": [
                                "DIN Offc Pro Medium",
                                "Arial Unicode MS Bold"
                            ],
                        "text-size": 12
                    }
                });
            } //END Clustering check if

            //LEGEND and Toolbar For https://www.mapbox.com/help/gl-dds-map-tutorial/




        });



        //Adding Legend

        map.addControl(new mapboxgl.Navigation());



        var labels=""
        for (var i = 0; i < color_ranges.length; i++) {
          eachcolor = color_ranges[i];
          console.log("eachcolor  "+eachcolor);
          labels+='<div><span style="width: 15px; height: 15px; margin:auto; display: inline-block;  background-color:' + eachcolor[1] + ';"></span> ' + eachcolor[0] + '</div>';
        }
        $("#legend").html("<h4>Qualification</h4>"+labels);


        var popup = new mapboxgl.Popup({
                closeButton: true,
                closeOnClick: true
        });



        map.on('mousemove',  function (e) {
            var features = map.queryRenderedFeatures(e.point, {layers:['population']});
            if(!features.length)
                return;
            var feature = features[0];

            // Populate the popup and set its coordinates
            // based on the feature found
              popup.setLngLat(feature.geometry.coordinates)
              .setHTML('<div id=\'popup\' class=\'popup\' style=\' padding: 0px 22px 0px; z-index: 10;\'> <h5> Detail:    </h5>' +
              '<ul class=\'list-group\'>' +
              '<li class=\'list-item\'> Qualification:  <span style="width: 15px; height: 15px; margin:auto; display: inline-block;  background-color:' + feature.properties['color'] + ';"></span> ' + feature.properties['title'] + '  </li>' +
              '<li class=\'list-item\'> Score: <b>' + feature.properties['score'] + ' </b></li>'+
              '<li class=\'list-item\'> Zone: <b>' + feature.properties['Zone'] + ' </b></li>'+
              '<li class=\'list-item\'> District: <b>' + feature.properties['District'] + ' </b></li>'+
              '<li class=\'list-item\'> Polder: <b>' + feature.properties['Polder'] + ' </b></li>'+
              '<li class=\'list-item\'> Date: <b>' + feature.properties['Date'] + ' </b></li></ul></div>')
              .addTo(map);
        });

        map.on('mouseleave', 'population', function() {
            popup.remove();
        });


    }
    catch(e) {
        console.log("MAP Loading Failed  "+e);
    }

}


/***
 * Navigation Filter Option OPEN onclick
 * @param nav
 * @param main
 */
function openNav(nav,main) {
        current_width=$("#"+nav).width();
        if(current_width=="0"){
            $("#"+nav).width("25%");
            $("#"+nav).css('padding', 10);
        }

 }


 /***
 * Navigation Filter Option CLOSE onclick
 * @param nav
 * @param main
 */
 function closeNav(nav) {
    console.log("Nav close  "+nav);
    //$("#"+nav).width(0);
    $("#"+nav).css('padding', 0);
    $("#"+nav).css('width', 0);
 }




 /********* Project Specific  Code********/

function create_wmg_tracker_report(element,filtering){
    var chart_object={}
    console.log("In data ");
    $.ajax({
        type: 'POST',
        url: "/dashboard/get_wmg_tracker_report/",
        data: filtering,
        beforeSend: function() {
            $("#"+element).html("Please Wait...loading....");
        },
        success: function(dataset) {
            $("#"+element).html("");
            dataset=JSON.parse(dataset);
            initCollapsedCustomizedDataTable(element, dataset.data, dataset.col_name,dataset.subtables,chart_object);
            $('#'+element).show();
        },
        error: function(data) {
            console.log("Data  Error");
            $(element).html("Error occurred! Please reload.");
        }
    });
 }






 function get_wmg_tracker_excel(){
     console.log(" data "+"/dashboard/getWMGTrackerExcel?"+$("#form_37").serialize());
     location.href = "/dashboard/getWMGTrackerExcel?"+$("#form_37").serialize();

 }
