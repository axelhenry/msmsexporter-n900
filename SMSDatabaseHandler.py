# -*- coding: utf-8 -*-

import logging

import utilities as utils
import arrow
import math


class SMSDatabaseHandler:

    _myPath = None
    _myProcessedSMSes = []

    def __init__(self, aPathToDb):
        self._myPath = aPathToDb
        self._logger = logging.getLogger()
        # on met le niveau du logger à DEBUG, comme ça il écrit tout
        self._logger.setLevel(logging.DEBUG)
        steam_handler = logging.StreamHandler()
        steam_handler.setLevel(logging.DEBUG)
        self._logger.addHandler(steam_handler)
        self._myProcessedSMSes = self.processSMSes()

    def getDatabaseEncoding(self):
        myEncoding = utils.processFunctionOnDb(
            self._myPath, self._logger, utils.getCharsetFromDb)
        return myEncoding

    def getSMSFromDb(self):
        return utils.processFunctionOnDb(self._myPath,
                                         self._logger, utils.getSMSFromDb)

    def processSMSes(self):
        return [self.processSMS(aSMS) for aSMS in self.getSMSFromDb()]

    def processSMS(self, aTuple):
        mySMS = {}
        mySMS['to'] = str(aTuple[1])
        mySMS['body'] = aTuple[2]
        mySMS['timestamp'] = arrow.get(aTuple[0]).timestamp
        mySMS['sent'] = True if aTuple[3] == 1 else False
        self.debugSMS(mySMS)
        return mySMS

    def debugSMS(self, aMMS):
        for key, value in aMMS.items():
            self._logger.info(
                'SMSDatabaseHandler :: debug SMS :: %s : %s', key, value)

    def addSMSesToTar(self, aTar):
        # utils.addJSonToTar(aTar, 'sms.json', self._myProcessedSMSes,
        #                    self.getTimestampOn13Characters, 'timestamp',
        #                    self._logger)
        utils.addJSonToTar(aTar, 'sms.json', self._myProcessedSMSes,
                           None, 'timestamp',
                           self._logger)

    def getTimestampOn13Characters(self, aDict, aKey, aLogger):
        myDict = aDict.copy()
        try:
            tStamp = myDict[aKey]
            digitsNumber = int(math.log10(tStamp)) + 1
            if digitsNumber == 10:
                myDict[aKey] = tStamp * 1000
        except(KeyError):
            aLogger.info('no key')
        return myDict
