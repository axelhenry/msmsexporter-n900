# -*- coding: utf-8 -*-

from messaging.mms.message import MMSMessage
import arrow
import logging
import json
import tempfile
import chardet
import os

import utilities as utils
import constants


class MMSHandler:

    _myMMSList = []
    _myProcessedMMSes = []
    _logger = None

    def __init__(self, aListOfMMS):
        self._logger = logging.getLogger()
        # on met le niveau du logger à DEBUG, comme ça il écrit tout
        self._logger.setLevel(logging.DEBUG)
        steam_handler = logging.StreamHandler()
        steam_handler.setLevel(logging.DEBUG)
        self._logger.addHandler(steam_handler)

        self._myMMSList = utils.getMessageFromListOfFile(aListOfMMS)
        self._myProcessedMMSes = self.processMMSes()

    def processMMSes(self):
        return [self.processMMS(aMMS) for aMMS in self._myMMSList]

    def processMMS(self, aMMSPath):
        myDict = {}
        myMMS = MMSMessage.from_file(aMMSPath)
        self._logger.info('for debugging sake, mmsPath : %s', aMMSPath)
        try:
            mySub = str(myMMS.headers['Subject'])
            self._logger.info('for debugging sake, mySub : %s', mySub)
            myDict['subject'] = myMMS.headers['Subject']
            self._logger.info(
                'for debugging sake, subject : %s', myDict['subject'])
        except(KeyError):
            myDict['subject'] = 'MMS'
        myDict['transactionid'] = myMMS.headers['Transaction-Id']
        self._logger.info(
            'for debugging sake, transactionid : %s', myDict['transactionid'])
        if myMMS.headers['Message-Type'] == 'm-send-req':
            try:
                mySenders = myMMS.headers['To']
                myDict['to'] = utils.asList(mySenders, ('/TYPE=PLMN', ''))
                # myL = []
                # for elem in mySenders:
                #     myL.append(elem)
                # myDict['to'] = myL
                # myDict['to'] = myMMS.headers['To'].replace('/TYPE=PLMN', '')
            except(KeyError):
                self._logger.info(
                    'Recipient not found, mms : %s not processed',
                    myDict['transactionid'])
                return None
            myDate = arrow.get(
                utils.getLastModificationDateForFile(aMMSPath))
            myDict['sent'] = True
        else:
            try:
                myDest = myMMS.headers['From']
                myDict['to'] = utils.asList(myDest, ('/TYPE=PLMN', ''))
                # myDict['to'] = myDest.replace('/TYPE=PLMN', '')
            except(KeyError):
                self._logger.info(
                    'Sender not found, mms : %s not processed',
                    myDict['transactionid'])
                return None
            myDate = arrow.get(myMMS.headers['Date'])
            myDict['sent'] = False
        myDict['timestamp'] = myDate.timestamp
        for part in myMMS.data_parts:
            myTuple = part.headers['Content-Type']
            if (myTuple[0] in constants.validMimeTypes):
                myDict['mimeType'] = myTuple[0]
                myDict['attachmentName'] = myTuple[1]['Name']
                myDict['originalPath'] = os.path.join(utils.getDirNameFromPath(
                    aMMSPath), myDict['attachmentName'])
                # myDict['originalPath'] = utils.getDirNameFromPath(
                #     aMMSPath) + "/" + myDict['attachmentName']
                myDict['pathToAttachment'] = os.path.join(myDict[
                    'transactionid'], myDict['attachmentName'])
                # myDict['pathToAttachment'] = myDict[
                # 'transactionid'] + "/" + myDict['attachmentName']
            if (myTuple[0] == 'text/plain'):
                myFileEncoding = myTuple[1]['Charset']
                self._logger.info(
                    'for debugging sake, encoding : %s', myFileEncoding)
                myFile = myTuple[1]['Name']
                try:
                    myTmp = None
                    with open(utils.getDirNameFromPath(aMMSPath) + "/"
                              + myFile, 'r', encoding=myFileEncoding) as f:
                        myTmp = f.read()
                        # print(f.read())
                        self._logger.info(
                            'for debugging sake, new subject : %s', myTmp)
                    if myTmp:
                        myDict['subject'] = myTmp
                except(IOError):
                    self._logger.info('text part not found, aborting')
                    return None

        return myDict

    def show(self):
        [self._logger.info(elem) for elem in self._myProcessedMMSes]

    def getProcessedMMSes(self):
        return self._myProcessedMMSes

    def _addAttachmentsToTar(self, aTar):
        for elem in self._myProcessedMMSes:
            # try:
            if elem:
                print('elem : ', elem)
                try:
                    myOPath = elem['originalPath']
                    myNPath = elem['pathToAttachment']
                    print('opath n : ', myOPath)
                    print('npath n : ', myNPath)
                    aTar.add(myOPath, myNPath)
                except(KeyError):
                    pass
            # except(KeyError, TypeError):
            #     print('opath e : ', myOPath)
            #     print('npath e :', myNPath)

    def _addJSonToTar(self, aTar):
        myDict = None
        myL = []
        for elem in self._myProcessedMMSes:
            if elem:
                try:
                    myDict = elem.copy()
                    myDict.pop('originalPath', None)
                except(KeyError):
                    self._logger.info('no key')
                myL.append(myDict)
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as myFile:
            myFile.write(
                json.dumps(myL, indent=4, ensure_ascii=False))
            # json.dumps(myL, indent=4, ensure_ascii=False).encode('utf8'))
            # json.dump(myL, myFile, indent=4)
            aTar.add(myFile.name, 'mms.json')

    def addMMSesToTar(self, aTar):
        self._addJSonToTar(aTar)
        self._addAttachmentsToTar(aTar)
