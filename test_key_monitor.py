from pynput import keyboard

def on_press(key):
    '''キーが押された時の処理'''
    try:
        print(f'pressed key: {key.char}')
    except AttributeError:
        print(f'特殊キー: {key}')

def on_release(key):
    '''escキーで終了'''
    if key == keyboard.Key.esc:
        print('監視を終了します')
        return False

print('キー監視を開始します(ESCで終了)')
print('-'*40)

with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()

print('test complete')