# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        pass

    def backwards(self, orm):
        pass

    models = {
        u'hhmodule.geoward': {
            'Meta': {'object_name': 'GeoWard', 'db_table': "'geo_ward'", 'managed': 'False'},
            'code': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150'})
        },
        u'hhmodule.hhmember': {
            'Meta': {'object_name': 'HhMember', 'db_table': "'hh_member'", 'managed': 'False'},
            'age': ('django.db.models.fields.IntegerField', [], {}),
            'disability': ('django.db.models.fields.IntegerField', [], {}),
            'gender': ('django.db.models.fields.IntegerField', [], {}),
            'highest_education_level': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['hhmodule.HighestEducationLevel']"}),
            'household': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['hhmodule.Household']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member_id': ('django.db.models.fields.CharField', [], {'max_length': '19'}),
            'member_relationship': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['hhmodule.MemberRelationship']"}),
            'member_status': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['hhmodule.MemberStatus']", 'null': 'True', 'blank': 'True'}),
            'mobile_no': ('django.db.models.fields.CharField', [], {'max_length': '11', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'occupation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['hhmodule.Occupation']", 'null': 'True', 'blank': 'True'}),
            'profile_photo': ('django.db.models.fields.CharField', [], {'max_length': '250', 'blank': 'True'}),
            'regular_attendence': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'work_for_cash': ('django.db.models.fields.IntegerField', [], {})
        },
        u'hhmodule.hhstatus': {
            'Meta': {'object_name': 'HhStatus', 'db_table': "'hh_status'", 'managed': 'False'},
            'code': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150'})
        },
        u'hhmodule.hhuseassetgrant': {
            'Meta': {'object_name': 'HhUseAssetGrant', 'db_table': "'hh_use_asset_grant'", 'managed': 'False'},
            'code': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150'})
        },
        u'hhmodule.highesteducationlevel': {
            'Meta': {'object_name': 'HighestEducationLevel', 'db_table': "'highest_education_level'", 'managed': 'False'},
            'code': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150'})
        },
        u'hhmodule.household': {
            'Meta': {'object_name': 'Household', 'db_table': "'household'", 'managed': 'False'},
            'geo_ward': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['hhmodule.GeoWard']"}),
            'hh_id': ('django.db.models.fields.CharField', [], {'max_length': '17'}),
            'hh_member_number': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'hh_phone': ('django.db.models.fields.CharField', [], {'max_length': '11', 'null': 'True'}),
            'hh_serial': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True'}),
            'hh_status': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['hhmodule.HhStatus']", 'null': 'True', 'blank': 'True'}),
            'hh_use_asset_grant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['hhmodule.HhUseAssetGrant']", 'null': 'True', 'blank': 'True'}),
            'holding_no': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'hhmodule.memberrelationship': {
            'Meta': {'object_name': 'MemberRelationship', 'db_table': "'member_relationship'", 'managed': 'False'},
            'code': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150'})
        },
        u'hhmodule.memberstatus': {
            'Meta': {'object_name': 'MemberStatus', 'db_table': "'member_status'", 'managed': 'False'},
            'code': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150'})
        },
        u'hhmodule.occupation': {
            'Meta': {'object_name': 'Occupation', 'db_table': "'occupation'", 'managed': 'False'},
            'code': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150'})
        }
    }

    complete_apps = ['hhmodule']