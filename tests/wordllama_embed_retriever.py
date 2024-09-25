import time
from pathlib import Path
import numpy as np
from tqdm import tqdm

# PID: 319437
from pyopengenai import WordLLamaRetreiver
txt = Path("/home/ntlpt59/Downloads/combined_text.txt").read_text()
ht = WordLLamaRetreiver(txt)
print(ht.top_k("what is negotation credit means?"))
