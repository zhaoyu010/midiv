from PIL import Image

from src.midi_tempo_tools import (
    get_midi_bpm,
    get_all_tempo_changes,
    normalize_tempo,
    get_tempo_from_midi,
    change_midi_bpm
)
print("how to use")

bpm1=get_midi_bpm("test.mid")

print("this is a bpm from hand tempo")
print(bpm1)
print("but midi will change in some time ,we must calculate")
bpm2=get_all_tempo_changes("test.mid")
print(bpm2)
print("if your midi like img.png or img1.pmg,you can use this")

        # 修改速度
#normalize_tempo(input_file, target_bpm, output_file)
normalize_tempo("test.mid", 100, "test_normalized.mid")
bpm3=get_all_tempo_changes("test_normalized.mid")
print(bpm3)

print("if your midi time offset is right but midi bpm is 120 (maybe it is music transcription),you can use this to chang bpm but time offset not chagne")
result = get_tempo_from_midi(
        midi_file="大雪.midi",
        new_tempo=96,
        output_file="大雪96.mid")# 可选，如果不指定会自动生成文件名)
print(result)

print("this is just change music bpm")
change_midi_bpm("test.mid", output_path="test500.mid", target_bpm=500)
