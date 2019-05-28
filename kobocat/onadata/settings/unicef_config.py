import logging
import os
import subprocess  # nopep8, used by included files
import sys  # nopep8, used by included files


JASPER_SERVER_URL='https://192.168.21.230:8443/jasperserver/rest_v2/reports/reports/interactive/'
JASPER_REPORT_EXECUTION_URL = 'https://192.168.21.230:8443/jasperserver/rest_v2/reportExecutions/'
JASPER_REPORT_PARAMETER_QUERY = '/inputControls'
xFORM_BIRTH_ID = 13
xFORM_FEEDING_ID = 7
xFORM_DIET_ID = 8
xFORM_HOUSEHOLD_ID = 10
