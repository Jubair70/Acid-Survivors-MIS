var dataSet = [];
var chartSeries = [];
function isArray(what) {
    return Object.prototype.toString.call(what) === '[object Array]';
}

function initDataTable(tableID, dataSet, tableColumn,chart_object) {
    console.log("initDataTable "+tableID);
    if (tableColumn.length == 0) {
        tableColumn = ["id", "user_id", "received", "pngo", "approvalstatus", "details"];
    }
    var query_column = []
    for (var column in tableColumn) {
        query_column.push({
            title: tableColumn[column]
        });

    }
    // Disable search and ordering by default
    $.extend($.fn.dataTable.defaults, {
        searching: true,
        ordering: true
    });
    if ($.fn.dataTable.isDataTable('#' + tableID)) {
        var data_table = $('#' + tableID).DataTable();
        data_table.clear().draw();
        data_table.rows.add(dataSet); // Add new data
        data_table.columns.adjust().draw(); // Redraw the DataTable
    } else {
        $('#' + tableID).DataTable({
            data: dataSet,
            // scrollY: 400,
            responsive: true,
            "columnDefs": [{
                className: "dt-body-center",
                "targets": "_all"
            }],

            scrollY: 400,
            scrollX: true,
            scrollCollapse: true,
            paging: true,
            columns: query_column,
            dom: 'Bfrtip',
            buttons: [
                'copy', 'csv', 'excel', 'pdf'
            ]
        });
        $('.dataTables_scrollHeadInner').css('width','auto');
    }
    $('#' + tableID + '_wrapper .dataTables_filter input').addClass("form-control input-medium"); // modify table search input
    $('#' + tableID + '_wrapper .dataTables_length select').addClass("form-control"); // modify table per page dropdown
}


function initGroupedDataTable(tableID, dataSet, tableColumn,chart_object) {
    var grouping_column_serial,paging;
    if('grouping_column_serial'  in chart_object)
            grouping_column_serial=chart_object['grouping_column_serial'];
        else grouping_column_serial=0;
     if('paging'  in chart_object)
            paging=chart_object['paging'];
        else paging=true;


    if (tableColumn.length == 0) {
        tableColumn = ["id", "user_id", "received", "pngo", "approvalstatus", "details"];
    }
    var query_column = []
    for (var column in tableColumn) {
        query_column.push({
            title: tableColumn[column]
        });

    }

    // Disable search and ordering by default
    $.extend($.fn.dataTable.defaults, {
        searching: true,
        ordering: true
    });
    if ($.fn.dataTable.isDataTable('#' + tableID)) {
        var data_table = $('#' + tableID).DataTable();
        data_table.clear().draw();
        data_table.rows.add(dataSet); // Add new data
        data_table.columns.adjust().draw(); // Redraw the DataTable
    } else {

        $('#' + tableID).DataTable({
            data: dataSet,
            responsive: true,
            "columnDefs":  [
            { "visible": false, "targets": grouping_column_serial } ],
            scrollY: 400,
            scrollX: true,
            scrollCollapse: true,
            bPaginate: paging,
            columns: query_column,
            "drawCallback": function(settings) {
                var api = this.api();
                var rows = api.rows( {page:'current'} ).nodes();
                var last=null;

                api.column(grouping_column_serial, {page:'current'} ).data().each( function ( group, i ) {
                    if ( last !== group ) {
                        $(rows).eq( i ).before(
                            '<tr  class="group"><td colspan="'+(tableColumn.length-1)+'">'+group+'</td></tr>'
                        );
                        last = group;
                    }
                } );
            },
            dom: 'Bfrtip',
            buttons: [
                'copy', 'csv', 'excel', 'pdf'
            ]

        });
        $('.dataTables_scrollHeadInner').css('width','auto');
    }


    $('#' + tableID + '_wrapper .dataTables_filter input').addClass("form-control input-medium"); // modify table search input
    $('#' + tableID + '_wrapper .dataTables_length select').addClass("form-control"); // modify table per page dropdown

}




function initCollapsedDataTable(tableID, dataSet, tableColumn,chart_object) {
    console.log("collapsed ");
    var grouping_column_serial,paging,table;
    if('grouping_column_serial'  in chart_object)
            grouping_column_serial=chart_object['grouping_column_serial'];
        else grouping_column_serial=0;
     if('paging'  in chart_object)
            paging=chart_object['paging'];
        else paging=true;


    if (tableColumn.length == 0) {
        tableColumn = ["id", "user_id", "received", "pngo", "approvalstatus", "details"];
    }
    var query_column = [{
                    "className":      'details-control',
                    "orderable":      false,
                    "data":           null,
                    "defaultContent": ''
                }]
    for (var column in tableColumn) {
        query_column.push({
            title: tableColumn[column]
        });

    }
    $.extend($.fn.dataTable.defaults, {
        searching: true,
        ordering: true
    });
    if ($.fn.dataTable.isDataTable('#' + tableID)) {
        var data_table = $('#' + tableID).DataTable();
        data_table.clear().draw();
        data_table.rows.add(dataSet); // Add new data
        data_table.columns.adjust().draw(); // Redraw the DataTable
    } else {

        table=$('#' + tableID).DataTable({
            data: dataSet,
            responsive: true,
            scrollY: 400,
            scrollX: true,
            scrollCollapse: true,
            bPaginate: paging,
            columns: [{
                    "className":      'details-control',
                    "orderable":      false,
                    "data":           null,
                    "defaultContent": ''
                },
                { "title": "name" },
                { "title": "category"},
            { "title": "value"}],

             "order": [[1, 'asc']],
            dom: 'Bfrtip',
            buttons: [
                'copy', 'csv', 'excel', 'pdf'
            ]

        });
        $('.dataTables_scrollHeadInner').css('width','auto');
    }

    table.rows().eq(0).each( function ( index ) {
        var row = table.row(index);
        row.child( "<h1>In Each Row</h1>" );
        // ... do something with data(), or row.node(), etc
    } );
    // Add event listener for opening and closing details
    $('#'+tableID).on('click', 'td.details-control', function () {
        var tr = $(this).closest('tr');
        var row = table.row( tr );

        if ( row.child.isShown() ) {
            // This row is already open - close it
            row.child.hide();
            tr.removeClass('shown');
        }
        else {
            // Open this row
            row.child.show();
            tr.addClass('shown');
        }
    } );

    $('#' + tableID + '_wrapper .dataTables_filter input').addClass("form-control input-medium"); // modify table search input
    $('#' + tableID + '_wrapper .dataTables_length select').addClass("form-control"); // modify table per page dropdown

}





function get_query_data(data_url, needfilter, filter_data, form_id_string,dateColumn) {
    var SendInfo = {
        'filter': '0'
    };
    var data_to_send = SendInfo;

    if (needfilter) {
        data_to_send = filter_data;
    }
    ///fetch data json.
    $.ajax({
        url: data_url,
        type: 'GET',
        data: data_to_send,
        dataType: 'json',
        success: function(response) {
            response.data.sort(function(a, b) {
                return new Date(b[2]).getTime() - new Date(a[2]).getTime()
            });
            var byStatus = filterByProperty(response.data, 4, 'New');
            initDataTable("pending_table", byStatus, response.col_name);
            initDataTable("example", response.data, response.col_name);
            chartSeries = generateChartData(response.data,dateColumn)
            createChartData(chartSeries,form_id_string,'chart-main-container',7,'column');
        },
        error: function() {
            alert("error");
        }
    });
}

function filterByProperty(array, prop, value) {
    var filtered = [];
    for (var i = 0; i < array.length; i++) {
        var obj = array[i];
        if (obj[prop] == value) {
            filtered.push(obj);
        }
    }
    return filtered;
}


function generateChartData(data,dateColumn){
    var chartSeries = [];
    var allExistingDateData = getCount(data,dateColumn);
    var lastSixtyDays = lastDays(60);
    for(var i=0;i<60;i++){
        if(!(lastSixtyDays[i] in allExistingDateData)){
            chartSeries.push(0);
        } else {
            chartSeries.push(allExistingDateData[lastSixtyDays[i]]);
        }
    }
    return chartSeries;
}


function pad(n) {
  return n.toString().length == 1 ? '0' + n : n;
}

function getCount(arr,dateColumn) {
  var obj = {};
  for (var i = 0, l = arr.length; i < l; i++) {
    var thisDate = new Date(arr[i][dateColumn]);
    var day = pad(thisDate.getDate());
    var month = pad(thisDate.getMonth() + 1);
    var year = thisDate.getFullYear();
    var key = [year, month, day].join('-');
    obj[key] = obj[key] || 0;
    obj[key]++;
  }
  return obj;
}

function formatDate(date){
    var dd = date.getDate();
    var mm = date.getMonth()+1;
    var yyyy = date.getFullYear();
    if(dd<10) {dd='0'+dd}
    if(mm<10) {mm='0'+mm}
    date = yyyy+'-' + mm + '-'+dd;
    return date
 }

function lastDays (n) {
    var result = [];
    for (var i=0; i<n; i++) {
        var d = new Date();
        d.setDate(d.getDate() - i);
        result.push( formatDate(d) )
    }

    return(result);
}


function innerTable(tableID,dataSet, tableColumn){
        var query_column = [ ]
        for (var column in tableColumn) {
            query_column.push({
                title: tableColumn[column]
            });
        }

        $('#' + tableID).DataTable({
            data: dataSet,
            responsive: true,
            /*"columnDefs": [{
                className: "dt-body-center",
                "targets": "_all"
            }],*/
            //scrollY: 400,
            scrollX: false,
            scrollCollapse: true,
            bPaginate: false,
            bFilter: false,
            "info":     false,
            columns: query_column
        });
}





function initCollapsedCustomizedDataTable(tableID, dataSet, tableColumn,subtables,chart_object) {
    var  paging,table;
    if('paging'  in chart_object)
          paging=chart_object['paging'];
    else paging=true;

    var query_column = [{
                "className":      'details-control',
                "orderable":      false,
                "searchable":      false,
                "data":           null,
                "defaultContent": ''
     }];
    for (var column in tableColumn) {
        query_column.push({
            title: tableColumn[column]
        });

    }
    $.extend($.fn.dataTable.defaults, {
        searching: true,
        ordering: true
    });
    if ($.fn.dataTable.isDataTable('#' + tableID)) {
        $("#"+tableID).dataTable().fnDestroy();
    } //else {

        table=$('#' + tableID).DataTable({
            data: dataSet,
            responsive: true,
            //scrollY: 400,
            //scrollX: true,
            scrollCollapse: true,
            bPaginate: false,
            bFilter: false,
            columns: query_column,
            "order": [[1, 'asc']]

        });
        $('.dataTables_scrollHeadInner').css('width','auto');
   // }

    //Adding Inner Table in each row
    table.rows().eq(0).each( function ( index ) {
        var row = table.row(index);
        console.log("row"+row);
        var innertableid="inner_table_"+index;
        try{
            row.child( '<table class="display table table-bordered table-striped table-condensed nowrap" id="'+innertableid+'"></table>' ).show();
            var obj=JSON.parse(subtables[row.data()[1]]);
            innerTable(innertableid, obj.data, obj.columns);
        }
        catch(e){
            console.log("One row caused error:  index "+index);
        }
    } );


    //Initially Hide Every inner table
    table.rows().eq(0).each( function ( index ) {
        var row = table.row(index);
        row.child.hide();
    });

    // Add event listener for opening and closing details
    $('#'+tableID).on('click', 'td.details-control', function () {
        var tr = $(this).closest('tr');
        var row = table.row( tr );

        if ( row.child.isShown() ) {
            // This row is already open - close it
            row.child.hide();
            tr.removeClass('shown');
        }
        else {
            // Open this row
            row.child.show();
            tr.addClass('shown');
        }
    });
    $('#' + tableID + '_wrapper .dataTables_filter input').addClass("form-control input-medium"); // modify table search input
    $('#' + tableID + '_wrapper .dataTables_length select').addClass("form-control"); // modify table per page dropdown

}


