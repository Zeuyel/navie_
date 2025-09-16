"""
WMEmail邮件供应商
API文档: https://www.wmemail.com/doc.html
"""

import requests
import logging
import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class WMEmailAccount:
    """WMEmail账号信息"""
    email: str
    password: str
    trade_no: str
    commodity_id: int
    amount: float

class WMEmailProvider:
    """WMEmail邮件供应商"""
    
    def __init__(self, token: str = None):
        """
        初始化WMEmail供应商
        
        Args:
            token: 商家密钥，如果不提供则从环境变量获取
        """
        self.token = token or os.getenv('WMEMAIL_TOKEN')
        if not self.token:
            raise ValueError("WMEmail token未配置，请设置WMEMAIL_TOKEN环境变量")
        
        self.base_url = "https://www.wmemail.com/user/api/api"
        self.session = requests.Session()
        
        # 设置请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        
        logger.info("WMEmail供应商初始化完成")
    
    def get_goods_list(self) -> List[Dict]:
        """
        获取商品列表
        
        Returns:
            商品列表
        """
        try:
            url = f"{self.base_url}/goods"
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            if data.get('code') == 200:
                logger.info(f"获取到 {len(data.get('data', []))} 个商品")
                return data.get('data', [])
            else:
                logger.error(f"获取商品列表失败: {data.get('msg', '未知错误')}")
                return []
                
        except Exception as e:
            logger.error(f"获取商品列表异常: {e}")
            return []
    
    def get_balance(self) -> Optional[float]:
        """
        查询余额
        
        Returns:
            余额金额，失败返回None
        """
        try:
            url = f"{self.base_url}/balance"
            data = {'token': self.token}
            
            response = self.session.post(url, data=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') == 200:
                balance = result.get('data', {}).get('balance', 0)
                logger.info(f"当前余额: {balance}")
                return float(balance)
            else:
                logger.error(f"查询余额失败: {result.get('msg', '未知错误')}")
                return None
                
        except Exception as e:
            logger.error(f"查询余额异常: {e}")
            return None
    
    def purchase_email(self, commodity_id: int, num: int = 1) -> Optional[WMEmailAccount]:
        """
        购买邮箱账号
        
        Args:
            commodity_id: 商品ID
            num: 购买数量，默认1
            
        Returns:
            邮箱账号信息，失败返回None
        """
        try:
            url = f"{self.base_url}/trade"
            data = {
                'commodity_id': commodity_id,
                'num': num,
                'token': self.token
            }
            
            response = self.session.post(url, data=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') == 200:
                trade_data = result.get('data', {})
                secret = trade_data.get('secret', '')
                
                # 解析secret字段，格式通常为: email----password
                if '----' in secret:
                    email, password = secret.split('----', 1)
                    
                    account = WMEmailAccount(
                        email=email.strip(),
                        password=password.strip(),
                        trade_no=trade_data.get('tradeNo', ''),
                        commodity_id=commodity_id,
                        amount=float(trade_data.get('amount', 0))
                    )
                    
                    logger.info(f"成功购买邮箱: {account.email}")
                    return account
                else:
                    logger.error(f"无法解析账号信息: {secret}")
                    return None
            else:
                logger.error(f"购买邮箱失败: {result.get('msg', '未知错误')}")
                return None
                
        except Exception as e:
            logger.error(f"购买邮箱异常: {e}")
            return None
    
    def find_hotmail_commodity(self) -> Optional[int]:
        """
        查找Hotmail商品ID
        
        Returns:
            Hotmail商品ID，未找到返回None
        """
        goods_list = self.get_goods_list()
        
        for goods in goods_list:
            name = goods.get('name', '').lower()
            if 'hotmail' in name and goods.get('card_count', 0) > 0:
                logger.info(f"找到Hotmail商品: {goods.get('name')} (ID: {goods.get('id')})")
                return goods.get('id')
        
        logger.warning("未找到可用的Hotmail商品")
        return None
    
    def get_hotmail_account(self) -> Optional[WMEmailAccount]:
        """
        获取一个Hotmail账号
        
        Returns:
            Hotmail账号信息，失败返回None
        """
        # 查找Hotmail商品
        commodity_id = self.find_hotmail_commodity()
        if not commodity_id:
            return None
        
        # 检查余额
        balance = self.get_balance()
        if balance is None or balance <= 0:
            logger.error("余额不足，无法购买邮箱")
            return None
        
        # 购买邮箱
        return self.purchase_email(commodity_id)
    
    def test_connection(self) -> bool:
        """
        测试API连接
        
        Returns:
            连接是否成功
        """
        try:
            balance = self.get_balance()
            return balance is not None
        except Exception as e:
            logger.error(f"连接测试失败: {e}")
            return False

# 工厂函数
def create_wmemail_provider() -> WMEmailProvider:
    """创建WMEmail供应商实例"""
    return WMEmailProvider()

if __name__ == "__main__":
    # 测试代码
    provider = create_wmemail_provider()
    
    # 测试连接
    if provider.test_connection():
        print("✅ WMEmail API连接成功")
        
        # 获取商品列表
        goods = provider.get_goods_list()
        for item in goods[:3]:  # 只显示前3个
            print(f"商品: {item.get('name')} (库存: {item.get('card_count')})")
        
        # 查询余额
        balance = provider.get_balance()
        print(f"余额: {balance}")
        
    else:
        print("❌ WMEmail API连接失败")
