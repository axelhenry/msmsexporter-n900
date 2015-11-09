#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import tarfile as tar

# import utilities as utils
# import MMSHandler as MMS
import MMSDatabaseHandler as MMS
import SMSDatabaseHandler as SMS

parser = argparse.ArgumentParser(
    description="""Get sms from a N900 database\
     and generate a xml to be used with sms backup restore""")
parser.add_argument(
    '--mms_database', '-mms',
    help='path to our folder containing FMMS\' mms.db', required=False)
parser.add_argument(
    '--sms_database', '-sms',
    help='path to our folder containing N900\' elv1.db', required=False)
parser.add_argument(
    '--tar_file', '-tar', help='path to write our tar archive', required=True)
args = parser.parse_args()

if args.mms_database is None and args.sms_database is None:
    args.error('at least one of --mms_database and --sms_database is required')
else:
    # myML = utils.getMessageFromListOfFile(
    #     utils.getListOfFilesForFolder(args.mms_folder, True))
    # myMMSHandler = MMS.MMSHandler(myML)
    if args.mms_database:
        myMMSHandler = MMS.MMSDatabaseHandler(args.mms_database)
    if args.sms_database:
        mySMSHandler = SMS.SMSDatabaseHandler(args.sms_database)

    try:
        with tar.open(args.tar_file, 'w') as myTar:
            if args.mms_database:
                myMMSHandler.addMMSesToTar(myTar)
            if args.sms_database:
                mySMSHandler.addSMSesToTar(myTar)
    except():
        pass
