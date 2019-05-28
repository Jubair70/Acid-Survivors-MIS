$( document ).ready(function() {
    // document.getElementById("adder").style.display = "none";
    var div = $("#message"); 
    if ( div !== null ){
        div.slideUp(3000);
    }
});

// For dynamically generated table and delete modal
$(document.body).on("click", ".delete-user-item", function(e){
    var criteria_id = $(this).attr("data-href");
    console.log(criteria_id);
    $('.btn-ok').attr("href",criteria_id);
});


//start add more button action
$(".organization").click(function(){
    // document.getElementById("adder").style.display = "none";
    var header_before_table = '<h2 id="partner-header">Partner Organizations</h2>';
    var table = '<table id="access-table" class="table table-striped table-bordered">'+
              '<tr>'+
                '<th style="text-align:center" >Organization</th>'+
                '<th style="text-align:center" >Can View</th>'+
                // '<th>Delete</th>'+
              '</tr>';
    var table_end = '</table>';
    var criteria_id = $(this).attr("data-id");
    // console.log(criteria_id);
    
    // $("tr a").not($("a[data-id~='"+criteria_id+"']")).parent().parent().css( "background-color", "green" );
    // $("a[data-id~='"+criteria_id+"']").parent().parent().css( "background-color", "red" );

    //background coloring
    var selected = $("a[data-id~='"+criteria_id+"']").parent().parent().hasClass("highlight");
    $(".organization").not("a[data-id~='"+criteria_id+"']").parent().parent().removeClass("highlight")//.css("background-color:none");;
    if(!selected)
            $("a[data-id~='"+criteria_id+"']").parent().parent().addClass("highlight")//.css("background-color:#D9EDF7");;


    var org_id = criteria_id.substring(criteria_id.lastIndexOf("-")+1); 
    // var org_name = $(this).attr("org-name");
    // var add_more_button = '<button type="button" id="add-more" class="btn btn-primary btn-lg">Add Another</button>';
    if ($("#access-table").length > 0){
        $("#access-table").remove();
    }
    
    // setting dropdown to be visible to add organization mapping
    // document.getElementById("adder").style.visibility = "visible";
    // setting currently selected org as observer in dropdown
    $("#id_observer_organization").val(org_id);
    
    // $("#add-more").remove();
    $("#partner-header").remove();
    
    // $("#tables").after(add_more_button);

    

    $.ajax({
        type: "POST",
        url:"/usermodule/organization-access-list/",
        data: {id: org_id},
        success: function(response){
            if (response.length > 0){
                response.forEach(function(option) {
                    var row = '<tr>'+
                                '<td style="text-align:center" >'+option.observer+'</td>'+
                                '<td style="text-align:center" >'+option.observable+'</td>'+
                                // '<td><a href="'+option.link+'"><i class="fa fa-trash-o"></i></a></td>'+
                                // '<td><a href="#" data-href="'+option.link+'" data-toggle="modal" data-target="#confirm-delete" class="delete-user-item"><i class="fa fa-trash-o"></i></a></td>'+
                              '</tr>';
                    table += row ;   
                });
                table += table_end ;
                //$("#organizations-table").after(header_before_table);
                $(".partner-box .portlet-body").html(table);
                $(".partner-box").show();
                $('html, body').animate({scrollTop: $("#access-table").offset().top}, 2000);
            }
            
        },
        error: function(){
            
        }
       }); // end-ajax
    $('.delete-user-item').on('click', function(e) {
        var criteria_id = $(this).attr("data-href");
        console.log(criteria_id);
        $('.btn-ok').attr("href",criteria_id);
    });    
});//end organization mapping view click


$(document).on('click', '#add-more', function(){
    var form = $('#adder');
    form.fadeIn();
    $('html, body').animate({scrollTop: $("#adder").offset().top}, 2000);


});


$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            var csrftoken = getCookie('csrftoken');
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

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
