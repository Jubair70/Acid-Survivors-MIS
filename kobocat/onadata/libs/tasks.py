__author__ = "Md Shiam Shabbir"
import os
import json
from django.db import connection
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from onadata.apps.logger.models import Instance, XForm

from celery import task

from celery.decorators import task
#from onadata.apps.main.database_utility import db_fetch_values, single_query, update_table
from datetime import timedelta
from celery.task.schedules import crontab
from celery.decorators import periodic_task

questionsDict = {}
groupNameList = []



'''
    Tup related asyn process
    @zinia
'''


def update_table(query):
    try:
        print query
        # create a new cursor
        cur = connection.cursor()
        # execute the UPDATE  statement
        cur.execute(query)
        # get the number of updated rows
        vendor_id = cur.fetchone()[0]
        print vendor_id
        # Commit the changes to the database_
        connection.commit()
        # Close communication with the PostgreSQL database
        cur.close()
    except (Exception) as error:
        print(error)
    finally:
        if connection is not None:
            connection.close()


def single_query(query):
    """function for  query where result is single"""

    fetchVal = db_fetch_values(query)
    if len(fetchVal) == 0:
        return None
    strType = map(str, fetchVal[0])
    ans = strType[0]
    return ans



def db_fetch_values(query):
    """
        Fetch database result set as list of tuples

        Args:
            query (str): raw query string

        Returns:
            str: Returns database result set as list of tuples
    """
    cursor = CONNECTION.cursor()
    cursor.execute(query)
    fetch_val = cursor.fetchall()
    cursor.close()
    return fetch_val


@periodic_task(run_every=timedelta(seconds=10),name="populate_table_queue")
def queue_info_insert():
    print "#####################task enter###################"
    '''Getting all new instance in the queue '''
    try:
        instance_query = "select id, instance_id, xform_id from instance_queue where status='new'"
        instance_queue = db_fetch_values(instance_query)
        print 'inside'
        '''calling procedure according form_id '''
        for each in instance_queue:
            function_query = 'select function_name from form_function where form_id =%s'%(each[2])
            form_function = single_query(function_query)
            if form_function is not None:
                insert_data_query = "select %s(%s)"%(form_function,each[1])
                result = single_query(insert_data_query)
                if result == '0':
		    print 'update'	
                    update_instance = "update instance_queue set status='old' and updated_at = now() where instance_id = %s"%(each[1])
                    update_table(update_instance)

    except Exception, e:
        print "db get error"
        print str(e)

    print "#####################task exit###################"






class Question:
    """This class represents a question object which stores
    question name,question type and question label if exists."""
    name = ''
    question_type = ''
    question_label = ''

    def __init__(self, q_name,q_type,q_label):
        self.name = q_name
        self.question_type = q_type
        self.question_label = q_label
    def getQuestion_name(self):
        return str(self.name)
    def getQuestion_type(self):
        return str(self.question_type)
    def getQuestion_label(self):
        return str(self.question_label)
        
@task()
def instance_parse():
    #print 'success'
    json_instances = get_instance_info()

    parsed_json = json.loads(json_instances)
    print parsed_json
    for key in parsed_json:
        questionsDict.clear()
        del groupNameList[:]
        try:
         username =  parsed_json[key]['username']
         id_string =  parsed_json[key]['xform_id_string']
         json_q_data = json.loads(get_form_json(username,id_string))
         #print json_data['children']
         question_parsed = parseQuestions(json_q_data['children'],'',None)
         if question_parsed:
            json_instance_data = get_form_instance_data(username,id_string,int(key))
            if json_instance_data is not None:
                process_data_and_save(json_instance_data,username,id_string,int(key))
        except Exception as e:
            print e
        
    

def get_instance_info():
    cursor = connection.cursor()
    query = "select instance_to_parse.form_id_string,instance_to_parse.form_instance_id,instance_to_parse.form_id_int from instance_to_parse where is_new=TRUE "


    #in (select instance_id from approval_instanceapproval where status like 'Approved')
    try:
        cursor.execute(query)
        form_informations = cursor.fetchall()
        rowcount = cursor.rowcount
    except Exception as e:
        print e
        connection.rollback()
    form_info_json = {}

    #print form_informations
    for info in form_informations:
        data={}
        form_id = int(info[2])
        #print form_id
        try:
            xform = get_object_or_404(XForm, pk=form_id)
            user_id = xform.user_id
            owner = get_object_or_404(User, pk=user_id)
            data['username'] = str(owner.username)
            data['xform_id_string'] = str(xform.id_string)
            form_info_json[str(info[1])] = data
        except Exception as e:
            print e
            connection.rollback()
        #print owner.username
    cursor.close()
    return json.dumps(form_info_json)

def get_form_json(username,id_string):
    owner = get_object_or_404(User, username__iexact=username)
    xform = get_object_or_404(XForm, user__username__iexact=username,
                              id_string__exact=id_string)

    return xform.json


def parseQuestions(children,prefix,cleanReplacement):
    idx = 0
    if cleanReplacement is None:
        cleanReplacement = '_'
    for idx in range(len(children)):
        question = children[idx]
        q_name = question.get('name',None)
        q_type = question.get('type',None)
        q_label = question.get('label',None)
        sub_children = question.get('children',None)
        #print sub_children
        if (sub_children is not None and (q_type == 'repeat' or q_type == 'group' or q_type == 'note')):
            #print sub_children
            groupNameList.append(str(q_name))
            #print '####Group_q_name: '+str(q_name)
            parseQuestions(question['children'],''+q_name+cleanReplacement,None)
        else:
            if prefix is not None:
                questionsDict[str(prefix)+str(q_name)] = Question(q_name,q_type,q_label if q_label is not None else '')
            else:
                questionsDict[str(q_name)] = Question(q_name,q_type,q_label if q_label is not None else '')
    #print str(groupNameList)
    '''for key in questionsDict:
                    print questionsDict[key].getQuestion_name()'''
    return True



def get_form_instance_data(username, id_string, instance_id):    
    #print instance_id
    instance = None
    try:
        xform = get_object_or_404(XForm, user__username__iexact=username, id_string__exact=id_string)
        instance = get_object_or_404(Instance, id=instance_id)
    except Exception as e:
        print e

    return instance.json


def process_data_and_save(data,username,id_string,instance_id):
    questionWithVal = {}
    
    cleanRe = '/[\[\]\/]/g'
    cleanReplacement = '_' 
    if data is not None:
        cleanData = {}
        print ('Data is currently Processing and trying to save...... ')
        for key in data:
            test_bool = False
            q_value = data[key]
            if any(grp_name in key for grp_name in groupNameList): 
                try:
                    isinst = isinstance(q_value, list)
                    if isinst:
                       # print '########################################'
                        for each in q_value:
                            for sub_key, value in each.iteritems():
                                #print sub_key,value
                                cleanKey = sub_key.replace('/','_')
                                if str(cleanKey) in cleanData:
                                    cleanData[str(cleanKey)] += ','+ value.encode('utf8')
                                else:
                                    cleanData[str(cleanKey)] = value.encode('utf8')
                    #print str(q_value)
                    else:
                        cleanKey = str(key).replace('/','_')
                        #print 'cleanKey: '+ str(cleanKey)
                        cleanData[str(cleanKey)] = q_value.encode('utf8')
                        test_bool = True
                except Exception as e:
                    print e
                #print str(key).split('/')[1]
                #print 'matched'
            else:
                cleanKey = key.replace(cleanRe,cleanReplacement)
                test_bool = False
                cleanData[str(cleanKey)] = q_value.encode('utf8')
           # if test_bool is True:
            #    print str(cleanData)
        for q_key in questionsDict:
            #print q_key
            value = {}
            ques_name  = q_key
            ques_label = questionsDict[q_key].getQuestion_label()
            ques_type  = questionsDict[q_key].getQuestion_type()
            ques_value = cleanData.get(q_key,None)
            
            
            value.update({
                'question_label': str(ques_label),
                'question_type' : str(ques_type),
                'question_value' : str(ques_value)
                })
            if ques_value is not None:
                questionWithVal[ques_name] = value
                #value.clear()
        try:
            cursor = connection.cursor()
            for key in questionWithVal:
                group_name = ''
                #print questionWithVal.get(key,None)
                if 'question_group' in questionWithVal[key]:
                    group_name = str(questionWithVal[key]['question_group'])
                cursor.execute("BEGIN")
                cursor.callproc("set_instance_parse_data",(str(id_string),int(instance_id),str(key),json.dumps(questionWithVal[key])))
                cursor.execute("COMMIT")
            update_is_new_query = "UPDATE public.instance_to_parse SET is_new = FALSE WHERE form_instance_id = "+str(instance_id)
            cursor.execute(update_is_new_query)
            #print update_is_new_query  
            cursor.close()
        except Exception as e:
            print e
    # Open a file
    #fo = open("q_dict.txt", "wb")
    #fo.write( str(questionWithVal));

    # Close opend file
    #fo.close()
    #print str(questionWithVal)
    

    

    
