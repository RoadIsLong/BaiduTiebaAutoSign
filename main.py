# -*- coding:utf-8 -*-
import os
import requests
import hashlib
import time
import copy
import logging
import random
from typing import Dict, List, Optional, Union

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('tieba_sign.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# API 地址
TBS_URL = "http://tieba.baidu.com/dc/common/tbs"
LIKIE_URL = "http://c.tieba.baidu.com/c/f/forum/like"
SIGN_URL = "http://c.tieba.baidu.com/c/c/forum/sign"

# 请求头
HEADERS = {
    'Host': 'tieba.baidu.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
    'Connection': 'keep-alive',
    'Accept-Encoding': 'gzip, deflate',
    'Cache-Control': 'no-cache'
}

# 签到基础数据
SIGN_DATA = {
    '_client_type': '2',
    '_client_version': '9.7.8.0',
    '_phone_imei': '000000000000000',
    'model': 'MI+5',
    "net_type": "1",
}

# 常量
COOKIE = "Cookie"
BDUSS = "BDUSS"
EQUAL = r'='
EMPTY_STR = r''
TBS = 'tbs'
PAGE_NO = 'page_no'
ONE = '1'
TIMESTAMP = "timestamp"
DATA = 'data'
FID = 'fid'
SIGN_KEY = 'tiebaclient!!!'
UTF8 = "utf-8"
SIGN = "sign"
KW = "kw"

# 全局会话
s = requests.Session()

def validate_bduss(bduss: str) -> bool:
    """验证BDUSS有效性"""
    return len(bduss) > 20 and '=' not in bduss

def safe_request(
    url: str, 
    method: str = 'get', 
    headers: Optional[Dict] = None, 
    data: Optional[Dict] = None, 
    retry: int = 3,
    delay_base: float = 1.5
) -> requests.Response:
    """
    安全的网络请求封装
    :param url: 请求URL
    :param method: 请求方法(get/post)
    :param headers: 请求头
    :param data: 请求数据
    :param retry: 重试次数
    :param delay_base: 基础延迟时间
    :return: Response对象
    """
    for i in range(retry):
        try:
            if method.lower() == 'get':
                response = s.get(url, headers=headers, timeout=10)
            else:
                response = s.post(url, headers=headers, data=data, timeout=10)
            
            response.raise_for_status()
            
            if not response.text.strip():
                raise ValueError("空响应内容")
                
            return response
        
        except Exception as e:
            logger.warning(f"请求失败(尝试 {i+1}/{retry}): {str(e)}")
            if i < retry - 1:
                wait_time = delay_base * (2 ** i) + random.uniform(0, 1)
                time.sleep(wait_time)
            continue
    
    raise Exception(f"请求失败，已达最大重试次数 {retry}")

def get_json_response(
    url: str, 
    method: str = 'get', 
    headers: Optional[Dict] = None, 
    data: Optional[Dict] = None
) -> Dict:
    """
    获取JSON格式响应
    :return: 解析后的JSON字典
    """
    response = safe_request(url, method, headers, data)
    try:
        return response.json()
    except ValueError as e:
        logger.error(f"JSON解析失败: {e}\n原始响应: {response.text[:200]}")
        raise

def encodeData(data: Dict) -> Dict:
    """
    生成签名参数
    :param data: 原始数据
    :return: 带签名的数据
    """
    s = EMPTY_STR
    for key in sorted(data.keys()):
        s += f"{key}={data[key]}"
    sign = hashlib.md5((s + SIGN_KEY).encode(UTF8)).hexdigest().upper()
    data.update({SIGN: sign})
    return data

def get_tbs(bduss: str) -> str:
    """
    获取tbs令牌
    :param bduss: 用户BDUSS
    :return: tbs字符串
    """
    logger.info("开始获取tbs")
    headers = copy.deepcopy(HEADERS)
    headers.update({COOKIE: f"{BDUSS}={bduss}"})
    
    try:
        result = get_json_response(TBS_URL, headers=headers)
        tbs = result[TBS]
        logger.info("tbs获取成功")
        return tbs
    except Exception as e:
        logger.error(f"获取tbs失败: {e}")
        raise

def get_favorite(bduss: str) -> List[Dict]:
    """
    获取用户关注的贴吧列表
    :param bduss: 用户BDUSS
    :return: 贴吧列表
    """
    logger.info("开始获取关注的贴吧")
    forums = []
    page_no = 1
    page_size = 200
    
    while True:
        data = {
            'BDUSS': bduss,
            '_client_type': '2',
            '_client_id': 'wappc_1534235498291_488',
            '_client_version': '9.7.8.0',
            '_phone_imei': '000000000000000',
            'from': '1008621y',
            'page_no': str(page_no),
            'page_size': str(page_size),
            'model': 'MI+5',
            'net_type': '1',
            'timestamp': str(int(time.time())),
            'vcode_tag': '11',
        }
        data = encodeData(data)
        
        try:
            res = get_json_response(LIKIE_URL, 'post', HEADERS, data)
            
            # 处理返回数据
            if 'forum_list' in res:
                for forum_type in ['non-gconforum', 'gconforum']:
                    if forum_type in res['forum_list']:
                        items = res['forum_list'][forum_type]
                        if isinstance(items, list):
                            forums.extend(items)
                        elif isinstance(items, dict):
                            forums.append(items)
            
            # 检查是否还有更多
            if res.get('has_more') != '1':
                break
                
            page_no += 1
            time.sleep(random.uniform(1, 2))
            
        except Exception as e:
            logger.error(f"获取贴吧列表出错: {e}")
            break
    
    logger.info(f"共获取到 {len(forums)} 个关注的贴吧")
    return forums

def client_sign(
    bduss: str, 
    tbs: str, 
    fid: str, 
    kw: str, 
    idx: int, 
    count: int
) -> Dict:
    """
    执行签到操作
    :param bduss: 用户BDUSS
    :param tbs: tbs令牌
    :param fid: 贴吧fid
    :param kw: 贴吧名称
    :param idx: 当前索引
    :param count: 总贴吧数
    :return: 签到结果
    """
    log_prefix = f"【{kw}】吧({idx+1}/{count})"
    logger.info(f"{log_prefix} 开始签到")
    
    data = copy.deepcopy(SIGN_DATA)
    data.update({
        BDUSS: bduss,
        FID: fid,
        KW: kw,
        TBS: tbs,
        TIMESTAMP: str(int(time.time()))
    })
    data = encodeData(data)
    
    try:
        result = get_json_response(SIGN_URL, 'post', HEADERS, data)
        
        if result.get('error_code') == '0':
            rank = result['user_info']['user_sign_rank']
            msg = f"{log_prefix} 签到成功，第{rank}个签到"
            logger.info(msg)
        elif result.get('error_code') == '160002':
            msg = f"{log_prefix} {result.get('error_msg', '今日已签到')}"
            logger.info(msg)
        else:
            msg = f"{log_prefix} 签到失败，错误: {result.get('error_msg', '未知错误')}"
            logger.warning(msg)
            
        return result
        
    except Exception as e:
        logger.error(f"{log_prefix} 签到异常: {str(e)}")
        return {'error': str(e)}

def smart_delay(last_time: float, base_delay: float = 1.0) -> float:
    """
    智能延迟控制
    :param last_time: 上次请求时间戳
    :param base_delay: 基础延迟时间(秒)
    :return: 新的时间戳
    """
    elapsed = time.time() - last_time
    delay = max(0, base_delay + random.uniform(0.5, 1.5) - elapsed)
    time.sleep(delay)
    return time.time()

def main():
    # 从环境变量获取BDUSS
    bduss_env = os.getenv('BDUSS', '')
    if not bduss_env:
        logger.error("未检测到BDUSS环境变量")
        return
    
    bduss_list = [b.strip() for b in bduss_env.split('#') if validate_bduss(b.strip())]
    if not bduss_list:
        logger.error("没有有效的BDUSS")
        return
    
    logger.info(f"开始处理 {len(bduss_list)} 个用户")
    
    for user_idx, bduss in enumerate(bduss_list, 1):
        user_prefix = f"用户{user_idx}/{len(bduss_list)}"
        logger.info(f"{user_prefix} 开始处理")
        
        try:
            # 获取tbs
            tbs = get_tbs(bduss)
            
            # 获取贴吧列表
            forums = get_favorite(bduss)
            if not forums:
                logger.info(f"{user_prefix} 没有获取到关注的贴吧")
                continue
                
            total_forums = len(forums)
            last_request_time = time.time()
            
            # 逐个贴吧签到
            for forum_idx, forum in enumerate(forums, 1):
                last_request_time = smart_delay(last_request_time)
                
                # 每10个贴吧增加额外延迟
                if forum_idx % 10 == 0:
                    extra_delay = random.uniform(5, 10)
                    time.sleep(extra_delay)
                
                client_sign(
                    bduss=bduss,
                    tbs=tbs,
                    fid=forum['id'],
                    kw=forum['name'],
                    idx=forum_idx-1,
                    count=total_forums
                )
                
            logger.info(f"{user_prefix} 处理完成")
            
        except Exception as e:
            logger.error(f"{user_prefix} 处理过程中出错: {str(e)}")
            continue
    
    logger.info("所有用户处理完成")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
