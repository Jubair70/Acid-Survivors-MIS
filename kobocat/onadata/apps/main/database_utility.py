import psycopg2
from collections import OrderedDict

from django.db import connection


def __db_fetch_values(query):
    """
        Fetch database result set as list of tuples

        Args:
            query (str): raw query string

        Returns:
            str: Returns database result set as list of tuples
    """
    cursor = connection.cursor()
    cursor.execute(query)
    fetch_val = cursor.fetchall()
    cursor.close()
    return fetch_val


def __db_fetch_single_value(query):
    """
        Fetch database result of single field as string

        Args:
            query (str): raw query string

        Returns:
            str: Returns database result of single field as string
    """
    cursor = connection.cursor()
    cursor.execute(query)
    fetch_val = cursor.fetchone()
    cursor.close()
    return fetch_val[0]


def __db_fetch_values_dict(query):
    """
        Fetch database result set as list of ordereddict

        Args:
            query (str): raw query string

        Returns:
            str: Returns database result set as list of ordereddict
    """
    cursor = connection.cursor()
    cursor.execute(query)
    desc = cursor.description
    fetch_val = [
        OrderedDict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()]
    cursor.close()
    return fetch_val


def __db_fetch_row_count(query):
    """
        Fetch database result set row count

        Args:
            query (str): raw query string

        Returns:
            str: Returns database result set row count
    """
    cursor = connection.cursor()
    cursor.execute(query)
    row_count = cursor.rowcount
    return row_count



def single_query(query):
    """function for  query where result is single"""

    fetchVal = __db_fetch_values(query)
    if len(fetchVal) == 0:
        return None
    strType = map(str, fetchVal[0])
    ans = strType[0]
    return ans


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

