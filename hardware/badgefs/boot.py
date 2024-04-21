from machine import I2C,Pin
import machine
import framebuf
import ssd1306
import time
import random
import gc
import asyncio
import network
import ubinascii
import umqtt.simple
from config import config

print()
print("=========================")
print("[+] Challenge the Cyber 2024 - Cyber Chef CTF")
print("[+] Here's a wel-com flag! CTF{com_join_the_fun}")
print("    Badge team ID = %s" % (config['team_num']))
print("=========================")

i2c = I2C(sda=Pin(14), scl=Pin(12))
display = ssd1306.SSD1306_I2C(128, 64, i2c)
display.fill(0)

def make_image(name, w, h, invert=False):
    buf = bytearray(open(f"img/{name}.fb", "rb").read())
    if invert:
        for i in range(len(buf)):
            buf[i] = ~buf[i] & 0xff
    fb = framebuf.FrameBuffer(buf, w, h, framebuf.MONO_HLSB)
    return fb

def offset_digits(dig):
    offset = 0
    if dig < 10:
        offset += 4
    if dig < 100:
        offset += 4
    return offset

def display_home():
    display.fill(0)
    
    chef = make_image("chef", 40, 40, True)
    display.blit(chef, 43, 16)

    display.text("Cyber", 82, 25, 1)
    display.text("Chef", 82, 40, 1)

    display.fill_rect(0, 0, 128, 15, 1)
    display.text("CTC 2024", 53, 6, 0)

    border = make_image("border", 128, 14)
    display.blit(border, 0, 57)
    
    display.show()

class ButtonPress():
    SHORT = 1
    LONG = 2
    
    last_press = 0

    @staticmethod
    def handle_press(press_type):
        ButtonPress.last_press = press_type
            
    @staticmethod        
    def reset():
        ButtonPress.last_press = 0

from ubutton import uButton
button = uButton(machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_UP))
button.callback_short = lambda: ButtonPress.handle_press(ButtonPress.SHORT)
button.callback_long = lambda: ButtonPress.handle_press(ButtonPress.LONG)

async def main():
    display_home()
    
    while not ButtonPress.last_press:
        await asyncio.sleep_ms(30)
    
    loop.create_task(game_loop())

async def as_draw_bars(num_bars):
    display.fill_rect(0, 0, 128, 9, 0)
    if num_bars >= 1:
        display.fill_rect(48, 6, 24, 3, 1)
        if num_bars >= 2:
            display.fill_rect(48 + 28, 6, 24, 3, 1)
            if num_bars >= 3:
                display.fill_rect(48 + 28 + 28, 6, 24, 3, 1)
    display.show()

gamebits = [random.getrandbits(1) for i in range(1000)]

class GameView:
    TURN_COMPUTER = 1
    TURN_PLAYER = 2
    GAME_OVER = 3
    
class GameSelection:
    DONUT = 0
    CROISSANT = 1
    
class GameResult:
    TIMEOUT = 0
    CORRECT = 1
    WRONG = 2

async def game_loop():
    gc.collect()
    
    crois = make_image("croissant", 48, 48, True)
    donut = make_image("donut", 48, 48, True)
    images = [donut, crois]

    crois_sm = make_image("croissant_sm", 24, 24, True)
    donut_sm = make_image("donut_sm", 24, 24, True)
    
    crois_sm_sel = make_image("croissant_sm", 24, 24)
    donut_sm_sel = make_image("donut_sm", 24, 24)

    display.fill(0)
    
    ## INITIAL VARS
    
    game_view = GameView.TURN_COMPUTER
    level = 0
    
    ## LOOP
    
    while True:
        
        if game_view == GameView.TURN_COMPUTER:
            level += 1
            
            display.fill(0)
            display.fill_rect(0, 0, 128, 15, 1)
            display.text(f"LEVEL {level}", 50 + offset_digits(level), 6, 0)
            
            display.fill_rect(58, 23, 56, 35, 1)
            display.text(f"LEVEL", 58 + offset_digits(level), 31, 0)
            display.text(str(level), 72 + offset_digits(level), 43, 0)
            display.show()
            
            await asyncio.sleep_ms(2500)
            
            display.fill_rect(0, 16, 128, 48, 0)
            display.text("Chefs turn!", 44, 35, 1)
            display.show()
            await asyncio.sleep_ms(2500)

            for iteration in range(1, level+1):
                randbit = gamebits[iteration-1]
                randimg = images[randbit]

                display.fill_rect(0, 16, 128, 48, 0)
                display.blit(randimg, 48, 16)
                        
                offset = 95 + offset_digits(iteration)
                
                display.text(str(iteration), offset, 35, 1)
                display.show()
                
                await asyncio.sleep_ms(2000)
                display.fill_rect(0, 16, 128, 63-16, 0)
                display.show()
                await asyncio.sleep_ms(100)
                
            # hand over the turn to the player
            # we do this here so that level is still shown at the top
            game_view = GameView.TURN_PLAYER
            display.text("Your turn!", 48, 35, 1)
            display.show()            
            await asyncio.sleep_ms(2500)
                
            
        if game_view == GameView.TURN_PLAYER:
            for iteration in range(1, level+1):
                display.fill(0)

                display.blit(donut_sm, 48+8, 20)
                display.rect(48+8, 20, 24, 24, 1) # rectangle drawn around
                display.blit(crois_sm, 48+24+12+4, 20)
                display.rect(48+24+12+4, 20, 24, 24, 1) # rectangle drawn around

                offset = 73 + offset_digits(iteration)
                display.text(str(iteration), offset, 51)
                display.show()
                
                ButtonPress.reset()                
                start_time = time.ticks_ms()
                
                selection = None
                result = None
                previous_bars = -1
                
                while True:
                    now_time = time.ticks_ms()
                    tick_diff = time.ticks_diff(now_time, start_time)
                    
                    if tick_diff >= 4000:
                        result = GameResult.TIMEOUT
                        break
                    
                    if ButtonPress.last_press:
                        selection = GameSelection.DONUT if ButtonPress.last_press == ButtonPress.SHORT else GameSelection.CROISSANT
                        randbit = gamebits[iteration-1]
                        
                        if randbit == selection:
                            result = GameResult.CORRECT
                        else:
                            result = GameResult.WRONG
                            
                        break
                    
                    bars_to_draw = 3 - (tick_diff // 1000)
                    if previous_bars != bars_to_draw:
                        previous_bars = bars_to_draw
                        loop.create_task(as_draw_bars(bars_to_draw))
                            
                    await asyncio.sleep_ms(50)
                        
                if result == GameResult.TIMEOUT:
                    display.fill(0)
                    display.fill_rect(0, 0, 128, 15, 1)
                    display.text(f"TOO SLOW", 54, 6, 0)
                    display.text(f"Game over!", 47, 31, 1)
                    display.text(f"Score: {level-1}",  47 + offset_digits(level-1), 43, 1)
                    display.show()
                    
                    ButtonPress.reset()
                    while not ButtonPress.last_press:
                        await asyncio.sleep_ms(30)
                    
                    loop.create_task(game_over(score=level-1))
                    return
                
                if selection == GameSelection.DONUT:
                    display.blit(donut_sm_sel, 48+8, 20)
                elif selection == GameSelection.CROISSANT:
                    display.blit(crois_sm_sel, 48+24+12+4, 20)
                    
                display.show()
                display.fill_rect(0, 0, 128, 15, 1)
                
                if result == GameResult.CORRECT:
                    display.text(f"CORRECT", 62, 6, 0)
                elif result == GameResult.WRONG:
                    display.text(f"WRONG", 70, 6, 0)
                
                display.show()
                await asyncio.sleep_ms(1000)
                
                if result == GameResult.WRONG:
                    display.fill_rect(0, 16, 128, 48, 0)
                    display.text(f"Game over!", 47, 31, 1)
                    display.text(f"Score: {level-1}",  47 + offset_digits(level-1), 43, 1)
                    display.show()
                    
                    ButtonPress.reset()
                    while not ButtonPress.last_press:
                        await asyncio.sleep_ms(30)
                    
                    loop.create_task(game_over(score=level-1))
                    return

            game_view = GameView.TURN_COMPUTER

async def game_over(score):
    if score < 1:
        machine.reset()
        return
    
    display.fill(0)
    display.fill_rect(0, 16, 128, 48, 0)
    display.text(f"Sending...", 47, 31, 1)
    display.text(f"Score: {score}",  47 + offset_digits(score), 43, 1)
    await as_draw_bars(3)
    display.show()
    
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(config['wifi_ssid'], config['wifi_pass'])

    start_time = time.ticks_ms()
    while not sta_if.isconnected():
        now_time = time.ticks_ms()
        tick_diff = time.ticks_diff(now_time, start_time)
        if tick_diff >= 20000:
                break
        else:
            bars_to_draw = (tick_diff // 1000 + 1) % 4
            loop.create_task(as_draw_bars(bars_to_draw))                    
            await asyncio.sleep_ms(1000)

    display.fill(0)
    
    if sta_if.isconnected():
        print("[*] Connected to WiFi")
        submit_success = False
        
        wlan_mac = sta_if.config('mac')
        mac_hex = ubinascii.hexlify(wlan_mac).decode()
        client_id = "%s-%s" % (config['team_num'], mac_hex)

        try:
            m = umqtt.simple.MQTTClient(client_id, config['score_server'], user=config['team_num'], password=config['team_key'])
            m.connect(True)
            m.publish(b"score/%s" % config['team_num'], b'{"score":%d}' % score)
            m.disconnect()
            
            submit_success = True
        except:
            pass
        
        if not submit_success:
            print("[*] Score submission failed")
            
            display.fill_rect(0, 0, 128, 15, 1)
            display.text(f"SEND FAIL", 51, 6, 0)
            display.fill_rect(0, 16, 128, 48, 0)
            display.text(f"Send fail", 51, 31, 1)
            display.text(f"Score: {score}",  47 + offset_digits(score), 43, 1)
            display.show()
        else:
            print("[*] Score submission OK")

            display.fill_rect(0, 0, 128, 15, 1)
            display.text(f"SEND OK", 59, 6, 0)
            display.fill_rect(0, 16, 128, 48, 0)
            display.text(f"Send OK!", 55, 31, 1)
            display.text(f"Score: {score}",  47 + offset_digits(score), 43, 1)
            display.show()
        
    else:
        print("[*] Connection to WiFi failed")

        display.fill_rect(0, 0, 128, 15, 1)
        display.text(f"SEND FAIL", 51, 6, 0)
        display.fill_rect(0, 16, 128, 48, 0)
        display.text(f"Send fail", 51, 31, 1)
        display.text(f"Score: {score}",  47 + offset_digits(score), 43, 1)
        display.show()
    
    ButtonPress.reset()
    while not ButtonPress.last_press:
        await asyncio.sleep_ms(30)
    
    machine.reset()   

loop = asyncio.get_event_loop()
loop.create_task(button.run())
loop.create_task(main())
loop.run_forever()
