var request_user;
function createTableRow(jsondata){
    
    var jsonObj = JSON.parse(jsondata);
    var table = $('#tg-xY4Sf');
    
    var spTableRowData = '';
    
    var length = jsonObj.instances.length;
     console.log(length);
    for (i = 0; i < length; i++){
        var serial = i+1;
        var form_title = jsonObj.instances[i].form_title;
        var form_id_string = jsonObj.instances[i].form_id_string;
        var submitted_by = jsonObj.instances[i].submittedBy;
        var submition_time = jsonObj.instances[i].form_time;
        var instanceID = jsonObj.instances[i].instance_id;
        var data_id = jsonObj.instances[i].data_id;
        var spDataTableRow = $('<tr></tr>');
        var spTableRowData = $('<td class="tg-yw4l" style="width:30px;">'+serial+'</td><td class="tg-yw4l"  align="center" style="width:160px;"><b>'+form_title+'</b><br>('+form_id_string+')</td>'+
            '<td class="tg-yw4l" id="'+submitted_by+'" align="center" style="width:90px; min-width: 20px; margin: 0 auto">'+submitted_by+'</td><td class="tg-yw4l" align="center" style="width:100px;">'+submition_time+'</td>');   

        var spTableRowDiffButton = $('<td class="tg-yw4l" align="center" style="width:90px;">'+
            '<button class="btn" type="button" onclick="gotoDiff(\''+form_id_string+'\',\''+request_user+'\',\''+instanceID+'\',\''+data_id+'\')">View Diff</button></td>');
        spDataTableRow.append(spTableRowData);
        spDataTableRow.append(spTableRowDiffButton);
        table.append(spDataTableRow);   
    }    
}

function gotoDiff(form_id_string,user_id,instance_id,data_id){
     window.open(user_id+'/forms/'+form_id_string+'/difference/'+instance_id+'/did/'+data_id);
       // window.location=user_id+'/forms/'+form_id_string+'/difference/'+instance_id;
    }