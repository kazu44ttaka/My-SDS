import queue

# local MMDAgent-EX executed from valles
mmdagent_process = None
use_MMD = False

# main thread
main_thread = None
main_event = None

# TTS
agent_audio = queue.Queue()

# GPT
messages = []