"""
WMEmail供应商测试脚本
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.wmemail_provider import WMEmailProvider
from utils.email_manager import EmailManagerFactory

def test_wmemail_connection():
    """测试WMEmail连接"""
    print("=" * 50)
    print("🧪 测试WMEmail API连接")
    print("=" * 50)
    
    try:
        provider = WMEmailProvider()
        
        # 测试连接
        if provider.test_connection():
            print("✅ WMEmail API连接成功")
            
            # 查询余额
            balance = provider.get_balance()
            print(f"💰 当前余额: {balance}")
            
            # 获取商品列表
            goods = provider.get_goods_list()
            print(f"📦 可用商品数量: {len(goods)}")
            
            # 显示前5个商品
            print("\n📋 商品列表 (前5个):")
            for i, item in enumerate(goods[:5], 1):
                print(f"  {i}. {item.get('name')} (ID: {item.get('id')}, 库存: {item.get('card_count')})")
            
            # 查找Hotmail商品
            hotmail_id = provider.find_hotmail_commodity()
            if hotmail_id:
                print(f"\n📧 找到Hotmail商品ID: {hotmail_id}")
            else:
                print("\n⚠️  未找到Hotmail商品")
            
            return True
            
        else:
            print("❌ WMEmail API连接失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_email_manager_factory():
    """测试邮箱管理器工厂"""
    print("\n" + "=" * 50)
    print("🧪 测试邮箱管理器工厂")
    print("=" * 50)
    
    try:
        # 测试获取商品列表
        goods = EmailManagerFactory.get_wmemail_goods_list()
        print(f"✅ 通过工厂获取到 {len(goods)} 个商品")
        
        # 测试获取余额
        balance = EmailManagerFactory.get_wmemail_balance()
        print(f"✅ 通过工厂获取余额: {balance}")
        
        return True
        
    except Exception as e:
        print(f"❌ 工厂测试失败: {e}")
        return False

def test_purchase_simulation():
    """模拟购买测试（不实际购买）"""
    print("\n" + "=" * 50)
    print("🧪 模拟购买测试")
    print("=" * 50)
    
    try:
        provider = WMEmailProvider()
        
        # 查找Hotmail商品
        hotmail_id = provider.find_hotmail_commodity()
        if not hotmail_id:
            print("⚠️  跳过购买测试：未找到Hotmail商品")
            return True
        
        # 检查余额
        balance = provider.get_balance()
        if balance is None or balance <= 0:
            print("⚠️  跳过购买测试：余额不足")
            return True
        
        print(f"💡 模拟购买商品ID: {hotmail_id}")
        print(f"💰 当前余额: {balance}")
        print("ℹ️  实际购买需要调用 provider.purchase_email(hotmail_id)")
        
        return True
        
    except Exception as e:
        print(f"❌ 模拟购买测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 WMEmail供应商测试开始")
    
    # 检查环境变量
    token = os.getenv('WMEMAIL_TOKEN')
    if not token:
        print("❌ 错误: 未设置WMEMAIL_TOKEN环境变量")
        print("请在.env文件中设置: WMEMAIL_TOKEN=your_token_here")
        return
    
    print(f"🔑 使用Token: {token[:10]}...")
    
    # 运行测试
    tests = [
        ("连接测试", test_wmemail_connection),
        ("工厂测试", test_email_manager_factory),
        ("模拟购买测试", test_purchase_simulation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}异常: {e}")
            results.append((test_name, False))
    
    # 显示测试结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 个测试通过")
    
    if passed == len(results):
        print("🎉 所有测试通过！WMEmail供应商配置正确")
    else:
        print("⚠️  部分测试失败，请检查配置")

if __name__ == "__main__":
    main()
