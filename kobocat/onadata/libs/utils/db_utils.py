from django.db import connection

class DbInstance(object):
    __instance = None
    def __new__(cls):
        if DbInstance.__instance is None:
            DbInstance.__instance = object.__new__(cls)
        DbInstance.__instance.cursor = connection.cursor()
        return DbInstance.__instance

    def set_db_connection_close(doClose):
        if doClose:
            if DbInstance.__instance is not None:
                try:
                    DbInstance.__instance.cursor.close()

                except Exception, e:
                    print('DB close error: ',str(e))

    def create_form_db_table(self,table_name):
        print("CREATE TABLE %s (ID  PRIMARY KEY     NOT NULL",table_name)
        create_table = "CREATE TABLE IF NOT EXISTS "+ str(table_name) + "(ID BIGSERIAL PRIMARY KEY);"
        try:
            if self.cursor.closed:
                self.cursor = connection.cursor()
            self.cursor.execute(create_table)
            self.cursor.execute("COMMIT")
        except Exception,e:
            print("db table creation failed: ",str(e))
            connection.rollback()
        finally:
            self.cursor.close()

    def create_form_db_table_column_name(self,table_name,header):
        print('table column creation started.. ')
        try:
            insert_column = 'ALTER TABLE ' + str(table_name)
        except TypeError, e:
            print('table name type error, returning from function. ',str(e))
            return

        for column_name in header:
            print('current column:: ',str(column_name))
            insert_column +=  ' ADD COLUMN "' + str(column_name) + '" text,'
        insert_column = insert_column[:-1]
        insert_column+=';'
        try:
            if self.cursor.closed:
                self.cursor = connection.cursor()
            self.cursor.execute(insert_column)
            connection.commit()
        except Exception,e:
            print("db table Column creation failed: ",str(e))
            connection.rollback()
        finally:
            self.cursor.close()

    def insert_from_db_table_row_data(self,table_name,data,fields):
        initial_insert_query = 'INSERT INTO ' + str(table_name)
        column_name = ''
        data_string = ''
        for f in fields:
            # print f
            column_name += '"' + str(f) + '"' + ','
            # print data.get(f)
            data_string += "'" + str(data.get(f)) + "'" + ","
        column_name = column_name[:-1] 
        data_string = data_string[:-1]

        build_full_statement = initial_insert_query + ' (' + column_name + ')'\
        ' ' + 'VALUES'+' (' +  data_string + ');'
        print build_full_statement
        try:
            if self.cursor.closed:
                self.cursor = connection.cursor()
            self.cursor.execute(build_full_statement)
            connection.commit()
        except Exception,e:
            print("db table data insertion failed: ",str(e))
            connection.rollback()
        finally:
            self.cursor.close()



   
