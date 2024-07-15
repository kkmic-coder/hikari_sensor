#!/usr/bin/env python
# coding: utf-8

# @author KKMIC.
# @version 1.0.0
# 2024/05/11 Sat

# *** センサーライトプログラム ***
# 暗い部屋で卓上ライトだけで作業後、卓上ライトを消灯してから部屋を出るまでの間に豆電球を自動点灯・自動消灯する
import time
import pigpio
#from gpiozero import LED as light
import logging

threshold = 10
sabun = 8
lighting_time = 30 * 2


pi = pigpio.pi()
sensor = pi.spi_open(0, 1000000, 0)
pi.set_mode(5, pigpio.OUTPUT)

# logging setup -----------------------------------
logger = logging.getLogger('jiritsu_log')

### ログレベル定義1/2 (INFO, WARNING, ERROR, DEBUG):logger
# logger に渡すログのレベル
logger.setLevel(logging.DEBUG)
format = '%(asctime)s:%(levelname)-9s :%(message)s'

# 動作ログ書き込みディレクトリの取得
#_log_dir = StaticDefine.aplog_path
#_log_dir = '/home/kkmic/hikari'
_log_dir = '/tmp'

# ファイルパスの生成
_filepath = _log_dir + '/' + 'sensor_light.log'
fl_handler = logging.FileHandler(filename=_filepath, encoding="utf-8")

### ログレベル定義2/2 (INFO, WARNING, ERROR, DEBUG):handler
# log handler に渡すログのレベル
# 出力するログのレベルを変更する場合は次の行を修正すること
fl_handler.setLevel(logging.INFO)
#fl_handler.setLevel(logging.DEBUG)

fl_handler.setFormatter(logging.Formatter(format))
logger.addHandler(fl_handler)
# logging setup -----------------------------------


# A/Dコンバータからデータを取得する関数を定義
def measure(ch):
    # SPI インターフェイスでデータの送受信を行う
    c, ad = pi.spi_xfer( sensor, [ 0x68 | ch, 0x00 ] )
    #ad = spi.xfer2( [ (start + sgl + ch + msbf), dummy ] )
    #
    val = ((ad[0] & 0x03) << 8) + ad[1] 
    # 受信した2バイトのデータを10 ビットデータにまとめる
    voltage =  ( val * 3.3 ) / 1023
    # 結果を返す
    return val, voltage

try:
    ch1_val_3 = 0
    ch1_val_2 = 0
    ch1_val_1 = 0
    light_status = False
    counter = 0

    while True:
        # 関数を呼び出してch1 のデータを取得
        ch1_val, ch1_voltage  = measure(0x10)
        print('ch1 = {:4d}, {:2.2f}[V]'.format(ch1_val, ch1_voltage))
        logger.debug('ch1 = {:4d}, {:2.2f}[V] {} '.format(ch1_val, ch1_voltage, light_status))
            
        # 3回前の値を使用するため変数処理
        ch1_val_3 = ch1_val_2
        ch1_val_2 = ch1_val_1
        ch1_val_1 = ch1_val

        # 現在の明るさと3回前の明るさを比較する
        # ライト点灯の条件：１　規定以上の明るさの差分を検知、２　現在点灯していない、３　明るさが規定以下（暗いとき）
        if ch1_val_3 - ch1_val > sabun and light_status == False and ch1_val < threshold:
            light_status = True
            pi.write(5, 1)
            #light_blub.on()
            
            print('BLUB is light')
            logger.debug('BLUB is light')

        # すでに点灯している場合
        elif light_status == True:
            # カウントを加算
            counter = counter + 1
            # もしカウンターが lighting_time になったらライト消灯しカウンターをクリアする
            if counter == lighting_time:
                light_status = False
                pi.write(5, 0)
                print('BLUB is off')
                logger.debug('BLUB is turn off')
                #light_blub.off()
                counter = 0

        time.sleep(0.5)
        print(light_status)

except KeyboardInterrupt:
    pass

pi.spi_close(sensor)
pi.stop()
