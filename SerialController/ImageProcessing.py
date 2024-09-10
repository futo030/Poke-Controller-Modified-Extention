#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import cv2
import numpy
import os
from typing import List, Tuple, Optional
from logging import getLogger, DEBUG, NullHandler


def crop_image(image: numpy.ndarray, crop: List[int] = None) -> numpy.ndarray:
    '''
    画像をトリミングする
    [y軸始点, y軸終点, x軸始点, x軸終点]
    '''
    try:
        cropped_image = image[crop[0]:crop[1], crop[2]: crop[3]]
    except:
        cropped_image = image

    return cropped_image


def crop_image_extend(image: numpy.ndarray, crop_fmt: int | str = None, crop: List[int] = None) -> numpy.ndarray:
    '''
    画像をトリミングする
    ・Pillow形式
    x軸(横軸),y軸(縦軸),画像の左上が原点
    crop_fmt=1: [x軸始点, y軸始点, x軸終点, y軸終点]
    crop_fmt=2: [x軸始点, y軸始点, トリミング後の画像のサイズ(横), トリミング後の画像のサイズ(縦)]
    crop_fmt=3: [x軸始点, x軸終点, y軸始点, y軸終点]
    crop_fmt=4: [x軸始点, トリミング後の画像のサイズ(横), y軸始点, トリミング後の画像のサイズ(縦)]
    ・opencv形式(y, xの順番)
    crop_fmt=11: [y軸始点, x軸始点, y軸終点, x軸終点]
    crop_fmt=12: [y軸始点, x軸始点, トリミング後の画像のサイズ(縦), トリミング後の画像のサイズ(横)]
    crop_fmt=13: [y軸始点, y軸終点, x軸始点, x軸終点]
    crop_fmt=14: [y軸始点, トリミング後の画像のサイズ(縦), x軸始点, トリミング後の画像のサイズ(横)]
    '''

    try:
        # pillow形式
        if crop_fmt == 1 or crop_fmt == "1":
            cropped_image = image[crop[1]:crop[3], crop[0]: crop[2]]
        elif crop_fmt == 2 or crop_fmt == "2":
            cropped_image = image[crop[1]:crop[1] + crop[3], crop[0]:crop[0] + crop[2]]
        elif crop_fmt == 3 or crop_fmt == "3":
            cropped_image = image[crop[2]:crop[3], crop[0]: crop[1]]
        elif crop_fmt == 4 or crop_fmt == "4":
            cropped_image = image[crop[2]:crop[2] + crop[3], crop[0]:crop[0] + crop[1]]
        # opencv形式
        elif crop_fmt == 11 or crop_fmt == "11":
            cropped_image = image[crop[0]:crop[2], crop[1]: crop[3]]
        elif crop_fmt == 12 or crop_fmt == "12":
            cropped_image = image[crop[0]:crop[0] + crop[2], crop[1]:crop[1] + crop[3]]
        elif crop_fmt == 13 or crop_fmt == "13":
            cropped_image = image[crop[0]:crop[1], crop[2]: crop[3]]
        elif crop_fmt == 14 or crop_fmt == "14":
            cropped_image = image[crop[0]:crop[0] + crop[1], crop[2]:crop[2] + crop[3]]
        else:
            cropped_image = image
    except:
        cropped_image = image

    return cropped_image


def getInterframeDiff(frame1: numpy.ndarray, frame2: numpy.ndarray, frame3: numpy.ndarray, threshold: float) -> numpy.ndarray:
    '''
    Get interframe difference binarized image
    フレーム間差分により2値化された画像を取得する
    '''
    diff1 = cv2.absdiff(frame1, frame2)
    diff2 = cv2.absdiff(frame2, frame3)

    diff = cv2.bitwise_and(diff1, diff2)

    # binarize
    img_th = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)[1]

    # remove noise
    mask = cv2.medianBlur(img_th, 3)
    return mask


def getImage(path: str, mode: str = "color"):
    '''
    画像の読み込みを行う。
    '''
    if path == None or path == "":
        return None
    elif mode == "binary":
        return cv2.imread(path, 0)
    elif mode == "gray":
        return cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    else:
        return cv2.imread(path, cv2.IMREAD_COLOR)


def doPreprocessImage(image: numpy.ndarray, use_gray: bool = True, crop: List[int] = None, BGR_range: Optional[dict] = None, threshold_binary: Optional[int] = None) -> Tuple[numpy.ndarray, int, int]:
    '''
    画像をトリミングしてグレースケール化/2値化する
    2値化関連のContributor: mikan kochan 空太 (敬称略)
    '''
    src = crop_image(image, crop=crop)     # トリミング

    if use_gray:
        src = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)         # グレースケール化
    elif BGR_range is not None:                             # 2値化
        src = cv2.inRange(src, numpy.array(BGR_range['lower']), numpy.array(BGR_range['upper']))    # inRangeで元画像を２値化(指定した色の範囲を抽出できる)

    if threshold_binary is not None:
        _, src = cv2.threshold(src, threshold_binary, 255, cv2.THRESH_BINARY)

    width, height = src.shape[1], src.shape[0]  # テンプレート画像のサイズ

    return src, width, height


def opneImage(image: numpy.ndarray, crop: List[int] = None, title="image"):
    '''
    キー入力があるまで画像を表示する
    Contributor: kochan (敬称略)
    '''
    src = crop_image(image, crop=crop)     # トリミング
    cv2.imshow(f'{title}', src)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


class ImageProcessing:
    '''
    画像に関する処理を行う。
    '''
    __logger = None
    __activate_logger = False
    __gsrc = None
    __gtmpl = None
    __gresult = None
    __use_gpu = False
    image_type = numpy.ndarray

    def __init__(self, use_gpu: bool = False):
        # ロガーを起動する(1回だけ)
        if not self.__activate_logger:
            self.__logger = getLogger(__name__)
            self.__logger.addHandler(NullHandler())
            self.__logger.setLevel(DEBUG)
            self.__logger.propagate = True
        # GUP使用時、デバイスのメモリを確保する(1回だけ)
        if use_gpu:
            '''
            テンプレートマッチングをGPUで行うようにする。
            うまく設定できたらuse_gpuのフラグをTrueにする。
            '''
            try:
                if self.__gsrc is None:
                    self.__gsrc = cv2.cuda_GpuMat()
                if self.__gtmpl is None:
                    self.__gtmpl = cv2.cuda_GpuMat()
                if self.__gresult is None:
                    self.__gresult = cv2.cuda_GpuMat()
                self.__use_gpu = True
                print("template matching:mask is ignored.")
            except:
                self.__use_gpu = False
        else:
            self.__use_gpu = False

    def imwrite(self, filename: str, image: numpy.ndarray, params: int = None) -> bool:
        '''
        画像を書き込む
        '''
        try:
            ext = os.path.splitext(filename)[1]
            result, n = cv2.imencode(ext, image, params)

            if result:
                with open(filename, mode='w+b') as f:
                    n.tofile(f)
                return True
            else:
                return False
        except Exception as e:
            print(e)
            self.__logger.error(f"Image Write Error: {e}")
            return False

    def doTemplateMatch(self, image: numpy.ndarray, template_image: numpy.ndarray, mask_image: numpy.ndarray = None) -> Tuple[float, tuple]:
        '''
        テンプレートマッチングをする
        画像は必要に応じて事前にグレースケール化やトリミングをしておく必要がある
        '''
        # 比較方式を設定する
        method = cv2.TM_CCORR_NORMED if type(mask_image) == numpy.ndarray else cv2.TM_CCOEFF_NORMED

        # テンプレートマッチングをする
        if self.__use_gpu:    # GPUを使用する場合(マスク非対応)
            print("template matching mode:GPU")
            self.__gsrc.upload(image)
            self.__gtmpl.upload(template_image)
            matcher = cv2.cuda.createTemplateMatching(cv2.CV_8UC1, method)
            self.__gresult = matcher.match(self.__gsrc, self.__gtmpl)
            res = self.gresult.download()
        else:
            res = cv2.matchTemplate(image, template_image, method, mask=mask_image)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)  # 結果から類似度と類似度が最大となる場所を抽出

        return max_val, max_loc

    def isContainTemplate(self, image: numpy.ndarray, template_image: numpy.ndarray, mask_image: numpy.ndarray = None, threshold: float = 0.7, use_gray: bool = True,
                          crop: List[int] = [], BGR_range: Optional[dict] = None, threshold_binary: Optional[int] = None, crop_template: list[int] = [], show_image: bool = False) -> Tuple[bool, tuple, int, int, float]:
        '''
        テンプレートマッチングを行い類似度が閾値を超えているかを確認する
        '''
        # テンプレートマッチング対象画像を加工する
        src, _, _ = doPreprocessImage(image, use_gray=use_gray, crop=crop, BGR_range=BGR_range, threshold_binary=threshold_binary)

        # [DEBUG] テンプレートマッチング対象画像を表示する
        if show_image:
            cv2.imshow("image", src)
            cv2.waitKey()

        # テンプレート画像を加工する
        template, width, height = doPreprocessImage(template_image, use_gray=use_gray, crop=crop_template, BGR_range=BGR_range, threshold_binary=threshold_binary)

        # テンプレートマッチングを行う
        max_val, max_loc = self.doTemplateMatch(src, template, mask_image=mask_image)

        # 類似度が閾値を超えたかを戻り値として返す(合わせて位置とテンプレート画像のサイズも返す)
        return max_val > threshold, max_loc, width, height, max_val

    def isContainTemplate_max(self, image: numpy.ndarray, template_image_list: List[numpy.ndarray], mask_image_list: List[numpy.ndarray] = [], threshold: float = 0.7, use_gray: bool = True,
                              crop: List[int] = [], BGR_range: Optional[dict] = None, threshold_binary: Optional[int] = None, crop_template: list[int] = [], show_image: bool = False) -> Tuple[int, List[float], List[tuple], List[int], List[int], List[bool]]:
        '''
        複数のテンプレート画像を用いてそれぞれテンプレートマッチングを行い類似度が最も大きい画像のindexを返す
        '''
        # パラメータチェックを行う
        if len(template_image_list) == len(mask_image_list):
            mask_image_list_temp = mask_image_list
        if len(mask_image_list) == 0:
            mask_image_list_temp = [None for i in range(len(template_image_list))]
        else:
            print("The number of template images and mask images don't match. ")
            return -1, [], [], [], [], []

        # ループをまわしてテンプレート画像数分テンプレートマッチングを行う
        max_val_list = []
        max_loc_list = []
        width_list = []
        height_list = []
        judge_threshold_list = []

        # テンプレートマッチング対象画像を加工する
        src, _, _ = doPreprocessImage(image, use_gray=use_gray, crop=crop, BGR_range=BGR_range, threshold_binary=threshold_binary)

        # [DEBUG] テンプレートマッチング対象画像を表示する
        if show_image:
            cv2.imshow("image", src)
            cv2.waitKey()

        for template_image, mask_image in zip(template_image_list, mask_image_list_temp):
            # テンプレート画像を加工する
            template, width, height = doPreprocessImage(template_image, use_gray=use_gray, crop=crop_template, BGR_range=BGR_range, threshold_binary=threshold_binary)
            max_val, max_loc = self.doTemplateMatch(src, template, mask_image=mask_image)
            max_val_list.append(max_val)
            max_loc_list.append(max_loc)
            width_list.append(width)
            height_list.append(height)
            judge_threshold_list.append(max_val > threshold)

        return numpy.argmax(max_val_list), max_val_list, max_loc_list, width_list, height_list, judge_threshold_list

    def saveImage(self, image: numpy.ndarray, filename: str = None, crop: List[int] = None):
        '''
        画像を保存する。
        '''
        # トリミングを行う
        cropped_image = crop_image(image, crop=crop)

        # ファイル名からパスを抽出する
        capture_dir = os.path.dirname(filename)

        # 画像保存用ディレクトリの存在を確認し、なかったら作成する。
        if not os.path.exists(capture_dir):
            os.makedirs(capture_dir)
            self.__logger.debug("Created Capture folder")

        # 画像を保存する
        try:
            self.imwrite(filename, cropped_image)
            self.__logger.debug(f"Capture succeeded: {filename}")
            print('capture succeeded: ' + filename)
        except cv2.error as e:
            print("Capture Failed")
            self.__logger.error(f"Capture Failed :{e}")


if __name__ == "__main__":
    ImgProc = ImageProcessing()
    ImgProc.set_template_path("./")
    camera = cv2.VideoCapture(0)
    if camera.isOpened():
        _, image = camera.read()
        ret, _, _, _ = ImgProc.isContainTemplate(image, "test.png")
        print(ret)
        camera.release()
    else:
        pass
