import re
import os
import glob
import math
import shlex
import shutil
from subprocess import Popen, PIPE, check_output
from time import strftime, strptime, sleep
from contextlib import contextmanager

from telegram import InlineKeyboardButton


class BadLink(Exception):
    pass


class Video:
    def __init__(self, link, init_keyboard=False):
        self.link = link
        self.file_name = None
        self.file_path = None
        self.real_file_name = None
        self.extension = None
        self.serialNumber = None
        self.videoSite = None
        self.downloadPath = '/tmp/'
        self.outputFileName = '%(title)s.%(ext)s'

        if init_keyboard:
            self.formats = self.get_formats()
            self.keyboard = self.generate_keyboard()

    def get_formats(self):
        formats = []

        # this command return the video info to string
        cmd = "youtube-dl --no-check-certificate -F {}".format(self.link)

        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE).communicate()
        # creat subprocess,args is a string, the string is interpreted as the name or path of the program to execute
        # If shell is True, it is recommended to pass args as a string rather than as a sequence.
        # communicate() returns a tuple (stdoutdata, stderrdata).
        # communicate() Interact with process: Send data to stdin. Read data from stdout and stderr, until end-of-file is reached. Wait for process to terminate.

        # stdoutdata split with /n in a array to a iterate
        it = iter(p[0].decode("utf-8", 'ignore').split('\n'))
        # iter([a,b,c])

        try:
            for line in it:
                if "Available formats for" in line:
                    self.serialNumber = line[29:-1]

                    if 'pornhub.com' in self.link:
                        self.link = 'pornhub:' + self.serialNumber
                        break
                    if 'twitter.com' in self.link:
                        self.link = 'twitter:' + self.serialNumber
                        break
                    break

            while "format code  extension" not in next(it):
                pass  # if has not this string then goto next line
        except StopIteration:
            raise BadLink  # Isn't a valid link

        while True:
            try:
                line = next(it)
                if not line:
                    raise StopIteration  # Usually the last line is empty
                if "video only" in line:
                    continue  # I don't need video without audio
            except StopIteration:
                break
            else:
                format_code, extension, resolution, *_ = line.strip().split()
                # strip() Remove spaces at the beginning and at the end of the string
                if extension != 'webm':
                    if extension == 'm4a':
                        extension = 'm4a'
                        #extension = 'mp3'
                    formats.append([format_code, extension, resolution])
        return formats

    def generate_keyboard(self):
        """ Generate a list of InlineKeyboardButton of resolutions """
        kb = []

        for code, extension, resolution in self.formats:
            kb.append([InlineKeyboardButton("{0}, {1}, file".format(extension, resolution),
                                            callback_data="{0} {1} file".format(code, self.link))])  # Data to be sent in a callback query to the bot, will trige CallbackQueryHandler in main.py
            kb.append([InlineKeyboardButton("{0}, {1}, link".format(extension, resolution),
                                            callback_data="{0} {1} link".format(code, self.link))])  # Data to be sent in a callback query to the bot, will trige CallbackQueryHandler in main.py
        return kb

    def download(self, resolution_code):
        if 'pornhub:' in self.link:
            self.link = 'https://www.pornhub.com/view_video.php?viewkey=' + \
                self.link.split(':')[1]
        if 'twitter:' in self.link:
            self.link = 'https://twitter.com/BleacherReport/status/' + \
                self.link.split(':')[1]
            self.outputFileName = '%(id)s.%(ext)s'

        cmd = 'youtube-dl --no-check-certificate -f {0} {1} -o "{2}"'.format(
            resolution_code, self.link, self.downloadPath + self.outputFileName)  # download video command
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE).communicate()

        for line in p[0].decode("utf-8", 'ignore').split('\n'):
            if "[download] Destination:" in line:
                self.file_path = line[24:]
                self.file_name = self.file_path.split(
                    '/')[-1]  # name of the file
            elif "has already been downloaded" in line:
                self.file_path = line[11:-28]
                self.file_name = self.file_path.split('/')[-1]

        new_fn = self.file_name.replace(
            ' ', '_').replace('[', '_').replace(']', '_').replace('，', '_').replace(',', '_').replace('：', '_').replace(':', '_')
        new_fp = self.downloadPath + new_fn
        os.system('mv "{0}" "{1}"'.format(self.file_path, new_fp))
        self.file_name = new_fn
        self.file_path = new_fp
        self.real_file_name = self.file_name.split('.')[0]
        self.extension = '.' + self.file_name.split('.')[-1]  # last matched

        if self.extension == 'flv':
            os.system('ffmpeg -i {} -vcodec libx264 -crf 19 {}'.format(self.file_path,
                                                                       self.downloadPath + self.real_file_name + '_ffmpeg.mp4'))
            os.remove(self.file_path)
            self.file_name = self.real_file_name + '_ffmpeg.mp4'
            self.file_path = self.downloadPath + self.file_name
            self.real_file_name = self.file_name.split('.')[0]
            self.extension = '.' + \
                self.file_name.split('.')[-1]  # last matched

    def check_dimension(self):
        '''
        if self.extension == '.m4a':
            os.system('ffmpeg -i "{0}" -acodec libmp3lame -aq 6 "{1}"'.format(self.file_name, self.real_file_name + '.mp3'))
            os.remove(self.file_name)
            self.file_name = self.real_file_name + '.mp3'
            self.extension = '.mp3'
        '''
        if os.path.getsize(self.file_path) > 50 * 1024 * 1023:  # big than 50mb
            #os.system('ffmpeg -i {} -fs 49M -c copy {}'.format(self.file_path, self.downloadPath + self.real_file_name + '_ffmpeg' + self.extension))

            video_bitrate = self.get_video_bitrate(self.file_path)
            split_length = 49 * 8192 / (video_bitrate / 1024)
            split_length = int(split_length)
            print('split_length is: {}'.format(split_length))

            self.split_by_seconds(filename=self.file_path,
                                  split_length=split_length)
            os.remove(self.file_path)  # remove orignal file

            #os.system('split -b 49M "{0}" "{1}"'.format(self.file_name, self.real_file_name + '_'))
            # os.system() run real command in your machine

            # os.remove(self.file_name)#remove orignal file

            #files = glob.glob(self.real_file_name + '*')
            # for file in files:
            #    nfile = "'" + file + "'"
            #    nfile_ext = "'" + file + self.extension + "'"
            #    cmd = 'mv ' + nfile + ' ' + nfile_ext
            #    os.system(cmd)

            # return files match in glob.glob('')
        return glob.glob(self.downloadPath + self.real_file_name + '*')

    def get_video_length(self, filename):

        output = check_output(("ffprobe", "-v", "error", "-show_entries",
                               "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", filename)).strip()
        video_length = int(float(output))
        print("Video length in seconds: "+str(video_length))

        return video_length

    def get_video_bitrate(self, filename):

        output = check_output(("ffprobe", "-v", "error", "-show_entries",
                               "format=bit_rate", "-of", "default=noprint_wrappers=1:nokey=1", filename)).strip()
        video_bitrate = int(float(output))
        print("Video bitrate: "+str(video_bitrate))

        return video_bitrate

    def ceildiv(self, a, b):
        return int(math.ceil(a / float(b)))

    def split_by_seconds(self, filename, split_length, vcodec="copy", acodec="copy", video_length=None):
        if split_length and split_length <= 0:
            print("Split length can't be 0")
            raise SystemExit

        if not video_length:
            video_length = self.get_video_length(filename)
        split_count = self.ceildiv(video_length, split_length)
        print('count is {}'.format(split_count))

        if(split_count == 1):
            print("Video length is less then the target split length.")
            raise SystemExit

        split_cmd = "ffmpeg -i " + filename + " -c:v " + vcodec + " -c:a " + acodec

        for n in range(0, split_count):
            if n == 0:
                split_start = 0
            else:
                split_start = split_length * n

            split_args = "-ss " + str(split_start) + " -t " + str(split_length) + " " + \
                self.downloadPath + self.real_file_name + "-" + \
                str(n+1) + "-of-" + str(split_count) + "." + self.extension
            cmd = '{} {}'.format(split_cmd, split_args)
            p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE).communicate()

    @contextmanager  # run this function with new defined send function
    def send_file(self):
        files = self.check_dimension()  # split if size >= 50MB
        yield files

    def send_link(self):
        #shutil.move(self.file_path, '/home/www/cloud/temp/')
        # cmd = 'mv "{0}" /home/www/cloud/temp/'.format(self.file_path)
        #Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE).communicate()

        os.system('mv "{0}" /home/www/cloud/temp/'.format(self.file_path))
        file_link = 'https://niekun.net/cloud/temp/{}'.format(self.file_name)
        return file_link

    def remove(self):
        files = glob.glob(self.downloadPath + self.real_file_name + '*')
        for f in files:  # removing old files
            os.remove(f)
