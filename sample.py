# 基本ライブラリ
import numpy as np
import pandas as pd
# pygrib
import pygrib
# pretty_midi
import pretty_midi

def getNearestLatLon(lat, lon, message):
    """
    概要: 指定した緯度経度から最も近いメッシュ上の緯度経度を算出する
    @param lat: 対象の緯度
    @param lon: 対象の経度
    @param message: 対象のpygrib.gribmessage
    @return 対象値に最も近いメッシュ上のlat,lon
    """

    # メッシュ上のlatとlonのリストを作成
    lats, lons = message.latlons()
    lat_list = []
    for n in range(0, len(lats)):
        tmp = lats[n][0]
        lat_list.append(float(tmp))
    lon_list = lons[0]

    # リスト要素と対象値の差分を計算し最小値の値を取得
    lat_near = lat_list[np.abs(np.asarray(lat_list) - lat).argmin()]
    lon_near = lon_list[np.abs(np.asarray(lon_list) - lon).argmin()]

    return lat_near, lon_near

def getGpvDf(lat, lon, gpv, max_time = 15):
    """
    概要: 指定した緯度経度から最も近いメッシュ上の緯度経度のGPVデータを抽出する
    @param lat: 対象の緯度
    @param lon: 対象の経度
    @param gpv: 対象日時のmsm-gpv
    @param max_time: 予測時間の最大値
    @return 対象値に最も近いメッシュ上のGPVデータをdataframeにて返す
    　　　　（index=変数、columns=予測時間の形式）
    """

    # 予測時間の範囲に応じて抽出するデータの範囲を変更
    if max_time == 15:
        for t in range(0, 15, 1):
            gpv_message = gpv.select(forecastTime=t)
            gpv_var_list = []
            for x in range(0, 11, 1):
                gpv_message_var = gpv_message[x]
                lat_near, lon_near = getNearestLatLon(lat, lon, gpv_message_var)
                gpv_data_var = gpv_message_var.data\
                    (lat1=lat_near, lat2=lat_near, lon1=lon_near, lon2=lon_near)
                gpv_var_list.append(gpv_data_var[0][0])
            if t == 0:
                gpv_df = pd.DataFrame(gpv_var_list)
            else:
                gpv_df = pd.concat([gpv_df, pd.DataFrame(gpv_var_list)], axis=1)
    else:
        for t in range(16, 33, 1):
            gpv_message = gpv.select(forecastTime=t)
            gpv_var_list = []
            for x in range(0, 11, 1):
                gpv_message_var = gpv_message[x]
                lat_near, lon_near = getNearestLatLon(lat, lon, gpv_message_var)
                gpv_data_var = gpv_message_var.data\
                    (lat1=lat_near, lat2=lat_near, lon1=lon_near, lon2=lon_near)
                gpv_var_list.append(gpv_data_var[0][0])
            if t == 16:
                gpv_df = pd.DataFrame(gpv_var_list)
            else:
                gpv_df = pd.concat([gpv_df, pd.DataFrame(gpv_var_list)], axis=1)

    return gpv_df

def getMelody(gpv_df):
    """
    概要: GPVデータのデータフレームから、各変数の変化を表現する音声ファイルを作成する
    @param gpv_df: 対象値に最も近いメッシュ上のGPVデータのdataframe
    @return GPVデータから作成したmidiファイル
    """

    #pretty_midiオブジェクトの作成
    pm = pretty_midi.PrettyMIDI(resolution=960, initial_tempo=120)

    # 各変数に楽器を割り当て、奏でる音階を値の変化から決定する
    for n in range(0, len(gpv_df.index), 1):
        # 楽器の割り当て、listは楽器の種別が重ならない様にするための工夫です
        instrument_list = [x*5 for x in range(0, 11, 1)]
        instrument = pretty_midi.Instrument(instrument_list[n])

        # 最小値0,最大値1にMin-Max Normalization
        gpv_df_norm = gpv_df.apply(lambda x : ((x - x.min())/(x.max()-x.min())),axis=1)
        for t in range(0, len(gpv_df), 1):
            tmp = gpv_df_norm.iloc[n,t]
            if 0<=tmp and tmp<=1/8:
                note_number = pretty_midi.note_name_to_number('C4')
            elif 1/8<tmp and tmp<=2/8:
                note_number = pretty_midi.note_name_to_number('D4')
            elif 2/8<tmp and tmp<=3/8:
                note_number = pretty_midi.note_name_to_number('E4')
            elif 3/8<tmp and tmp<=4/8:
                note_number = pretty_midi.note_name_to_number('F4')
            elif 4/8<tmp and tmp<=5/8:
                note_number = pretty_midi.note_name_to_number('G4')
            elif 5/8<tmp and tmp<=6/8:
                note_number = pretty_midi.note_name_to_number('A4')
            elif 6/8<tmp and tmp<=7/8:
                note_number = pretty_midi.note_name_to_number('B4')
            elif 7/8<tmp and tmp<=1:
                note_number = pretty_midi.note_name_to_number('C5')
            else:
                # 全ての値が0の場合適当な音を（正規化の段階でNanとなるため）
                note_number = pretty_midi.note_name_to_number('C5')

            note = pretty_midi.Note(velocity=100, pitch=note_number, start=t, end=t+1)
            instrument.notes.append(note)
        pm.instruments.append(instrument)
    pm.write('output/midi/test.mid') #midiファイルを書き込みます。

    return gpv_df_norm

# 対象としたいlat、lon
lat = 35.0
lon = 139.0
# 対象としたい日時のMSM-GPVデータ
gpv = pygrib.open\
('input/msmgpv_raw/Z__C_RJTD_20180205150000_MSM_GPV_Rjp_Lsurf_FH00-15_grib2.bin')

gpv_df = getGpvDf(lat, lon, gpv, max_time = 15)
