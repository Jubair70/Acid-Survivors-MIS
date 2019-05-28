var days = ['Sunday','Monday','Tuesday','Wednesday', 'Thursday','Friday','Saturday']; 
var tanahashi_x_catag = ['Accessibility','Utilization','Adequate Coverage','Effective Coverage'];
var br_x_catag = ['Have Birth Certificate','Seen Birth Certificate','Registered within 45_days'];
var abr_x_catag = ['Know where apply','Know how application','Know who help'];
var series_val = [];
var jasper_url = "";
var jasper_rprt_exec_url = "";
var jasper_param_query = "";

var rprt_name = "";
var param_id  = "";
var param_value = "";



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

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function initializeOptions(select_id){
    $('#'+select_id).append($('<option id=0>').text('All').attr('value', '0'));
}
function visitBRPage(){
      $("#dashboard_query").slideDown();
        window.location='/unicef/unicef_br_report';
    }

function generateReport(){
    $("#dashboard_query").slideDown();
    alert('We are not ready to show this now..');
}

function generateJasperReport(){
   // console.log(jasper_url);
    callJasper(jasper_url+'Group_Test_A4.html?j_username=dosthim&j_password=123456');
}

function callAjax(call_type,withCred,uname,pass,server_url,data,onSuccess,fileFormat){

  $.ajax({
      type: call_type,
      xhrFields: {
          withCredentials: withCred
      },
      
      dataType: (call_type == 'POST')? "xml" : '',
      contentType: (call_type == 'POST')? "application/xml" : '',
      data: (call_type == 'POST')? data : '',
      
      beforeSend: (withCred == true)? function (xhr) {
          xhr.setRequestHeader('Authorization', 'Basic ' + btoa(uname+':'+pass));
      }:'',
      url: server_url,
      success: function (data) {
        console.log(data);
        if(onSuccess == 'FILTERFORM'){
          $("#dashboard_query").hide();
          showFilterForm(data);
       }
        if(onSuccess =='SHOW'){

          $("#download_div").slideDown();
            $("#btn_pdf").click(function(){
            generateDynamicJasperReport(rprt_name,'\''+param_id+'\'',param_value,'pdf');
          });
          $("#btn_xcl").click(function(){
            generateDynamicJasperReport(rprt_name,'\''+param_id+'\'',param_value,'xls');
          });
          $("#btn_xml").click(function(){
            generateDynamicJasperReport(rprt_name,'\''+param_id+'\'',param_value,'xml');            
          }); 
          if(fileFormat == 'html'){
            showData(data);
          } else if(fileFormat == 'pdf'){
             document.getElementById("download_pdf").href=server_url;
             $("#download_pdf").show();
             $("#btn_pdf").html('Ready');
          }else if(fileFormat == 'xls'){
             document.getElementById("download_xls").href=server_url;
             $("#download_xls").show();
             $("#btn_xcl").html('Ready');
          }else if(fileFormat == 'xml'){
             document.getElementById("download_xml").href=server_url;
             $("#download_xml").show();
             $("#btn_xml").html('Ready');
          }
        
       }
       if(onSuccess == 'CHECKSTATUS'){
        $xml = $( data ),
        $requestid = $xml.find('requestId');
        $exportid = $xml.find('id');
        checkStatus($requestid.text(),$exportid.text(),fileFormat);
       }
       
      },
      error: function (data) {
          alert("dynamic ajax : not working! " + data.statusText);
      },
    });
}

function showFilterForm(data){
  if (typeof data ==='undefined'){
          $("#dashboard_query").slideDown();  
        }else{
          $xml = $( data );
          $label = $xml.find('description'); 
          $param_id = $xml.find('id');  
          var div = document.getElementById('dynamic_query');
          
          var l = document.createElement("label");
              l.innerHTML = $label.text();
          var i = document.createElement("input"); //input element, text
              i.setAttribute('type',"text");
              i.setAttribute('name',$param_id.first().text());
              i.setAttribute('id',$param_id.first().text());

          var s = document.createElement("input"); //input element, Submit button
              s.setAttribute('type',"submit");
              s.setAttribute('value',"Submit");
             s.onclick = function(){
                  //   alert('here be dragons');
                  $("#download_pdf").hide();
                  $("#btn_pdf").html('Download PDF');
                  $("#download_xls").hide();
                  $("#btn_xcl").html('Download Excel');
                  $("#download_xml").hide();
                  $("#btn_xml").html('Download XMl');
                  rprt_name = 'paramtest_2';
                  param_id  = $param_id.first().text();
                  param_value = i.value;
                  generateDynamicJasperReport('paramtest_2','\''+param_id+'\'',param_value,'html');

                  return false;
              };
              div.appendChild(l);
              div.appendChild(i);
              div.appendChild(s);
        }
}
function generateDynamicFilterForm(reportName){
  $("#dashboard_query").slideUp();
  var  input_control_url = jasper_url +
                      reportName+jasper_param_query;
  //$("#download_div").hide();
  callAjax('GET',true,'jasperadmin','jasperadmin',input_control_url,'','FILTERFORM','html');
}

function showData(data){
  $('#empty_view').html(data);
}

function downloadAndShow(requestid,exportid,outFormat){
  var  download_url = jasper_rprt_exec_url +
                      requestid+'/exports/'+exportid+'/outputResource';

  callAjax('GET',true,'jasperadmin','jasperadmin',download_url,'','SHOW',outFormat);
}

function checkStatus(requestid,exportid,outFormat) {
  var checking_url =jasper_rprt_exec_url+requestid+'/status/';
  var timer=1;

  $.ajax({
    type: 'GET',
    xhrFields: {
        withCredentials: true
    },
    beforeSend: function (xhr) {
        xhr.setRequestHeader('Authorization', 'Basic ' + btoa('jasperadmin:jasperadmin'));
    },
    url: checking_url, 
    success: function(data) {
      $xml = $( data ),
      $status = $xml.find('status');
      if($status.text() == 'ready'){
        clearTimeout(timer);
        timer=0;
        //console.log('export id: '+exportid);
        downloadAndShow(requestid,exportid,outFormat);

      }
    },
    complete: function() {
      // Schedule the next request when the current one's complete
      if(timer != 0){
        timer = setTimeout(function(){
            checkStatus(requestid,exportid,outFormat) ;
        }, 5000);  
      }
    }
  });
};

function generateDynamicJasperReport(reportName,param_name,value,outFormat){
  $("#dashboard_query").slideUp();
  var data_xml = 
  "<reportExecutionRequest><reportUnitUri>/reports/interactive/"+reportName+"</reportUnitUri>"+
    "<async>true</async><outputFormat>"+outFormat+"</outputFormat>"+
    "<ignorePagination>false</ignorePagination>"+
    "<parameters><reportParameter name="+param_name+">"+
    "<value>"+value+"</value>"+
    "</reportParameter></parameters>"+
    "</reportExecutionRequest>";
    console.log(data_xml);

    callAjax('POST',true,'jasperadmin','jasperadmin',jasper_rprt_exec_url,data_xml,'CHECKSTATUS',outFormat);
}

function callJasper(calling_url){

    document.getElementById("download_pdf").href='http://192.168.21.230:8081/jasperserver/rest_v2/reportExecutions/3f6a04db-a5ba-4b7c-8c3f-e34eee2d3b82/exports/7ef62de1-5dfa-4951-89f0-1f43e2893fe9/outputResource';
    document.getElementById("download_xls").href='http://192.168.21.50:8081/jasperserver/rest_v2/reports/reports/interactive/Group_Test_A4.xls?j_username=dosthim&j_password=123456';
    document.getElementById("download_xml").href='http://192.168.21.50:8081/jasperserver/rest_v2/reports/reports/interactive/Group_Test_A4.xml?j_username=dosthim&j_password=123456';
    document.getElementById("download_csv").href='http://192.168.21.50:8081/jasperserver/rest_v2/reports/reports/interactive/Group_Test_A4.csv?j_username=dosthim&j_password=123456';

     $.get( 
           calling_url,
           function(data) {
           $('#empty_view').html(data);
           }
      );
}

function createFormButton(jsondata,create_chart,is_ajax){
   // console.log('createFormButton::data:: '+JSON.stringify(jsondata));
    var jsonObj = JSON.parse(jsondata);
   // console.log('createFormButton::birth_registration:: '+jsonObj.birth_registration);

    var formName = 'paramtest_2';
    var btnDiv = $('#tg-xY4Sf');
    var btn1 = $('<button class="btn" type="button" onclick="visitBRPage()">'+jsonObj.birth_registration+'</button>'); 
    var btn2 = $('<button class="btn" type="button" onclick="generateReport()">'+jsonObj.complementary_feeding+'</button>'); 
    var btn3 = $('<button class="btn" type="button" onclick="generateReport()">'+jsonObj.maternal_diet+'</button>'); 
    var btn4 = $('<button class="btn" type="button" onclick="generateReport()">'+jsonObj.household_information+'</button>'); 
    var btn5 = $('<button class="btn" type="button" onclick="generateJasperReport()">Jasper Report</button>'); 
    var btn6 = $('<button class="btn" type="button" onclick="generateDynamicFilterForm(\''+formName+'\')">Dynamic Jasper Report</button>'); 
    btnDiv.append(btn1);
    btnDiv.append(btn2);
    btnDiv.append(btn3);
    btnDiv.append(btn4);
    btnDiv.append(btn5);
    btnDiv.append(btn6);
    reloadReportChart(jsondata,is_ajax,create_chart);
}
function reloadReportChart(rawJsonObj,is_ajax,create_chart){
    var jsonObj;
     if(is_ajax){
        jsonObj = rawJsonObj;    
    }else{
        jsonObj = JSON.parse(rawJsonObj);
    }
    var series_json = createChartSeries('column',jsonObj,'Tanahashi Framework',tanahashi_x_catag,false);
    var series_br_json = createChartSeries('column',jsonObj,'Birth Registration',br_x_catag,false);
    var series_rnsbr_json = createChartSeries('pie',jsonObj,'Birth Registration',br_x_catag,true);
    var series_abr_json = createChartSeries('column',jsonObj,'Awarness Birth Registration',abr_x_catag,false);
    //console.log(JSON.stringify(series_json));

    if(create_chart){
        createChart('column','graph1',series_json,'','',tanahashi_x_catag);
        createChart('column','graph2',series_br_json,'','',br_x_catag);
        createChart('pie','graph3',series_rnsbr_json,'','','');
        createChart('column','graph4',series_abr_json,'','',abr_x_catag);    
    }
}
function callServer(str,select_id){
    $('#'+select_id).empty();
    $.ajax({
      url:'/unicef/get-options/',
      type:'GET',
      data: 'q=' + str,
      dataType: 'json',
      success: function( json ) {
        initializeOptions(select_id);
        $.each(json, function(i, value) {
           $('#'+select_id).append($('<option id='+value['id']+'>').text(value['name']).attr('value', value['id']));
        });
      }
    });
}

function pageReloadWithFilter(param_str){
    $.ajax({
      url:'/unicef/unicef_br_report/',
      type:'POST',
      data: param_str,
      dataType: 'json',
      success: function( json ) {
        //console.log('returned json:: '+json);
        reloadReportChart(json,true,true);
      },
    });
}

function onChange(dom_id,to_populate_id){
    var type = dom_id.split('-')[1];
    var key_type;
    if(type == 'district'){
        key_type = 'UP_';
    }
    if(type == 'upazilla'){
        key_type = 'UN_';
    }
    if(type == 'union'){
        key_type = 'PSU_';   
    }
    $('#'+dom_id).change(function () {
        var selected_val=$(this).val();
        //do ajax now
        callServer(key_type+selected_val,to_populate_id);
    });
}

function onClickSubmit(dom_id){
    $("#"+dom_id).click(function(){
        var district_val=$('#sel-district').val();
        var upazilla_val=$('#sel-upazilla').val();
        var union_val=$('#sel-union').val();
        var psu_val=$('#sel-psu').val();        
        var from_val=$('#from-date').val();
        from_val = dateFormat(from_val);
        //console.log('from_val::'+from_val);
        var to_val=$('#to-date').val();
        to_val = dateFormat(to_val);
        var param_data = {
            'district':district_val,
            'upazilla':upazilla_val,
            'union':union_val,
            'psu':psu_val,
            'from_date':from_val,
            'to_date':to_val
        }
        //console.log(param_data);
        pageReloadWithFilter(param_data);
    }); 
}

function dateFormat (date_string) {

  dateParse = Date.parse(date_string);
  now = new Date(dateParse); 
  year = "" + now.getFullYear();
  month = "" + (now.getMonth() + 1); if (month.length == 1) { month = "0" + month; }
  day = "" + now.getDate(); if (day.length == 1) { day = "0" + day; }
  hour = "" + now.getHours(); if (hour.length == 1) { hour = "0" + hour; }
  minute = "" + now.getMinutes(); if (minute.length == 1) { minute = "0" + minute; }
  second = "" + now.getSeconds(); if (second.length == 1) { second = "0" + second; }
  if(isNaN(year) && isNaN(month) && isNaN(day) && isNaN(hour) && isNaN(minute) && isNaN(second))
    return date_string= ""
  return year + "-" + month + "-" + day + "T" + hour + ":" + minute + ":" + second;
}