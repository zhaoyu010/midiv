from mido import MidiFile, MidiTrack, Message
import subprocess
import os
import math
import shutil
class TempoError(Exception):
    """MIDI速度处理相关的自定义异常"""
    pass


def get_midi_bpm(midi_file):
    """
    获取MIDI文件的BPM（每分钟节拍数）

    Args:
        midi_file (str): MIDI文件路径

    Returns:
        float: BPM值，保留两位小数
        None: 如果没找到tempo消息

    Raises:
        FileNotFoundError: 如果MIDI文件不存在
        TempoError: 如果读取MIDI文件出错
    """
    if not os.path.exists(midi_file):
        raise FileNotFoundError(f"MIDI文件不存在: {midi_file}")

    try:
        mid = MidiFile(midi_file)

        for track in mid.tracks:
            for msg in track:
                if msg.type == 'set_tempo':
                    tempo = msg.tempo
                    bpm = 60000000 / tempo
                    return round(bpm, 2)

        return None
    except Exception as e:
        raise TempoError(f"读取MIDI文件时出错: {str(e)}")


def get_all_tempo_changes(midi_file):
    """
    获取MIDI文件中所有的tempo变化

    Args:
        midi_file (str): MIDI文件路径

    Returns:
        list: 包含时间和BPM的字典列表，按时间排序

    Raises:
        FileNotFoundError: 如果MIDI文件不存在
        TempoError: 如果读取MIDI文件出错
    """
    if not os.path.exists(midi_file):
        raise FileNotFoundError(f"MIDI文件不存在: {midi_file}")

    try:
        mid = MidiFile(midi_file)
        tempo_changes = []

        for track in mid.tracks:
            track_time = 0
            for msg in track:
                track_time += msg.time
                if msg.type == 'set_tempo':
                    bpm = round(60000000 / msg.tempo, 2)
                    tempo_changes.append({
                        'time': track_time,
                        'bpm': bpm
                    })

        return sorted(tempo_changes, key=lambda x: x['time'])
    except Exception as e:
        raise TempoError(f"读取MIDI文件时出错: {str(e)}")


def normalize_tempo(midi_path, target_bpm=120, output_path=None):
    """
    统一MIDI文件中的速度(BPM)

    Args:
        midi_path (str): 输入MIDI文件路径
        target_bpm (int): 目标BPM（每分钟节拍数）
        output_path (str, optional): 输出文件路径，如果为None则覆盖原文件

    Raises:
        FileNotFoundError: 如果MIDI文件不存在
        TempoError: 如果处理MIDI文件出错
    """
    if not os.path.exists(midi_path):
        raise FileNotFoundError(f"MIDI文件不存在: {midi_path}")

    if output_path is None:
        output_path = midi_path

    try:
        mid = MidiFile(midi_path)
        new_mid = MidiFile()
        new_mid.ticks_per_beat = mid.ticks_per_beat
        target_tempo = int(60_000_000 / target_bpm)

        for track in mid.tracks:
            new_track = MidiTrack()
            new_mid.tracks.append(new_track)

            for msg in track:
                if msg.type == 'set_tempo':
                    new_msg = msg.copy(tempo=target_tempo)
                    new_track.append(new_msg)
                else:
                    new_track.append(msg)

        new_mid.save(output_path)
    except Exception as e:
        raise TempoError(f"处理MIDI文件时出错: {str(e)}")


def get_tempo_from_midi( midi_file, new_tempo, output_file=None):
    """
    使用外部JAR文件获取MIDI文件的速度并生成新的MIDI文件

    Args:
        jar_path (str): MidiTempoConverter.jar文件的路径
        midi_file (str): 输入MIDI文件路径
        new_tempo (int): 新的速度值
        output_file (str, optional): 输出MIDI文件路径，如果为None则自动生成

    Returns:
        dict: 包含处理结果的字典，包括：
            - tempo_info: 原速度和新速度信息列表
            - output_file: 输出文件路径

    Raises:
        FileNotFoundError: 如果JAR文件或MIDI文件不存在
        TempoError: 如果执行JAR文件时出错
    """

    package_dir = os.path.dirname(os.path.abspath(__file__))
    # JAR文件路径（与tempo.py在同一目录）
    jar_path = os.path.join(package_dir, "MidiTempoConverter.jar")
    if not os.path.exists(jar_path):
        raise FileNotFoundError(f"找不到JAR文件: {jar_path}")

    if not os.path.exists(midi_file):
        raise FileNotFoundError(f"找不到MIDI文件: {midi_file}")

    # 如果没有指定输出文件，则自动生成输出文件名
    if output_file is None:
        file_name, file_ext = os.path.splitext(midi_file)
        output_file = f"{file_name}_tempo{new_tempo}{file_ext}"

    source_file = midi_file
    name, ext = source_file.rsplit('.', 1)
    # 创建新文件名（例如在原文件名后添加 "_new" 后缀）
    new_file = output_file  # 复制文件
    shutil.copy(source_file, new_file)

    try:
        # 调用JAR文件，添加输出文件参数
        process = subprocess.Popen(
            ['java', '-jar', jar_path, new_file, str(new_tempo), output_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        output, error = process.communicate()

        if process.returncode != 0:
            raise TempoError(f"JAR执行失败: {error.decode()}")

        # 过滤输出，只保留包含 'Old Tempo' 和 'New Tempo' 的行
        filtered_output = [
            line for line in output.decode().splitlines()
            if 'Old Tempo' in line or 'New Tempo' in line
        ]

        return {
            'tempo_info': filtered_output,
            'output_file': output_file
        }
    except subprocess.SubprocessError as e:
        raise TempoError(f"执行JAR文件时出错: {str(e)}")
    except Exception as e:
        raise TempoError(f"未知错误: {str(e)}")




def change_midi_bpm(input_file, output_path=None, target_bpm=120):
    """
    修改MIDI文件的BPM（综合函数）

    Args:
        input_file (str): 输入MIDI文件路径
        output_path (str, optional): 输出文件路径，如果为None则覆盖原文件
        target_bpm (int): 目标BPM值

    Returns:
        dict: 包含原始BPM和新BPM的信息

    Raises:
        FileNotFoundError: 如果MIDI文件不存在
        TempoError: 如果处理MIDI文件出错
    """
    try:
        # 获取原始BPM
        original_bpm = get_midi_bpm(input_file)

        # 修改BPM
        normalize_tempo(input_file, target_bpm, output_path)

        # 获取新的BPM
        new_bpm = get_midi_bpm(output_path or input_file)

        return {
            'original_bpm': original_bpm,
            'new_bpm': new_bpm,
            'file_path': output_path or input_file
        }
    except Exception as e:
        raise TempoError(f"修改MIDI文件BPM时出错: {str(e)}")