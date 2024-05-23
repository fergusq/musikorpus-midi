from pathlib import Path
import traceback
import music21 as m21
from postprocess import add_repeats
import random

def read_symbols(score):
    def find_part(obj) -> m21.stream.Part | None:
        while not isinstance(obj, m21.stream.Part):
            obj = obj.activeSite

        if isinstance(obj, m21.stream.Part):
            return obj

        return None
    
    def find_measure(obj) -> m21.stream.Measure | None:
        while not isinstance(obj, m21.stream.Measure):
            obj = obj.activeSite

        if isinstance(obj, m21.stream.Measure):
            return obj

        return None

    part_instruments = {}

    symbols = []
    metronome_marks = set()
    instrument = None
    for i, symbol in enumerate(score.recurse()):
        if symbol.measureNumber is not None and symbol.beat is not None:
            part = find_part(symbol)
            measure = find_measure(symbol)
            if isinstance(symbol, m21.instrument.Instrument):
                part_instruments[id(part)] = symbol
            instrument = part_instruments.get(id(part), None)
            if instrument:
                symbols.append((symbol.measureNumber, instrument.midiProgram or 10000, symbol.beat, part, measure, symbol))
            
            if isinstance(symbol, m21.tempo.MetronomeMark):
                metronome_marks.add((symbol.measureNumber, symbol.beat, symbol.number))
    
    #metronome_marks = sorted(metronome_marks)

    symbols.sort(key=lambda p: p[:3])
    return symbols, part_instruments, metronome_marks

def symbols_to_tokens(symbols, part_instruments, metronome_marks):
    metronome_marks = {(m, b): mm for (m, b, mm) in metronome_marks}
    tokens = []
    prev_measure = None
    prev_part = None
    prev_key = None
    max_measure = max(p[0] for p in symbols)
    tokens.append(f"bar:{max_measure+1}")
    parts = list(part_instruments)
    random.shuffle(parts)
    for part in parts:
        name = part_instruments[part].instrumentName or "Unknown"
        program = part_instruments[part].midiProgram
        tokens.append(f"part:{name.replace(' ', '_')}:{program}")
    for measureNumber, _, beat, part, measure, symbol in symbols:
        if measureNumber != prev_measure:
            prev_measure = measureNumber
            tokens.append(f"bar:{max_measure-measureNumber+1}")
            if tempo := metronome_marks.get((measureNumber, 1.0), None):
                tokens.append(f"tempo:{tempo}")
            key = measure.keySignature.sharps if measure.keySignature else prev_key
            tokens.append(f"key:{key}")
            prev_key = key
            tokens.append(f"beats:{measure.barDuration.quarterLength}")
            prev_part = None

        if part != prev_part:
            prev_part = part
            if id(part) in part_instruments:
                name = part_instruments[id(part)].instrumentName or "Unknown"
                program = part_instruments[id(part)].midiProgram
                tokens.append(f"part:{name.replace(' ', '_')}:{program}")

            else:
                tokens.append(f"part:{id(part)}:0")

        if isinstance(symbol, m21.note.Unpitched):
            tokens.append(f"beat:{beat}")
            name = (symbol.storedInstrument.instrumentName or "Unknown") if symbol.storedInstrument else "Unknown"
            tokens.append(f"unpitched:{name.replace(' ', '_')}:{symbol.duration.quarterLength}")

        elif isinstance(symbol, m21.note.Note):
            tokens.append(f"beat:{beat}")
            tokens.append(f"note:{symbol.nameWithOctave}:{symbol.duration.quarterLength}")

        elif isinstance(symbol, m21.chord.Chord):
            tokens.append(f"beat:{beat}")
            for note in symbol.notes:
                tokens.append(f"note:{note.nameWithOctave}:{note.duration.quarterLength}")

        elif isinstance(symbol, m21.chord.Chord):
            tokens.append(f"beat:{beat}")
            for note in symbol.notes:
                tokens.append(f"note:{note.nameWithOctave}:{note.duration.quarterLength}")

        elif isinstance(symbol, m21.tempo.MetronomeMark) and beat > 1:
            tokens.append(f"tempo:{symbol.number}")

        #elif isinstance(symbol, m21.note.Rest):
        #    tokens.append(f"beat:{beat}")
        #    tokens.append(f"rest:{symbol.duration.quarterLength}")
    
    tokens = add_repeats(tokens)
    
    return tokens

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("midi_file")
    args = parser.parse_args()
    score = m21.converter.parse(args.midi_file)
    symbols, instruments, mms = read_symbols(score)
    tokens = symbols_to_tokens(symbols, instruments, mms)
    for token in tokens:
        indent = 0 if token.startswith("bar:") else 1 if token.startswith("part:") or token.startswith("beats:") else 2 if token.startswith("beat:") else 3
        print("  "*indent + token)