
# domoticz-theme-manager - Theme Manager
#
# Author: galadril, 2020
#
#  Since (2020-07-23): Initial Version
#
#


"""
<plugin key="THEME-MANAGER" name="Domoticz Theme Manager" author="galadril" version="1.0.0">
    <description>
		<h2>Theme Manager v.1.0.0</h2><br/>
		<h3>Features</h3>
		<ul style="list-style-type:square">
			<li>Install themes</li>
			<li>Update All/Selected themes</li>
			<li>Update Notification for All/Selected</li>
		</ul>
		<h3>----------------------------------------------------------------------</h3>
		<h3>WARNING:</h3>
		<h2>         Auto Updating themes without verifying their code</h2>
		<h2>         makes you system vulnerable to developer's code intensions!!</h2>
		<h3>----------------------------------------------------------------------</h3>
		<h2>NOTE: After selecting your options press "Update" button!!</h2>
    </description>
     <params>
        <param field="Mode2" label="Theme to install" width="200px">
            <options>
                <option label="Nothing" value="Idle"  default="true" />
                <option label="ThinkTheme" value="Domoticz-ThinkTheme"/>
                <option label="Aurora" value="domoticz-aurora-theme"/>
                <option label="Machinon" value="machinon-domoticz_theme "/>
            </options>
        </param>
         <param field="Mode4" label="Auto Update" width="175px">
            <options>
                <option label="All" value="All"/>
                <option label="All (NotifyOnly)" value="AllNotify" default="true"/>
                <option label="Selected" value="Selected"/>
                <option label="Selected (NotifyOnly)" value="SelectedNotify"/>
                <option label="None" value="None"/>
            </options>
        </param>
         <param field="Mode5" label="Security Scan (Experimental)" width="75px">
            <options>
                <option label="True" value="True"/>
                <option label="False" value="False"  default="true" />
            </options>
        </param>
         <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="true" />
            </options>
        </param>
    </params>
</plugin>
"""

import Domoticz
import os
import subprocess
import sys
import urllib
import urllib.request
import urllib.error
import re
import time
import platform
#from urllib2 import urlopen
from datetime import datetime, timedelta

class BasePlugin:
    enabled = False
    themeState = "Not Ready"
    sessionCookie = ""
    privateKey = b""
    socketOn = "FALSE"


    def __init__(self):
        self.debug = False
        self.error = False
        self.nextpoll = datetime.now()
        self.pollinterval = 60  #Time in seconds between two polls
        self.ExceptionList = []
        self.SecPolUserList = {}

        self.plugindata = {
            # theme Key: [gitHub author, repository, theme Text, Branch]
            "Idle": ["Idle", "Idle", "Idle", "master"],
            "machinon-domoticz_theme": ["EdddieN", "machinon-domoticz_theme", "Machinon", "master"],
            "Domoticz-ThinkTheme": ["DewGew", "Domoticz-ThinkTheme", "ThinkTheme", "master"],
            "domoticz-aurora-theme": ["flatsiedatsie", "domoticz-aurora-theme", "Aurora", "master"]
        }
        
        return

    def onStart(self):

        Domoticz.Debug("onStart called")

        if Parameters["Mode6"] == 'Debug':
            self.debug = True
            Domoticz.Debugging(1)
            DumpConfigToLog()
        else:
            Domoticz.Debugging(0)


        Domoticz.Log("Domoticz Node Name is:" + platform.node())
        Domoticz.Log("Domoticz Platform System is:" + platform.system())
        Domoticz.Debug("Domoticz Platform Release is:" + platform.release())
        Domoticz.Debug("Domoticz Platform Version is:" + platform.version())
        Domoticz.Log("Default Python Version is:" + str(sys.version_info[0]) + "." + str(sys.version_info[1]) + "." + str(sys.version_info[2]) + ".")

        if platform.system() == "Windows":
            Domoticz.Error("Windows Platform NOT YET SUPPORTED!!")
            return


        themeText = ""
        themeAuthor = ""
        themeRepository = ""
        themeKey = ""

        themeKey = Parameters["Mode2"]
        themeAuthor = self.plugindata[themeKey][0]
        themeRepository = self.plugindata[themeKey][1]
        themeText = self.plugindata[themeKey][2]
        themeBranch = self.plugindata[themeKey][3]    # GitHub branch to clone

        # Reading exception file and populating array of values
        exceptionFile = str(os.getcwd()) + "/plugins/PP-MANAGER/exceptions.txt"
        Domoticz.Debug("Checking for Exception file on:" + exceptionFile)
        if (os.path.isfile(exceptionFile) == True):
            Domoticz.Log("Exception file found. Processing!!!")

            # Open the file
            f = open(exceptionFile)

            # use readline() to read the first line 
            line = f.readline()

            while line:
                if ((line[:1].strip() != "#") and (line[:1].strip() != " ") and (line[:1].strip() != "")):
                    Domoticz.Log("File ReadLine result:'" + line.strip() + "'")
                    self.ExceptionList.append(line.strip())    
                # use realine() to read next line
                line = f.readline()
            f.close()
        Domoticz.Debug("self.ExceptionList:" + str(self.ExceptionList))

        
        if Parameters["Mode4"] == 'All':
            Domoticz.Log("Updating All Themes!!!")
            i = 0
            path = str(os.getcwd()) + "/www/styles/"
            for (path, dirs, files) in os.walk(path):
                for dir in dirs:
                    if str(dir) != "":
                        if str(dir) in self.plugindata:
                            self.UpdatePythonPlugin(themeAuthor, themeRepository, str(dir))
                        elif str(dir) == "THEME-MANAGER":
                            Domoticz.Debug("THEME-MANAGER Folder found. Skipping!!")      
                        else:
                            Domoticz.Log("theme:" + str(dir) + " cannot be managed with THEME-MANAGER!!.")      
                i += 1
                if i >= 1:
                   break

        if Parameters["Mode4"] == 'AllNotify':
            Domoticz.Log("Collecting Updates for All themes!!!")
            i = 0
            path = str(os.getcwd()) + "/www/styles/"
            for (path, dirs, files) in os.walk(path):
                for dir in dirs:
                    if str(dir) != "":
                        if str(dir) in self.plugindata:
                            self.CheckForUpdatePythonPlugin(themeAuthor, themeRepository, str(dir))
                        elif str(dir) == "THEME-MANAGER":
                            Domoticz.Debug("THEME-MANAGER Folder found. Skipping!!")      
                        else:
                            Domoticz.Log("Theme:" + str(dir) + " cannot be managed with THEME-MANAGER!!.")      
                i += 1
                if i >= 1:
                   break

        if (Parameters["Mode4"] == 'SelectedNotify'): 
                Domoticz.Log("Collecting Updates for theme:" + themeKey)
                self.CheckForUpdatePythonPlugin(themeAuthor, themeRepository, themeKey)
           

        if themeKey == "Idle":
            Domoticz.Log("Theme Idle")
            Domoticz.Heartbeat(60)
        else:
            Domoticz.Debug("Checking for dir:" + str(os.getcwd()) + "/www/styles/" + themeKey)
            #If theme Directory exists
            if (os.path.isdir(str(os.getcwd()) + "/www/styles/" + themeKey)) == True:
                Domoticz.Debug("Folder for theme:" + themeKey + " already exists!!!")
                #Domoticz.Debug("Set 'Python Theme Manager' attribute to 'idle' in order t.")
                if Parameters["Mode4"] == 'Selected':
                    Domoticz.Debug("Updating Enabled for theme:" + themeText + ".Checking For Update!!!")
                    self.UpdatePythonPlugin(themeAuthor, themeRepository, themeKey)
                Domoticz.Heartbeat(60)
            else:
               Domoticz.Log("Installation requested for theme:" + themeText)
               Domoticz.Debug("Installation URL is:" + "https://github.com/" + themeAuthor +"/" + themeRepository)
               Domoticz.Debug("Current Working dir is:" + str(os.getcwd()))
               if themeKey in self.plugindata:
                    Domoticz.Log("Theme Display Name:" + themeText)
                    Domoticz.Log("Theme Author:" + themeAuthor)
                    Domoticz.Log("Theme Repository:" + themeRepository)
                    Domoticz.Log("Theme Key:" + themeKey)
                    Domoticz.Log("Theme Branch:" + themeBranch)
                    self.InstallPythonPlugin(themeAuthor, themeRepository, themeKey, themeBranch)
               Domoticz.Heartbeat(60)
            

    def onStop(self):
        Domoticz.Debug("onStop called")
        Domoticz.Log("Theme is stopping.")
        self.UpdatePythonPlugin("galadril", "THEME-MANAGER", "THEME-MANAGER")
        Domoticz.Debugging(0)


    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat called")
        themeKey = Parameters["Mode2"]

        CurHr = str(datetime.now().hour)
        CurMin = str(datetime.now().minute)
        if len(CurHr) == 1: CurHr = "0" + CurHr
        if len(CurMin) == 1: CurMin = "0" + CurMin
        Domoticz.Debug("Current time:" + CurHr + ":" + CurMin)

        if (mid(CurHr,0,2) == "12" and  mid(CurMin,0,2) == "00"):
            Domoticz.Log("Its time!!. Trigering Actions!!!")


            #-------------------------------------
            if Parameters["Mode4"] == 'All':
                Domoticz.Log("Checking Updates for All themes!!!")
                i = 0
                path = str(os.getcwd()) + "/www/styles/"
                for (path, dirs, files) in os.walk(path):
                    for dir in dirs:
                        if str(dir) != "":
                            self.UpdatePythonPlugin(self.plugindata[Parameters["Mode2"]][0], self.plugindata[Parameters["Mode2"]][1], str(dir))
                    i += 1
                    if i >= 1:
                       break

            if Parameters["Mode4"] == 'AllNotify':
                Domoticz.Log("Collecting Updates for All themes!!!")
                i = 0
                path = str(os.getcwd()) + "/www/styles/"
                for (path, dirs, files) in os.walk(path):
                    for dir in dirs:
                        if str(dir) != "":
                            self.CheckForUpdatePythonPlugin(self.plugindata[Parameters["Mode2"]][0], self.plugindata[Parameters["Mode2"]][1], str(dir))
                    i += 1
                    if i >= 1:
                       break

            if Parameters["Mode4"] == 'SelectedNotify':
                Domoticz.Log("Collecting Updates for theme:" + themeKey)
                self.CheckForUpdatePythonPlugin(self.plugindata[Parameters["Mode2"]][0], self.plugindata[Parameters["Mode2"]][1], Parameters["Mode2"])

            #-------------------------------------
            if Parameters["Mode4"] == 'Selected':
                Domoticz.Log("Checking Updates for theme:" + self.plugindata[themeKey][2])
                self.UpdatePythonPlugin(self.plugindata[Parameters["Mode2"]][0], self.plugindata[Parameters["Mode2"]][1], Parameters["Mode2"])

            #if Parameters["Mode2"] == "Idle":
                #Domoticz.Log("Theme Idle. No actions to be performed!!!")



    # InstallPyhtontheme function
    def InstallPythonPlugin(self, ppAuthor, ppRepository, ppKey, ppBranch):
        Domoticz.Debug("InstallPythonPlugin called")

        Domoticz.Log("Installing theme:" + self.plugindata[ppKey][2])
        ppCloneCmd = "LANG=en_US /usr/bin/git clone -b " + ppBranch + " https://github.com/" + ppAuthor + "/" + ppRepository + ".git " + ppKey
        Domoticz.Log("Calling:" + ppCloneCmd)
        try:
            pr = subprocess.Popen( ppCloneCmd , cwd = os.path.dirname(str(os.getcwd()) + "/www/styles/"), shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE )
            (out, error) = pr.communicate()
            if out:
                   Domoticz.Log("Succesfully installed:" + str(out).strip)
                   Domoticz.Log("---Restarting Domoticz MAY BE REQUIRED to activate new themes---")
            if error:
                Domoticz.Debug("Git Error:" + str(error))
                if str(error).find("Cloning into") != -1:
                   Domoticz.Log("Theme " + ppKey + " installed Succesfully")
        except OSError as e:
            Domoticz.Error("Git ErrorNo:" + str(e.errno))
            Domoticz.Error("Git StrError:" + str(e.strerror))

        return None


    # UpdatePyhtontheme function
    def UpdatePythonPlugin(self, ppAuthor, ppRepository, ppKey):
        Domoticz.Debug("UpdatePythonPlugin called")

        if ppKey == "THEME-MANAGER":
            Domoticz.Log("Self Update Initiated")
            ppGitReset = "LANG=en_US /usr/bin/git reset --hard HEAD"
            try:
                pr = subprocess.Popen( ppGitReset , cwd = str(os.getcwd() + "/www/styles/" + ppKey), shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE )
                (out, error) = pr.communicate()
                if out:
                    Domoticz.Debug("Git Response:" + str(out))
                if error:
                    Domoticz.Debug("Git Error:" + str(error.strip()))
            except OSError as eReset:
                Domoticz.Error("Git ErrorNo:" + str(eReset.errno))
                Domoticz.Error("Git StrError:" + str(eReset.strerror))

        elif (self.plugindata[ppKey][2] in self.ExceptionList):
            Domoticz.Log("Theme:" + self.plugindata[ppKey][2] + " excluded by Exclusion file (exclusion.txt). Skipping!!!")
            return

        Domoticz.Log("Updating theme:" + ppKey)
        ppUrl = "LANG=en_US /usr/bin/git pull --force"
        Domoticz.Debug("Calling:" + ppUrl + " on folder " + str(os.getcwd()) + "/www/styles/" + ppKey)
        try:
            pr = subprocess.Popen( ppUrl , cwd = str(os.getcwd() + "/www/styles/" + ppKey), shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE )
            (out, error) = pr.communicate()
            if out:
                Domoticz.Debug("Git Response:" + str(out))
                if (str(out).find("Already up-to-date") != -1) or (str(out).find("Already up to date") != -1):
                   Domoticz.Log("Theme " + ppKey + " already Up-To-Date")
                   #Domoticz.Log("find(error):" + str(str(out).find("error")))
                elif (str(out).find("Updating") != -1) and (str(str(out).find("error")) == "-1"):
                   ppUrl = "chmod "
                   Domoticz.Log("Succesfully pulled gitHub update:" + str(out)[str(out).find("Updating")+8:26] + " for theme " + ppKey)
                   Domoticz.Log("---Restarting Domoticz MAY BE REQUIRED to activate new themes---")
                else:
                   Domoticz.Error("Something went wrong with update of " + str(ppKey))
            if error:
                Domoticz.Debug("Git Error:" + str(error.strip()))
                if str(error).find("Not a git repository") != -1:
                   Domoticz.Log("Theme:" + ppKey + " is not installed from gitHub. Cannot be updated with Theme Manager!!.")
        except OSError as e:
            Domoticz.Error("Git ErrorNo:" + str(e.errno))
            Domoticz.Error("Git StrError:" + str(e.strerror))

        return None


    # CheckForUpdatePythonPlugin function
    def CheckForUpdatePythonPlugin(self, ppAuthor, ppRepository, ppKey):
        Domoticz.Debug("CheckForUpdatePythonPlugin called")

        if (self.plugindata[ppKey][2] in self.ExceptionList):
            Domoticz.Log("Theme:" + self.plugindata[ppKey][2] + " excluded by Exclusion file (exclusion.txt). Skipping!!!")
            return

        Domoticz.Debug("Checking theme:" + ppKey + " for updates")
        
        
        #Domoticz.Log("Fetching Repository Details")
        ppGitFetch = "LANG=en_US /usr/bin/git fetch"
        try:
            prFetch = subprocess.Popen( ppGitFetch , cwd = str(os.getcwd() + "/www/styles/" + ppKey), shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE )
            (outFetch, errorFetch) = prFetch.communicate()
            if outFetch:
                Domoticz.Debug("Git Response:" + str(outFetch))
            if errorFetch:
                Domoticz.Debug("Git Error:" + str(errorFetch.strip()))
        except OSError as eFetch:
            Domoticz.Error("Git ErrorNo:" + str(eFetch.errno))
            Domoticz.Error("Git StrError:" + str(eFetch.strerror))


        ppUrl = "LANG=en_US /usr/bin/git status -uno"
        Domoticz.Debug("Calling:" + ppUrl + " on folder " + str(os.getcwd()) + "/www/styles/" + ppKey)

        try:
            pr = subprocess.Popen( ppUrl , cwd = str(os.getcwd() + "/www/styles/" + ppKey), shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE )
            (out, error) = pr.communicate()
            if out:
                Domoticz.Debug("Git Response:" + str(out))
                if (str(out).find("up-to-date") != -1) or (str(out).find("up to date") != -1):
                   Domoticz.Log("Theme " + ppKey + " already Up-To-Date")
                   Domoticz.Debug("find(error):" + str(str(out).find("error")))
                elif (str(out).find("Your branch is behind") != -1) and (str(str(out).find("error")) == "-1"):
                   Domoticz.Log("Found that we are behind on theme " + ppKey)
                   self.fnSelectedNotify(ppKey)
                elif (str(out).find("Your branch is ahead") != -1) and (str(str(out).find("error")) == "-1"):
                   Domoticz.Debug("Found that we are ahead on theme " + ppKey + ". No need for update")
                else:
                   Domoticz.Error("Something went wrong with update of " + str(ppKey))
            if error:
                Domoticz.Debug("Git Error:" + str(error.strip()))
                if str(error).find("Not a git repository") != -1:
                   Domoticz.Log("Theme:" + ppKey + " is not installed from gitHub. Ignoring!!.")
        except OSError as e:
            Domoticz.Error("Git ErrorNo:" + str(e.errno))
            Domoticz.Error("Git StrError:" + str(e.strerror))

        return None



    # fnSelectedNotify function
    def fnSelectedNotify(self, themeText):
        Domoticz.Debug("fnSelectedNotify called")
        Domoticz.Log("Preparing Notification")
        ServerURL = "http://127.0.0.1:8080/json.htm?param=sendnotification&type=command"
        MailSubject = urllib.parse.quote(platform.node() + ":Domoticz theme Updates Available for " + self.plugindata[themeText][2])
        MailBody = urllib.parse.quote(self.plugindata[themeText][2] + " has updates available!!")
        MailDetailsURL = "&subject=" + MailSubject + "&body=" + MailBody + "&subsystem=email"
        notificationURL = ServerURL + MailDetailsURL
        Domoticz.Debug("ConstructedURL is:" + notificationURL)
        try:
            response = urllib.request.urlopen(notificationURL, timeout = 30).read()
        except urllib.error.HTTPError as err1:
            Domoticz.Error("HTTP Request error: " + str(err1) + " URL: " + notificationURL)
        return
        Domoticz.Debug("Notification URL is :" + str(notificationURL))


        return None

    #
    # Parse an int and return None if no int is given
    #

    def parseIntValue(s):
        Domoticz.Debug("parseIntValue called")

        try:
            return int(s)
        except:
            return None


    def parseFileForSecurityIssues(self, pyfilename, pythemeid):
       Domoticz.Debug("parseFileForSecurityIssues called")
       secmonitorOnly = False

       if Parameters["Mode5"] == 'Monitor':
           Domoticz.Log("Theme Security Scan is enabled")
           secmonitorOnly = True


       # Open the file
       file = open(pyfilename, "r")

       ips = {}
       #safeStrings = ["['http://schemas.xmlsoap.org/soap/envelope/', 'http://schemas.xmlsoap.org/soap/encoding/']",
       #               "127.0.0.1",
       #               "http://schemas.xmlsoap.org/soap/envelope/'",
       #               "import json",
       #               "import time",
       #               "import platform",
       #               'import re']

       if pythemeid not in self.SecPolUserList:
            self.SecPolUserList[pythemeid] = []

       lineNum = 1
       #Domoticz.Error("self.SecPolUserList[pythemeid]:" + str(self.SecPolUserList[pythemeid]))
       for text in file.readlines():
          text = text.rstrip()

          #Domoticz.Log("'text' is:'" + str(text))
          regexFound = re.findall(r'(?:[\d]{1,3})\.(?:[\d]{1,3})\.(?:[\d]{1,3})\.(?:[\d]{1,3})',text)
          paramFound = re.findall(r'<param field=',text)
          if ((regexFound) and not (paramFound)):
              #regexFound[rex] = regexFound[rex].strip('"]')
              #Domoticz.Error("Security Finding(IPregex):" + str(regexFound) + " LINE: " + str(lineNum) + " FILE:" + pyfilename)
              for rex in range(0,len(regexFound)):
                   if ((str(text).strip() not in self.SecPolUserList["Global"]) and (str(text).strip() not in self.SecPolUserList[pythemeid]) and (str(text).strip() != "") and (mid(text,0,1) != "#")):
                       Domoticz.Error("Security Finding(IP):-->" + str(text).strip() + "<-- LINE: " + str(lineNum) + " FILE:" + pyfilename)
                       #Domoticz.Error("Security Finding(IPr):" + regexFound[rex] + " LINE: " + str(lineNum) + " FILE:" + pyfilename)
                       ips["IP" + str(lineNum)] = (regexFound[rex], "IP Address")

          #rex = 0
          #regexFound = re.findall('import', text)

          #if regexFound:
              #regexFound[rex] = regexFound[rex].strip('"]')
              #Domoticz.Error("Security Finding(IPregex):" + str(regexFound) + " LINE: " + str(lineNum) + " FILE:" + pyfilename)
          #    for rex in range(0,len(regexFound)):
          #         if ((str(text).strip() not in self.SecPolUserList["Global"]) and (str(text).strip() not in self.SecPolUserList[pythemeid]) and (str(text).strip() != "") and (mid(text,0,1) != "#")):
          #             Domoticz.Error("Security Finding(IMP):-->" + str(text) + "<-- LINE: " + str(lineNum) + " FILE:" + pyfilename)
                       #Domoticz.Error("Security Finding(IPr):" + regexFound[rex] + " LINE: " + str(lineNum) + " FILE:" + pyfilename)
          #             ips["IP" + str(lineNum)] = (regexFound[rex], "Import")

          #rex = 0
          #regexFound = re.findall('subprocess.Popen', text)

          #if regexFound:
              #regexFound[rex] = regexFound[rex].strip('"]')
              #Domoticz.Error("Security Finding(IPregex):" + str(regexFound) + " LINE: " + str(lineNum) + " FILE:" + pyfilename)
          #    for rex in range(0,len(regexFound)):
          #         if ((str(text).strip() not in self.SecPolUserList["Global"]) and (str(text).strip() not in self.SecPolUserList[pythemeid]) and (str(text).strip() != "") and (mid(text,0,1) != "#")):
          #             Domoticz.Error("Security Finding(SUB):-->" + str(text) + "<-- LINE: " + str(lineNum) + " FILE:" + pyfilename)
                       #Domoticz.Error("Security Finding(IPr):" + regexFound[rex] + " LINE: " + str(lineNum) + " FILE:" + pyfilename)
          #             ips["IP" + str(lineNum)] = (regexFound[rex], "Subprocess")

          #rex = 0
          #regexFound = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
          #paramFound = re.findall(r'<param field=',text)

          #if ((regexFound) and not (paramFound)):
              #regexFound[rex] = regexFound[rex].strip('"]')
              #Domoticz.Error("Security Finding(IPregex):" + str(regexFound) + " LINE: " + str(lineNum) + " FILE:" + pyfilename)
          #    for rex in range(0,len(regexFound)):
          #         if ((str(text).strip() not in self.SecPolUserList[pythemeid]) and (str(text).strip() != "") and (mid(text,0,1) != "#")):
          #             Domoticz.Error("Security Finding(HTTP):-->" + str(text) + "<-- LINE: " + str(lineNum) + " FILE:" + pyfilename)
                       #Domoticz.Error("Security Finding(IPr):" + regexFound[rex] + " LINE: " + str(lineNum) + " FILE:" + pyfilename)
          #             ips["IP" + str(lineNum)] = (regexFound[rex], "HTTP Address")


          lineNum = lineNum + 1



       file.close()
       Domoticz.Debug("IPS Table contents are:" + str(ips))



global _theme
_theme = Basetheme()

def onStart():
    global _theme
    _theme.onStart()

def onStop():
    global _theme
    _theme.onStop()

def onHeartbeat():
    global _theme
    _theme.onHeartbeat()


# Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
    return


def mid(s, offset, amount):
    #Domoticz.Debug("mid called")
    return s[offset:offset+amount]


