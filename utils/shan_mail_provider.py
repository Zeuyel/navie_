#!/usr/bin/env python3
"""
闪邮箱 API 提供者
用于从 https://zizhu.shanyouxiang.com/ 获取邮箱账号
"""

import requests
import json
from typing import Dict, List, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ShanMailProvider:
    """闪邮箱 API 提供者"""
    
    def __init__(self, card_key: str):
        self.base_url = "https://zizhu.shanyouxiang.com"
        self.card_key = card_key
        self.session = requests.Session()
        self.session.timeout = 30
    
    def get_stock(self) -> Optional[Dict[str, int]]:
        """
        查询库存
        返回: {"hotmail": 数量, "outlook": 数量} 或 None
        """
        try:
            url = f"{self.base_url}/kucun"
            response = self.session.get(url)
            response.raise_for_status()
            
            # 假设返回格式为 JSON，如果是文本需要解析
            data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {"raw": response.text}
            logger.info(f"库存查询成功: {data}")
            return data
            
        except Exception as e:
            logger.error(f"查询库存失败: {e}")
            return None
    
    def get_balance(self) -> Optional[int]:
        """
        查询余额
        返回: 剩余可提取数量 或 None
        """
        try:
            url = f"{self.base_url}/yue"
            params = {"card": self.card_key}
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            # 尝试解析返回的余额数字
            # text = response.text.strip()
            data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {"raw": response.text}
            print(data)
            if isinstance(data["num"], int):
                balance = data["num"]
                logger.info(f"余额查询成功: {balance}")
                return balance
            else:
                logger.warning(f"余额返回格式异常: {data}")
                return None
                
        except Exception as e:
            logger.error(f"查询余额失败: {e}")
            return None
    
    def fetch_emails(self, count: int = 1, email_type: str = "outlook") -> Optional[List[str]]:
        """
        提取邮箱账号
        
        Args:
            count: 提取数量
            email_type: 邮箱类型 ("outlook" 或 "hotmail")
        
        Returns:
            邮箱账号列表，格式: ["邮箱----密码----令牌----client_id", ...]
            或 None 如果失败
        """
        try:
            url = f"{self.base_url}/huoqu"
            params = {
                "card": self.card_key,
                "shuliang": count,
                "leixing": email_type
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            # 解析返回的邮箱账号
            text = response.text.strip()
            if not text:
                logger.warning("接口返回空内容")
                return None
            
            # 按行分割，每行一个账号
            email_lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            if not email_lines:
                logger.warning("未获取到有效的邮箱账号")
                return None
            
            logger.info(f"成功获取 {len(email_lines)} 个邮箱账号")
            return email_lines
            
        except Exception as e:
            logger.error(f"提取邮箱失败: {e}")
            return None
    
    def parse_email_token(self, email_token: str) -> Optional[Dict[str, str]]:
        """
        解析邮箱 token 字符串

        Args:
            email_token: "邮箱----密码----令牌----client_id" 格式的字符串

        Returns:
            {"email": "...", "password": "...", "access_token": "...", "client_id": "..."}
            或 None 如果解析失败
        """
        try:
            # 分割字符串，使用实际的分隔符 ----
            parts = email_token.split('----')

            if len(parts) != 4:
                logger.error(f"邮箱 token 格式错误，期望4个部分，实际{len(parts)}个: {email_token}")
                return None

            return {
                "email": parts[0].strip(),
                "password": parts[1].strip(),
                "access_token": parts[2].strip(),  # 实际是 refresh_token
                "client_id": parts[3].strip()
            }

        except Exception as e:
            logger.error(f"解析邮箱 token 失败: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        测试连接和认证
        通过查询余额来验证 card_key 是否有效
        """
        balance = self.get_balance()
        return balance is not None

if __name__ == "__main__":
    # 测试代码
    import os
    
    card_key = os.getenv("SHAN_MAIL_CARD_KEY", "")
    if not card_key:
        print("请设置环境变量 SHAN_MAIL_CARD_KEY")
        exit(1)
    
    provider = ShanMailProvider(card_key)
    
    print("测试连接...")
    if provider.test_connection():
        print("✓ 连接成功")
        
        print("\n查询库存...")
        stock = provider.get_stock()
        if stock:
            print(f"库存: {stock}")
        
        print("\n查询余额...")
        balance = provider.get_balance()
        if balance is not None:
            print(f"余额: {balance}")
        
        print("\n提取1个邮箱...")
        emails = provider.fetch_emails(1, "outlook")
        if emails:
            print(f"获取到邮箱: {emails}")
            
            # 测试解析
            parsed = provider.parse_email_token(emails[0])
            if parsed:
                print(f"解析结果: {parsed}")
    else:
        print("✗ 连接失败")
