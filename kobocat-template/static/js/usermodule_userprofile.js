// =======================================================================
// Depemdency: 
// 1. jquery
// 2. jquery.searchable-ie-1.1.0.min.js
// 3. bootstrap.js
// 4. bootstrap.css
// =======================================================================
$( "#id_username" ).keyup(function() {
    var lowercase_username = $( "#id_username" ).val().toLowerCase();
    $( "#id_username" ).val(lowercase_username);
});


var icon = '<a href="#" class="ajax_flag" data-toggle="modal" data-target="#myModal"><i class="fa fa-cog"></i></a>'
$('#id_psu').after(icon);

$(".modal-body").append('<div id="animate" style="text-align:center"><img src="/static/images/ring.svg"></div>');
$( document ).ready(function() {
    var selected_psu_value = $("#id_psu").val();
    $("#id_psu").prop("disabled", true);
    // For a dropdown select make a hidden input with same 
    // name and set its value same as chosen one.
    $("#id_psu").after('<input type="hidden" id="real_psu" name="psu" value="'+selected_psu_value+'">');
});

$(document).on("click", ".clickable-row", function(e) {
    var jsonString = "{" ;
    $(this).find('td').each (function() {
        jsonString += '"' + $(this).attr('data-id') + '" : "' + $(this).html() + '",';
    });
    var last_comma = jsonString.lastIndexOf(",");
    jsonString = jsonString.substring(0, last_comma);
    jsonString += "}" ;
    json_object = JSON.parse(jsonString);
    set_form_input_value(json_object);
    $('#myModal').modal('hide');
});

// functionality changes based on project requirements
function set_form_input_value(json_object) {
    if (json_object.hasOwnProperty('id')) {
        $("#id_psu").val(json_object['id']);
        $("#real_psu").val(json_object['id']);
    }

}

$(".ajax_flag").click(function() {
    var table = '<table id="access-table" class="table" border="1">';
    var table_end = '</table>';
    $.ajax({
    type: "POST",
    url:"/unicef/get-object/",
    data: {id: "some_id"},
    success: function(data){
        var table_header_flag = true ;
        var count = 0;
        if (data.length > 0){
            data.forEach(function(option) {
                var row = '<tr id="row'+count+'" class="clickable-row">' ;
                for (var key in option) {
                    if (option.hasOwnProperty(key)) {
                        if(table_header_flag){
                            row = row + '<th data-id="'+key+'">'+option[key]+'</th>' ;
                        }else{
                            row = row + '<td data-id="'+key+'">'+option[key]+'</td>' ;    
                        }
                        
                    }
                }
                table_header_flag = false ;
                option = null;
                row = row + '</tr>';
                table += row ;
                count += 1;
            });
            table += table_end ;
            // $("#organizations-table").after(header_before_table);
            $(".modal-body").empty();
            $(".modal-body").append('<input type="text" id="search" placeholder="Search...">');
            $(".modal-body").append(table);
            $( '#access-table' ).searchable({clearOnLoad: true});
            $( '#animate' ).remove();
        }
    },
    error: function(){
    } 
}) // end-ajax
});