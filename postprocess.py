from collections import defaultdict

def split_to_bars(tokens: list[str]):
	bars = [[]]
	for token in tokens:
		if token.startswith("bar:"):
			bars.append([])
		
		else:
			bars[-1].append(token)
	
	bars = [tuple(bar) for bar in bars if bar]
	return bars

def split_to_parts(bar: tuple[str]):
	parts = {None: []}
	part = None
	for token in bar:
		if token.startswith("part:"):
			part = token
			parts[part] = []
		
		parts[part].append(token)
	
	return {key: tuple(val) for key, val in parts.items()}

def add_repeats(tokens: list[str], repeat_parts=False):
	tokens = [t for t in tokens if t]
	bars = split_to_bars(tokens)
	indices = defaultdict(list)
	for i, bar in enumerate(bars):
		indices[bar].append(i)
	
	bars2 = []
	i = 0
	while i < len(bars):
		bar = bars[i]
		repeats_found = []
		for j in reversed(indices[bar]):
			if j > i:
				l = j-i
				if tuple(bars[i:i+l]) == tuple(bars[j:j+l]):
					n = 1
					while tuple(bars[i:i+l]) == tuple(bars[j+l*n:j+l*(n+1)]):
						n += 1
					a = ("repeat:start",) + bars[i]
					b = (f"repeat:end:{n}",) + bars[i+l-1]
					s = [a] + [("repeat:continue",) + x for x in bars[i+1:i+l-1]] + [b]
					repeats_found.append((j+l*n, s))
		
		if repeats_found:
			repeats_found.sort()
			i, span = repeats_found[-1]
			bars2 += span
			
		else:
			bars2.append(bar)
		
			i += 1
	
	if repeat_parts:
		bars3 = []
		prev_parts = {}
		for bar in bars2:
			new_bar = tuple()
			parts = split_to_parts(bar)
			for key, val in parts.items():
				if key and len(val) > 1 and prev_parts.get(key, None) == val:
					val = (key, "repeat:part")

				new_bar += val

			prev_parts = parts
			bars3.append(new_bar)
	
	else:
		bars3 = bars2
	
	output_tokens = []
	for i, bar in enumerate(bars3):
		output_tokens.append(f"bar:{len(bars3) - i}")
		output_tokens += bar
	
	return output_tokens

def open_repeats(tokens: list[str], max_repeat=None):
	tokens = [t for t in tokens if t]
	bars = split_to_bars(tokens)
	bars2 = []
	i = 0
	while i < len(bars):
		bar = bars[i]
		if bar[0] == "repeat:start":
			bars[i] = bars[i][1:]
			j = i + 1
			while not bars[j][0].startswith("repeat:end:"):
				if bars[j][0] == "repeat:continue":
					bars[j] = bars[j][1:]
				j += 1
			
			n = int(bars[j][0].split(":")[2])
			if max_repeat:
				n = min(n, max_repeat)
			bars[j] = bars[j][1:]
			bars2 += bars[i:j+1]*(n+1)
			i = j + 1
		
		else:
			bars2.append(bar)
			i += 1
	
	bars3 = []
	prev_parts = {}
	for bar in bars2:
		new_bar = tuple()
		parts = split_to_parts(bar)
		for key, val in list(parts.items()):
			if val == (key, "repeat:part"):
				val = prev_parts.get(key, (key,))
				parts[key] = val
			
			new_bar += val
		
		prev_parts = parts
		bars3.append(new_bar)
	
	output_tokens = []
	for i, bar in enumerate(bars3):
		output_tokens.append(f"bar:{len(bars3) - i}")
		output_tokens += bar
	
	return output_tokens

if __name__ == "__main__":
	tokens = "bar:10 part:a X part:b Z bar:9 part:a A part:b Z bar:8 part:a B part:b W bar:7 part:a A part:b W bar:6 part:a B part:b W bar:5 part:a A part:b W bar:4 part:a B part:b W bar:3 part:a A part:b W bar:2 part:a B part:b W bar:1 part:a Y part:b W".replace("  ", " ").split()

	import pprint
	pprint.pprint(add_repeats(tokens))
	tokens2 = open_repeats(add_repeats(tokens))
	tokens3 = add_repeats(tokens)
	#print(len(tokens), tokens)
	#print(len(tokens2), tokens2)
	print(len(tokens), len(tokens2), tuple(tokens) == tuple(tokens2))
	for a, b, c in zip(tokens, tokens2 + [""]*100, tokens3 + [""]*100):
		print(f"{a: <16}{b: <16}{c: <16}", a==b, a==c, sep="\t")