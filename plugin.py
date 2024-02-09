
# domoticz-theme-manager - Theme Manager
#
# Author: galadril, 2020
#
#  Since (2020-07-23): Initial Version
#
#


"""
<plugin key="THEME-MANAGER" name="Domoticz Theme Manager" author="galadril" version="1.0.1">
    <description>
		<h2>Theme Manager v.1.0.2</h2><br/>
		<h3>Features</h3>
		<ul style="list-style-type:square">
			<li>Install themes</li>
			<li>Update All/Selected themes</li>
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
                <option label="ThinkTheme" value="ThinkTheme"/>
                <option label="Aurora" value="Aurora"/>
                <option label="Machinon" value="Machinon"/>
                <option label="FLAT" value="FLAT"/>
                <option label="OsiTransparent" value="OsiTransparent"/>
                <option label="FlatBlue" value="FlatBlue"/>
		<option label="Serenity" value="Serenity"/>
            </options>
        </param>
         <param field="Mode4" label="Auto Update" width="175px">
            <options>
                <option label="All" value="All"/>
                <option label="Selected" value="Selected"/>
                <option label="None" value="None"/>
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
    pluginState = "Not Ready"
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
            "Aurora": ["flatsiedatsie", "domoticz-aurora-theme", "Aurora", "master"],
            "Machinon": ["domoticz", "machinon", "machinon", "master"],
            "ThinkTheme": ["DewGew", "Domoticz-ThinkTheme", "ThinkTheme", "master"],
            "FLAT": ["mixmint", "domoticz-flat-theme", "FLAT", "master"],
            "OsiTransparent": ["DT27", "osi-trans", "OsiTransparent", "master"],
            "FlatBlue": ["jonferreira", "domoticz-flat-blue-theme", "FlatBlue", "master"],
            "Serenity": ["gpajot", "domoticz-serenity-theme", "Serenity", "main"],
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


        pluginText = ""
        pluginAuthor = ""
        pluginRepository = ""
        pluginKey = ""

        pluginKey = Parameters["Mode2"]
        pluginAuthor = self.plugindata[pluginKey][0]
        pluginRepository = self.plugindata[pluginKey][1]
        pluginText = self.plugindata[pluginKey][2]
        pluginBranch = self.plugindata[pluginKey][3]    # GitHub branch to clone

        # Reading exception file and populating array of values
        exceptionFile = str(os.getcwd()) + "/plugins/THEME-MANAGER/exceptions.txt"
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
            Domoticz.Log("Updating All Plugins!!!")
            i = 0
            path = str(os.getcwd()) + "/www/styles/"
            for (path, dirs, files) in os.walk(path):
                for dir in dirs:
                    if str(dir) != "":
                        if str(dir) in self.plugindata:
                            self.UpdatePythonPlugin(pluginAuthor, pluginRepository, str(dir))
                        elif str(dir) == "THEME-MANAGER":
                            Domoticz.Debug("THEME-MANAGER Folder found. Skipping!!")      
                        else:
                            Domoticz.Log("Plugin:" + str(dir) + " cannot be managed with THEME-MANAGER!!.")      
                i += 1
                if i >= 1:
                   break

        if pluginKey == "Idle":
            Domoticz.Log("Plugin Idle")
            Domoticz.Heartbeat(60)
        else:
            Domoticz.Debug("Checking for dir:" + str(os.getcwd()) + "/www/styles/" + pluginKey)
            #If plugin Directory exists
            if (os.path.isdir(str(os.getcwd()) + "/www/styles/" + pluginKey)) == True:
                Domoticz.Debug("Folder for Theme:" + pluginKey + " already exists!!!")
                #Domoticz.Debug("Set 'Python Plugin Manager'/ 'Domoticz plugin' attribute to 'idle' in order t.")
                if Parameters["Mode4"] == 'Selected':
                    Domoticz.Debug("Updating Enabled for Theme:" + pluginText + ".Checking For Update!!!")
                    self.UpdatePythonPlugin(pluginAuthor, pluginRepository, pluginKey)
                Domoticz.Heartbeat(60)
            else:
               Domoticz.Log("Installation requested for Theme:" + pluginText)
               Domoticz.Debug("Installation URL is:" + "https://github.com/" + pluginAuthor +"/" + pluginRepository)
               Domoticz.Debug("Current Working dir is:" + str(os.getcwd()))
               if pluginKey in self.plugindata:
                    Domoticz.Log("Theme Display Name:" + pluginText)
                    Domoticz.Log("Theme Author:" + pluginAuthor)
                    Domoticz.Log("Theme Repository:" + pluginRepository)
                    Domoticz.Log("Theme Key:" + pluginKey)
                    Domoticz.Log("Theme Branch:" + pluginBranch)
                    self.InstallPythonPlugin(pluginAuthor, pluginRepository, pluginKey, pluginBranch)
               Domoticz.Heartbeat(60)
            


    def onStop(self):
        Domoticz.Debug("onStop called")
        Domoticz.Log("Theme is stopping.")
        #self.UpdatePythonPlugin("ycahome", "THEME-MANAGER", "THEME-MANAGER")
        Domoticz.Debugging(0)

    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat called")
        pluginKey = Parameters["Mode2"]

        CurHr = str(datetime.now().hour)
        CurMin = str(datetime.now().minute)
        if len(CurHr) == 1: CurHr = "0" + CurHr
        if len(CurMin) == 1: CurMin = "0" + CurMin
        Domoticz.Debug("Current time:" + CurHr + ":" + CurMin)

        if (mid(CurHr,0,2) == "12" and  mid(CurMin,0,2) == "00"):
            Domoticz.Log("Its time!!. Trigering Actions!!!")


            #-------------------------------------
            if Parameters["Mode4"] == 'All':
                Domoticz.Log("Checking Updates for All Plugins!!!")
                i = 0
                path = str(os.getcwd()) + "/www/styles/"
                for (path, dirs, files) in os.walk(path):
                    for dir in dirs:
                        if str(dir) != "":
                            self.UpdatePythonPlugin(self.plugindata[Parameters["Mode2"]][0], self.plugindata[Parameters["Mode2"]][1], str(dir))
                    i += 1
                    if i >= 1:
                       break

            if Parameters["Mode4"] == 'Selected':
                Domoticz.Log("Checking Updates for Theme:" + self.plugindata[pluginKey][2])
                self.UpdatePythonPlugin(self.plugindata[Parameters["Mode2"]][0], self.plugindata[Parameters["Mode2"]][1], Parameters["Mode2"])

            #if Parameters["Mode2"] == "Idle":
                #Domoticz.Log("Theme Idle. No actions to be performed!!!")
 









    # InstallPyhtonPlugin function
    def InstallPythonPlugin(self, ppAuthor, ppRepository, ppKey, ppBranch):
        Domoticz.Debug("InstallPythonPlugin called")


        Domoticz.Log("Installing Theme:" + self.plugindata[ppKey][2])
        ppCloneCmd = "LANG=en_US /usr/bin/git clone -b " + ppBranch + " https://github.com/" + ppAuthor + "/" + ppRepository + ".git " + ppKey
        Domoticz.Log("Calling:" + ppCloneCmd)
        try:
            pr = subprocess.Popen( ppCloneCmd , cwd = os.path.dirname(str(os.getcwd()) + "/www/styles/"), shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE )
            (out, error) = pr.communicate()
            if out:
                   Domoticz.Log("Succesfully installed:" + str(out).strip)
                   Domoticz.Log("---Restarting Domoticz MAY BE REQUIRED to activate new plugins---")
            if error:
                Domoticz.Debug("Git Error:" + str(error))
                if str(error).find("Cloning into") != -1:
                   Domoticz.Log("Theme " + ppKey + " installed Succesfully")
        except OSError as e:
            Domoticz.Error("Git ErrorNo:" + str(e.errno))
            Domoticz.Error("Git StrError:" + str(e.strerror))

        #try:
        #    pr1 = subprocess.Popen( "/etc/init.d/domoticz.sh restart" , cwd = os.path.dirname(str(os.getcwd()) + "/www/styles/"), shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE )
        #    (out1, error1) = pr1.communicate()
        #    if out1:
        #        Domoticz.Log("Command Response1:" + str(out1))
        #    if error1:
        #        Domoticz.Log("Command Error1:" + str(error1.strip()))
        #except OSError1 as e1:
        #    Domoticz.Error("Command ErrorNo1:" + str(e1.errno))
        #    Domoticz.Error("Command StrError1:" + str(e1.strerror))


        return None




    # UpdatePyhtonPlugin function
    def UpdatePythonPlugin(self, ppAuthor, ppRepository, ppKey):
        Domoticz.Debug("UpdatePythonPlugin called")

        if ppKey == "THEME-MANAGER":
            Domoticz.Log("Self Update Initiated")
            ppGitReset = "LANG=en_US /usr/bin/git reset --hard HEAD"
            try:
                pr = subprocess.Popen( ppGitReset , cwd = str(os.getcwd() + "/plugins/" + ppKey), shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE )
                (out, error) = pr.communicate()
                if out:
                    Domoticz.Debug("Git Response:" + str(out))
                if error:
                    Domoticz.Debug("Git Error:" + str(error.strip()))
            except OSError as eReset:
                Domoticz.Error("Git ErrorNo:" + str(eReset.errno))
                Domoticz.Error("Git StrError:" + str(eReset.strerror))

            
            
        elif (self.plugindata[ppKey][2] in self.ExceptionList):
            Domoticz.Log("Plugin:" + self.plugindata[ppKey][2] + " excluded by Exclusion file (exclusion.txt). Skipping!!!")
            return

        Domoticz.Log("Updating Theme:" + ppKey)
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
                   Domoticz.Log("Succesfully pulled gitHub update:" + str(out)[str(out).find("Updating")+8:26] + " for plugin " + ppKey)
                   Domoticz.Log("---Restarting Domoticz MAY BE REQUIRED to activate new plugins---")
                else:
                   Domoticz.Error("Something went wrong with update of " + str(ppKey))
            if error:
                Domoticz.Debug("Git Error:" + str(error.strip()))
                if str(error).find("Not a git repository") != -1:
                   Domoticz.Log("Plugin:" + ppKey + " is not installed from gitHub. Cannot be updated with THEME-MANAGER!!.")
        except OSError as e:
            Domoticz.Error("Git ErrorNo:" + str(e.errno))
            Domoticz.Error("Git StrError:" + str(e.strerror))

        return None


    # CheckForUpdatePythonPlugin function
    def CheckForUpdatePythonPlugin(self, ppAuthor, ppRepository, ppKey):
        Domoticz.Debug("CheckForUpdatePythonPlugin called")

        if (self.plugindata[ppKey][2] in self.ExceptionList):
            Domoticz.Log("Plugin:" + self.plugindata[ppKey][2] + " excluded by Exclusion file (exclusion.txt). Skipping!!!")
            return

        Domoticz.Debug("Checking Theme:" + ppKey + " for updates")
        
        
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
                   Domoticz.Log("Found that we are behind on plugin " + ppKey)
                elif (str(out).find("Your branch is ahead") != -1) and (str(str(out).find("error")) == "-1"):
                   Domoticz.Debug("Found that we are ahead on plugin " + ppKey + ". No need for update")
                else:
                   Domoticz.Error("Something went wrong with update of " + str(ppKey))
            if error:
                Domoticz.Debug("Git Error:" + str(error.strip()))
                if str(error).find("Not a git repository") != -1:
                   Domoticz.Log("Plugin:" + ppKey + " is not installed from gitHub. Ignoring!!.")
        except OSError as e:
            Domoticz.Error("Git ErrorNo:" + str(e.errno))
            Domoticz.Error("Git StrError:" + str(e.strerror))

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



        
    def parseFileForSecurityIssues(self, pyfilename, pypluginid):
       Domoticz.Debug("parseFileForSecurityIssues called")
       secmonitorOnly = False

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

       if pypluginid not in self.SecPolUserList:
            self.SecPolUserList[pypluginid] = []

       lineNum = 1
       #Domoticz.Error("self.SecPolUserList[pypluginid]:" + str(self.SecPolUserList[pypluginid]))
       for text in file.readlines():
          text = text.rstrip()

          #Domoticz.Log("'text' is:'" + str(text))
          regexFound = re.findall(r'(?:[\d]{1,3})\.(?:[\d]{1,3})\.(?:[\d]{1,3})\.(?:[\d]{1,3})',text)
          paramFound = re.findall(r'<param field=',text)
          if ((regexFound) and not (paramFound)):
              #regexFound[rex] = regexFound[rex].strip('"]')
              #Domoticz.Error("Security Finding(IPregex):" + str(regexFound) + " LINE: " + str(lineNum) + " FILE:" + pyfilename)
              for rex in range(0,len(regexFound)):
                   if ((str(text).strip() not in self.SecPolUserList["Global"]) and (str(text).strip() not in self.SecPolUserList[pypluginid]) and (str(text).strip() != "") and (mid(text,0,1) != "#")):
                       Domoticz.Error("Security Finding(IP):-->" + str(text).strip() + "<-- LINE: " + str(lineNum) + " FILE:" + pyfilename)
                       #Domoticz.Error("Security Finding(IPr):" + regexFound[rex] + " LINE: " + str(lineNum) + " FILE:" + pyfilename)
                       ips["IP" + str(lineNum)] = (regexFound[rex], "IP Address")

          #rex = 0
          #regexFound = re.findall('import', text)

          #if regexFound:
              #regexFound[rex] = regexFound[rex].strip('"]')
              #Domoticz.Error("Security Finding(IPregex):" + str(regexFound) + " LINE: " + str(lineNum) + " FILE:" + pyfilename)
          #    for rex in range(0,len(regexFound)):
          #         if ((str(text).strip() not in self.SecPolUserList["Global"]) and (str(text).strip() not in self.SecPolUserList[pypluginid]) and (str(text).strip() != "") and (mid(text,0,1) != "#")):
          #             Domoticz.Error("Security Finding(IMP):-->" + str(text) + "<-- LINE: " + str(lineNum) + " FILE:" + pyfilename)
                       #Domoticz.Error("Security Finding(IPr):" + regexFound[rex] + " LINE: " + str(lineNum) + " FILE:" + pyfilename)
          #             ips["IP" + str(lineNum)] = (regexFound[rex], "Import")

          #rex = 0
          #regexFound = re.findall('subprocess.Popen', text)

          #if regexFound:
              #regexFound[rex] = regexFound[rex].strip('"]')
              #Domoticz.Error("Security Finding(IPregex):" + str(regexFound) + " LINE: " + str(lineNum) + " FILE:" + pyfilename)
          #    for rex in range(0,len(regexFound)):
          #         if ((str(text).strip() not in self.SecPolUserList["Global"]) and (str(text).strip() not in self.SecPolUserList[pypluginid]) and (str(text).strip() != "") and (mid(text,0,1) != "#")):
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
          #         if ((str(text).strip() not in self.SecPolUserList[pypluginid]) and (str(text).strip() != "") and (mid(text,0,1) != "#")):
          #             Domoticz.Error("Security Finding(HTTP):-->" + str(text) + "<-- LINE: " + str(lineNum) + " FILE:" + pyfilename)
                       #Domoticz.Error("Security Finding(IPr):" + regexFound[rex] + " LINE: " + str(lineNum) + " FILE:" + pyfilename)
          #             ips["IP" + str(lineNum)] = (regexFound[rex], "HTTP Address")


          lineNum = lineNum + 1



       file.close()
       Domoticz.Debug("IPS Table contents are:" + str(ips))



       
        
        
        
        
        
        
        
        
        









global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()


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


