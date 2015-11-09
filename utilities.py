# -*- coding: utf-8 -*-

import os
import six
import sqlite3
import json
import tempfile


def getFileNameFromPath(filePath):
    return os.path.basename(filePath)


def getDirNameFromPath(filePath):
    return os.path.dirname(filePath)


def isFile(filePath):
    return os.path.isfile(filePath)


def getListOfFilesForFolder(aFolder, isRecursive):
    try:
        if not isFile(aFolder):
            myFiles = []
            if isRecursive:
                for root, subs, files in os.walk(aFolder):
                    for name in files:
                        myFiles.append(os.path.join(root, name))
            else:
                root, subs, files = next(os.walk(aFolder))
                for name in files:
                    myFiles.append(os.path.join(root, name))
            return myFiles
        else:
            return []
    except (OSError):
        return []


def getMessageFromListOfFile(aListOfFile):
    return [aFile for aFile in aListOfFile if aFile.endswith("message")]


def getLastModificationDateForFile(aPath):
    return os.path.getmtime(aPath)


def asList(elem, tuple):
    myList = []
    if isinstance(elem, six.string_types):
        myList.append(elem.replace(tuple[0], tuple[1]))
    else:
        for e in elem:
            # myList.append(e.replace(tuple[0], tuple[1]))
            myList.append(e)
    return myList


def convert(input):
    if isinstance(input, dict):
        return {convert(key): convert(value) for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [convert(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input


def safe_unicode(obj, *args):
    """ return the unicode representation of obj """
    try:
        return unicode(obj, *args)
    except UnicodeDecodeError:
        # obj is byte string
        ascii_text = str(obj).encode('string_escape')
        return unicode(ascii_text)


def safe_str(obj):
    """ return the byte string representation of obj """
    try:
        return str(obj)
    except UnicodeEncodeError:
        # obj is unicode
        return unicode(obj).encode('unicode_escape')


def getCharsetFromDb(aDb, aLogger, *args):
    myCursor = aDb.cursor()
    myRequest = myCursor.execute('PRAGMA encoding')
    myResults = myRequest.fetchone()
    aLogger.info('DatabaseHandler :: Charset : %s', myResults)
    return myResults[0]


def getMMSIdFromDb(aDb, aLogger, *args):
    myCursor = aDb.cursor()
    myRequest = myCursor.execute(
        'SELECT id, transactionid, direction, file FROM mms')
    myResults = myRequest.fetchall()
    return myResults


def processFunctionOnDb(aPath, aLogger, func, *args):
    try:
        aLogger.info(
            'DatabaseHandler :: processed function : %s', func.__name__)
        with sqlite3.connect(aPath) as myDb:
            myResult = func(myDb, aLogger, *args)
            return myResult
    except Exception as e:
        raise e
    finally:
        myDb.close()


def getMMSHeadersForId(aDb, aLogger, aId):
    myCursor = aDb.cursor()
    myRequest = myCursor.execute(
        'SELECT header, value FROM mms_headers WHERE mms_id=?', (aId,))
    myResults = myRequest.fetchall()
    return myResults


def getMMSAttachmentsForId(aDb, aLogger, aId):
    myCursor = aDb.cursor()
    myRequest = myCursor.execute(
        'SELECT file FROM attachments WHERE mmsidattach=?', (aId,))
    myResults = myRequest.fetchall()
    return myResults


def getMMSTimestampForId(aDb, aLogger, aId):
    myCursor = aDb.cursor()
    myRequest = myCursor.execute(
        'SELECT msg_time FROM push WHERE idpush=(SELECT pushid FROM mms WHERE id=?)', (aId,))
    myResults = myRequest.fetchone()
    return myResults[0]


def checkMMSValidity(aDb, aLogger, aId):
    myCursor = aDb.cursor()
    myRequest = myCursor.execute(
        'SELECT msg_time FROM push WHERE idpush=(SELECT pushid FROM mms WHERE id=?)', (aId,))
    myResults = myRequest.fetchone()
    return True if myResults else False


def getSMSFromDb(aDb, aLogger):
    myCursor = aDb.cursor()
    myRequest = myCursor.execute(
        'SELECT storage_time, remote_uid, free_text, outgoing FROM Events WHERE event_type_id=?', (11,))
    myResults = myRequest.fetchall()
    return myResults


def stringify(aElem):
    if isinstance(aElem, six.integer_types):
        return str(aElem)
    elif isinstance(aElem, six.string_types):
        return aElem
    else:
        return None


def addJSonToTar(aTar, aFileName, aListOfDict, func, *args):
    # myDict = None
    myL = []
    print('args : ', args)
    for elem in aListOfDict:
        if elem:
            if func is not None:
                # try:
                    #     myDict = elem.copy()
                    #     myDict.pop('originalPath', None)
                    # except(KeyError):
                    #     self._logger.info('no key')
                myL.append(func(elem, *args))
            else:
                myL.append(elem)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as myFile:
        myFile.write(
            json.dumps(myL, indent=4, ensure_ascii=False))
        # json.dumps(myL, indent=4, ensure_ascii=False).encode('utf8'))
        # json.dump(myL, myFile, indent=4)
        aTar.add(myFile.name, aFileName)
