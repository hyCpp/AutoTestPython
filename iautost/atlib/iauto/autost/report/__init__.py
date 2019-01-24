# -*- coding: utf-8 -*-

import os
import io
import copy
import sys
import jinja2
import shutil
import collections
from urllib.parse import urlparse
from airtest.report.report import LogToHtml
import wave as we
import matplotlib.pyplot as plt
import numpy as np
from scipy.io import wavfile

LOGDIR = "log"
HTML_TPL = "report_template.html"
HTML_FILE = "report.html"
STATIC_DIR = os.path.dirname(__file__)

class ReportToHtml(LogToHtml):
    def __init__(self, script_root, log_root, static_root=STATIC_DIR, author="", export_dir=None, logfile="log.txt", lang="en"):
        super(ReportToHtml, self).__init__(script_root, log_root, static_root, author, export_dir, logfile, lang)
        self.img_type += ('touch_in', 'touch_or', 'touch_if', 'long_touch', 'flick', 'switch_device')
        if script_root:
            airdir = os.path.abspath(script_root)
            self.casename = airdir[airdir.rfind(os.path.sep) + 1 : airdir.rfind('.')]
        self.org_log = copy.deepcopy(self.log)
        self.current_deivce_uri = None

    def render(self, template_name, output_file=HTML_FILE, record_list=None):
        if self.export_dir:
            self.script_root, self.log_root = self._make_export_dir()
            output_file = os.path.join(self.script_root, output_file)
            self.static_root = "static/"

        if self.all_step is None:
            self.analyse()

        if not record_list:
            record_list = [f for f in os.listdir(self.log_root) if f.endswith(".mp4")]
        records = [os.path.join(self.log_root, f) for f in record_list]

        if not self.static_root.endswith(os.path.sep):
            self.static_root += "/"

        self.parse_wav_file()
        data = {}
        data['casename'] = self.casename
        data['all_steps'] = self.all_step
        data['host'] = self.script_root
        data['script_name'] = get_script_name(self.script_root)
        data['scale'] = self.scale
        data['test_result'] = self.test_result
        data['run_end'] = self.run_end
        data['run_start'] = self.run_start
        data['static_root'] = self.static_root
        data['author'] = self.author
        data['records'] = records
        data['lang'] = self.lang

        return self._render(template_name, output_file, **data)
    
    def _make_export_dir(self):
        # mkdir
        dirname = os.path.basename(self.script_root).replace(".air", ".log")
        dirpath = os.path.join(self.export_dir, dirname)
        if os.path.isdir(dirpath):
            shutil.rmtree(dirpath, ignore_errors=True)
        
        # copy script
        shutil.copytree(self.script_root, dirpath, ignore=shutil.ignore_patterns(LOGDIR))
        
        # copy log
        logpath = os.path.join(dirpath, LOGDIR)
        if os.path.normpath(logpath) != os.path.normpath(self.log_root):
            if os.path.isdir(logpath):
                shutil.rmtree(logpath, ignore_errors=True)
            shutil.copytree(self.log_root, logpath, ignore=shutil.ignore_patterns(LOGDIR))
        
        # copy static files
        for subdir in ["css", "fonts", "image", "js"]:
            shutil.copytree(os.path.join(STATIC_DIR, subdir), os.path.join(dirpath, "static", subdir))
        
        return dirpath, logpath
    
    @staticmethod
    def _render(template_name, output_file=None, **template_vars):
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(STATIC_DIR),
            extensions=(),
            autoescape=True
        )
        template = env.get_template(template_name)
        html = template.render(**template_vars)

        if output_file:
            with io.open(output_file, 'w', encoding="utf-8") as f:
                f.write(html)
            print(output_file)

        return html
    
    def translate(self, step):
        step['device'] = self.get_device(step)
        step['type'] = step[1]['name']
        if step['type'] == 'switch_device':
            return None
        if step['type'] == 'swipe':
            swipe_args = self.get_swipe_args(step)
            step['swipe_from'] = swipe_args[0]
            step['swipe_to'] = swipe_args[1]
        step = LogToHtml.translate(self, step)
        if step['type'] in self.img_type:
            if len(step[1]['args']) > 0:
                target = step[1]['args'][0]
                if 'filename' in target:
                    image_path = str(target['filename'])
                    if not self.export_dir:
                        image_path = os.path.join(self.script_root, image_path)
                    step['image_to_find'] = image_path

        if step['type'] in ('touch_in', 'touch_or', 'touch_if'):
            try:
                target = step[1]['args'][0]
            except (IndexError, KeyError):
                target = None
            if isinstance(target, (tuple, list)):
                step['target_pos'] = target
                step['left'], step['top'] = target
        
        if step['type'] in ('touch', 'touch_in', 'exists', 'assert_exists', 'long_touch'):
            if len(step[1]['args']) > 1:
                target2 = step[1]['args'][1]
                if 'filename' in target2:
                    image_path = str(target2['filename'])
                    if not self.export_dir:
                        image_path = os.path.join(self.script_root, image_path)
                    step['image_to_find_in'] = image_path

        if step['type'] in ('touch_or', ):
            if len(step[1]['args']) > 1:
                target2 = step[1]['args'][1]
                if 'filename' in target2:
                    image_path = str(target2['filename'])
                    if not self.export_dir:
                        image_path = os.path.join(self.script_root, image_path)
                    step['image_to_find_or'] = image_path
        return step
    
    def get_swipe_args(self, step):
        swipe_args = ['','']
        if len(step[1]['args']) > 0:
            args = step[1]['args'][:2]
            for i in range(2):
                if type(args[i]) == type([]):
                    swipe_args[i] = args[i]
                elif type(args[i]) == type({}):
                    filepath = args[i].get('_filepath')
                    if filepath:
                        ret = ''
                        for log in self.org_log:
                            depth = log.get('depth')
                            if depth and depth == 2 and log.get('data', {}).get('args', [{}])[0].get('_filepath') == filepath:
                                ret = log['data'].get('ret')
                                if ret:
                                    break
                    swipe_args[i] = ret
                else:
                    pass
        return swipe_args

    @staticmethod
    def func_desc(step):
        if step['type'] in ('keyevent', ):
            if len(step[1]['args']) > 0:
                step['keyname'] = step[1]['args'][0]
        if step['type'] in ('usb_on', 'usb_off'):
            if len(step[1]['args']) > 0:
                step['usb_port'] = step[1]['args'][0]
        if step['type'] == 'spd_speed':
            if len(step[1]['args']) > 0:
                step['spd_speed'] = step[1]['args'][0]
        if step['type'] == 'ill_down':
            if len(step[1]['args']) > 0:
                step['ill_down_args'] = tuple(step[1]['args'])
        if step['type'] == 'flick':
            step['flick_from'] = step.get('target_pos')
            if len(step[1]['args']) > 0:
                step['flick_direction'] = step[1]['args'][-1]
                if not step['flick_from']:
                    step['flick_from'] = step[1]['args'][0]
        port_mapping = {1: 'A',
                        2: 'B',
                        3: 'C',
                        4: '1',
                        5: '2',
                        6: '3',
                        7: '4'
                        }
        desc = {"touch_in": u"Search for target object, touch the screen coordinates %s" % repr(step.get('target_pos', '')),
                "touch_or": u"Search for target object, touch the screen coordinates %s" % repr(step.get('target_pos', '')),
                "touch_if": u"Search for target object, touch the screen coordinates %s" % repr(step.get('target_pos', '')),
                "long_touch": u"Search for target object, touch the screen coordinates %s" % repr(step.get('target_pos', '')),
                "keyevent": u"Press button %s" % step.get('keyname', ''),
                "usb_on": u"Turn on USB-%s" % port_mapping.get(step.get('usb_port'), ''),
                "usb_off": u"Turn off USB-%s" % port_mapping.get(step.get('usb_port'), ''),
                "spd_speed": u"Set the current speed to %s" % step.get('spd_speed'),
                "ill_down": u"Set the parameters of ILL- to (Hz: %s, val: %s)" % step.get('ill_down_args', ('','')),
                "flick": u" Flick from %s, direction : %s" % (repr(step.get('flick_from', '')),
                                                               repr(step.get('flick_direction'))
                                                               ),
                "switch_device": u"Switch device to %s" % (step.get(1).get('args', [""])[0] if 1 in step else ""),
                }
        name = step['type']
        if name in desc:
            return desc.get(name)
        elif name == 'swipe':
            swipe_from = repr(step.get('swipe_from', ''))
            swipe_to = repr(step.get('swipe_to', ''))
            vector = step.get('vector')
            desc_string = "Swipe from %s to %s" % (swipe_from, swipe_to)
            if vector:
                desc_string += ' , vector: %s' % str(vector)
            return desc_string
        elif name.endswith('_on') or name.endswith('_off'):
            if name.startswith('ill_'):
                name = name.replace('ill_', 'ILL+_')
            if name.startswith('bup_'):
                name = name.replace('bup_', 'B+_')
            name = name.split('_')
            desc_string = 'Turn %s %s' % (name[1], name[0].upper(),)
            return desc_string
        else:
            return LogToHtml.func_desc(step)


    def get_device(self, step):
        device_uri = None
        if step[1].get('name', '') == 'switch_device':
            device_uri = step[1].get('args', [None])[0]
            if device_uri:
                self.current_deivce_uri = device_uri
            device_uri = None
        else:
            if len(step[1].get('kwargs', {})) > 0:
                device_uri = step[1].get('kwargs').get('device')
            if not device_uri:
                device_uri = self.current_deivce_uri
        if device_uri:
            d = urlparse(device_uri)
            platform = d.scheme
            platform = platform[0] + platform[1:].capitalize()
            if d.path:
                serial_no = d.path.split('/')[1]
            else:
                serial_no = None
            if serial_no:
                device = '{}-{}'.format(platform, serial_no)
            else:
                device = platform
        else:
            device = 'main'
        return device

    @staticmethod
    def func_title(step):
        title = {
            "touch_in": u"Touch In",
            "touch_or": u"Touch Or",
            "touch_if": u"Touch If",
            "long_touch": u"Long Touch",
            "ill_down": u"Tbox ILL-",
            "spd_speed": u"Tbox Speed",
            "flick": u"Flick",
            "switch_device": u"Switch Device",
        }
        name = step['type']
        if name in title:
            return title.get(name)
        elif name.endswith('_on') or name.endswith('_off'):
            if name.startswith('ill_'):
                name = name.replace('ill_', 'ILL+_')
            if name.startswith('bup_'):
                name = name.replace('bup_', 'B+_')
            name = name.split('_')
            return 'Tbox %s %s' % (name[0].upper(), name[1].capitalize())
        else:
            return LogToHtml.func_title(step)

    @staticmethod
    def gen_waveform(filename):
        try:
            WAVE = we.open(filename)
        except FileNotFoundError:
            print("[" + filename + "] Not Found")
            return "";
        except EOFError:
            print("Is [" + filename + "] a wav file?")
            return ""
        else:
            for item in enumerate(WAVE.getparams()):
                print(item)

            a = WAVE.getparams().nframes
            f = WAVE.getparams().framerate

            sample_time = 1 / f
            time = a / f

            sample_frequency, audio_sequence = wavfile.read(filename)

            print(audio_sequence)

            x_seq = np.arange(0, time, sample_time)

            plt.rcParams['figure.figsize'] = (20.0, 4.0)
            plt.rcParams['figure.dpi'] = 200

            plt.plot(x_seq, audio_sequence, 'blue')
            plt.xlabel("time(s)")
            plt.savefig(filename + '.png')
            return filename + '.png'

    def parse_wav_file(self):
        for step in self.all_step:
            one_step = self.all_step[step]
            for i in range(len(one_step)):
                info = one_step[i]
                for value in info:
                    if value == 1 :
                        detail = info[value]
                        for key in detail:
                            if key == "audio_file":
                                self.gen_waveform(detail[key])



def find_latest_log_file(log_path, prefix='report', ext='.txt'):
    latest_file = ""
    latest_time = 0
    if os.path.isdir(log_path):
        listsub = os.listdir(log_path)
        for sub in listsub:
            filepath = os.path.join(log_path, sub)
            if sub.startswith(prefix) and sub.endswith(ext):
                    cur_mtime = os.path.getmtime(filepath)
                    if cur_mtime > latest_time:
                        latest_time = cur_mtime
                        latest_file = sub
    return latest_file

def convert(case_folder, log_dir, log_file=None, export_dir=None, export_file="log.html", lang='en'):
    case_name = case_folder[case_folder.rfind(os.path.sep)+1 : -4]
    py_file = os.path.sep.join([case_folder, '%s.py' % case_name])
    author = get_file_author(py_file)
    
    if not log_file:
        log_file = find_latest_log_file(log_dir)
    
    if not export_dir:
        export_dir = os.path.sep.join([log_dir, 'report'])
    if not os.path.exists(export_dir):
        os.mkdir(export_dir)
    
    if not export_file:
        export_file = '%s.html' % case_name
    
    rpt = ReportToHtml(case_folder, log_dir, author=author, logfile=log_file, export_dir=export_dir,lang=lang)
    rpt.render(HTML_TPL, output_file=export_file)

def get_script_name(path):
    pp = path.replace('\\', '/').split('/')
    for p in pp:
        if p.endswith('.owl'):
            return p
    return ''

def get_file_author(file_path):
    author = ''
    if not os.path.exists(file_path) and not PY3:
        file_path = file_path.encode(sys.getfilesystemencoding())
    if os.path.exists(file_path):
        fp = io.open(file_path, encoding="utf-8")
        for line in fp:
            if '__author__' in line and '=' in line:
                author = line.split('=')[-1].strip()[1:-1]
                break
    return author