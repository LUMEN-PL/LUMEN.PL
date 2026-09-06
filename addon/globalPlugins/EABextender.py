# -*- coding: utf-8 -*-
# EABextender
# Copyright (C) 2025
# Version 1.0
# License GNU GPL
# Date: 25/12/2025
# work: LUMEN PL

# Define context sensitive keyboard shortcuts for Papenmeier braille terminals  

import globalCommands
import threading
import os
from configobj import ConfigObj
import globalPluginHandler
import inputCore
import keyboardHandler
import gui
import wx
import config
import globalVars
import scriptHandler
import ui
import api
import winUser
import versionInfo
import addonHandler
import logging

log = logging.getLogger("EABextender")

# Turning on the translation
addonHandler.initTranslation()

# Each global constant is prefixed with "GS".

# Constants
GSProfiles = os.path.join(globalVars.appArgs.configPath, "addons", "EABextender", "Profiles")
        
class DeleteConfirmationDialog(wx.Dialog):
    def __init__(self, parent, name):
        title = _("Delete profile")
        super().__init__(parent, title=title)

        message = _(
            "Are you sure you want to delete the profile named {name}? "
            "This cannot be undone."
        ).format(name=name)

        mainSizer = wx.BoxSizer(wx.VERTICAL)

        text = wx.StaticText(self, label=message)
        mainSizer.Add(text, 0, wx.ALL, 10)

        btnSizer = self.CreateButtonSizer(wx.YES | wx.CANCEL)
        mainSizer.Add(btnSizer, 0, wx.ALL | wx.ALIGN_CENTER, 10)

        self.SetSizerAndFit(mainSizer)

class AccordInputDialog(wx.Dialog):
    def __init__(self, parent, title,inputString):
        super(AccordInputDialog,self).__init__( parent, title=title )
        
        self.accords = {
            "EAB left" : "",
            "EAB right" : "",
            "EAB up" : "",
            "EAB down" : "",
            "Routing+EAB left" : "",
            "Routing+EAB right" : "",
            "Routing+EAB up" : "",
            "Routing+EAB down" : "",
        }
        
        inputList=inputString.split(",")
        
        self.accords["EAB left"]=inputList[0]
        self.accords["EAB right"]=inputList[1]
        self.accords["EAB up"]=inputList[2]
        self.accords["EAB down"]=inputList[3]
        self.accords["Routing+EAB left"]=inputList[4]
        self.accords["Routing+EAB right"]=inputList[5]
        self.accords["Routing+EAB up"]=inputList[6]
        self.accords["Routing+EAB down"]=inputList[7]
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        sHelper = gui.guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
        # Translators: The label for the list view of the accords for the current profile.
        accordsText = _('Press Enter, then press the key or keyboard shortcut you want to assign to this EAB action')
        self.ListAccordList = sHelper.addLabeledControl(
            accordsText, wx.ListCtrl, style=wx.LC_REPORT | wx.LC_SINGLE_SEL, size=(900, 350)
        )
        self.ListAccordList.Bind(wx.EVT_KEY_DOWN, self.onListKeyDown)
        
        self.ListAccordList.InsertColumn(0, _("Accord"), width=250)
        self.ListAccordList.InsertColumn(1, _("Shortcut"), width=300)
        self.ListAccordList.InsertColumn(2, "NVDA", width=350)
        self.ListAccordList.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.onGetShortcut)            
        
        
        for entry in self.accords.keys():
            shortcut = self.accords[entry]
            self.ListAccordList.Append((entry, shortcut, self.getNvdaFunction(shortcut)))
            
        self.ListAccordList.Select(0, on=1)
        self.ListAccordList.SetItemState(0, wx.LIST_STATE_FOCUSED, wx.LIST_STATE_FOCUSED)


        # Borrowed from NVDA Core (add-ons manager).
        # To allow the dialog to be closed with the escape key.

        mainSizer.Add(sHelper.sizer, border=gui.guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
        
        #btnSizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        #mainSizer.Add(btnSizer, flag=wx.EXPAND | wx.ALL, border=10)
        
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.defineButton = wx.Button(self, label=_("&Define"))
        self.okButton = wx.Button(self, wx.ID_OK)
        self.cancelButton = wx.Button(self, wx.ID_CANCEL)
        btnSizer.Add(self.defineButton, flag=wx.RIGHT, border=5)
        btnSizer.Add(self.okButton, flag=wx.RIGHT, border=5)
        btnSizer.Add(self.cancelButton)

        self.defineButton.Bind(wx.EVT_BUTTON, self.onGetShortcut)

        mainSizer.Add(btnSizer, flag=wx.ALIGN_RIGHT | wx.ALL, border=10)
        
        self.Sizer = mainSizer
        mainSizer.Fit(self)
        self.ListAccordList.SetFocus()
        self.CenterOnScreen()
        
    def onListKeyDown(self,event):
        key = event.GetKeyCode()
        lc = self.ListAccordList
        count = lc.GetItemCount()
        selected = lc.GetFirstSelected()
        
        if count == 0:
            event.Skip()
            return
        
        if key == wx.WXK_LEFT:
            nextIndex = (selected-1) % count
            lc.Select(selected,False)
            lc.Select(nextIndex)
            lc.Focus(nextIndex)
            return
        
        if key == wx.WXK_RIGHT:
            nextIndex = (selected+1) % count
            lc.Select(selected, False)
            lc.Select(nextIndex)
            lc.Focus(nextIndex)
            return

        if key == wx.WXK_DOWN:
            if selected == count -1:
                lc.Select(selected,False)
                lc.Select(0)
                lc.Focus(0)
                return
                
        if key == wx.WXK_UP:
            if selected == 0:
                lc.Select(0,False)
                lc.Select(count-1)
                lc.Focus(count-1)
                return
                

                
        event.Skip()
        

    def getNvdaFunction(self, shortcut):
        """Return the command NVDA actually resolves for this keyboard shortcut."""
        if not shortcut:
            return ""
        try:
            # This follows the same effective route as NVDA Input Help:
            # build a real keyboard gesture and ask NVDA which script is bound to it.
            gesture = keyboardHandler.KeyboardInputGesture.fromName(shortcut)
            script = gesture.script
            if script:
                description = getattr(script, "__doc__", None)
                if description:
                    return description.strip()
                try:
                    return scriptHandler.getScriptName(script)
                except Exception:
                    return getattr(script, "__name__", "")
        except Exception:
            log.exception("Cannot directly resolve NVDA command for shortcut %r", shortcut)

        # Fallback: inspect the mappings exposed to the Input Gestures dialog.
        try:
            gestureId = inputCore.normalizeGestureIdentifier("kb:" + shortcut)
            mappings = inputCore.manager.getAllGestureMappings()
            matches = []
            for category in mappings.values():
                for displayName, scriptInfo in category.items():
                    for gestureIdentifier in scriptInfo.gestures:
                        try:
                            normalized = inputCore.normalizeGestureIdentifier(gestureIdentifier)
                        except Exception:
                            continue
                        if normalized == gestureId:
                            if displayName not in matches:
                                matches.append(displayName)
                            break
            return " / ".join(matches)
        except Exception:
            log.exception("Cannot resolve mapped NVDA command for shortcut %r", shortcut)
            return ""

    def getValue(self):
        return ",".join([
            self.accords["EAB left"],
            self.accords["EAB right"],
            self.accords["EAB up"],
            self.accords["EAB down"],
            self.accords["Routing+EAB left"],
            self.accords["Routing+EAB right"],
            self.accords["Routing+EAB up"],
            self.accords["Routing+EAB down"],])
        
    def onGetShortcut(self,event):
        wx.CallLater(500, ui.message, _("Enter input gesture:"))
        #t = threading.Timer(0.5, ui.message, [_("Enter input gesture:")])
        #t.start()
        inputCore.manager._captureFunc = self.addGestureCaptor
        
    def addGestureCaptor(self, gesture: inputCore.InputGesture):
        if gesture.isModifier:
            return False
        inputCore.manager._captureFunc = None
        wx.CallAfter(self.saveShortCut, gesture.identifiers[-1])
        return False
        
    def saveShortCut(self,str):
        global shortCut
        index = self.ListAccordList.GetFirstSelected()
        name = self.ListAccordList.GetItemText(index)
        shortCut = str.split(":")[1]
        shortCut = shortCut.replace("control","CONTROL")
        # we wanna explicitely forbid using , in the shortcut
        if "," in shortCut: #or shortCut in [
#            "tab", "shift+tab", "upArrow", "downArrow", "leftArrow", "rightArrow", "home", "end", "escape",
#            "pageUp", "pageDown", "numpadEnter", "space", "enter"]:
            gui.messageBox(
                # Translators: Message displayde if shortCut is not valid.
                _("This shortCut is not valid, choose another one please"),
                # Translators: Title of message box.
                _("Information"), wx.OK | wx.ICON_INFORMATION
            )
            return
        self.accords[name]=shortCut
        self.ListAccordList.SetItem(index,1,shortCut)
        self.ListAccordList.SetItem(index,2,self.getNvdaFunction(shortCut))
        self.ListAccordList.SetFocus()


# beda potrzebne dwie takie klasy - jedna do trybu a druga do wprowadzania skrotow
class ProfileList(wx.Dialog):
    """
    This dialog is for listing the profiles saved for the current application
    For now, it is accesible via script script_ProfileList activated by nvda+control+p shortcut
    """
    # The following comes from exit dialog class from GUI package (credit: NV Access and Zahari from Bulgaria).
    _instance = None

    def __new__(cls, parent, *args, **kwargs):
        inst = cls._instance() if cls._instance else None
        if not inst:
            return super(cls, cls).__new__(cls, parent, *args, **kwargs)
        return inst

    def __init__(self, parent, appModule, appName=None):
        inst = ProfileList._instance() if ProfileList._instance else None
        if inst:
            return
        # Use a weakref so the instance can die.
        import weakref
        ProfileList._instance = weakref.ref(self)

        if appName:
            #Translators: title of the dialog window listing profiles for selected application
            super(ProfileList, self).__init__(parent, title=_("Profile selector for %s") % (appName), size=(420, 300))
            self.appModule = appModule
            self.profileDefinitionDialog = None
            self.otherDialog = None
            self.dlgDelete = None
            self.ListProfileList(appName=appName)
        else:
            # this should never happen.
            ui.message(_("Sorry, something went wrong."))
            log.error("Cannot recognize active application - this should never happen.")
            
    def onListKeyDown(self,event):
        key = event.GetKeyCode()
        lc = self.ListProfileList
        count = lc.GetItemCount()
        selected = lc.GetFirstSelected()
        
        if count == 0:
            event.Skip()
            return
        
        if key == wx.WXK_LEFT:
            nextIndex = (selected-1) % count
            lc.Select(selected,False)
            lc.Select(nextIndex)
            lc.Focus(nextIndex)
            return
        
        if key == wx.WXK_RIGHT:
            nextIndex = (selected+1) % count
            lc.Select(selected, False)
            lc.Select(nextIndex)
            lc.Focus(nextIndex)
            return

        if key == wx.WXK_DOWN:
            if selected == count -1:
                lc.Select(selected,False)
                lc.Select(0)
                lc.Focus(0)
                return
                
        if key == wx.WXK_UP:
            if selected == 0:
                lc.Select(0,False)
                lc.Select(count-1)
                lc.Focus(count-1)
                return
                
                
        event.Skip()

    def ListProfileList(self, appName):
        self.appName = appName
        # If the files path does not exist, create it now.
        if not os.path.exists(GSProfiles):
            os.mkdir(GSProfiles)
        self.profiles = ConfigObj(os.path.join(GSProfiles, f"{appName}.gs"), encoding="UTF-8")
        self.activeprof = None
        if len(self.profiles) :
            for entry in self.profiles.keys():
                if entry == "activProf" :
                    self.activeprof = self.profiles[entry]
                    
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        sHelper = gui.guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
        # Translators: The label for the list view of the profiles in the current application.
        # NVDA announces the label associated with the list control, not only the
        # control's accessible name. Therefore the label itself must change when
        # there are no profiles.
        hasProfiles = any(entry != "activProf" for entry in self.profiles.keys())
        if hasProfiles:
            profilesText = _("&Saved profiles")
        else:
            profilesText = _('No profile has been created for this application yet. Click "New" to create a profile.')
        self.ListProfileList = sHelper.addLabeledControl(
            profilesText, wx.ListCtrl, style=wx.LC_REPORT | wx.LC_SINGLE_SEL, size=(550, 350)
        )
        self.profileListLabel = self.ListProfileList.GetPrevSibling()
        
        self.ListProfileList.Bind(wx.EVT_KEY_DOWN, self.onListKeyDown)
        self.listItems()
        self.updateProfileListAccessibleName()
		
        bHelper = gui.guiHelper.ButtonHelper(orientation=wx.HORIZONTAL)

        activateButtonID = wx.NewIdRef()
        # Translators: the button to activate a profile position.
        self.activateButton = bHelper.addButton(self, activateButtonID, _("&OK"), wx.DefaultPosition)

        defineButtonID = wx.NewIdRef()
        # Translators: the button to define the shortcuts for this profile.
        self.defineButton = bHelper.addButton(self, defineButtonID, _("&Define"), wx.DefaultPosition)

        renameButtonID = wx.NewIdRef()
        # Translators: the button to rename a profile name.
        bHelper.addButton(self, renameButtonID, _("&Rename"), wx.DefaultPosition)

        deleteButtonID = wx.NewIdRef()
        # Translators: the button to delete the profile.
        bHelper.addButton(self, deleteButtonID, _("&Delete"), wx.DefaultPosition)

        newButtonID = wx.NewIdRef()
        # Translators: the button to create a new profile for this app.
        self.newButton = bHelper.addButton(self, newButtonID, _("&New"), wx.DefaultPosition)

        # Translators: The label of a button to close the profile listing dialog.
        bHelper.addButton(self, wx.ID_CLOSE, _("&Close"), wx.DefaultPosition)

        sHelper.addItem(bHelper)

        self.Bind(wx.EVT_BUTTON, self.onActivate, id=activateButtonID)
        self.Bind(wx.EVT_BUTTON, self.onDefine, id=defineButtonID)
        self.Bind(wx.EVT_BUTTON, self.onRename, id=renameButtonID)
        self.Bind(wx.EVT_BUTTON, self.onDelete, id=deleteButtonID)
        self.Bind(wx.EVT_BUTTON, self.onNew, id=newButtonID)
        self.Bind(wx.EVT_BUTTON, lambda evt: self.Close(), id=wx.ID_CLOSE)

        # Borrowed from NVDA Core (add-ons manager).
        # To allow the dialog to be closed with the escape key.
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.EscapeId = wx.ID_CLOSE

        mainSizer.Add(sHelper.sizer, border=gui.guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
        self.Sizer = mainSizer
        mainSizer.Fit(self)
        self.ListProfileList.SetFocus()
        self.CenterOnScreen()
        
    def updateProfileListAccessibleName(self):
        """Update the accessible name and the label associated with the profile list."""
        if self.ListProfileList.GetItemCount() == 0:
            label = _('No profile has been created for this application yet. Click "New" to create a profile.')
        else:
            label = _("Saved profiles")
        self.ListProfileList.SetName(label)
        if getattr(self, "profileListLabel", None):
            self.profileListLabel.SetLabel(label)

    def listItems(self):
        # Translators: the column in profile list to identify the profile name.
        self.ListProfileList.InsertColumn(0, _("Name"), width=150)
        self.ListProfileList.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.onActivate)
		
        if len(self.profiles):
            item_count=-1
            for entry in sorted(self.profiles.keys()):
                if entry != "activProf":
                    self.ListProfileList.Append((entry,))
                    item_count = item_count+1
                if entry == self.activeprof :
                    self.ListProfileList.Select(item_count, on=1)
                    self.ListProfileList.SetItemState(item_count, wx.LIST_STATE_FOCUSED, wx.LIST_STATE_FOCUSED)

    def onRename(self, event):
        if self.ListProfileList.GetItemCount() == 0:
            return;
        index = self.ListProfileList.GetFirstSelected()
        oldName = self.ListProfileList.GetItemText(index)
        self.otherDialog = wx.TextEntryDialog(
            parent = self,
            message = _("New name"),
            caption = _("Rename"),
            value= oldName
        )
        
        name=""
        if self.otherDialog.ShowModal() == wx.ID_OK:
            name = self.otherDialog.GetValue()
            
        self.otherDialog.Destroy()
        self.otherDialog = None

        # When escape is pressed, an empty string is returned.
        if name in ("", oldName):
            return
        if name in self.profiles:
            ui.message(_("Another profile has the same name as the entered name. Please choose a different name."))
            log.warning("Rename: trying to use the same profile name twice.")
            #gui.messageBox(
            #    # Translators: An error displayed when renaming a profile
                # with the new name already exists.
            #    _("Another profile has the same name as the entered name. Please choose a different name."),
            #    _("Error"), wx.OK | wx.ICON_ERROR, self
            #)
            return

        
        self.ListProfileList.SetItemText(index, name)
        self.ListProfileList.SetFocus()
        self.profiles[name] = self.profiles[oldName]
        del self.profiles[oldName]

        if oldName == self.activeprof :
            self.profiles["activProf"] = name
            self.activeprof = name

    def onNew(self,event):
        
#        name = wx.GetTextFromUser(
#            # Translators: The label of a field to enter a new name for a profile.
#            _("Profile name"),
#            # Translators: The title of the dialog to rename a profile.
#            _("New profile")
#        )
        self.otherDialog = wx.TextEntryDialog(
            parent = self,
            message = _("Profile name"),
            caption = _("New profile"),
            value=_("NVDA default settings")
        )
        
        name=""
        if self.otherDialog.ShowModal() == wx.ID_OK:
            name = self.otherDialog.GetValue()
            
        self.otherDialog.Destroy()
        self.otherDialog = None        
        # When escape is pressed, an empty string is returned.
        if name in (""):
            return
        if name in self.profiles or name == "activProf":
            ui.message(_("Please choose a different name."))
            log.warning("New: the new profile name has to be different than existing ones.")
            #gui.messageBox(
                # Translators: An error displayed when creating a profile
                # and a tag with the new name already exists.
            #    _("Please choose a different name."),
            #    _("Error"), wx.OK | wx.ICON_ERROR, self
            #)
            return
        self.ListProfileList.InsertItem(self.ListProfileList.GetItemCount(),name)
        
        self.updateProfileListAccessibleName()
        # this are the shortcuts mapped to default papenmeier NVDA actions
        # the routing keyboard shortcuts are already in NVDA
        # for the EAB left/right/up/down we need to extra code the assignment of the action to the keyboard shortcut
        self.profiles[name]="alt+CONTROL+shift+leftArrow,alt+CONTROL+shift+rightArrow,alt+CONTROL+shift+upArrow,alt+CONTROL+shift+downArrow,NVDA+numpad4,NVDA+numpad6,NVDA+numpad8,NVDA+numpad2"
        
        itemCount = self.ListProfileList.GetItemCount()
        selectedIndex = itemCount-1
        
        if( itemCount == 1 ):
            self.profiles["activProf"]=name
            
        self.ListProfileList.Select(selectedIndex, on=1)
        self.ListProfileList.SetItemState(selectedIndex, wx.LIST_STATE_FOCUSED, wx.LIST_STATE_FOCUSED)
            
        wx.CallAfter(self.defineButton.SetFocus)

    def onDelete(self,event):
        if self.ListProfileList.GetItemCount() == 0:
            return;
        #message, title = "", ""
        entry = self.ListProfileList.GetFirstSelected()
        name = self.ListProfileList.GetItemText(entry)
        #message = _(
        #        # Translators: The confirmation prompt displayed when the user requests to delete the selected tag.
        #        "Are you sure you want to delete the profile named {name}? This cannot be undone."
        #    ).format(name=name)
        ## Translators: The title of the confirmation dialog for deletion of selected position.
        #title = _("Delete profile")
        #if gui.messageBox(
        #    message, title, wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION, self
        #) == wx.NO:
        #    return
        
        self.dlgDelete = DeleteConfirmationDialog(self, name)
        result = self.dlgDelete.ShowModal()
        self.dlgDelete.Destroy()

        if result != wx.ID_YES:
            return      
        
        delActive = False

        if name == self.activeprof :
            delActive = True
            
        del self.profiles[name]
        self.ListProfileList.DeleteItem(entry)

        self.updateProfileListAccessibleName()
        if self.ListProfileList.GetItemCount() > 0:
            self.ListProfileList.Select(0, on=1)    
            if delActive:
                entry = self.ListProfileList.GetFirstSelected()
                name = self.ListProfileList.GetItemText(entry)
                self.profiles["activProf"] = name
                self.activeprof = name
        else: 
            self.activeprof = None
            del self.profiles["activProf"]
        self.ListProfileList.SetFocus()

        
    def onActivate(self, event):
        if self.ListProfileList.GetItemCount() == 0:
            return;
        #message, title = "", ""
        entry = self.ListProfileList.GetFirstSelected()
        name = self.ListProfileList.GetItemText(entry)
        #message = _(
        #        # Translators: The confirmation prompt displayed when the user requests to activate the selected profile.
        #        "Do you want to activate the profile named {name}?"
        #    ).format(name=name)
        # Translators: The title of the confirmation dialog for activating selected profile.
        #title = _("Activate profile")
        #if gui.messageBox(
        #    message, title, wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION, self
        #) == wx.NO:
        #    return
        self.profiles["activProf"] = name
        self.activeprof = name
        self.onClose(event)
        
    def onDefine(self,event):
        if self.ListProfileList.GetItemCount() == 0:
            ui.message(_('No profile has been created for this application yet. Click "New" to create a profile.'))
            wx.CallAfter(self.newButton.SetFocus)
            log.warning("Define: cannot define an empty profile.")
            #gui.messageBox(
                # Translators: An error trying to define a profile when there isnt any
            #    _("Please create some profiles."),
            #    _("Error"), wx.OK | wx.ICON_ERROR, self
            #)
            return
        entry = self.ListProfileList.GetFirstSelected()
        profileName = self.ListProfileList.GetItemText(entry)
        # Translators: the title of the profile definition dialog
        self.profileDefinitionDialog=AccordInputDialog(parent=self,
            title=_("Defining profile {profileName} for {aName}").format(profileName=profileName,aName=self.appName),
            inputString=self.profiles[profileName])
        result=self.profileDefinitionDialog.ShowModal()
        if result==wx.ID_OK:
            accordStr=self.profileDefinitionDialog.getValue()
            self.profiles[profileName]=accordStr
            # After closing the Define dialog with OK, move focus
            # to the OK button in the main profile dialog.
            wx.CallAfter(self.activateButton.SetFocus)
            #log.warning(accordStr)

    def onClose(self, evt):
        self.profileDefinitionDialog = None
        self.appModule.mainDialog = None
        self.Destroy()
        if len(self.profiles):
            self.profiles.write()
        else:
            if os.path.exists(self.profiles.filename):
                os.remove(self.profiles.filename)
        self.profiles = None
        
class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    scriptCategory = _("EABextender")

    def __init__(self, *args, **kwargs):
        super(GlobalPlugin, self).__init__(*args, **kwargs)
        self.getAppRestriction = None
        self.restriction = False
        self.mouseArrows = False
        self.mainDialog = None
        self.gestures = {
            "br(papenmeier):left": "kb:leftarrow",
            "br(papenmeier):right": "kb:rightarrow",
            "br(papenmeier):up": "kb:uparrow",
            "br(papenmeier):dn": "kb:downarrow",
            "br(papenmeier):left2": "kb:shift+tab",
            "br(papenmeier):right2": "kb:tab",
            "br(papenmeier):up2": "kb:escape",
            "br(papenmeier):dn2": "kb:enter",
        }

        self.defaultNVDAgestures = {
            "br(papenmeier):left": "kb:alt+CONTROL+shift+leftArrow",
            "br(papenmeier):right": "kb:alt+CONTROL+shift+rightArrow",
            "br(papenmeier):up": "kb:alt+CONTROL+shift+upArrow",
            "br(papenmeier):dn": "kb:alt+CONTROL+shift+downArrow",
            "br(papenmeier):left2": "kb:NVDA+numpad4",
            "br(papenmeier):right2": "NVDA+numpad6",
            "br(papenmeier):up2": "kb:NVDA+numpad8",
            "br(papenmeier):dn2": "kb:NVDA+numpad2",
        }
        
#		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(GoldenCursorSettings)
#
#	def terminate(self):
#		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(GoldenCursorSettings)

    def event_gainFocus(self, obj, nextHandler):
        if self.isInMyDialog(obj):
            #ui.message("Focus moved withing our dialog.")
            self.mapDefaultGestures()
        else:
            self.mapBrGestures()
        nextHandler()
        
    def mapDefaultGestures(self):
        for src, dst in self.gestures.items():
            #log.warning("INSTALLING %s -> %s" % (src, dst))
            inputCore.manager.userGestureMap.add(
                src, "globalCommands", "GlobalCommands", dst, True)
                
    def mapDefaultNVDAGestures(self):
        for src, dst in self.defaultNVDAgestures.items():
            #log.warning("INSTALLING %s -> %s" % (src, dst))
            inputCore.manager.userGestureMap.add(
                src, "globalCommands", "GlobalCommands", dst, True)
        
    def mapBrGestures(self):
        appName = api.getFocusObject().appModule.appName
        #ui.message(f"Focus moved within {appName}")
        if os.path.exists(os.path.join(GSProfiles, f"{appName}.gs")):
            lprofiles = ConfigObj(os.path.join(GSProfiles, f"{appName}.gs"), encoding="UTF-8")
            lactiveprof = None
            if len(lprofiles) :
                for entry in lprofiles.keys():
                    if entry == "activProf" :
                        lactiveprof = lprofiles[entry]
                #log.warning(lactiveprof)
                #log.warning(lprofiles[lactiveprof])
                
                inputString = lprofiles[lactiveprof]
                inputList=inputString.split(",")
                
                accords = {
                    "br(papenmeier):left" : "kb:"+inputList[0],
                    "br(papenmeier):right" : "kb:"+inputList[1],
                    "br(papenmeier):up" : "kb:"+inputList[2],
                    "br(papenmeier):dn" : "kb:"+inputList[3],
                    "br(papenmeier):left2" : "kb:"+inputList[4],
                    "br(papenmeier):right2" : "kb:"+inputList[5],
                    "br(papenmeier):up2" : "kb:"+inputList[6],
                    "br(papenmeier):dn2" : "kb:"+inputList[7],
                }
                for src, dst in accords.items():
                    #log.warning("INSTALLING %s -> %s" % (src, dst))
                    inputCore.manager.userGestureMap.add(
                        src, "globalCommands", "GlobalCommands", dst, True)
        else: 
            self.mapDefaultNVDAGestures()


    def isInMyDialog(self, obj):
        if self.mainDialog:
            while obj:
                #log.warning("object exists")
                if getattr(obj, "windowHandle", None) == self.mainDialog.GetHandle():
                    return True
                if self.mainDialog.profileDefinitionDialog:
                    if getattr(obj, "windowHandle", None) == self.mainDialog.profileDefinitionDialog.GetHandle():
                        return True
                if self.mainDialog.otherDialog:
                    if getattr(obj, "windowHandle", None) == self.mainDialog.otherDialog.GetHandle():
                        return True
                if self.mainDialog.dlgDelete:
                    if getattr(obj, "windowHandle", None) == self.mainDialog.dlgDelete.GetHandle():
                        return True        
                    
                obj = obj.parent
                
            #log.warning("object stopped existing")
        return False

    @scriptHandler.script(
        # Translators: input help message for a Golden Shortcut command.
        description=_("Opens a dialog listing profiles for the current application"),
        gesture="kb:nvda+control+e"
    )
    def script_ProfileList(self, gesture):
        appName = api.getForegroundObject().appModule.appName
        try:
            self.mainDialog = ProfileList(parent=gui.mainFrame, appModule=self, appName=appName)
            gui.mainFrame.prePopup()
            self.mainDialog.Raise()
            self.mainDialog.Show()
            gui.mainFrame.postPopup()
        except RuntimeError:
            pass
            
    __gestures = {
        "br(papenmeier):r1" : "ProfileList",
        "br(papenmeier):l2" : "displayNVDABrailleSettings",
        "kb:alt+CONTROL+shift+upArrow": "brailleLineUp",
        "kb:alt+CONTROL+shift+downArrow": "brailleLineDown",
        "kb:alt+CONTROL+shift+leftArrow": "brailleLineLeft",
        "kb:alt+CONTROL+shift+rightArrow": "brailleLineRight",
    }
    
    @scriptHandler.script(
        description=_("Moves the braille display to the previous line"),
        category=_("Braille"),
    )
    
    def script_brailleLineUp(self,gesture):
        gc = globalCommands.commands
        gc.script_braille_previousLine(gesture)
        
    @scriptHandler.script(
        description=_("Moves the braille display to the next line"),
        category=_("Braille"),
    )
    
    def script_brailleLineDown(self,gesture):
        gc = globalCommands.commands
        gc.script_braille_nextLine(gesture)
        
    @scriptHandler.script(
        description=_("Scrolls the braille display back"),
        category=_("Braille"),
    )
    
    def script_brailleLineLeft(self,gesture):
        gc = globalCommands.commands
        gc.script_braille_scrollBack(gesture)
        
    @scriptHandler.script(
        description=_("Scrolls the braille display forward"),
        category=_("Braille"),
    )
    
    def script_brailleLineRight(self,gesture):
        gc = globalCommands.commands
        gc.script_braille_scrollForward(gesture)
        
    @scriptHandler.script(
        description = _("Shows NVDA's braille settings"),
        category = _("Configuration"),
        gesture = "kb:alt+control+shift+b"
    )
    
    def script_displayNVDABrailleSettings(self,gesture):
        gc = globalCommands.commands
        gc.script_activateBrailleSettingsDialog(gesture)


## Add-on config database
## Borrowed from Enhanced Touch Gestures by Joseph Lee
#confspec = {
#	"reportNewMouseCoordinates": "boolean(default=true)",
#	"mouseMovementUnit": "integer(min=1, max=100, default=5)",
#}
#config.conf.spec["goldenCursor"] = confspec
#
## this we will not need at all (for now) - soon to be commented out
#class GoldenCursorSettings(gui.settingsDialogs.SettingsPanel):
#	# Translators: This is the label for the Golden Cursor settings category in NVDA Settings screen.
#	title = _("Golden Cursor")
#
#	def makeSettings(self, settingsSizer):
#		gcHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
#		self.mouseCoordinatesCheckBox = gcHelper.addItem(
#			# Translators: This is the label for a checkbox in the
#			# Golden Cursor settings dialog.
#			wx.CheckBox(self, label=_("&Announce new mouse coordinates when mouse moves"))
#		)
#		self.mouseCoordinatesCheckBox.SetValue(config.conf["goldenCursor"]["reportNewMouseCoordinates"])
#		self.mouseMovementUnit = gcHelper.addLabeledControl(
#			# Translators: The label for a setting in Golden Cursor settings dialog to change mouse movement units.
#			_("Mouse movement &unit (in pixels)"), gui.nvdaControls.SelectOnFocusSpinCtrl,
#			min=1, max=100, initial=config.conf["goldenCursor"]["mouseMovementUnit"]
#		)
#
#	def onSave(self):
#		config.conf["goldenCursor"]["reportNewMouseCoordinates"] = self.mouseCoordinatesCheckBox.IsChecked()
#		config.conf["goldenCursor"]["mouseMovementUnit"] = self.mouseMovementUnit.Value
#