"""
事件总线 - 改进版事件发布订阅系统
"""

import asyncio
import logging
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class EventPriority(Enum):
    """事件优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Event:
    """事件数据类"""
    name: str
    data: Dict[str, Any]
    timestamp: datetime
    source: str
    priority: EventPriority = EventPriority.NORMAL
    event_id: str = None
    
    def __post_init__(self):
        if not self.event_id:
            import uuid
            self.event_id = str(uuid.uuid4())

@dataclass
class EventSubscription:
    """事件订阅信息"""
    event_name: str
    handler: Callable
    handler_name: str
    priority: EventPriority = EventPriority.NORMAL
    once: bool = False  # 是否只执行一次
    condition: Callable[[Event], bool] = None  # 执行条件

class EventBus:
    """改进版事件总线"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[EventSubscription]] = {}
        self._event_history: List[Event] = []
        self._max_history = 1000  # 最大历史记录数
        self._middleware: List[Callable[[Event], Event]] = []
        
        logger.info("EventBus 初始化完成")
    
    def subscribe(self, event_name: str, handler: Callable, 
                 priority: EventPriority = EventPriority.NORMAL,
                 once: bool = False,
                 condition: Callable[[Event], bool] = None):
        """订阅事件"""
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        
        subscription = EventSubscription(
            event_name=event_name,
            handler=handler,
            handler_name=handler.__name__,
            priority=priority,
            once=once,
            condition=condition
        )
        
        self._subscribers[event_name].append(subscription)
        
        # 按优先级排序
        self._subscribers[event_name].sort(key=lambda x: x.priority.value, reverse=True)
        
        logger.info(f"订阅事件: {event_name} -> {handler.__name__} (优先级: {priority.name})")
    
    def unsubscribe(self, event_name: str, handler: Callable):
        """取消订阅"""
        if event_name in self._subscribers:
            self._subscribers[event_name] = [
                sub for sub in self._subscribers[event_name] 
                if sub.handler != handler
            ]
            logger.info(f"取消订阅: {event_name} -> {handler.__name__}")
    
    def add_middleware(self, middleware: Callable[[Event], Event]):
        """添加中间件"""
        self._middleware.append(middleware)
        logger.info(f"添加中间件: {middleware.__name__}")
    
    async def publish(self, event: Event):
        """发布事件"""
        # 应用中间件
        for middleware in self._middleware:
            try:
                event = middleware(event)
            except Exception as e:
                logger.error(f"中间件 {middleware.__name__} 处理失败: {e}")
        
        # 记录事件历史
        self._add_to_history(event)
        
        logger.info(f"发布事件: {event.name} (ID: {event.event_id}) from {event.source}")
        
        if event.name in self._subscribers:
            # 创建订阅者副本，避免在执行过程中修改
            subscribers = self._subscribers[event.name].copy()
            
            # 需要移除的一次性订阅者
            to_remove = []
            
            for subscription in subscribers:
                try:
                    # 检查执行条件
                    if subscription.condition and not subscription.condition(event):
                        continue
                    
                    # 执行处理器
                    if asyncio.iscoroutinefunction(subscription.handler):
                        await subscription.handler(event)
                    else:
                        subscription.handler(event)
                    
                    # 标记一次性订阅者待移除
                    if subscription.once:
                        to_remove.append(subscription)
                        
                except Exception as e:
                    logger.error(f"事件处理器 {subscription.handler_name} 执行失败: {e}")
            
            # 移除一次性订阅者
            for subscription in to_remove:
                self._subscribers[event.name].remove(subscription)
                logger.info(f"移除一次性订阅者: {event.name} -> {subscription.handler_name}")
    
    async def publish_and_wait(self, event: Event, timeout: float = 30.0) -> List[Any]:
        """发布事件并等待所有处理器完成，返回结果列表"""
        # 应用中间件
        for middleware in self._middleware:
            try:
                event = middleware(event)
            except Exception as e:
                logger.error(f"中间件 {middleware.__name__} 处理失败: {e}")
        
        # 记录事件历史
        self._add_to_history(event)
        
        logger.info(f"发布事件并等待: {event.name} (ID: {event.event_id}) from {event.source}")
        
        results = []
        
        if event.name in self._subscribers:
            subscribers = self._subscribers[event.name].copy()
            to_remove = []
            
            # 收集所有异步任务
            tasks = []
            
            for subscription in subscribers:
                try:
                    # 检查执行条件
                    if subscription.condition and not subscription.condition(event):
                        continue
                    
                    if asyncio.iscoroutinefunction(subscription.handler):
                        task = asyncio.create_task(subscription.handler(event))
                        tasks.append((task, subscription))
                    else:
                        # 同步处理器直接执行
                        result = subscription.handler(event)
                        results.append(result)
                    
                    # 标记一次性订阅者待移除
                    if subscription.once:
                        to_remove.append(subscription)
                        
                except Exception as e:
                    logger.error(f"事件处理器 {subscription.handler_name} 执行失败: {e}")
                    results.append(None)
            
            # 等待所有异步任务完成
            if tasks:
                try:
                    completed_tasks = await asyncio.wait_for(
                        asyncio.gather(*[task for task, _ in tasks], return_exceptions=True),
                        timeout=timeout
                    )
                    results.extend(completed_tasks)
                except asyncio.TimeoutError:
                    logger.error(f"事件处理超时: {event.name}")
                    # 取消未完成的任务
                    for task, subscription in tasks:
                        if not task.done():
                            task.cancel()
                            logger.warning(f"取消超时任务: {subscription.handler_name}")
            
            # 移除一次性订阅者
            for subscription in to_remove:
                self._subscribers[event.name].remove(subscription)
                logger.info(f"移除一次性订阅者: {event.name} -> {subscription.handler_name}")
        
        return results
    
    def _add_to_history(self, event: Event):
        """添加事件到历史记录"""
        self._event_history.append(event)
        
        # 限制历史记录数量
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
    
    def get_event_history(self, event_name: str = None, limit: int = 100) -> List[Event]:
        """获取事件历史"""
        if event_name:
            filtered_events = [e for e in self._event_history if e.name == event_name]
        else:
            filtered_events = self._event_history
        
        return filtered_events[-limit:]
    
    def get_subscribers(self, event_name: str = None) -> Dict[str, List[str]]:
        """获取订阅者信息"""
        if event_name:
            if event_name in self._subscribers:
                return {event_name: [sub.handler_name for sub in self._subscribers[event_name]]}
            else:
                return {}
        else:
            return {
                name: [sub.handler_name for sub in subs] 
                for name, subs in self._subscribers.items()
            }
    
    def clear_history(self):
        """清空事件历史"""
        self._event_history.clear()
        logger.info("事件历史已清空")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取事件总线统计信息"""
        return {
            'total_subscribers': sum(len(subs) for subs in self._subscribers.values()),
            'event_types': len(self._subscribers),
            'history_count': len(self._event_history),
            'middleware_count': len(self._middleware),
            'subscriber_details': {
                name: len(subs) for name, subs in self._subscribers.items()
            }
        }

# 便捷函数
def create_event(name: str, data: Dict[str, Any], source: str, 
                priority: EventPriority = EventPriority.NORMAL) -> Event:
    """创建事件的便捷函数"""
    return Event(
        name=name,
        data=data,
        timestamp=datetime.now(),
        source=source,
        priority=priority
    )
