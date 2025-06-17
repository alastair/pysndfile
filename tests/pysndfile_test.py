from __future__ import print_function
import os
from pathlib import Path
import sys
import numpy as np

from pysndfile_inst_dir.pysndfile import get_sndfile_version
from pysndfile_inst_dir.pysndfile import *
import pysndfile_inst_dir.pysndfile as pysndfile

mydir = os.path.dirname(__file__)


print("pysndfile version:",get_pysndfile_version())
print("libsndfile version:",get_sndfile_version())

majors = get_sndfile_formats()

def test_compressed(input_file, format, encoding, lossy):
    if format in majors:
        if encoding in get_sndfile_encodings(format):
            failed = False
            ss, sr, enc = pysndfile.sndio.read(os.path.join(mydir,input_file), force_2d=True)
            print('test writing {0}/{1}'.format(format, encoding))
            output_file = PySndfile(os.path.join(mydir,'test.{0}_{1}'.format(format, encoding)), "w", construct_format(format, encoding), ss.shape[1], sr)
            output_file.set_compression_level(1.)
            output_file.write_frames(ss)
            output_file.close()
            ss_out, sr_out, enc_out = pysndfile.sndio.read(os.path.join(mydir,'test.{0}_{1}'.format(format, encoding)), force_2d=True)
            if sr != sr_out:
                print('error::{0}/{1} writing sample rate {2} read {3}'.format(format, encoding, sr, sr_out))
                failed = True
            if encoding != enc_out:
                print('error::{0}/{1} writing enc read as {2}'.format(format, encoding, enc_out))
                failed = True
            if lossy:
                if ss.shape != ss_out.shape:
                    print('error in {0}/{1}: shape different wrote {2} read {2}'.format(format, encoding, ss.shape, ss_out.shape))
                    failed = True
            else:
                if np.any (ss != ss_out):
                    print('error in {0}/{1}: signal different'.format(format, encoding))
                    failed = True
            if failed:
                print("errors encountered for {0}/{1}".format(format, encoding))
                sys.exit(1)
            print('test sndio.write {0}/{1}'.format(format, encoding))
            pysndfile.sndio.write(os.path.join(mydir,'testsndio.{0}_{1}'.format(format, encoding)), ss, rate=sr, format=format, enc=encoding, compression_level=1.)
            ss_out2, sr_out2, enc_out2 = pysndfile.sndio.read(os.path.join(mydir,'testsndio.{0}_{1}'.format(format, encoding)), force_2d=True)
            if sr != sr_out2:
                print('error::{0}/{1} writing sample rate {2} read {3}'.format(format, encoding, sr, sr_out2))
                failed = True
            if encoding != enc_out2:
                print('error::{0}/{1} writing enc read as {2}'.format(format, encoding, enc_out2))
                failed = True
            if np.any (ss_out2 != ss_out):
                print('error in {0}/{1}: signal different'.format(format, encoding))
                failed = True
            if failed:
                print("errors encountered for {0}/{1}".format(format, encoding))
                sys.exit(1)
        else:
            print('your libsndfile version does not support {1} encoding of {0} format, skip writing test'.format(format, encoding))
    else:
        print('your libsndfile version does not support {0} format, skip writing test'.format(format))


print( "majors", majors)
for mm in majors:
    if mm in fileformat_name_to_id:
        print("format {0:x}".format(fileformat_name_to_id[mm]), "->", mm)
    else:
        print("format {0}".format(mm), "-> not supported by pysndfile")
        
print( get_sndfile_encodings('wav'))

try:
    a = PySndfile(os.path.join(mydir,'test1.wav'))
except IOError as e:
    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print("The following error is expected, as the file test1.wav does not exist.")
    print("--------------------------------")
    print(e)
    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

a = PySndfile(os.path.join(mydir,'test.wav'))
for d in [np.float64, np.float32, np.int32, np.short]:
    print("d:",d)
    ff=a.read_frames(dtype=d)
    a.rewind()
    b = PySndfile(os.path.join(mydir,'test{0}.wav'.format(str(d).split("'")[1])), "w", a.format(), a.channels(), a.samplerate())
    print(b)
    b.write_frames(ff)
    b.close()
    del b

ff=a.read_frames(dtype=np.float64)
ff2 = np.concatenate(((ff,),(ff,))).T

print("ff2.shape    ",ff2.shape)
b = PySndfile(os.path.join(mydir,'test_2cC.wav'), "w", a.format(), 2, a.samplerate())
b.write_frames(np.require(ff2, requirements='C'))

b = PySndfile(Path(os.path.join(mydir,'test_2cF.wav')), "w", a.format(), 2, a.samplerate())
b.write_frames(np.require(ff2, requirements='F'))
del b

b= PySndfile(Path(mydir) /'test_2cF.wav')
bff=b.read_frames()
with PySndfile(os.path.join(mydir,'test_2cC.wav')) as b:
    bfc=b.read_frames()

read_error= False
write_error =False
if np.any (ff2 != bff):
    print('error in test_2cF.wav')
    print("ff2", ff2)
    print("bff", bff)
    write_error = True
elif np.any (ff2 != bfc):
    print('error in test_2cC.wav')
    print("ff2", ff2)
    print("bfc", bfc)
    write_error = True
else:
    print("no errors detected for io with different sample encodings")

# check reading part of file
ss,_,_ =  pysndfile.sndio.read(os.path.join(mydir,'test.wav'), force_2d=True)
ssstart,_,_ =  pysndfile.sndio.read(os.path.join(mydir,'test.wav'), end=100, force_2d=True)
ssend,_,_ =  pysndfile.sndio.read(os.path.join(mydir,'test.wav'), start=100, force_2d=True)

if np.any(ss != np.concatenate((ssstart, ssend), axis=0)):
    read_error = True
    print("error reading file segments with sndio")

ww = PySndfile(os.path.join(mydir,'test.wav'))
wwstart = ww.read_frames(100, force_2d=True)
wwend = ww.read_frames(force_2d=True)

if np.any(ss != np.concatenate((wwstart, wwend), axis=0)):
    read_error = True
    print("error reading file segments with class")

# check writing flac
test_compressed('test.wav', 'flac', 'pcm16', False)

test_compressed('test.wav', 'ogg', 'vorbis', True)

# opus does not support 41000
test_compressed('test48000.wav', 'ogg', 'opus', True)

test_compressed('test.wav', 'mpeg', 'mp3', True)

print("all seems ok")
sys.exit(0)
