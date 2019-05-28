function getDesiredDate(n) {
    var today = new Date();
    var n_month_before_today = new Date(today);
    n_month_before_today.setMonth((today.getMonth() + 1) - n);
    var dd = n_month_before_today.getDate();
    var mm = n_month_before_today.getMonth() + 1;

    if (dd < 10) {
        dd = '0' + dd
    }
    if (mm < 10) {
        mm = '0' + mm
    }
    var yyyy = n_month_before_today.getFullYear();
    formatted_date = yyyy + '-' + mm + '-' + dd;
    return formatted_date;
}


function generateHHListTable(rowData) {
    var tbody = '';
    for (var i = 0; i < rowData.length; i++) {
        tbody += '<tr><td>' + checkNullVal(rowData[i].hh_id) + '</td><td>' + checkNullVal(rowData[i].hh_name) + '</td><td>' + checkNullVal(rowData[i].hh_husband_father_name) + '</td><td>' + checkNullVal(rowData[i].group_selection) + '</td><td>' + checkNullVal(rowData[i].hh_status) + '</td><td><a class="btn red" onclick="getProfile(\'' + rowData[i].hh_id + '\')" role="button">Profile</a></td></tr>';
    }
    $('#hh_table').find('tbody').html(tbody);
}

function generateSLAListTable(rowData) {
    var tbody = '';
    for (var i = 0; i < rowData.length; i++) {
        var view = '"'+"/hhmodule/view_sla/"+rowData[i].id+'"';
        tbody += '<tr><td><a href = '+view+'>' + checkNullVal(rowData[i].sla_number) + '</a></td><td>' + checkNullVal(rowData[i].sla_name) + '</td><td>' + checkNullVal(rowData[i].sla_address) + '</td><td>' + checkNullVal(rowData[i].ward) + '</td><td>' + checkNullVal(rowData[i].sla_chairperson) + '</td><td>' + checkNullVal(rowData[i].sla_member_count) + '</td><td><a style="margin-right: 10px;" class="btn red" role="button">Profile</a><a href="/hhmodule/show_sla_meeting_list/'+rowData[i].id+'/" class="btn red" role="button">Meeting</a></td></tr>';
    }
    $('#sla_table').find('tbody').html(tbody);
}

//Get Household Profile
function getProfile(hh_id) {
    console.log(hh_id)
    $.ajax({
        url: 'profile/',
        type: 'POST',
        dataType: 'json',
        data: {'profile_id': hh_id},
        success: function (result) {
            splitData = result.split('@@@@@');
            generateHHProfile(splitData[0]);
            $('#active_hh_id').val(hh_id);
            $('#base_line_btn').attr('href', '/cupadmin/forms/Urban_Programme_2016_Baseline_Survey_2/instance/#/' + splitData[1])
            $('#filter-form').hide();
        }

    });
}
//TUP @zinia
function generateDropDownList(active_hh_id) {

    var division = $('#f_division').val();
    var district = $('#f_district').val();
    var upazila = $('#f_upazila').val();
    var union = $('#f_union').val();
    var branch = $('#f_branch').val();
    var village = $('#f_village').val();

    $.ajax({
        url: 'dropdownlist/',
        type: 'POST',
        dataType: 'json',
        data: {'division': division,'district': district,'upazila': upazila, 'union': union, 'branch': branch ,'village': village},
        success: function (result) {
            // rowData = JSON.parse(result);
            //
            // var tbody = '';
            // for (var i = 0; i < rowData.length; i++) {
            //     tbody += '<tr><td>' + (i + 1) + '</td><td>' + checkNullVal(rowData[i].visit_date) + '</td><td>' + checkNullVal(rowData[i].visitor) + '</td><td>' + checkNullVal(rowData[i].visitor_role) + '</td><td>' + checkNullVal(rowData[i].type_of_visit) + '</td><td>' + checkNullVal(rowData[i].details) + '</td></tr>';
            //         // <td>' + checkNullVal(rowData[i].occupation) + '</td><td>' + checkNullVal(rowData[i].disability) + '</td><td></td><td></td><td>' + checkNullVal(rowData[i].member_status) + '</td></tr>';
            // }
            // $('#hh_visit_log').find('tbody').html(tbody);
        }
    });
}



//TUP @zinia
function generateHouseHoldVisitList(active_hh_id) {
    $.ajax({
        url: 'visitlist/',
        type: 'POST',
        dataType: 'json',
        data: {'profile_id': active_hh_id},
        success: function (result) {
            rowData = JSON.parse(result);

            var tbody = '';
            for (var i = 0; i < rowData.length; i++) {
                tbody += '<tr><td>' + (i + 1) + '</td><td>' + checkNullVal(rowData[i].visit_date) + '</td><td>' + checkNullVal(rowData[i].visitor) + '</td><td>' + checkNullVal(rowData[i].visitor_role) + '</td><td>' + checkNullVal(rowData[i].type_of_visit) + '</td><td>' + checkNullVal(rowData[i].details) + '</td></tr>';
                    // <td>' + checkNullVal(rowData[i].occupation) + '</td><td>' + checkNullVal(rowData[i].disability) + '</td><td></td><td></td><td>' + checkNullVal(rowData[i].member_status) + '</td></tr>';
            }
            $('#hh_visit_log').find('tbody').html(tbody);
        }
    });
}
//TUP @zinia
function generateHouseHoldMemberList(active_hh_id) {
    $.ajax({
        url: 'memberlist/',
        type: 'POST',
        dataType: 'json',
        data: {'profile_id': active_hh_id},
        success: function (result) {
            rowData = JSON.parse(result);
            console.log('inside household')
            console.log(rowData)
            var tbody = '';
            for (var i = 0; i < rowData.length; i++) {
                tbody += '<tr><td>' + (i + 1) + '</td><td>' + checkNullVal(rowData[i].name) + '</td><td>' + checkNullVal(rowData[i].age) + '</td><td>' + checkNullVal(rowData[i].gender) + '</td><td>' + checkNullVal(rowData[i].member_relationship_id) + '</td><td>' + checkNullVal(rowData[i].involved_iga) + '</td><td>' + checkNullVal(rowData[i].maritial_status) + '</td></tr>';
            }
            $('#hh_member_list').find('tbody').html(tbody);
            $('#hh_member_list').fadeIn("slow");
        }
    });
}


function generateSnapShotData(active_hh_id) {
    $.ajax({
        url: '/hhmodule/snapshot-data/',
        type: 'POST',
        dataType: 'json',
        data: {'profile_id': active_hh_id},
        success: function (result) {
            rowData = JSON.parse(result);

            var tbody = '';
            for (var i = 0; i < rowData.length; i++) {
                tbody += '<tr><td>' + rowData[i].respondent_name + '</td><td>' + rowData[i].visit_date + '</td><td>' + rowData[i].visit_type + '</td><td>' + rowData[i].sender + '</td><td style="text-align: center;"><a href = /'+rowData[i].form_owner+'/forms/snapshot_form_v3/instance/?s_id='+rowData[i].id+'#/'+rowData[i].id+' class="btn red">Details</a></td></tr>';
            }
            $('#snapshot_table').find('tbody').html(tbody);
        }
    });
}

//TUP @zinia
function generateHHProfile(rowData) {
    hh_data = JSON.parse(rowData)[0];
    //place data to household profile
    $('#profile_hh_id').html(hh_data.hh_id);
    $('#profile_name').html(hh_data.hh_name);
    $('#profile_age').html(hh_data.age);
    $('#profile_gender').html(hh_data.gender);
    $('#profile_wealth').html(hh_data.wealth_rank);
    $('#profile_cohort').html(hh_data.cohort);
    $('#profile_hh_status').html(hh_data.hh_status);
    //transition of tables
    $('#hh_table').fadeOut("slow");
    $('html,body').animate({scrollTop: 0}, 0);
    $('#hh_profile').fadeIn("slow");
    // generateHouseHoldMemberLsit(hh_data.hh_id);
    generateHouseHoldMemberList(hh_data.hh_id);

    generateHouseHoldVisitList(hh_data.hh_id);
    // generateSnapShotData(hh_data.hh_id);
    // generateHH_Analytics(hh_data.hh_id);    //  Dashboard_HH_Analytics (cup_hh_profile_hh_analyst_dashboard.js)
    // getChangesExpenditureData(hh_data.hh_id,5);
    // getOverAllPerformanceTable(hh_data.hh_id);
    //drawHouseholdMap();
}

function loadHouseholdList() {
    $('#hh_table').fadeIn("slow");
    $('html,body').animate({scrollTop: 0}, 0);
    $('#hh_profile').fadeOut("slow");
    $('#hh_member_lsit').find('tbody').html('');
    $('#filter-form').show();
}


function checkNullVal(field_value) {
    if (field_value == null) {
        return 'N/A';
    } else {
        return field_value;
    }
}

function checkNullMobileNumber(field_value) {
    if (field_value == null) {
        return '<center><i style="cursor: pointer;" onclick="updateMobileNumber(this);" class="fa fa-pencil"></i></center>';
    } else {
        return field_value;
    }
}

function generate_drop_down(villageData, divisionData, districtData, branchData,unionData, upazilaData){
    console.log("dropdown");
    generate_village_dropdown(villageData);
    generate_division_dropdown(divisionData);
    generate_district_dropdown(districtData);
    generate_branch_dropdown(branchData);
    generate_union_dropdown(unionData);
    generate_upazila_dropdown(upazilaData);
}

function generate_village_dropdown(villageData) {
    for (var i = 0; i < villageData.length; i++) {
        $('#f_village').append($("<option></option>").attr("value", villageData[i].id).text(villageData[i].name));
    }
}

function generate_division_dropdown(divisionData) {
    for (var i = 0; i < divisionData.length; i++) {
        $('#f_division').append($("<option></option>").attr("value", divisionData[i].id).text(divisionData[i].name));
    }
}
function generate_district_dropdown(districtData) {
    for (var i = 0; i < districtData.length; i++) {
        $('#f_district').append($("<option></option>").attr("value", districtData[i].id).text(districtData[i].name));
    }
}
function generate_branch_dropdown(branchData) {
    for (var i = 0; i < branchData.length; i++) {
        $('#f_branch').append($("<option></option>").attr("value", branchData[i].id).text(branchData[i].name));
    }
}
function generate_union_dropdown(unionData) {
    for (var i = 0; i < unionData.length; i++) {
        $('#f_union').append($("<option></option>").attr("value", unionData[i].id).text(unionData[i].name));
    }
}
function generate_upazila_dropdown(upazilaData) {
    for (var i = 0; i < upazilaData.length; i++) {
        $('#f_upazila').append($("<option></option>").attr("value", upazilaData[i].id).text(upazilaData[i].name));
    }
}

function filterHouseHoldList() {
    var f_hh_division = $('#f_division').val();
    var f_hh_district = $('#f_district').val();
    var f_hh_upazila = $('#f_upazila').val();
    var f_hh_village = $('#f_village').val();
    var f_hh_branch = $('#f_branch').val();
    var f_hh_union = $('#f_union').val();

    var params = {};
    if (f_hh_id != '') {
        params['f_division'] = f_hh_division;
    }
    if (f_hh_head_name != '') {
        params['f_district'] = f_hh_district;
    }
    if (f_hh_ward != 'custom') {
        params['f_upazila'] = f_hh_upazila;
    }
    if (f_hh_mobile != '') {
        params['f_village'] = f_hh_village;
    }
    if (f_hh_mobile != '') {
        params['f_union'] = f_hh_union;
    }
    if (f_hh_mobile != '') {
        params['f_branch'] = f_hh_branch;
    }



    $.ajax({
        url: '/hhmodule/household-filter/',
        type: 'POST',
        dataType: 'json',
        data: params,
        success: function (result) {
            rowData = JSON.parse(result);
            var tbody = '';
            for (var i = 0; i < rowData.length; i++) {
                tbody += '<tr><td>' + checkNullVal(rowData[i].hh_id) + '</td><td>' + checkNullVal(rowData[i].hhhead_name) + '</td><td>' + checkNullVal(rowData[i].holding_no) + '</td><td>' + checkNullVal(rowData[i].ward) + '</td><td>' + checkNullVal(rowData[i].hh_phone) + '</td><td>' + checkNullVal(rowData[i].hh_status) + '</td><td><a class="btn red" onclick="getProfile(\'' + rowData[i].hh_id + '\')" role="button">Profile</a></td></tr>';
            }
            $('#hh_table').find('tbody').html(tbody);
        }
    });
}

function editHouseHold() {
    var active_hh_id = $('#active_hh_id').val();
    createCookie("active_hh_id", active_hh_id);
    window.location.href = '/hhmodule/add_household/'

}

function addNewSLA() {
    window.location = '/hhmodule/add_sla/';
}

function loadSLAlist() {
    window.location = '/hhmodule/cupdashboard/#tab_1_3';
}


function UpdateBeneficiaryList() {
    //console.log("row data start@@@@@@@");
    var geo_ward = $("#id_geo_ward").val();
    if (geo_ward != '') {
        $.ajax({
            url: '/hhmodule/update-beneficiary/',
            type: 'POST',
            dataType: 'json',
            data: {'geo_ward': geo_ward},
            success: function (result) {
                rowData = JSON.parse(result);
                //console.log("row data add");
                console.log(rowData);
                if (rowData.length > 0) {
                    var tbody = '';
                    for (var i = 0; i < rowData.length; i++) {
                        tbody += '<tr><td>' + checkNullVal(rowData[i].name) + '</td><td>' + checkNullVal(rowData[i].member_id) + '</td><td>' + checkNullVal(rowData[i].gender) + '</td><td>' + checkNullMobileNumber(rowData[i].mobile_no) + '</td><td><select class = "member_status"><option value = "">Select</option><option value = "1" selected>Active</option><option value="2">Left Group</option><option value = "3">Migrated</option></select></td><td><input type="checkbox" class = "status_check" name="selected_members[]" id="' + rowData[i].id + '" value="' + rowData[i].id + '"></td></tr>';
                    }
                    $('#beneficiary_block').html('<table class="table table-bordered table-hover" id=beneficiary_table><thead><tr><th>Member Name<th>Member ID<th>Gender<th>Mobile No<th>SLA Membership Status<th>Action<tbody></table>');
                    $('#beneficiary_table').find('tbody').html(tbody);
                    $('#beneficiary_table').dataTable({
                        "bFilter": true,
                        "paging": false,
                        "scrollY": "300px",
                        "scrollCollapse": true,
                        "aoColumns": [
                            null,
                            null,
                            //null,
                            null,
                            null,
                            {"bSortable": false},
                            {"bSortable": false}
                        ]
                    });
                }
            }
        });
    }
}


function updateMobileNumber(obj) {
    var member_id = $(obj).parents().eq(2).find("td:eq(1)").html();
    $(obj).parent().html('<input maxlength="11" pattern="\d*" type="text" id="member_' + member_id + '"/><span onclick="ajaxSendMobileNumber(\'' + member_id + '\',this)" class="btn btn-sm red">Submit</span>')
}

function ajaxSendMobileNumber(mem_id, obj) {
    var mobile_number = $('#member_' + mem_id).val();
    $.ajax({
        url: '/hhmodule/update-mobile-number/',
        type: 'POST',
        dataType: 'json',
        data: {'mobile_number': mobile_number, 'member_id': mem_id},
        success: function (result) {
            $(obj).parent().html(mobile_number);
        }
    });
}

function showBeneficiary(rowData,result){
    var check = "", val = "", hhmember_id = "",slamember_id = "", active_str = "", leftGroup_str = "", migrated_str = "", member_status = 0;
    if (rowData.length > 0) {
        var tbody = '';
        for (var i = 0; i < rowData.length; i++) {
            check = "";val = rowData[i].id;
            //iterate selected sla members
            for (var j = 0; j < result.length; j++) {                                   
                hhmember_id = rowData[i].member_id;slamember_id = result[j].member_id;
                var n = parseInt(hhmember_id.localeCompare(slamember_id));
                if(n == 0){
                    console.log("matched");
                    active_str = "", leftGroup_str = "", migrated_str = "";
                    member_status = parseInt(result[j].membership_status);
                    check = "checked";val = rowData[i].id+","+result[j].membership_status;
                    if(member_status == 1){
                        active_str = "selected", leftGroup_str = "", migrated_str = "";
                    }
                    if(member_status == 2){
                        active_str = "", leftGroup_str = "selected", migrated_str = "";
                    }
                    if(member_status == 3){
                        active_str = "", leftGroup_str = "", migrated_str = "selected";
                    }
                    if( parseInt(flag_for_view) == 1){
                        tbody += '<tr><td>' + checkNullVal(rowData[i].name) + '</td><td>' + checkNullVal(rowData[i].member_id) + '</td><td>' + checkNullVal(rowData[i].gender) + '</td><td>' + checkNullMobileNumber(rowData[i].mobile_no) + '</td><td><select disabled="disabled" class = "member_status"><option value = "">Select</option><option '+active_str+'  value = "1" >Active</option><option '+leftGroup_str+'  value="2">Left Group</option><option  '+migrated_str+' value = "3">Migrated</option></select></td><td><input disabled="disabled" type="checkbox"'+ check +'  class = "status_check" name="selected_members[]" id="' + rowData[i].id + '" value="' + val + '"></td></tr>';
                    }
                }
               //console.log(active_str+","+leftGroup_str+","+migrated_str);
            }
            //tbody += '<tr><td>' + checkNullVal(rowData[i].name) + '</td><td>' + checkNullVal(rowData[i].member_id) + '</td><td>' + checkNullVal(rowData[i].gender) + '</td><td></td><td>' + checkNullMobileNumber(rowData[i].mobile_no) + '</td><td><select class = "member_status"><option value = "">Select</option><option ' + (member_status == 1 ? "selected" : "")+  ' value = "1" >Active</option><option '+ (member_status == 2 ? "selected" : "")+ ' value="2">Left Group</option><option '+ (member_status == 3 ? "selected" : "")+ ' value = "3">Migrated</option></select></td><td><input type="checkbox"'+ check +'  class = "status_check" name="selected_members[]" id="' + rowData[i].id + '" value="' + val + '"></td></tr>';
            if( parseInt(flag_for_view) == 1){
                //do nothing
            }
            else{
                tbody += '<tr><td>' + checkNullVal(rowData[i].name) + '</td><td>' + checkNullVal(rowData[i].member_id) + '</td><td>' + checkNullVal(rowData[i].gender) + '</td><td>' + checkNullMobileNumber(rowData[i].mobile_no) + '</td><td><select class = "member_status"><option value = "">Select</option><option '+active_str+'  value = "1" >Active</option><option '+leftGroup_str+'  value="2">Left Group</option><option  '+migrated_str+' value = "3">Migrated</option></select></td><td><input type="checkbox"'+ check +'  class = "status_check" name="selected_members[]" id="' + rowData[i].id + '" value="' + val + '"></td></tr>';
                active_str = "", leftGroup_str = "", migrated_str = "";
            }
        }
            
        $('#beneficiary_block').html('<table class="table table-bordered table-hover" id=beneficiary_table><thead><tr><th>Member Name<th>Member ID<th>Gender<th>Mobile No<th>SLA Membership Status<th><tbody></table>');
        $('#beneficiary_table').find('tbody').html(tbody);
        $('#beneficiary_table').dataTable({
            "bFilter": true,
            "paging": false,
            "scrollY": "300px",
            "scrollCollapse": true,
            "aoColumns": [
                null,
                null,
                //null,
                null,
                null,
                {"bSortable": false},
                {"bSortable": false}
            ]
        });
    }
}


function checkMobileNumber(obj){
    console.log(obj.value);
    if(!isNaN(parseInt(obj.value))){
        str_length = obj.value.length;
        if(str_length >= 8 && str_length <= 11){
            //Do nothing
        }
        else{
            alert("Phone number must be 8 to 11 digits!");
        }
    }
    else{
        alert("Please enter a valid number");
        //this.clear()
    }

    
}

function checkEndDate(){
    console.log("check end date triggered");
    var startDate = new Date($('.start_date_class').val());
    var endDate = new Date($('.end_date_class').val());
    //console.log(ob.value);
    //console.log(endDate);

    if (startDate >=  endDate){
        //alert("SLA Cycle End date should be greater than SLA Formation date");
        //alertify.alert('end date is not smaller than startdate');
        $("#hh_sla_modal").modal('show');
        $('.end_date_class').val('');
    }
}

function checkInteger(ob){
    console.log(ob.value);
     var str1 = "mkyong"
     if(isNaN(ob.value)){
       alert(ob.value+" is not a number.");
       $('#id_sla_member_count').val('');
     }else{
        //do nothing
     }
}


function getNotAssignedHHData(rowData){
    
    if (rowData.length > 0) {
                    var tbody = '';
                    for (var i = 0; i < rowData.length; i++) {
                        tbody += '<tr id = '+rowData[i].id+'><td>' + checkNullVal(rowData[i].hh_id) + '</td><td>' + checkNullVal(rowData[i].head) + '</td><td>' + checkNullVal(rowData[i].holding_no)  + '</td><td><input class = "common" type = "checkbox" id = '+rowData[i].id+' value = '+rowData[i].id+'  name = ""></input></td></tr>';
                    }
                    $('#hh_block').html('<table style="width : 50%" class="table table-bordered table-hover" id=hhDataTable><thead><tr><th>household id<th>Head<th>Holding No<th>Action<tbody></table>');
                    $('#hhDataTable').find('tbody').html(tbody);
                    var dataTbl = $('#hhDataTable').dataTable({
                        "bFilter": true,
                        "paging": true,
                        "scrollY": "300px",
                        "scrollCollapse": true,
                        "aoColumns": [
                            null,
                            null,
                            null,
                            null//,
                            //null,
                            //{"bSortable": false},
                            //{"bSortable": false}
                        ]
                    });
                    console.log(dataTbl);
                }
}

function updateNotAssignedList(){
    console.log("changed not assigned list");
    var geo_ward = $("#geo_ward_id").val();
    if (geo_ward != '') {
        $.ajax({
            url: '/hhmodule/updateNotAssignedList/',
            type: 'POST',
            dataType: 'json',
            data: {'geo_ward': geo_ward},
            success: function (result) {
                rowData = result;
                console.log(rowData);
                if (rowData.length > 0) {
                    var tbody = '';
                    for (var i = 0; i < rowData.length; i++) {
                        tbody += '<tr id = '+rowData[i].id+'><td>' + checkNullVal(rowData[i].hh_id) + '</td><td>' + checkNullVal(rowData[i].head) + '</td><td>' + checkNullVal(rowData[i].holding_no)  + '</td><td><input class = "common" type = "checkbox" id = '+rowData[i].id+' value = '+rowData[i].hh_id+'  name = ""></input></td></tr>';
                    }
                    $('#hh_block').html('<table style="width : 50%" class="table table-bordered table-hover" id=hhDataTable><thead><tr><th>Household id<th>Head<th>Holding No<th>Toggle all <input id = "select_all" type = "checkbox" ></input><tbody></table>');
                    $('#hhDataTable').find('tbody').html(tbody);
                    dataTbl = $('#hhDataTable').DataTable({
                        "bFilter": true,
                        "paging": true,
                        "scrollY": "300px",
                        "scrollCollapse": true,
                        "aoColumns": [
                            null,
                            null,
                            null,
                            null//,
                            //null,
                            //{"bSortable": false},
                            //{"bSortable": false}
                        ]
                    });

                    //load empty assigned table
                    /*$('#hh_assign_block').html('<table style="width : 50%" class="table table-bordered table-hover" id=assignedTable><thead><tr><th>household id<th>Head<th>Holding No<th>Action<tbody></table>');
                   /// $('#hhDataTable').find('tbody').html(tbody);
                    var dataTblAssign = $('#assignedTable').DataTable({
                        "bFilter": true,
                        "paging": true,
                        "scrollY": "300px",
                        "scrollCollapse": true,
                        "aoColumns": [
                            null,
                            null,
                            null,
                            null//,
                            //null,
                            //{"bSortable": false},
                            //{"bSortable": false}
                        ]
                    });*/
                    dataTblAssign
                    .clear()
                    .draw();
                    
                }
            }
        });
    
    }
}

function getChangesData() {
    console.log("kk::"+this.val);
    var hhId = $('#active_hh_id').val();
    paramId = $('#exp_changes_id').val();
    getChangesExpenditureData(hhId,paramId);

}

function getAssignedHHList(){
    console.log("trigger assigned list");
    var enum_id = $("#enum_id").val();
    if (enum_id != '') {
        $.ajax({
            url: '/hhmodule/getAssignedList/',
            type: 'POST',
            dataType: 'json',
            data: {'enum_id': enum_id},
            success: function (result) {
                //console.log("successfully rendered");
                console.log(result);
                var rowData = result;
                 dataTblAssign
                    .clear()
                    .draw();
                 if (rowData.length > 0) {
                     var tbody = '';

                     for (var i = 0; i < rowData.length; i++) {
                         tbody += '<tr id = ' + rowData[i].id + '><td>' + checkNullVal(rowData[i].hh_id) + '</td><td>' + checkNullVal(rowData[i].head) + '</td><td>' + checkNullVal(rowData[i].holding_no) + '</td><td><input class = "common2" type = "checkbox" checked   value = ' + rowData[i].hh_id + '   name="selected_households[]"></input></td></tr>';
                     }
                     //$('#hh_block').html('<table style="width : 50%" class="table table-bordered table-hover" id=hhDataTable><thead><tr><th>Household id<th>Head<th>Holding No<th>Toggle all <input id = "select_all" type = "checkbox" ></input><tbody></table>');
                     $('#hh_assign_block').html('<table style="width : 50%" class="table table-bordered table-hover" id=assignedTable><thead><tr><th>Household id<th>Head<th>Holding No<th>Toggle all <input id = "select_all_assign" type = "checkbox" checked ></input><tbody></table>');
                     $('#assignedTable').find('tbody').html(tbody);
                     dataTblAssign = $('#assignedTable').DataTable({
                        "bFilter": true,
                        "paging": true,
                        "scrollY": "300px",
                        "scrollCollapse": true,
                        "aoColumns": [
                            null,
                            null,
                            null,
                            null//,
                            //null,
                            //{"bSortable": false},
                            //{"bSortable": false}
                        ]
                     });

                 }


            }
        });

    }
}
