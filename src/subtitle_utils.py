import pysrt

def load_srt(path):
    subs = pysrt.open(path)
    result = []
    for sub in subs:
        result.append({
            "start": sub.start.ordinal / 1000,
            "end": sub.end.ordinal / 1000,
            "text": sub.text
        })
    return result
