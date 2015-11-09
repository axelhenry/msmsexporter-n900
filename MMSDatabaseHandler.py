# -*- coding: utf-8 -*-


import os
import logging
import utilities as utils
import constants as csts
import magic
import arrow


class MMSDatabaseHandler:

    _myPath = None
    _myDirName = None
    _myEncoding = None
    _myProcessedMMSes = []

    def __init__(self, aPathToDb):
        self._myPath = aPathToDb
        self._myDirName = os.path.dirname(self._myPath)
        self._logger = logging.getLogger()
        # on met le niveau du logger à DEBUG, comme ça il écrit tout
        self._logger.setLevel(logging.DEBUG)
        steam_handler = logging.StreamHandler()
        steam_handler.setLevel(logging.DEBUG)
        self._logger.addHandler(steam_handler)

        self._myEncoding = self.getDatabaseEncoding()
        self._logger.info(
            'DatabaseHandler :: database encoding : %s', self._myEncoding)
        self._myProcessedMMSes = self.processMMSes()

    def getProcessedMMSes(self):
        return self._myProcessedMMSes

    def getDatabaseEncoding(self):
        myEncoding = utils.processFunctionOnDb(
            self._myPath, self._logger, utils.getCharsetFromDb)
        return myEncoding

    def getMMSTuplesFromDb(self):
        myTuples = utils.processFunctionOnDb(
            self._myPath, self._logger, utils.getMMSIdFromDb)
        return myTuples

    def getMMSHeadersForId(self, aId):
        myHeaders = utils.processFunctionOnDb(
            self._myPath, self._logger, utils.getMMSHeadersForId, aId)
        return myHeaders

    def getAttachmentsForId(self, aId):
        myAttachments = utils.processFunctionOnDb(
            self._myPath, self._logger, utils.getMMSAttachmentsForId, aId)
        return myAttachments

    def getTimestampForId(self, aId):
        myTimeStamp = utils.processFunctionOnDb(
            self._myPath, self._logger, utils.getMMSTimestampForId, aId)
        self._logger.info('DatabaseHandler :: getTimestampForId :: ' +
                          'timestamp : %s', myTimeStamp)
        return myTimeStamp

    def checkMMSValidity(self, aId):
        return utils.processFunctionOnDb(
            self._myPath, self._logger, utils.checkMMSValidity, aId)

    def processMMSes(self):
        myMMSes = self.getMMSTuplesFromDb()
        processedMMSes = []
        for elem in myMMSes:
            myId = elem[0]
            self._logger.info(
                'DatabaseHandler :: processMMSes :: mms_id : %s', myId)
            myHeaders = self.getMMSHeadersForId(myId)
            self._logger.info(
                'DatabaseHandler :: processMMSes :: headers : %s', myHeaders)
            myAttachments = self.getAttachmentsForId(myId)
            self._logger.info(
                'DatabaseHandler :: processMMSes '
                + ':: attachments : %s', myAttachments)
            processedMMSes.append(
                self.processMMS(elem, myHeaders, myAttachments))
        return processedMMSes

    def processMMS(self, aTuple, headers, attachments):
        myMMS = {}
        if self.checkMMSValidity(aTuple[0]):
            myMMS['transactionid'] = utils.stringify(aTuple[1])
            self._logger.info(
                'DatabaseHandler :: processMMS :: transactionid : %s',
                myMMS['transactionid'])
            myMMS['sent'] = True if aTuple[2] == 1 else False
            self._logger.info(
                'DatabaseHandler :: processMMS :: sent : %s',
                myMMS['sent'])
            myMMS['timestamp'] = arrow.get(
                self.getTimestampForId(aTuple[0])).timestamp
            self._logger.info(
                'DatabaseHandler :: processMMS :: timestamp : %s',
                myMMS['timestamp'])
            myDirPath = os.path.dirname(
                aTuple[3].split(csts.commonMMSPathPrefix)[1])
            self._logger.info(
                'DatabaseHandler :: processMMS :: dirpath : %s', myDirPath)
            mySubject = self.getFieldFromHeaders('Subject', headers)
            self._logger.info(
                'DatabaseHandler :: processMMS :: subject : %s', mySubject)
            myDescription = self.getFieldFromHeaders('Description', headers)
            self._logger.info(
                'DatabaseHandler :: processMMS :: description : %s',
                myDescription)
            myFileContent = None
            myFrom = self.getFieldFromHeaders('From', headers)
            self._logger.info(
                'DatabaseHandler :: processMMS :: from : %s', myFrom)
            myTo = self.getFieldFromHeaders('To', headers)
            self._logger.info(
                'DatabaseHandler :: processMMS :: to : %s', myTo)
            myMMS['to'] = utils.asList(
                myTo if myFrom == '<not inserted>' else myFrom,
                ('/TYPE=PLMN', ''))
            for tuple in attachments:
                attachment = tuple[0]
                myFilePath = os.path.join(
                    os.path.abspath(self._myDirName), myDirPath, attachment)
                self._logger.info('DatabaseHandler: : processMMS ::'
                                  + ' attachment path : % s', myFilePath)
                try:
                    myMimeType = magic.from_file(
                        myFilePath, mime=True).decode('utf-8')
                    self._logger.info('DatabaseHandler :: processMMS ::'
                                      + ' mimeType : %s', myMimeType)
                    # if myMimeType != 'application/smil':
                    if myMimeType != 'text/html':
                        if myMimeType in csts.validMimeTypes:
                            self._logger.info('DatabaseHandler :: '
                                              + 'processMMS :: '
                                              + 'valid mime type for %s',
                                              myFilePath)
                            myMMS['mimeType'] = myMimeType
                            myMMS['attachmentName'] = attachment
                            myMMS['originalPath'] = myFilePath
                            myMMS['pathToAttachment'] = os.path.join(
                                myMMS['transactionid'], myMMS['attachmentName'])
                        elif myMimeType == 'text/plain':
                            myFileContent = self.processTxtPart(myFilePath)
                        else:
                            self._logger.info('DatabaseHandler :: processMMS ::'
                                              + ' attachment : '
                                              + 'nothing to see here')
                    # if 'smil' not in attachment.lower():
                    #     self._logger.info(
                    #         'DatabaseHandler :: processMMS :: attachment :%s',
                    #         attachment)
                    #     if attachment.endswith('.txt'):
                    #         myFileContent = self.processTxtPart(myFilePath)
                except(IOError) as e:
                    self._logger.info(
                        'DatabaseHandler :: processMMS :: error : %s', e)

            mySelectedSubject = self.selectSubject(
                mySubject, myDescription, myFileContent)
            self._logger.info(
                'DatabaseHandler :: processMMS :: selectedSubject : %s',
                mySelectedSubject)
            myMMS['subject'] = mySelectedSubject

            self.debugMMS(myMMS)
            return myMMS

    def getFieldFromHeaders(self, field, headers):
        for tuple in headers:
            if tuple[0] == field:
                return tuple[1]

    def processTxtPart(self, myFilePath):
        # self._logger.info(
        #     'DatabaseHandler :: processTxtPart :: tempdir : %s',
        #     self._myDirName)
        # myNewPath = os.path.join(self._myDirName, myDirPath, attachment)
        # self._logger.info(
        #     'DatabaseHandler :: processTxtPart :: filepath : %s',
        #     myNewPath)
        myFileContent = None
        try:
            with open(myFilePath, encoding=self._myEncoding) as f:
                myFileContent = f.read()
            self._logger.info(
                'DatabaseHandler :: processTxtPart :: filecontent : %s',
                myFileContent)
        except(FileNotFoundError):
            self._logger.info(
                'DatabaseHandler :: processTxtPart :: filenotfound')
        return myFileContent

    # def selectSubject(self, subject, description, filecontent):
    #     if filecontent:
    #         return filecontent
    #     elif description:
    #         return description
    #     elif subject:
    #         return subject
    #     else:
    #         return 'MMS'

    def selectSubject(self, *args):
        myReturn = 'MMS'
        for elem in args:
            if elem is not None and elem != '':
                myReturn = elem
        return myReturn

    def debugMMS(self, aMMS):
        for key, value in aMMS.items():
            self._logger.info(
                'DatabaseHandler :: debug MMS :: %s : %s', key, value)

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

    def addMMSesToTar(self, aTar):
        utils.addJSonToTar(aTar, 'mms.json', self._myProcessedMMSes,
                           self.removeKeyValueFromDict, 'originalPath',
                           self._logger)
        self._addAttachmentsToTar(aTar)

    def removeKeyValueFromDict(self, aDict, aKey, aLogger):
        myDict = aDict.copy()
        try:
            myDict.pop(aKey, None)
        except(KeyError):
            aLogger.info('no key')
        return myDict
