#!/usr/bin/env python3
"""Build persistent SYNTHESIZED Russian listening (not human recordings).

Requirements: Python 3.11+, edge-tts==7.3.1, pydub==0.25.1, ffmpeg/ffprobe.
Install edge-tts into _inbox/tts-deps or the active Python environment.
Run: python scripts/build-russian-audio.py --kind lesson
     python scripts/build-russian-audio.py --kind all
     python scripts/build-russian-audio.py --verify-only
All source JSON is read-only. Segment cache and provenance live in _inbox;
never commit _inbox. Only validated MP3s are added to the manifest.
The public Edge TTS service needs internet; no account/key is used.
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
CACHE = ROOT / '_inbox' / 'russian-audio-cache'
DEPS = ROOT / '_inbox' / 'tts-deps'
if DEPS.exists():
    sys.path.insert(0, str(DEPS))
DATA = ROOT / 'src/data/russian'
OUT = ROOT / 'public/russian/audio'
MANIFEST = DATA / 'audio-manifest.json'
FEMALE = 'ru-RU-SvetlanaNeural'
MALE = 'ru-RU-DmitryNeural'
VERSION = 1


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


def voice_map(lines, number):
    # Alternate casting; honor explicit self-introductions where unambiguous.
    mapping = {'A': FEMALE if number % 2 else MALE,
               'B': MALE if number % 2 else FEMALE}
    female_names = r'Тома|Анна|Лола|Малика|Дилноза|Ольга|Мария|Нина|Елена|Светлана|Ирина|Наташа|Алина'
    male_names = r'Али|Азиз|Тимур|Иван|Дмитрий|Алексей|Олег|Сергей|Антон|Рустам|Бахтиёр|Джамшид'
    hints = {}
    for speaker in ('A', 'B'):
        text = ' '.join(x['ru'] for x in lines if x['speaker'] == speaker)
        if re.search(r'Меня зовут (' + female_names + r')\b', text, re.I):
            hints[speaker] = FEMALE
        elif re.search(r'Меня зовут (' + male_names + r')\b', text, re.I):
            hints[speaker] = MALE
    # Keep two distinct voices even if a role-play names two same-gender people.
    if hints:
        speaker = next(iter(hints))
        mapping[speaker] = hints[speaker]
        mapping['B' if speaker == 'A' else 'A'] = MALE if hints[speaker] == FEMALE else FEMALE
    return mapping


def load_jobs(kind):
    jobs = []
    if kind in ('all', 'lesson'):
        lessons = [row for p in sorted(DATA.glob('part-*.json')) for row in read_json(p)]
        if sorted(r['no'] for r in lessons) != list(range(1, 145)):
            raise ValueError('Expected exactly lessons 1..144')
        for row in lessons:
            n = row['no']
            rate = f'{round(-18 * (144 - n) / 143):+d}%'
            jobs.append((f'lesson-{n}', 'lesson', n, row['dialog'], rate))
    if kind in ('all', 'extended'):
        path = DATA / 'listening-extended.json'
        if not path.exists():
            if kind == 'extended':
                raise FileNotFoundError(path)
            print('Extended source is not ready; building lessons only.', flush=True)
        else:
            rows = read_json(path)
            if not isinstance(rows, list):
                raise ValueError('Extended source must be an array')
            if len(rows) != 12:
                raise ValueError('Expected exactly 12 extended recordings')
            for i, row in enumerate(rows, 1):
                number = row.get('month', i)
                lines = row.get('dialog', row.get('script', row.get('lines')))
                if isinstance(lines, list):
                    lines = [{'speaker': line['speaker'], 'ru': line.get('ru', line.get('text'))}
                             for line in lines]
                if not isinstance(lines, list):
                    raise ValueError(f'Unknown extended script structure: {row.keys()}')
                jobs.append((f'extended-{number}', 'extended', number, lines,
                             f'{round(-15 * (12 - number) / 11):+d}%'))
    for ident, _, _, lines, _ in jobs:
        if not lines or any(s.get('speaker') not in ('A', 'B') or
                            not isinstance(s.get('ru'), str) or not s['ru'].strip() for s in lines):
            raise ValueError(f'Invalid speaking turns: {ident}')
    if len({j[0] for j in jobs}) != len(jobs):
        raise ValueError('Duplicate audio IDs')
    return jobs


async def build(args):
    import edge_tts
    from pydub import AudioSegment
    CACHE.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    # The cache is explicitly disposable and must never be staged.
    (ROOT / '_inbox' / '.gitignore').write_text('*\n', encoding='utf-8')
    jobs = load_jobs(args.kind)
    if args.limit:
        jobs = jobs[:args.limit]
    entries = {r['id']: r for r in read_json(MANIFEST)} if MANIFEST.exists() else {}
    semaphore = asyncio.Semaphore(args.concurrency)
    locks = {}
    failures = []

    def save_manifest():
        atomic_json(MANIFEST, sorted(entries.values(), key=lambda r:
            (r['kind'] != 'lesson', int(r['id'].split('-')[-1]))))

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
                tmp = CACHE / (key + '.partial.mp3')
                try:
                    await asyncio.wait_for(edge_tts.Communicate(text, voice, rate=rate).save(str(tmp)), 120)
                    await asyncio.to_thread(validate, tmp)
                    tmp.replace(path)
                    return path
                except Exception as exc:
                    tmp.unlink(missing_ok=True)
                    if attempt + 1 == args.retries:
                        raise
                    delay = min(60, 2 ** (attempt + 1)) + random.random()
                    print(f'Retry {attempt + 1}: {type(exc).__name__}; waiting {delay:.1f}s', flush=True)
                    await asyncio.sleep(delay)

    def join(paths, target, ident, gap):
        audio = AudioSegment.silent(duration=180, frame_rate=24000)
        for i, path in enumerate(paths):
            if i:
                audio += AudioSegment.silent(duration=gap, frame_rate=24000)
            audio += AudioSegment.from_mp3(str(path)).set_frame_rate(24000).set_channels(1)
        audio += AudioSegment.silent(duration=250, frame_rate=24000)
        tmp = target.with_suffix('.partial.mp3')
        audio.export(str(tmp), format='mp3', bitrate='64k', tags={
            'title': ident, 'artist': 'Microsoft Edge neural speech synthesis',
            'comment': 'SYNTHESIZED Russian speech; SvetlanaNeural / DmitryNeural. Not human recordings.'})
        duration = validate(tmp)
        tmp.replace(target)
        return duration

    async def recording(job):
        ident, kind, number, lines, rate = job
        async with semaphore:
            try:
                voices = voice_map(lines, number)
                if kind == 'extended':
                    # Casting follows the supplied scripts' names and grammatical gender.
                    a_voice = FEMALE if number in (1, 2, 3, 5, 8, 9, 12) else MALE
                    voices = {'A': a_voice, 'B': MALE if a_voice == FEMALE else FEMALE}
                gap = 440 if kind == 'lesson' and number <= 36 else 300
                signature = digest({'lines': lines, 'voices': voices, 'rate': rate,
                                    'gap': gap, 'version': VERSION})
                stamp = CACHE / (ident + '.json')
                target = OUT / (ident + '.mp3')
                if target.exists() and stamp.exists() and read_json(stamp).get('signature') == signature:
                    duration = await asyncio.to_thread(validate, target)
                    if read_json(stamp).get('sha256') != file_hash(target):
                        raise ValueError(f'Output checksum changed: {ident}; remove stamp to rebuild')
                    print(f'Cached {ident}: {duration:.1f}s', flush=True)
                else:
                    paths = []
                    for line in lines:
                        paths.append(await segment(line['ru'], voices[line['speaker']], rate))
                    duration = await asyncio.to_thread(join, paths, target, ident, gap)
                    atomic_json(stamp, {'signature': signature, 'sha256': file_hash(target),
                        'rate': rate, 'voices': voices, 'synthesized': True})
                    print(f'Built {ident}: {duration:.1f}s ({rate})', flush=True)
                entries[ident] = {'id': ident, 'path': f'/russian/audio/{ident}.mp3',
                    'duration': duration, 'sha256': file_hash(target),
                    'voices': list(dict.fromkeys(voices[s['speaker']] for s in lines)), 'kind': kind}
                save_manifest()
            except Exception as exc:
                failures.append(ident)
                entries.pop(ident, None)
                save_manifest()
                print(f'FAILED {ident}: {exc}', file=sys.stderr, flush=True)
    await asyncio.gather(*(recording(job) for job in jobs))
    print(f'Finished: {len(jobs) - len(failures)}/{len(jobs)} requested recordings', flush=True)
    if failures:
        raise RuntimeError(f'Rerun to resume failed recordings: {failures}')


def verify():
    rows = read_json(MANIFEST)
    expected = {j[0] for j in load_jobs('all')}
    if {r['id'] for r in rows} != expected or len(rows) != len(expected):
        raise ValueError('Manifest does not match all available source recordings')
    for row in rows:
        path = ROOT / 'public' / row['path'].lstrip('/')
        duration = validate(path)
        if abs(duration - row['duration']) > 0.02 or file_hash(path) != row['sha256']:
            raise ValueError(f'Invalid manifest entry: {row["id"]}')
    print(f'VERIFIED {len(rows)} MP3 files; {sum(r["duration"] for r in rows) / 60:.1f} minutes; all decode and SHA-256 checks pass.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind', choices=['lesson', 'extended', 'all'], default='all')
    parser.add_argument('--concurrency', type=int, choices=range(1, 7), default=6)
    parser.add_argument('--retries', type=int, default=6)
    parser.add_argument('--limit', type=int)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if args.retries < 1:
        parser.error('--retries must be positive')
    for binary in ('ffmpeg', 'ffprobe'):
        if not shutil.which(binary):
            parser.error(f'{binary} must be on PATH')
    if args.verify_only:
        verify()
    else:
        asyncio.run(build(args))


if __name__ == '__main__':
    main()
