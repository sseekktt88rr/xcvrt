import argparse as arg
import subprocess as sb
import os, time, sys, yt_dlp, shutil, librosa
from mutagen.mp3 import MP3
from mutagen.flac import FLAC, Picture
from mutagen.id3 import TIT2, TPE1, TALB, TRCK, APIC, USLT
import timecode

pars = arg.ArgumentParser(prog="xcvrt")
pars.add_argument('-m', '--mode', help="mode: y=youtube, l=local, t=parse timecodes")
pars.add_argument('-f', '--format', help='mp3 flac wav')
pars.add_argument('-o', '--out', help="output file")
pars.add_argument('-i', '--input', help="input file")
pars.add_argument('-l', '--link', help='link youtube')
pars.add_argument('-a', '--artist', help='author')
pars.add_argument('-t', '--title', help='title')
pars.add_argument('-b', '--album', help='album')
pars.add_argument('-n', '--number', help='track number')
pars.add_argument('-c', '--cover', help='track cover')
pars.add_argument('-y', '--lyrics', help='lyrics file')
pars.add_argument('--time', help='timecodes file')
args = pars.parse_args()
formats=['mp3', 'flac', 'wav']
now = f"{time.strftime("%Y-%m-%d-%H-%M-%S")}"

def outputParse(args):
    if args.format: args.format = args.format.lower()
    if not args.out:
        if not args.format: args.out=f"{now}.mp3"; args.format = 'mp3'
        if args.format: args.out=f"{now}.{args.format}"
    if args.out and not args.format:
        ext = os.path.splitext(args.out)[-1][1:].lower()
        if ext in formats: args.format = ext
        else: args.out=f"{now}.mp3"
    if args.out and args.format:
        ext = os.path.splitext(args.out)[-1][1:].lower()
        if ext in formats: 
            if ext != args.format: print('format conflict'); sys.exit(0)
        else: args.out=f"{args.out}.{args.format}"
    print(f"[outputParse] parsed successfuly\n[outputParse] args.out: {args.out}\n[outputParse] args.format: {args.format}")
    return args.out, args.format

def download(args):
    if args.format == 'mp3' or args.format == 'wav': args.out = args.out[:-4]
    elif args.format == 'flac': args.out = args.out[:-5]
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key':'FFmpegExtractAudio',
            'preferredcodec':args.format,
        }],
        'outtmpl':f"{args.out}",
        'writedescription': True,
        'quiet': False,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(args.link, download=True)
            descfile = f"{args.out}.desc"
            if os.path.exists(descfile):
                print(f"[download] description saved: {descfile}")
            print(f"[download] audio saved: {args.out}.{args.format}")
            args.out = f"{args.out}.{args.format}"
            return True
    except Exception as e:
        print(f"[download] error, except: {e}")
        return False

def setTag(args):
    if not args.title and not args.artist and not args.album and not args.number and not args.cover: 
        print("[setTag] no tags. there is nothing to do")
        return
    if args.format == 'mp3':
        print("[setTag] try to use mp3")
        try:
            audio = MP3(args.out)
            if audio.tags is None: audio.add_tags()

            if args.lyrics:
                if not os.path.exists(args.lyrics): print("[setTag] lyrics file not found. skip...")
                if os.path.exists(args.lyrics): 
                    with open(args.lyrics, 'r') as f: 
                        audio.tags['USLT'] = USLT(encoding=3, text=f.read())
            if args.title: audio.tags['TIT2'] = TIT2(encoding=3, text=[args.title])
            if args.artist: audio.tags['TPE1'] = TPE1(encoding=3, text=[args.artist])
            if args.album: audio.tags['TALB'] = TALB(encoding=3, text=[args.album])
            if args.number: audio.tags['TRCK'] = TRCK(encoding=3, text=[args.number])
            if args.cover and not os.path.exists(args.cover):
                print('[setTag] cover not found. skip...')
            if args.cover and os.path.exists(args.cover):
                with open(args.cover, 'rb') as img:
                    cover_data = img.read()
                mime_type = 'image/jpeg'
                if args.cover.lower().endswith('.png'): mime_type = 'image/png'
                audio.tags['APIC'] = APIC(encoding=3,mime=mime_type,type=3,desc='Cover',data=cover_data)
            audio.save()
            print("[setTag] success")
        except Exception as e:
            print(f"[setTag] error, except: {e}")
            return False
    elif args.format == 'flac':
        print("[setTag] try to use flac")
        try:
            audio = FLAC(args.out)
            if args.lyrics:
                if not os.path.exists(args.lyrics): print("[setTag] lyrics file not found. skip...")
                if os.path.exists(args.lyrics): 
                    with open(args.lyrics, 'r', encoding='utf-8') as f:
                        audio['LYRICS'] = [f.read()]
            if args.title: audio['TITLE'] = args.title
            if args.artist: audio['ARTIST'] = args.artist
            if args.album: audio['ALBUM'] = args.album
            if args.number: audio['TRACKNUMBER'] = args.number
            if args.cover and not os.path.exists(args.cover):
                print('[setTag] cover not found. exiting...'); sys.exit(0)
            if args.cover and os.path.exists(args.cover):
                with open(args.cover, 'rb') as img:
                    cover_data = img.read()
                pic = Picture()
                pic.data = cover_data
                pic.type = 3
                mime_type = 'image/jpeg'
                if args.cover.lower().endswith('.png'): mime_type = 'image/png'
                pic.mime = mime_type
                audio.add_picture(pic)
            audio.save()
            print("[setTag] success")
            return True
        except Exception as e:
            print("[setTag] error, except: {e}")
            return False
    elif args.format == 'wav': print("[setTag] try to use wav\n[setTag] there is nothing to do")
    else: print('[setTag] format error (not mp3,flac,wav). exiting...'); sys.exit(0)

print("[main] xcvrt starting!")
if not args.mode: print("[main] no mode selected"); sys.exit(0)
print("[main] init outputParse")
outputParse(args)
if args.format not in formats: print("[main] output format in not supported"); sys.exit(0)
if args.input:
    if os.path.splitext(args.input)[-1][1:].lower() not in formats: print("[main] input format in not supported"); sys.exit(0)
if args.mode == 'l':
    print("[main] xcvrt mode: local")
    if not args.out: args.out = args.input
    else:
        if os.path.splitext(args.out)[-1][1:].lower() != os.path.splitext(args.input)[-1][1:].lower():
            print('[main] <local> format conflict. not supported in this version of xcvrt, sorry. use same format for in and out.')
            sys.exit(0)
        else:
            shutil.copy2(args.input, args.out)
    print("[main] <local> starting setTag...")
    setTag(args)

if args.mode == 'y':
    print("[main] xcvrt mode: youtube")
    print("[main] <youtube> try to download...")
    download(args)
    print("[main] try to set tags")
    setTag(args)

if args.mode == 't':
    print('[main] try to split a file by timecodes...\n[main] <timecode> try to open timecodes file...')
    try:
        with open(args.time, 'r') as f:
            t = timecode.parse_tracks(f.read(), round(librosa.get_duration(path=args.input)))
    except Exception as e:
        print(f'[main] <timecode> failed to read file, error: {e}')
    print("[main] <timecode> try to split file...")
    for s in t:
        a = " ".join(['ffmpeg', '-i', f'"{args.input}"', '-ss', s["start"], '-to', s["end"], '-c', 'copy', f'"{s["title"]}.{args.format}"'])
        #print(a)
        result = sb.run(a)
        #result = sb.run(['ffmpeg', '-i', f'"{args.input}"', '-ss', s["start"], '-to', s["end"], '-c', 'copy', f'"{s["title"]}.{args.format}"'], capture_output=True, text=True)
        if result.returncode == 0: print("[main] <timecode> success")
        else: print(f"[main] <timecode> failed to split, error: {result.stderr}")
