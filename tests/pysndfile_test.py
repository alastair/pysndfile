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

def test_compressed(input_file, format, encoding, level, lossy):
    if format in majors:
        if encoding in get_sndfile_encodings(format):
            failed = False
            ss, sr, enc = pysndfile.sndio.read(os.path.join(mydir,input_file), force_2d=True)
            print('test writing {0}/{1}'.format(format, encoding))
            output_file = PySndfile(os.path.join(mydir,'test.{0}_{1}'.format(format, encoding)), "w", construct_format(format, encoding), ss.shape[1], sr)
            output_file.set_compression_level(level)
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
            pysndfile.sndio.write(os.path.join(mydir,'testsndio.{0}_{1}'.format(format, encoding)), ss, rate=sr, format=format, enc=encoding, commands=pysndfile.sndio.Commands(SFC_SET_COMPRESSION_LEVEL=level))
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
ss,sr,_ =  pysndfile.sndio.read(os.path.join(mydir,'test.wav'), force_2d=True)
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
test_compressed('test.wav', 'flac', 'pcm16', 1., False)

test_compressed('test.wav', 'ogg', 'vorbis', 1., True)

# opus does not support 41000
test_compressed('test48000.wav', 'ogg', 'opus', 1., True)

# lame does not accept 1 for compression level (or 0 for VBR)
test_compressed('test.wav', 'mpeg', 'mp3', 0.9999, True)

cart=SfCartInfo(version='0101', title='Cart Chunk: the traffic data file format for the Radio Industry', artist='Jay Rose, dplay.com', cut_id='DEMO-0101', client_id='CartChunk.org', category='DEMO', classification='Demo and sample files', out_cue='the Radio Industry', start_date='1900/01/01', start_time='Cart Chu', end_date='2099/12/31', end_time='23:59:59', producer_app_id='AUDICY', producer_app_version='3.10/623', user_def="Demo ID showing basic 'cart' chunk attributes", level_reference=32768, post_timers=[SfCartTimer(usage='MRK ', value=112000), SfCartTimer(usage='SEC1', value=152533), SfCartTimer(usage='EOD ', value=201024)], url='http://www.cartchunk.org', tag_text="The radio traffic data, or 'cart' format utilizes a widely\r\nused standard audio file format (wave and broadcast wave file).\r\nIt incorporates the common broadcast-specific cart labeling\r\ninformation into a specialized chunk within the file itself.\r\nAs a result, the burden of linking multiple systems is reduced\r\nto producer applications writing a single file, and the consumer\r\napplications reading it. The destination application can extract\r\ninformation and insert it into the native database application\r\nas needed.\r\n")
pysndfile.sndio.write(os.path.join(mydir, 'testdict.wav'), ss, format="wav", enc="float32", rate=sr, commands=pysndfile.sndio.Commands(SFC_SET_ADD_PEAK_CHUNK=True, SFC_SET_CART_INFO=cart))
info=pysndfile.sndio.get_info_command(os.path.join(mydir, 'testdict.wav'), commands=["SFC_GET_CURRENT_SF_INFO", "SFC_CALC_SIGNAL_MAX", "SFC_GET_SIGNAL_MAX", "SFC_GET_CART_INFO"])
if not info["SFC_CALC_SIGNAL_MAX"]:
    print("computed max signal failed")
    sys.exit(1)
if not info["SFC_GET_SIGNAL_MAX"]:
    print("unexpected max signal chunk not available")
    sys.exit(1)
if info["SFC_CALC_SIGNAL_MAX"] != info["SFC_GET_SIGNAL_MAX"]:
    print("inconsistent signal max")
    sys.exit(1)
read_format = info["SFC_GET_CURRENT_SF_INFO"]
if read_format.frames != ss.shape[0] or read_format.channels != ss.shape[1] \
   or read_format.samplerate != sr or read_format.format != construct_format("wav", "float32"):
    print("incorrect format information")
    sys.exit(1)
read_cart = info["SFC_GET_CART_INFO"]
if read_cart.version != cart.version:
    print("read cart version is different")
    sys.exit(1)
if read_cart.title != cart.title:
    print("read cart title is different")
    sys.exit(1)
if read_cart.artist != cart.artist:
    print("read cart artist is different")
    sys.exit(1)
if read_cart.cut_id != cart.cut_id:
    print("read cart cut_id is different")
    sys.exit(1)
if read_cart.client_id != cart.client_id:
    print("read cart client_id is different")
    sys.exit(1)
if read_cart.category != cart.category:
    print("read cart category is different")
    sys.exit(1)
if read_cart.classification != cart.classification:
    print("read cart classification is different")
    sys.exit(1)
if read_cart.out_cue != cart.out_cue:
    print("read cart out_cue is different")
    sys.exit(1)
if read_cart.start_date != cart.start_date:
    print("read cart start_date is different")
    sys.exit(1)
if read_cart.start_time != cart.start_time:
    print("read cart start_time is different")
    sys.exit(1)
if read_cart.end_date != cart.end_date:
    print("read cart end_date is different")
    sys.exit(1)
if read_cart.end_time != cart.end_time:
    print("read cart end_time is different")
    sys.exit(1)
if read_cart.producer_app_id != cart.producer_app_id:
    print("read cart producer_app_id is different")
    sys.exit(1)
if read_cart.producer_app_version != cart.producer_app_version:
    print("read cart producer_app_version is different")
    sys.exit(1)
if read_cart.user_def != cart.user_def:
    print("read cart user_def is different")
    sys.exit(1)
if read_cart.level_reference != cart.level_reference:
    print("read cart level_reference is different")
    sys.exit(1)
if read_cart.post_timers != cart.post_timers:
    print("read cart post_timers is different")
    sys.exit(1)
if read_cart.url != cart.url:
    print("read cart url is different")
    sys.exit(1)
if read_cart.tag_text[0:-2] != cart.tag_text:
    print("read cart tag_text is different",read_cart.tag_text[0:-2],cart.tag_text)
    sys.exit(1)

if 'mpeg' in majors and 'mp3' in get_sndfile_encodings('mpeg'): 
    pysndfile.sndio.write(os.path.join(mydir, 'test.mp3'), ss, format="mpeg", enc="mp3", commands=pysndfile.sndio.Commands(SFC_SET_BITRATE_MODE="SF_BITRATE_MODE_AVERAGE", SFC_SET_VBR_ENCODING_QUALITY=0.5))
    info=pysndfile.sndio.get_info_command(os.path.join(mydir, 'test.mp3'), commands=["SFC_GET_BITRATE_MODE", "SFC_GET_CURRENT_SF_INFO", "SFC_CALC_SIGNAL_MAX", "SFC_GET_SIGNAL_MAX"])
    if info["SFC_GET_BITRATE_MODE"] != "SF_BITRATE_MODE_AVERAGE":
        print("bitrate mode not as expected, returned {0} should have been SF_BITRATE_MODE_AVERAGE".format(info["SFC_GET_BITRATE_MODE"]))
        sys.exit(1)

print("all seems ok")
sys.exit(0)
