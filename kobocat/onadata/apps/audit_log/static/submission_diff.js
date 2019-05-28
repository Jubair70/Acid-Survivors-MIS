var GROUP_TYPE;
var Groups=[];
Question = function(questionData)
{
    this.name = questionData.name;
    this.type = questionData.type;
    this.label = questionData.label;
}

Group = function(group_no,question,response)
{
    this.group_no = group_no;
    this.question = question;
    this.response = response;
}

Question.prototype.getLabel = function(language)
{
    /// if plain string, return
    if(typeof(this.label) == "string")
        return this.label;
    else if(typeof(this.label) == "object")
    {
        if(language && this.label.hasOwnProperty(language))
            return this.label[language];
        else
        {
            var label = null;
            for(key in this.label)
            {
                label = this.label[key];
                break;// break at first instance and return that
            }
            return label;
        }

    }
    // return raw name
    return this.name;
}

function parseQuestions(children, prefix, cleanReplacement)
{
    var idx;
    cleanReplacement = typeof cleanReplacement !== 'undefined' ? cleanReplacement : '_';

    for(idx in children)
    {
        var question = children[idx];
        //@TODO: do we just want to add anything with children, concern could be it item has children and is alos avalid question - if thats possible
        if(question.hasOwnProperty('children') && ( question.type == "note" || question.type == "repeat" || question.type == "group"))
        {
            if((typeof question.label!='undefined')||question.type.toLowerCase() === 'repeat'){
                GROUP_TYPE = question.type;
                //console.log('GROUP_TYPE '+GROUP_TYPE);
            }
            parseQuestions(question.children, ((prefix?prefix:'') + question.name + cleanReplacement));
        }
        else
        {
            // TODO: question class that has accessor mesthods for type, label, language etc
            questions[((prefix?prefix:'') + question.name)] = new Question(question);
        }
    }
}

function parseLanguages(children)
{
    // run through question objects, stop at first question with label object and check it for multiple languages
    for(questionName in children)
    {
        var question = children[questionName];
        if(question.hasOwnProperty("label"))
        {
            var labelProp = question["label"];
            if(typeof(labelProp) == "string")
                languages = ["default"];
            else if(typeof(labelProp) == "object")
            {
                for(key in labelProp)
                {
                    languages.push(key)
                }
            }
            break;
        }
    }
    if (languages.length == 0) {
        languages.push('en');
    }
}

function redirectToFirstId(context)
{
    $.getJSON(postgresAPIUrl)
            .success(function(data){
                //alert('success');
                if(data.length > 0)
                    context.log('Routing');
                    context.redirect('#/id');
                    
            })
            .error(function(){
                alert('error');
                app.run('#/');
            })
}

function loadOldData(context, query, canEdit)
{

    //console.log('loading data...');
    //TODO: show loader
    $.getJSON(postgresAPIUrl)
            .success(function(data){
                reDraw(context, data, canEdit,true);
                //alert(data[0]['_id']);
                // check if we initialised the browsePos
                loadNewData(context, query, canEdit);
                
            })
            .error(function(){
                alert(gettext("BAD REQUEST"));
            })
}
function loadNewData(context, query, canEdit)
{

    //console.log('loading data...');
    //TODO: show loader
    $.getJSON(postgresAPIUrl2)
            .success(function(data){
                reDraw(context, data, canEdit,false);
                //alert(data[0]['_id']);
                // check if we initialised the browsePos
                
            })
            .error(function(){
                alert(gettext("BAD REQUEST"));
            })
}

function isArray(what) {
    return Object.prototype.toString.call(what) === '[object Array]';
}

function reDraw(context, data, canEdit,isOld)
{
    // make sure we have some data, if the id was in valid we would gte a blank array
    if(data)
    {
        var cleanData = {};
        /*------custom group data view start---------*/
        // check for group types if it is a group type with no repeat then we do not need to proces it. 
        //console.log('HIMEL group type: '+ GROUP_TYPE);
    /*if((typeof GROUP_TYPE!='undefined') && GROUP_TYPE!='group'){
         var key;
         var index =0;
         var group_no = 1;
        for(key in data){
            var cleanKey = key.replace(cleanRe, cleanReplacement);
            //console.log('key '+key+'cleanRe: '+cleanRe+' cleankey: '+cleanKey);
          
                    if( key.indexOf("group") >- 1 ){
                    
                    for(var child in data[key]){
                        var childkey;
                       for(var childob in data[key][child]){
                         childkey = childob.toString();
                         //console.log('childkey: '+childkey);
                         childkey = childkey.replace(key,"").replace(cleanRe,"");
                         
                         Groups[index] = new Group(group_no,childkey,(data[key][child][childob]).toString());
                          //console.log('stringified: '+childkey );
                          if( data.hasOwnProperty(childkey) )
                            data[childkey] += ' , '+data[key][child][childob] ;
                        else
                            data[childkey] = data[key][child][childob];
                        index++;
                       }
                       group_no++;
                    }
                    }        
        }
    }
    else if(GROUP_TYPE==="group"){
        var index = 0;
        var group_no = 1;
        for(key in data){
            if( key.indexOf("group") >- 1 ){
               var cleanKey= key.slice(0, key.indexOf("/"));
               var newKey = key.split('/')[1];
               data[newKey] = data[key]; 
            Groups[index] = new Group(group_no,newKey,(data[key]).toString());
            //var cleanKey = key.replace(cleanRe, cleanReplacement);
               //console.log('key '+key+'cleanRe: '+cleanRe+' newkey: '+newKey+ ' data[newKey]'+ data[newKey]);
               index++;
            }
        }
    }*/

    /*------custom group data view end---------*/
        
           
       
        //console.log('modified data: '+JSON.stringify(data));
        var key;
        for(key in data)
        {
            var value = data[key];
            if (isArray(value)){
                for (var idx in value){
                    var val_array = value[idx];
                    for(var sub_key in val_array){
                        //console.log(sub_key); 
                        var cleanKey = sub_key.replace(cleanRe, '_');
                        
                        if (cleanData.hasOwnProperty(cleanKey))
                            cleanData[cleanKey] = cleanData[cleanKey]+'<br>'+val_array[sub_key];   
                        else
                            cleanData[cleanKey] = val_array[sub_key];
                        //console.log(cleanData[cleanKey]);
                    }
                }
                
            }else{

            var cleanKey = key.replace(cleanRe, cleanReplacement);
            // check if its an image, audio or video and create thumbs or links to
            if(questions.hasOwnProperty(cleanKey))
            {
                if(questions[cleanKey].type == 'image' || questions[cleanKey].type == 'photo')
                {
                    var src = _attachment_url(value, 'small');
                    var href = _attachment_url(value, 'medium');
                    var imgTag = $('<img/>').attr('src', src);
                    value = $('<div>').append($('<a>').attr('href', href).attr('target', '_blank').append(imgTag)).html();
                }
                else if(questions[cleanKey].type == 'audio' || questions[cleanKey].type == 'video')
                {
                    var href = _attachment_url(value, 'medium');
                    value = $('<div>').append($('<a>').attr('href', href).attr('target', '_blank').append(value)).html();
                }
            }

            cleanData[cleanKey] = value;
        }
    }
        // check if table has been created, if not reCreate
        if($("#data_before").html()){
            console.log($("#data_before").html());
        } else{
            createTable(canEdit);
            createNewTable(canEdit);
        }
        // if($('#data_before').length == 0){
        //     createTable(canEdit);
        // }if($('#data_after').length == 0){
        //     createNewTable(canEdit);
        // }
        // clear data cells before we re-populate
        
        
        if(isOld){
            $('#data-table td[data-key]').html('');
            context.meld($('#data_before'), cleanData, {
            selector: function(k) {
                k = k.replace(cleanRe, cleanReplacement);
                return '[data-key="' + k + '"]';
            }
        });    
        } else{
            $('#data-table-new td[data-key-new]').html('');
            context.meld($('#data_after'), cleanData, {
            selector: function(k) {
                k = k.replace(cleanRe, cleanReplacement);
                return '[data-key-new="' + k + '"]';
            }
        }); 

        }
        
    
   // var result = document.getElementsByClassName("data_load")[0].innerHTML;
    // console.log(result);
    }
    else
    {
        $('#data_before').empty();
        $('#data_after').empty();
        $('#data_before').html("<h3>" + gettext('The requested content was not found.') + "<h3>");
        $('#data_after').html("<h3>" + gettext('The requested content was not found.') + "<h3>");
        //$('#data').empty();
        //$('#data').html("<h3>" + gettext('The requested content was not found.') + "<h3>");
        
    }
}

function createTable(canEdit)
{
    var dataContainer = $('#data_before'); 
    //dataContainer.empty();

    var table = $('<table id="data-table" class="table table-bordered table-striped"></table');
    var tHead = $('<thead><tr><th class="header" width="12%">' + gettext("Question") + '</th><th class="header" width="12%">' + gettext("Response") + '</th></tr></thead>');
    var tBody = $('<tbody></tbody>');
    var key;
    var GROUP_CREATED = false;
    for(key in questions)
    {
        var question = questions[key];
        var tdLabel = $('<td style="width:12%"></td>');
        var idx;
      //  console.log('question: '+question.name+ ' key:'+ key);
        if( key.indexOf("group") >- 1){
         if( (GROUP_TYPE === "repeat" && !GROUP_CREATED)|| (GROUP_TYPE === "group" && !GROUP_CREATED)){
            
                GROUP_CREATED = true;
                var groupNumber = 0;
                for(var i=0;i<Groups.length;i++){
                    if( groupNumber!=Groups[i].group_no && GROUP_TYPE!="group"){
                        var trGroupHeadData = $('<tr style="color: #fff; background: black;"></tr>');
                        var tdGroupHeadData = $('<td width="12%" style="align:center;color: #fff; background: black;" colspan="2">Group Data '+Groups[i].group_no+'</td>');
                        trGroupHeadData.append(tdGroupHeadData);
                        tBody.append(trGroupHeadData);
                        groupNumber = Groups[i].group_no;     
                    }
                    var tdGroupLabel = $('<td width="12%"></td>');
                    tdGroupLabel.append(Groups[i].question);
                    var trgroupData = $('<tr class="" ></tr>');
                    trgroupData.append(tdGroupLabel);
                    var tdgroupData = $('<td width="12%"></td>');
                    tdgroupData.append(Groups[i].response);
                    trgroupData.append(tdgroupData);
                    tBody.append(trgroupData);
                }
            }
        } else {
            for(idx in languages){
                var language = languages[idx];
                var label = question.getLabel(language);
                var style = "display:none;";
                var spanLanguage = $('<span class="language language-' +idx +'" style="'+ style +'">'+ label +'</span>');
                tdLabel.append(spanLanguage);
            }
        
            var trData = $('<tr class=""></tr>');
        
            trData.append(tdLabel);
            var tdData = $('<td data-key="' + key + '" width="12%"></td>');
            trData.append(tdData);
            tBody.append(trData);

        }
        
    }
    table.append(tHead);
    table.append(tBody);
    dataContainer.append(table);
    

    $('select.language').change(function(){
        setLanguage(languages[parseInt($(this).val())]);
    });

    // set default language
    setLanguage(languages[0]);
}

function createNewTable(canEdit)
{
    var dataContainer = $('#data_after');
    //dataContainer.empty();

    var table = $('<table id="data-table-new" class="table table-bordered table-striped"></table');
    var tHead = $('<thead><tr><th class="header" width="12%">' + gettext("Question") + '</th><th class="header" width="12%">' + gettext("Response") + '</th></tr></thead>');
    var tBody = $('<tbody></tbody>');
    var key;
    var GROUP_CREATED = false;
    for(key in questions)
    {
        var question = questions[key];
        var tdLabel = $('<td width="12%"></td>');
        var idx;
      //  console.log('question: '+question.name+ ' key:'+ key);
        if( key.indexOf("group") >- 1){
         if( (GROUP_TYPE === "repeat" && !GROUP_CREATED)|| (GROUP_TYPE === "group" && !GROUP_CREATED)){
            
                GROUP_CREATED = true;
                var groupNumber = 0;
                for(var i=0;i<Groups.length;i++){
                    if( groupNumber!=Groups[i].group_no && GROUP_TYPE!="group"){
                        var trGroupHeadData = $('<tr style="color: #fff; background: black;"></tr>');
                        var tdGroupHeadData = $('<td width="15%" style="align:center;color: #fff; background: black;" colspan="2">Group Data '+Groups[i].group_no+'</td>');
                        trGroupHeadData.append(tdGroupHeadData);
                        tBody.append(trGroupHeadData);
                        groupNumber = Groups[i].group_no;     
                    }
                    var tdGroupLabel = $('<td width="12%"></td>');
                    tdGroupLabel.append(Groups[i].question);
                    var trgroupData = $('<tr class=""></tr>');
                    trgroupData.append(tdGroupLabel);
                    var tdgroupData = $('<td width="12%"></td>');
                    tdgroupData.append(Groups[i].response);
                    trgroupData.append(tdgroupData);
                    tBody.append(trgroupData);
                }
            }
        } else {
            for(idx in languages){
                var language = languages[idx];
                var label = question.getLabel(language);
                var style = "display:none;";
                var spanLanguage = $('<span class="language language-' +idx +'" style="'+ style +'">'+ label +'</span>');
                tdLabel.append(spanLanguage);
            }
        
            var trData = $('<tr class="" width="12%"></tr>');
        
            trData.append(tdLabel);
            var tdData = $('<td data-key-new="' + key + '"></td>');            
            trData.append(tdData);            
            tBody.append(trData);

        }
        
    }
    table.append(tHead);
    table.append(tBody);
    dataContainer.append(table);
    

    $('select.language').change(function(){
        setLanguage(languages[parseInt($(this).val())]);
    });

    // set default language
    setLanguage(languages[0]);
}

function setLanguage(language)
{
    var idx = languages.indexOf(language);
    if(idx>-1)
    {
        $('span.language').hide();
        $(('span.language-' + idx)).show();
    }
}