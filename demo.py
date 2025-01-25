from utils.load_env import load_env
env = load_env()

gas_sensor_pin = int(env.get("GAS_SENSOR_PIN"))
neo_dir_pin = int(env.get("NEO_PIXEL_DIR_PIN"))
neo_cross_pin = int(env.get("NEO_PIXEL_CROSS_PIN"))
audio_pin = int(env.get("AUDIO_PIN"))

np_dir = [(0,0,0) for _ in range(24)]
np_cross = [(0,0,0) for _ in range(24)]
alarm_duty = 0
alarm_freq = 0

dirty = False

def colored_pound(c, d='#'):
  return f"\x1b[38;2;{c[0]};{c[1]};{c[2]}m{d}\x1b[0m"

cp = colored_pound

def update():

  print(f" {cp(np_dir[15], '-')} {cp(np_dir[16], '-')} {cp(np_dir[17], '-')}   {cp(np_dir[6], '-')} {cp(np_dir[7], '-')} {cp(np_dir[8], '-')}\n"
        f"{cp(np_dir[14], '|')}{cp(np_cross[0], '\\')}           {cp(np_cross[12], '/')}{cp(np_dir[9], '|')}\n"
        f"  {cp(np_cross[1], '\\')}         {cp(np_cross[13], '/')}  \n"
        f"{cp(np_dir[13], '|')}  {cp(np_cross[2], '\\')}       {cp(np_cross[14], '/')}  {cp(np_dir[10], '|')}\n"
        f"    {cp(np_cross[3], '\\')}     {cp(np_cross[15], '/')}    \n"
        f"{cp(np_dir[12], '|')}    {cp(np_cross[4], '\\')}   {cp(np_cross[16], '/')}    {cp(np_dir[11], '|')}\n"
        f"      {cp(np_cross[5], '\\')} {cp(np_cross[17], '/')}      \n"
        f"\n"
        f"      {cp(np_cross[18], '/')} {cp(np_cross[6], '\\')}       \n"
        f"{cp(np_dir[0], '|')}    {cp(np_cross[19], '/')}   {cp(np_cross[7], '\\')}    {cp(np_dir[18], '|')}\n"
        f"    {cp(np_cross[20], '/')}     {cp(np_cross[8], '\\')}     \n"
        f"{cp(np_dir[1], '|')}  {cp(np_cross[21], '/')}       {cp(np_cross[9], '\\')}  {cp(np_dir[19], '|')}\n"
        f"  {cp(np_cross[22], '/')}         {cp(np_cross[10], '\\')}   \n"
        f"{cp(np_dir[2], '|')}{cp(np_cross[23], '/')}           {cp(np_cross[11], '\\')}{cp(np_dir[20], '|')}\n"
        f" {cp(np_dir[3], '-')} {cp(np_dir[4], '-')} {cp(np_dir[5], '-')}   {cp(np_dir[23], '-')} {cp(np_dir[22], '-')} {cp(np_dir[21], '-')}\n"
        f"Alarm: {'\x1b[38;2;255;0;0m###############\x1b[0m' if alarm_duty else ''}"
        )