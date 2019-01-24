# -*- coding: UTF8 -*-
#!/usr/bin/python
'''
Created on 2018-5-22

@author: wushengbing
'''
import os
import sys
import time
import json
import shutil
import subprocess
import traceback
import PyQt5.QtWidgets
import PyQt5.QtGui
import PyQt5.QtCore
import autost.report
import autost.api
from ui.common.defaultWindow import CDefaultWindow
from ui.common.traceback import trace
from . import model, tree, caseAttributesSetting, newCase
from .. import res


PWD = os.getcwd() + os.sep + 'workspace'
REPORT_DIR = os.path.join(os.getcwd(), 'temp')


class CCaseManager(CDefaultWindow):
    fileOpen = PyQt5.QtCore.pyqtSignal(str, object)
    captureInsert = PyQt5.QtCore.pyqtSignal()
    caseManagerDelete = PyQt5.QtCore.pyqtSignal()
    caseRun = PyQt5.QtCore.pyqtSignal()
    multiCaseRun = PyQt5.QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(CCaseManager, self).__init__()
        self.parent = parent
        self.initGui()
        self.copy_file_list = None
        self.tree.setDragDropMode(PyQt5.QtWidgets.QAbstractItemView.InternalMove)  #DragDrop
        self.tree.setDropIndicatorShown(False)
        self.shift_flag = False
        self.current_index = []
        self.current_path = []
        self.action_dict = {}
        self.reload_setup_list = []

    def initGui(self):
        self.model = model.CDirModel()
        self.model.setSorting(PyQt5.QtCore.QDir.DirsFirst \
                              |PyQt5.QtCore.QDir.IgnoreCase \
                              |PyQt5.QtCore.QDir.Name)
        self.model.setFilter(PyQt5.QtCore.QDir.AllDirs \
                             | PyQt5.QtCore.QDir.Files
                             | PyQt5.QtCore.QDir.NoDotAndDotDot)
        self.model.setNameFilters(['*.py', '*.txt', '*.jpg', '*.png', '*.gz'])
        self.model.setResolveSymlinks(True)
        self.selModel =PyQt5.QtCore.QItemSelectionModel(self.model)
        self.tree = tree.CTreeView(self)
        self.tree.setFont(PyQt5.QtGui.QFont("微软雅黑",10))
        self.tree.setModel(self.model)
        self.tree.header().setSortIndicator(0, PyQt5.QtCore.Qt.AscendingOrder)
        self.tree.setSelectionModel(self.selModel)
        self.tree.setRootIndex(self.model.index(PWD))
        self.tree.setEditTriggers(PyQt5.QtWidgets.QAbstractItemView.NoEditTriggers)
        style_sheet = '''
            QTreeView::item:hover {
                                    background: rgb(134,247,151);
                                    border: 1px solid;
                                    }

            QTreeView::item:selected {border: 1px solid;}

            QTreeView::item:selected:active{
                                            background: rgb(130,166,225);
                                            }

            QTreeView::item:selected:!active {
                                              background: rgb(130,166,225);
                                            }

            QTreeView::branch:has-siblings:!adjoins-item {
                                border-image: url(:/icon/vline.png);
                            }

            QTreeView::branch:has-siblings:adjoins-item {
                                 border-image: url(:/icon/branch_more.png);
                            }

            QTreeView::branch:!has-children:!has-siblings:adjoins-item {
                                border-image: url(:/icon/branch_end.png);
                            }

            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings {
                                border-image: none;
                                image: url(:/icon/branch_closed.png);
                            }

            QTreeView::branch:open:has-children:!has-siblings,
            QTreeView::branch:open:has-children:has-siblings  {
                                border-image: none;
                                image: url(:/icon/branch_open.png);
                            }

        '''
        self.tree.setStyleSheet(style_sheet)
#        self.tree.header().hide()
        for i in [1, 2, 3]:
            self.tree.setColumnHidden(i, True)
        self.tree.setContextMenuPolicy(PyQt5.QtCore.Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.showMenu)
        self.tree.doubleClicked.connect(self.open)
        self.tree.expanded.connect(self.reloadConfigs)
        self.splitter = PyQt5.QtWidgets.QSplitter() 
        self.splitter.addWidget(self.tree)  
#        self.splitter.setWindowTitle(self.splitter.tr("Workspace"))

    @staticmethod
    def addAction(menu, action_dict, action_name_list, action_connect_list,
                  icon_list=None,short_cut_list=None, separetor_list=None, 
                  action_store=False, parent=None, checkable=False, action_name_filter=None):
        if action_name_filter is None:
            action_name_filter = []
        for a in action_name_list:
            action_name = a.split('(')[0].strip()
            if action_name_filter:
                if action_name not in action_name_filter:
                    continue
            index = action_name_list.index(a)
            try:
                if icon_list:
                    icon = icon_list[index]
                else:
                    icon = ''
            except:
                icon = ''
            try:
                if short_cut_list:
                    short_cut = short_cut_list[index]
                else:
                    short_cut = None
            except:
                short_cut = None
            if icon != '':
                icon = ':/icon/%s' % icon
            action = PyQt5.QtWidgets.QAction(PyQt5.QtGui.QIcon(icon), '%s' % a, parent)
            action.setCheckable(checkable)
            if short_cut:
                action.setShortcut(short_cut)
            if action_store:
                action_dict[action_name] = action
            action_connect = action_connect_list[index]
            if action_connect:
                action.triggered.connect(action_connect)
            menu.addAction(action)
            try:
                if separetor_list[index]:
                    menu.addSeparator()
            except:
                pass

    def addMenu(self, menu, menu_name, action_name_list,
                action_connect_list, icon_list=None):
        new_menu = menu.addMenu(menu_name)
#        self.action_dict[menu_name] = new_menu
        for a in action_name_list:
            index = action_name_list.index(a)
            try:
                icon = icon_list[index]
            except:
                icon = ''
            if icon:
                icon = ':/icon/%s' % icon
            action = PyQt5.QtWidgets.QAction(PyQt5.QtGui.QIcon(icon), '%s' % a, new_menu)
            self.action_dict[a] = action
            action_connect = action_connect_list[index]
            if action_connect:
                action.triggered.connect(action_connect)
            new_menu.addAction(action)
        return new_menu

    def getMenuNameList(self):
        filepath = self.getCurrentPath()
        filepath = filepath.replace('/', os.sep)
        menu_name_list = ['New File','New Case','New Folder','New Setup','New Teardown', 'Copy',
                          'Paste','Delete','Rename','Refresh','Properties']
        if os.path.isdir(filepath):
            if filepath.endswith('.air'):
#                menu_name_list.remove('New Case')
                menu_name_list.extend(['Import Setup',
                                       'Import Teardown',
                                       'Run Configurations...',
                                       'Run',
                                       'Clear Logs',
                                       'Show Report'])
            else:
                flag = False
                for f in os.listdir(filepath):
                    if f.endswith('.air') and os.path.isdir(os.path.join(filepath, f)):
                        flag = True
                        break
                if flag:
                    menu_name_list.extend(['Run Configurations...',
                                           'Run',
                                           'Clear Logs'])
                filename = filepath.split(os.sep)[-1]
                if filename == 'log':
                    menu_name_list.extend(['Show Report','Clear Logs'])
                else:
                    try:
                        if filename.split('.')[1] == 'log':
                            menu_name_list.append('Show Report')
                    except:
                        pass
        else:
            menu_name_list.append('Open')
            file_tail = filepath.split('.')[-1]
            if file_tail in ['png','jpg','bmp']:
                menu_name_list.append('Insert as capture')
            elif file_tail == 'py':
                if filepath.split(os.sep)[-2].endswith('.air'):
                    menu_name_list.append('Run')
        return menu_name_list

    def setMenuStatus(self, menu_name_list):  
        for name in self.action_dict.keys():
            if name not in menu_name_list:
                self.action_dict[name].setEnabled(False)

    def showMenu(self, point):
        menu_name_list = self.getMenuNameList()
        menu = PyQt5.QtWidgets.QMenu()
        ## New
        action_name_list = ['New Case', 'New File', 'New Folder']
        action_connect_list = [self.newCase, self.newFile, self.newFolder]
        self.addMenu(menu, 'New', action_name_list, action_connect_list)
        menu.addSeparator()
        ## Setup Configurations
        action_name_list = ['New Setup', 'New Teardown', 'Import Setup', 'Import Teardown']
        action_connect_list = [self.newSetup, self.newTeardown, self.importSetup, self.importTeardown]
        icon_list = ['', '', 'import.png', 'import.png']
        self.addMenu(menu, 'Configurations',
                     action_name_list, action_connect_list, icon_list)
        menu.addSeparator()
        action_name_list = ['Open',
                            'Copy    (Ctrl+C)',
                            'Paste    (Ctrl+V)',
                            'Delete    (Delete)',
                            'Rename    (F2)',
                            'Refresh', 'Run', 'Run Configurations...',
                            'Insert as capture', 'Show Report',
                            'Clear Logs','Properties']
        action_connect_list = [self.open, self.copy, self.paste, self.delete,self.rename,
                               self.refresh, self.run,self.multiRun, self.insert,
                               self.showReport, self.clearLog, self.showProperties]
        icon_list = ['open.png','copy.png', '', 'delete.png', '','refresh.png',
                     'run.png', '', 'screenCapture.png', 'report.png', 'clear.png', '']
        short_cut_list = [None, 'Ctrl+C', 'Ctrl+V', 'Delete', None,
                          None, None, None, None, None, None, None]
        separetor_list = [True, False, False, False, True, True,
                          False, True, True, False, True, False]
        self.addAction(menu=menu,
                       action_dict=self.action_dict,
                       action_name_list=action_name_list,
                       action_connect_list=action_connect_list,
                       icon_list=icon_list,
                       short_cut_list=short_cut_list,
                       separetor_list=separetor_list,
                       action_store=True,
                       parent=self)
        self.setMenuStatus(menu_name_list)
        menu.exec_(self.tree.mapToGlobal(point))

    def importSetup(self):
        self.importSetupTeardown('setup')
        
    def importTeardown(self):
        self.importSetupTeardown('teardown')  
         
    def importSetupTeardown(self, name): ##name in ('setup', 'teardown')
        index = self.tree.currentIndex()
        path = self.model.filePath(index).replace('/', os.sep)
        if not path.endswith('.air'):
            self.message('Import Setup&Teardown', 'No valid .air case!')
            return
        dirname = self.setDir()
        if not dirname:
            return
        if not dirname.endswith('.%s' % name):
            self.message('Import Setup&Teardown', 'No valid .setup | .teardown file!')
            return
        setup_dir = os.path.join(path, name + 's')
        if not os.path.isdir(setup_dir):
            os.mkdir(setup_dir)
        caseAttributesSetting.CAttributesSetting.importSetupFile(dirname, setup_dir)
        self.updateConfigFile(path, dirname, name)
        self.refresh(index)
        self.newFileRefresh(setup_dir, False)

    def updateConfigFile(self, case_dir, new_setup_dir, name): ##name in ('setup', 'teardown')
        name = name + 's'
        try:
            configs = json.load(open(os.path.join(case_dir, 'config.ini')))
        except:
            configs = {}
        setup_files = configs.get(name)
        if not setup_files:
            configs[name] = []
        for f in os.listdir(new_setup_dir):
            if f.endswith('.py'):
                new_setup_file = os.path.relpath(os.path.join(new_setup_dir, f), case_dir)
                new_setup_file = new_setup_file.replace(os.sep, '/')
                if new_setup_file not in configs[name]:
                    configs[name].append(new_setup_file)
#        dirs = os.path.join(case_dir, 'setups')
#        if not os.path.isdir(dirs):
#            os.mkdir(dirs)
        setup_config = json.dumps(configs, sort_keys=True,
                                  indent = 6,skipkeys=True,ensure_ascii = False)
        with open(os.path.join(case_dir, 'config.ini'), 'w') as f:
            f.write(setup_config)

    def setDir(self):
        PWD = os.getcwd() + os.sep + 'workspace'
        dirname = PyQt5.QtWidgets.QFileDialog.getExistingDirectory(self, 'Set Directory',
                                                                   PWD,
                                                                   PyQt5.QtWidgets.QFileDialog.ShowDirsOnly)
        dirname = dirname.replace('/', os.sep)
        return dirname

    def rename(self):
        rename_index = self.tree.currentIndex()
        self.rename_filepath = self.model.filePath(rename_index)
        self.tree.edit(rename_index)

    def copy(self, filelist=None):
        if filelist:
            self.copy_file_list = filelist
            return
        filelist = []
        try:
            indexs = self.tree.selectedIndexes()
            for index in indexs:
                filelist.append(self.model.filePath(index).replace('/', os.sep))
            self.copy_file_list = filelist
        except:
            print(traceback.print_exc())

    @trace
    def paste(self, paste_dir=None):
        paste_file_list = []
        if not self.copy_file_list:
            self.message('Paste', 'Please copy before paste!')
            return paste_file_list
        if not paste_dir:
            index = self.tree.currentIndex()
            filepath = self.model.filePath(index)
            if self.model.fileInfo(index).isDir():
                paste_dir = filepath.replace('/', os.sep)
            else:
                paste_dir = os.sep.join(filepath.split('/')[:-1])
                index = index.parent()
        else:
            index = self.findIndex(paste_dir)
        for copy_file in self.copy_file_list:
            copy_file_name = copy_file.split(os.sep)[-1]
            paste_file = os.path.join(paste_dir, copy_file_name)
            try:
                filename, suffix = copy_file_name.split('.')
            except:
                if os.path.isdir(copy_file):
                    filename, suffix = copy_file_name, None
            i = 1
            while 1:
                if os.path.exists(paste_file):
                    new_filename = filename + '(%s)' % i
                    if suffix:
                        paste_file = os.path.join(paste_dir, new_filename + '.' + suffix)
                    else:
                        paste_file = os.path.join(paste_dir, new_filename)
                else:
                    break
                i += 1
            if os.path.isdir(copy_file):
                shutil.copytree(copy_file, paste_file)
            else:
                shutil.copyfile(copy_file, paste_file)
            paste_file_list.append(paste_file)
        self.refresh(index)
        self.copy_file_list = None
        return paste_file_list

    def insert(self):
        self.captureInsert.emit()

    def open(self, index=None): 
        if not index:
            index = self.tree.currentIndex()
        filepath = self.model.filePath(index)
        filename = self.model.fileName(index)
        if os.path.islink(filepath):
            symlink_path = os.readlink(filepath)
            current_dir = os.getcwd()
            os.chdir(filepath[:filepath.rfind('/')])
            filepath = os.path.abspath(symlink_path)
            filepath = filepath.replace(os.sep, '/')
            os.chdir(current_dir)
            index = self.model.index(filepath)
            self.tree.setCurrentIndex(index)
        if self.model.fileInfo(index).isFile():
            if filename.split('.')[-1] in ['py', 'txt', 'config']:
                self.fileOpen.emit(filepath, True)
            elif filename.split('.')[-1] in ['png', 'jpg', 'bmp']:
                filepath = filepath.replace('/',os.sep)
                cmd = """
                    start rundll32.exe C:\\Windows\\System32\\shimgvw.dll,ImageView_Fullscreen %s
                """ % filepath
                os.system(cmd)
            elif filename.endswith('.html'):
                self.openHtml(filepath.replace('/', os.sep))
            else:
                pass

    def getCurrentPath(self):
        index = self.tree.currentIndex()
        filepath = self.model.filePath(index)
        return filepath

    def getCurrentDir(self):
        filepath = self.getCurrentPath().replace('/', os.sep)
        if not os.path.isdir(filepath):
            filepath = filepath[:filepath.rfind(os.sep)]
        return filepath

    def getSelectedPath(self):
        filepath = []
        indexs = self.tree.selectedIndexes()
        for index in indexs:
            filepath.append(self.model.filePath(index).replace('/', os.sep))
        return filepath

    def run(self):
        self.caseRun.emit()

    def multiRun(self):
        self.multiCaseRun.emit()

    def newCase(self):
        c = newCase.CCase(self.getCurrentDir())
        c.loadTemplate()
        c.exec_()
        if c.case_dir:
            case_dir = c.case_dir.replace('/', os.sep)
            self.newFileRefresh(case_dir[:case_dir.rfind(os.sep)], False)
            self.newFileRefresh(case_dir, False)
            self.fileOpen.emit(c.filepath.replace(os.sep, '/'), True)

    def newSetup(self):
        self.newSetupTeardown('setup')

    def newTeardown(self):
        self.newSetupTeardown('teardown')

    def newSetupTeardown(self, name): ##name in ('setup', 'teardown')
        case_flag = False
        filepath = self.getCurrentDir()
        if filepath.endswith('.air'):
            case_flag = True
            self.newFileRefresh(filepath, False)
            setup_dir = os.path.join(filepath, name + 's')
            if not os.path.isdir(setup_dir):
                os.mkdir(setup_dir)
            filepath = setup_dir
            self.newFileRefresh(setup_dir, False)
        if name == 'setup':
            title = 'New Setup'
            file_type = "Setup Files(*.setup)"
        else:
            title = 'New Teardown'
            file_type = "Teardown Files(*.teardown)"
        dirname, _ = PyQt5.QtWidgets.QFileDialog.getSaveFileName(self,
                                                                 title,
                                                                 filepath,
                                                                 file_type)
        if dirname:
            dirname = dirname.replace('/', os.sep)
            os.mkdir(dirname)
            dir = dirname.split(os.sep)
            filename = dir[-1].split('.')[0] + '.py'
            filepath = os.sep.join(dir + [filename])
            with open(filepath, 'w') as f:
                f.write('from autost.api import *\n\n')
            self.newFileRefresh(os.sep.join(dir[:-1]), False)
            self.newFileRefresh(dirname, False)
            self.fileOpen.emit(filepath.replace(os.sep, '/'), True)
            if case_flag:
                if not dirname[:dirname.rfind(os.sep)] == setup_dir:
                    caseAttributesSetting.CAttributesSetting.importSetupFile(dirname, setup_dir)
                self.updateConfigFile(setup_dir[:setup_dir.rfind(os.sep)], dirname, name)
                self.newFileRefresh(setup_dir, False)

    def newFile(self):
        filename, _ = PyQt5.QtWidgets.QFileDialog.getSaveFileName(self, 'New File',
                                                                         self.getCurrentDir(),
                    "All Files(*);;Python Files(*.py);;Text Files (*.txt);;Image(*.png)")
        if filename:
            with open(filename, 'w') as f:
                pass
            self.fileOpen.emit(filename.replace(os.sep, '/'), True)
            case_dir = filename.split('.air')[0] + '.air'
            file_dir = '/'.join(filename.split('/')[:-1])
            if case_dir != file_dir:
                self.newFileRefresh(case_dir.replace('/', os.sep))
            self.newFileRefresh(file_dir.replace('/', os.sep))

    def newFolder(self):
        folder, _ = PyQt5.QtWidgets.QFileDialog.getSaveFileName(self, 'New Folder',
                                                                self.getCurrentDir())
        if folder:
            os.mkdir(folder)
            file_dir = folder[:folder.rfind('/')]
            self.newFileRefresh(file_dir.replace('/', os.sep))

    def delete(self):
        self.caseManagerDelete.emit()

    def question(self, quesion_str):
        reply = PyQt5.QtWidgets.QMessageBox.question(self, 'Message',
                                                    quesion_str,
                                                    PyQt5.QtWidgets.QMessageBox.Yes,
                                                    PyQt5.QtWidgets.QMessageBox.No)
        if reply == PyQt5.QtWidgets.QMessageBox.Yes:
            return True
        else:
            return False

    def message(self, title, msg):
        PyQt5.QtWidgets.QMessageBox.information(self,
                                                title,
                                                msg,
                                                PyQt5.QtWidgets.QMessageBox.Ok,
                                                PyQt5.QtWidgets.QMessageBox.Cancel)

    def refresh(self, index=None):
        if not index:
            index = self.tree.currentIndex()
        try:
            self.model.refresh(index)
            self.tree.expand(index)
        except:
            pass

    def rootRefresh(self):
        index = self.tree.rootIndex()
        self.refresh(index)

    def findIndex(self, filename, root_refresh=True):
        if root_refresh:
            self.model.refresh(self.tree.rootIndex())
        root_index = self.tree.rootIndex()
        result_index = self.__findIndexFromChild(root_index, filename)
        if len(result_index) == 0:
            return None
        else:
            return result_index[0]

    def newFileRefresh(self, filename, root_refresh=True):
        index = self.findIndex(filename, root_refresh)
        if index:
            self.refresh(index)

    def __findIndexFromChild(self, index, filename):
        result = []
        filepath = self.model.filePath(index).replace('/', os.sep)
        if filename.find(filepath) == -1:
            return result
        if filepath == filename:
            result.append(index)
            return result
        if self.model.hasChildren(index):
            for i in range(self.model.rowCount(index)):
                child = PyQt5.QtWidgets.QDirModel.index(self.model, i, 0, index)
                result += self.__findIndexFromChild(child, filename)
        return result

    def showProperties(self):
        index = self.tree.currentIndex()
        filepath = self.model.filePath(index).replace('/', os.sep)
        filename = self.model.fileName(index)
        fileinfo = self.model.fileInfo(index)
        date = fileinfo.lastModified()
        date = date.toString("yyyy-MM-dd hh:mm:ss")
        size = str(fileinfo.size()) + ' bytes'
        suffix = fileinfo.completeSuffix()
        device = autost.api.G.DEVICE_URI
        if fileinfo.isDir():
            Type = 'Folder'
            content = [['Path :', filepath],
                       ['Type :', Type],
                       ['Date Modified :', date]
                       ]
            if filename.endswith('.air'):
                case = filepath
            else:
                case = ''
        else:
            Type = 'File (%s file)' % suffix
            content = [['Path :', filepath],
                       ['Type :', Type],
                       ['Size :', size],
                       ['Date Modified :', date]
                       ]
            case = ''
        self.tree.expanded.disconnect(self.reloadConfigs)
        s = caseAttributesSetting.CAttributesSetting(content, case, device)
        s.init()
        s.setupRefresh.connect(self.newFileRefresh)
        s.exec_()
        self.tree.expanded.connect(self.reloadConfigs)

    @trace
    def getReportDirs(self, air_dir=None, log_file_dir=None, report_dir=None, report_file=None):
        log_dir = None
        if report_file:
            filelist = report_file.split(os.sep)
            case_name = filelist[-1].split('_')[1]
            if filelist[-2].startswith('%s.log' % case_name) and filelist[-3] == 'log' \
                and filelist[-4].endswith('.air'):
                air_dir = os.sep.join(filelist[:-3])
                log_dir = os.sep.join(filelist[:-1])
            return [air_dir, log_dir, report_file]
        ##
        if report_dir:
            filelist = report_dir.split(os.sep)
            if filelist[-2] == 'log' and filelist[-3].endswith('.air'):
                log_dir = report_dir
                air_dir = os.sep.join(filelist[:-2])
            return [air_dir, log_dir, report_file]
        ##
        if log_file_dir:
            filelist = log_file_dir.split(os.sep)
            if filelist[-2].endswith('.air'):
                air_dir = os.sep.join(filelist[:-1])
        if air_dir:
            case_name = air_dir.split(os.sep)[-1][:-4]
            temp_log_dir = os.path.join(air_dir, 'log')
            if os.path.isdir(temp_log_dir):
                latest_log_dir = self.getLatestLogDir(case_name, temp_log_dir)
                if latest_log_dir:
                    file_list = os.listdir(latest_log_dir)
                    for f in file_list:
                        if os.path.isfile(os.path.join(latest_log_dir, f)) \
                            and f.startswith('report') and f.endswith('.txt'):
                            log_dir = latest_log_dir
                            break
            return [air_dir, log_dir, report_file]
        return [air_dir, log_dir, report_file]

    def showReport(self):
        index = self.tree.currentIndex()
        filepath = self.model.filePath(index).replace('/', os.sep)
        filename = self.model.fileName(index)
        if filename.endswith('.air'):
            air_dir, log_dir, report_file = self.getReportDirs(air_dir=filepath)
        elif filename == 'log' and os.path.isdir(filepath):
            air_dir, log_dir, report_file = self.getReportDirs(log_file_dir=filepath)
        elif filename.find('.log') > -1 and os.path.isdir(filepath) and filename.split('.')[1] == 'log':
            air_dir, log_dir, report_file = self.getReportDirs(report_dir=filepath)
        elif os.path.isfile(filepath) and filename.startswith('report') and filename.endswith('.txt'):
            air_dir, log_dir, report_file = self.getReportDirs(report_file=filepath)
        else:
            air_dir, log_dir, report_file = self.getReportDirs()

        if air_dir and log_dir:
            air_dir = air_dir.replace('/', os.sep)
            log_dir = log_dir.replace('/', os.sep)
            self.openReport(air_dir, log_dir, report_file)
        else:
            self.message('Show Report', 'No valid report exists...')

    @trace
    def openReport(self, air_dir, log_dir, log_file):
        case_name = air_dir[air_dir.rfind(os.path.sep)+1 : -4]
        report_dir = os.path.join(REPORT_DIR, case_name + '.report')
        if os.path.isdir(report_dir):
            shutil.rmtree(report_dir)
        os.makedirs(report_dir)
        autost.report.convert(case_folder=air_dir,
                              log_dir=log_dir,
                              log_file=log_file,
                              export_dir=report_dir)
        html_log_file = os.path.join(report_dir,
                                     case_name + '.log',
                                     'log.html')
        self.openHtml(html_log_file)

    def openHtml(self, html_file):
        import webbrowser
        try:
            webbrowser.open(html_file)
        except:
            pass

    def getLatestLogDir(self, case_name, log_dir):
        log_dir = log_dir.replace('/', os.sep)
        file_list = os.listdir(log_dir)
        log_time = 0
        latest_log = None
        for f in file_list:
            current_log = os.path.join(log_dir, f)
            if os.path.isdir(current_log) and f.startswith('%s.log' % case_name):
                try:
                    current_log_time = int(''.join(f.split('.')[-1].split('_')))
                except:
                    current_log_time = 0
                if log_time < current_log_time:
                    log_time = current_log_time
                    latest_log = current_log
        return latest_log

    @trace
    def clearLog(self):
        index = self.tree.currentIndex()
        filepath = self.model.filePath(index)
        logs = self.getLogDir(filepath)
        if logs:
            for log in logs:
                new_log = os.path.join(REPORT_DIR, '.'.join(log.split(os.sep)[-2:]))
                self.__moveFiles(log, new_log)
            self.refresh(index)
            import threading
            t = threading.Thread(target=self.__deleteTempLogs)
            t.start()

    def __deleteTempLogs(self):
        for d in os.listdir(REPORT_DIR):
            if d.endswith('.log'):
                shutil.rmtree(os.path.join(REPORT_DIR, d))

    def getLogDir(self, current_dir):
        current_dir = current_dir.replace('/', os.sep)
        log_dir_list = []
        if not os.path.isdir(current_dir):
            return log_dir_list
        if current_dir.endswith('.air'):
            log_dir = os.path.join(current_dir, 'log')
            if os.path.isdir(log_dir):
                log_dir_list.append(log_dir)
        elif current_dir.split(os.sep)[-1] == 'log':
            if current_dir.split(os.sep)[-2].endswith('.air'):
                log_dir_list.append(current_dir)
        else:
            for d in os.listdir(current_dir):
                log_dir = os.path.join(current_dir, d)
                if os.path.isdir(log_dir):
                    log_dir_list += self.getLogDir(log_dir)
        return log_dir_list

    def __moveFiles(self, src, dest):
        for root, dirs, files in os.walk(src):
            for file in files:
                filename = os.path.join(root, file)
                new_filename = filename.replace(src, dest)
                new_root = root.replace(src, dest)
                if not os.path.isdir(new_root):
                    os.makedirs(new_root)
                os.rename(filename, new_filename)
        shutil.rmtree(src)

    def setCurrentIndex(self, index):
        if index is None:
            self.current_index = []
            self.current_path = []
            return
        path = self.model.filePath(index)
        if path not in self.current_path:
            if len(self.current_index) > 1:
                self.current_index[-1] = index
                self.current_path[-1] = path
            else:
                self.current_index.append(index)
                self.current_path.append(path)

    def setSelection(self):
        length = len(self.current_index)
        if length not in (1,2):
            print('current index is invalid...')
            return
        start = self.current_index[0]
        end = self.current_index[-1]
        start_path = self.model.filePath(start)
        end_path = self.model.filePath(end)
        select_index = []
        index = start
        reversal_flag = False
        while 1:
            select_index.append(index)
            path = self.model.filePath(index)
            if path == end_path:
                break
            if not path:
                index = start
                reversal_flag = True
                select_index = []
                continue
            if reversal_flag:
                index = self.tree.indexAbove(index)
            else:
                index = self.tree.indexBelow(index)
        self.tree.clearSelection()
        for index in select_index:
            self.tree.selectionModel().select(index,
                                              PyQt5.QtCore.QItemSelectionModel.Select)

    def editSetupFlies(self):
        filepath = self.getCurrentPath()
        if os.path.isdir(filepath) and filepath.endswith('.air'):
            try:
                configs = json.load(open(os.path.join(filepath, 'config.ini')))
            except:
                configs = {}
            setup_files = configs.get('setups', [])
            if not setup_files:
                self.message('Edit Setups', 'Have no setup configs')
                return
            for f in setup_files:
                self.fileOpen.emit(f, True)
        else:
            self.message('Edit Setups', 'Not a valid .air case')
        
    def reloadConfigs(self, index):
        filepath = self.model.filePath(index).replace('/', os.sep)
        filepath_list = filepath.split(os.sep)
        if filepath_list[-1] in ['setups','teardowns'] and filepath_list[-2].endswith('.air'):
            config_type = filepath_list[-1]
            if filepath in self.reload_setup_list:
                return
            self.reload_setup_list.append(filepath)
            for f in os.listdir(filepath):
                f_path = os.path.join(filepath, f)
                if f_path.endswith('.lnk'):
                    os.remove(f_path)
            setup_config = os.path.join(filepath[:filepath.rfind(os.sep)],'config.ini')
            if os.path.isfile(setup_config):
                try:
                    configs = json.load(open(setup_config))
                except:
                    configs = {}
                case_dir = os.sep.join(filepath_list[:-1])
                
                setup_files = configs.get(config_type, [])
                abs_setup_files = [caseAttributesSetting.CAttributesSetting.getAbsPath(s, case_dir)
                                   for s in setup_files]
                try:
                    caseAttributesSetting.CAttributesSetting.addSetupTeardownFiles(filepath, abs_setup_files)
                except:
                    pass
            self.model.refresh(index)

    def findExpandedNode(self, index=None):
        if index is None:
            index = self.tree.rootIndex()
        expanded_filepath = []
        if self.tree.isExpanded(index) or index == self.tree.rootIndex():
            filepath = self.model.filePath(index)
            expanded_filepath.append(filepath)
            if self.model.hasChildren(index):
                for i in range(self.model.rowCount(index)):
                    child = PyQt5.QtWidgets.QDirModel.index(self.model, i, 0, index)
                    expanded_filepath += self.findExpandedNode(child)
        expanded_filepath = [os.path.relpath(f, os.getcwd()) for f in expanded_filepath]
        expanded_filepath = [f.replace(os.sep, '/') for f in expanded_filepath]
        return expanded_filepath

    def expandedIndex(self, filepath_list, index=None):
        if index is None:
            index = self.tree.rootIndex()
        filepath = self.model.filePath(index)
        if filepath in filepath_list:
            self.tree.expand(index)
            filepath_list.remove(filepath)
        if self.existsChild(filepath, filepath_list):
            if self.model.hasChildren(index):
                for i in range(self.model.rowCount(index)):
                    child = PyQt5.QtWidgets.QDirModel.index(self.model, i, 0, index)
                    self.expandedIndex(filepath_list, child)

    def existsChild(self, filepath, filepath_list):
        for f in filepath_list:
            if f.find(filepath) != -1:
                return True
        return False

    def expandedNodes(self, node_list):
        abs_node_list = [caseAttributesSetting.CAttributesSetting.getAbsPath(node, os.getcwd())
                         for node in node_list]
        abs_node_list = [f.replace(os.sep, '/') for f in abs_node_list]
        self.expandedIndex(abs_node_list)


if __name__ == '__main__':
    import sys  
    app = PyQt5.QtWidgets.QApplication(sys.argv)  
    w = CCaseManager()
#    w.show()
    w.splitter.show()
    sys.exit(app.exec_())
        