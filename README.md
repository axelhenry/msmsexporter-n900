## (M|S)MSExporter - N900

### About

This application aims to allow N900 users to export their SMSes or/and MMSes

### Installation

- Clone this repo on your computer.  
- Go into the newly created directory.  
- Open a terminal and install required dependencies:
```bash
pip install -r stable-req.txt
```
You're good to go.

### Usage

To use this app, you'll need at least one of the following file from your N900:
- __el-v1.db__ to export SMSes:   
```bash
cp /home/user/.rtcom-eventlogger/el-v1.db /home/user/MyDocs/el-v1.db
```
- __mms.db__ inside __.fmms__ folder to export MMSes, if you used FMMS on your N900:  
```bash
cp -r /home/user/.fmms /home/user/MyDocs/FMMS/
```
__WARNING__: In some cases, some subfolders of .fmms could contain special characters like * and cannot be copied with cp. If you run into this issue, you can use [WinSCP](https://winscp.net) (or any other ftp client) to connect over ssh on your N900. More informations on how to install and configure ftp over SSH on [maemo.org](https://wiki.maemo.org/SSH)

Once you've got __el-v1.db__ or/and __mms.db__, you can proceed to the next step.

### Usage

This app takes 2 or 3 arguments:
- __--tar_file__
- one or both arguments:
  - __mms_database__
  - __sms_database__


```bash
./launcher.py --mms_database path/to/mms.db --sms_database /path/to/el-v1.db --tar_file /path/to/archive.tar
```
