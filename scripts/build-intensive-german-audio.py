#!/usr/bin/env python3
"""Persistent SYNTHESIZED English/German lesson audio, never human recordings.
Run: python scripts/build-intensive-german-audio.py
     python scripts/build-intensive-german-audio.py --verify-only
Requires edge-tts and pydub (optionally in _inbox/tts-deps), ffmpeg/ffprobe.
Source JSON is read-only. Resume uses source/config/output SHA-256 hashes.
Only validated files enter src/data/course-audio-manifest.json.
"""
import argparse
import asyncio
import hashlib
import json
import math
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '_inbox/course-audio-cache'
DEPS = ROOT / '_inbox/tts-deps'
if DEPS.exists():
    sys.path.insert(0, str(DEPS))
MANIFEST = ROOT / 'src/data/course-audio-manifest.json'
VERSION = 1
COURSES = {
    'intensive': ('src/data/intensive-skills.json', 'lesson', 192, 'en-GB',
                  ('en-GB-SoniaNeural', 'en-GB-RyanNeural')),
    'german': ('src/data/german/skills.json', 'no', 72, 'de-DE',
               ('de-DE-KatjaNeural', 'de-DE-ConradNeural')),
}


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path, value):
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)


def validate(path):
    if not path.is_file() or path.stat().st_size < 512:
        raise ValueError(f'Missing or empty audio: {path}')
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
        'format=duration:stream=codec_name,codec_type', '-of', 'json', str(path)],
        check=True, capture_output=True)
    probe = json.loads(result.stdout)
    duration = float(probe['format']['duration'])
    if not math.isfinite(duration) or duration <= 0.1:
        raise ValueError(f'Invalid duration: {path}')
    if not any(s.get('codec_type') == 'audio' and s.get('codec_name') == 'mp3'
               for s in probe['streams']):
        raise ValueError(f'Not MP3: {path}')
    subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(path),
        '-f', 'null', '-'], check=True, capture_output=True)
    return round(duration, 3)



def split_turns(text, course):
    # Only remove speaker labels when an entire clearly marked dialogue is found.
    lines = [s.strip() for s in text.splitlines() if s.strip()]
    matched = [re.fullmatch(r"([\w -]{1,40}):\s*(.+)", s) for s in lines]
    if len(lines) > 1 and all(matched):
        return [(m[1], m[2]) for m in matched]
    if course == 'german':
        marks = list(re.finditer(r'(?:^|(?<=[.!?])\s+)((?:(?:Herr|Frau) )?[A-ZÄÖÜ][\w-]{1,24}):\s+', text))
        names = {m[1] for m in marks}
        if marks and marks[0].start() == 0 and 2 <= len(names) <= 4 and len(marks) >= 3:
            return [(m[1], text[m.end():marks[i+1].start() if i+1 < len(marks) else len(text)].strip())
                    for i, m in enumerate(marks)]
    return [('Narrator', text)]


def load_jobs():
    jobs = []
    for course, (source, key, count, language, voices) in COURSES.items():
        rows = read_json(ROOT / source)
        if sorted(r[key] for r in rows) != list(range(1, count+1)):
            raise ValueError(f'{course}: expected lessons 1..{count}')
        for row in rows:
            number = row[key]
            text = row['listening']['text']
            if not isinstance(text, str) or not text.strip():
                raise ValueError(f'{course}/{number}: empty script')
            turns = split_turns(text, course)
            names = list(dict.fromkeys(s for s, _ in turns))
            casting = {s: voices[i % len(voices)] for i, s in enumerate(names)}
            rate = f'{round(-15 * (count-number) / (count-1)):+d}%'
            config = {'turns': turns, 'casting': casting, 'rate': rate,
                      'gapMs': 350, 'version': VERSION}
            jobs.append({'course': course, 'lesson': number, 'language': language,
                         'source': source, 'sourceSha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
                         'generationSha256': digest(config), 'config': config,
                         'path': f'/{course}/audio/lesson-{number:03d}.mp3'})
    return jobs


def compatible(row, job):
    return row and all(row.get(k) == job[k] for k in
        ('course', 'lesson', 'path', 'sourceSha256', 'generationSha256'))


async def build(args):
    import edge_tts
    from pydub import AudioSegment
    CACHE.mkdir(parents=True, exist_ok=True)
    jobs = load_jobs()
    source_hashes = {c: file_hash(ROOT / spec[0]) for c, spec in COURSES.items()}
    if args.limit:
        jobs = jobs[:args.limit]
    entries = {(r['course'], r['lesson']): r for r in read_json(MANIFEST)} if MANIFEST.exists() else {}
    semaphore = asyncio.Semaphore(args.concurrency)
    locks, failures = {}, []

    def save():
        atomic_json(MANIFEST, sorted(entries.values(), key=lambda r: (r['course'], r['lesson'])))

    async def segment(text, voice, rate):
        key = digest({'text': text, 'voice': voice, 'rate': rate, 'version': VERSION})
        path = CACHE / (key + '.mp3')
        async with locks.setdefault(key, asyncio.Lock()):
            if path.exists():
                try:
                    await asyncio.to_thread(validate, path)
                    return path
                except Exception:
                    path.unlink()
            for attempt in range(args.retries):
                tmp = path.with_suffix('.partial.mp3')
                try:
                    await asyncio.wait_for(edge_tts.Communicate(text, voice, rate=rate).save(str(tmp)), 120)
                    await asyncio.to_thread(validate, tmp)
                    tmp.replace(path)
                    return path
                except Exception as exc:
                    tmp.unlink(missing_ok=True)
                    if attempt+1 == args.retries:
                        raise
                    delay = min(60, 2**(attempt+1)) + random.random()
                    print(f'Retry {attempt+1}: {type(exc).__name__}; {delay:.1f}s', flush=True)
                    await asyncio.sleep(delay)

    def join(paths, target, job):
        audio = AudioSegment.silent(duration=180, frame_rate=24000)
        for i, path in enumerate(paths):
            if i:
                audio += AudioSegment.silent(duration=350, frame_rate=24000)
            audio += AudioSegment.from_mp3(str(path)).set_frame_rate(24000).set_channels(1)
        audio += AudioSegment.silent(duration=250, frame_rate=24000)
        tmp = target.with_suffix('.partial.mp3')
        audio.export(str(tmp), format='mp3', bitrate='64k', tags={
            'title': f"{job['course']} lesson {job['lesson']:03d}",
            'artist': 'Microsoft Edge neural speech synthesis',
            'comment': 'SYNTHESIZED speech for language learning; not a human recording.'})
        duration = validate(tmp)
        tmp.replace(target)
        return duration

    async def recording(job):
        key = (job['course'], job['lesson'])
        async with semaphore:
            try:
                target = ROOT / 'public' / job['path'].lstrip('/')
                target.parent.mkdir(parents=True, exist_ok=True)
                old = entries.get(key)
                cached = False
                if compatible(old, job) and target.exists() and file_hash(target) == old['sha256']:
                    try:
                        duration = await asyncio.to_thread(validate, target)
                        cached = True
                    except Exception:
                        pass
                config = job['config']
                if not cached:
                    paths = [await segment(text, config['casting'][speaker], config['rate'])
                             for speaker, text in config['turns']]
                    duration = await asyncio.to_thread(join, paths, target, job)
                entries[key] = {k: v for k, v in job.items() if k != 'config'} | {
                    'duration': duration, 'sha256': file_hash(target), 'bytes': target.stat().st_size,
                    'synthesized': True, 'label': 'Synthesized speech / Sun\u2019iy ovoz',
                    'provider': 'Microsoft Edge TTS', 'voices': list(dict.fromkeys(config['casting'].values())),
                    'speakers': config['casting'], 'rate': config['rate'], 'kind': 'lesson'}
                save()
                print(f"{'Cached' if cached else 'Built'} {key[0]}/{key[1]:03d}: {duration:.1f}s", flush=True)
            except Exception as exc:
                failures.append(key)
                entries.pop(key, None)
                save()
                print(f'FAILED {key}: {exc}', flush=True)
    await asyncio.gather(*(recording(j) for j in jobs))
    if source_hashes != {c: file_hash(ROOT / spec[0]) for c, spec in COURSES.items()}:
        raise RuntimeError('Source changed during generation; rerun to refresh affected lessons')
    print(f'Finished {len(jobs)-len(failures)}/{len(jobs)}', flush=True)
    if failures:
        raise RuntimeError(f'Rerun to resume: {failures}')


def verify():
    jobs = load_jobs()
    rows = read_json(MANIFEST)
    entries = {(r['course'], r['lesson']): r for r in rows}
    expected = {(j['course'], j['lesson']) for j in jobs}
    if len(rows) != len(expected) or set(entries) != expected:
        raise ValueError('Expected exactly 264 unique manifest entries')
    for job in jobs:
        row = entries[(job['course'], job['lesson'])]
        path = ROOT / 'public' / job['path'].lstrip('/')
        duration = validate(path)
        if not compatible(row, job) or not row.get('synthesized') or \
                file_hash(path) != row['sha256'] or path.stat().st_size != row['bytes'] or \
                abs(duration-row['duration']) > 0.02:
            raise ValueError(f'Invalid file/source/config hash or metadata: {path}')
    for course in COURSES:
        group = [r for r in rows if r['course'] == course]
        print(f"VERIFIED {course}: {len(group)} MP3s, {sum(r['bytes'] for r in group):,} bytes, "
              f"{sum(r['duration'] for r in group)/60:.1f} minutes", flush=True)
    print('All 264: ffprobe, full ffmpeg decode, source/config/output SHA-256 checks PASS.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--concurrency', type=int, choices=range(1, 13), default=8)
    parser.add_argument('--retries', type=int, default=6)
    parser.add_argument('--limit', type=int)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if args.retries < 1 or (args.limit is not None and args.limit < 1):
        parser.error('retries and limit must be positive')
    for binary in ('ffmpeg', 'ffprobe'):
        if not shutil.which(binary):
            parser.error(f'{binary} must be on PATH')
    if args.verify_only:
        verify()
    else:
        asyncio.run(build(args))
        if not args.limit:
            verify()


if __name__ == '__main__':
    main()
