"""
状态管理器 - 改进版状态管理系统
"""

import logging
from enum import Enum
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class RegistrationState(Enum):
    """注册状态枚举"""
    INIT = "init"
    BROWSER_INITIALIZING = "browser_initializing"
    BROWSER_READY = "browser_ready"
    FORM_FILLING = "form_filling"
    FORM_SUBMITTED = "form_submitted"
    CAPTCHA_PENDING = "captcha_pending"
    CAPTCHA_SOLVING = "captcha_solving"
    CAPTCHA_COMPLETED = "captcha_completed"
    EMAIL_VERIFICATION = "email_verification"
    COMPLETED = "completed"
    ERROR = "error"
    PAUSED = "paused"

@dataclass
class StateTransition:
    """状态转换记录"""
    from_state: RegistrationState
    to_state: RegistrationState
    timestamp: datetime
    trigger_event: str
    data: Dict[str, Any] = field(default_factory=dict)

class StateManager:
    """改进版状态管理器"""
    
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.current_state = RegistrationState.INIT
        self.state_data: Dict[str, Any] = {}
        self.state_history: List[StateTransition] = []
        self.state_listeners: Dict[RegistrationState, List[Callable]] = {}
        
        # 状态转换规则
        self.transition_rules = self._setup_transition_rules()
        
        # 订阅状态转换事件
        self._setup_state_subscriptions()
        
        logger.info("StateManager 初始化完成")
    
    def _setup_transition_rules(self) -> Dict[str, RegistrationState]:
        """设置状态转换规则"""
        return {
            # 浏览器相关
            'browser_init_started': RegistrationState.BROWSER_INITIALIZING,
            'browser_ready': RegistrationState.BROWSER_READY,
            
            # 表单相关
            'form_filling_started': RegistrationState.FORM_FILLING,
            'form_submitted': RegistrationState.FORM_SUBMITTED,
            
            # 验证码相关
            'captcha_detected': RegistrationState.CAPTCHA_PENDING,
            'captcha_solving_started': RegistrationState.CAPTCHA_SOLVING,
            'captcha_completed': RegistrationState.CAPTCHA_COMPLETED,
            
            # 邮箱验证
            'email_verification_required': RegistrationState.EMAIL_VERIFICATION,
            
            # 完成和错误
            'registration_completed': RegistrationState.COMPLETED,
            'error_occurred': RegistrationState.ERROR,
            'process_paused': RegistrationState.PAUSED,
        }
    
    def _setup_state_subscriptions(self):
        """设置状态转换事件订阅"""
        for event_name in self.transition_rules.keys():
            self.event_bus.subscribe(event_name, self._handle_state_transition)
    
    async def _handle_state_transition(self, event):
        """处理状态转换"""
        event_name = event.name
        
        if event_name in self.transition_rules:
            new_state = self.transition_rules[event_name]
            await self.transition_to(new_state, event_name, event.data)
    
    async def transition_to(self, new_state: RegistrationState, trigger_event: str = "", data: Dict[str, Any] = None):
        """状态转换"""
        if data is None:
            data = {}
        
        old_state = self.current_state
        
        # 检查状态转换是否有效
        if not self._is_valid_transition(old_state, new_state):
            logger.warning(f"无效的状态转换: {old_state.value} -> {new_state.value}")
            return False
        
        # 记录状态转换
        transition = StateTransition(
            from_state=old_state,
            to_state=new_state,
            timestamp=datetime.now(),
            trigger_event=trigger_event,
            data=data
        )
        self.state_history.append(transition)
        
        # 更新当前状态
        self.current_state = new_state
        
        logger.info(f"状态转换: {old_state.value} -> {new_state.value} (触发: {trigger_event})")
        
        # 通知状态监听器
        await self._notify_state_listeners(new_state, transition)
        
        # 发布状态变更事件
        from .event_bus import create_event
        state_change_event = create_event(
            name='state_changed',
            data={
                'old_state': old_state.value,
                'new_state': new_state.value,
                'trigger_event': trigger_event,
                'transition_data': data
            },
            source='StateManager'
        )
        await self.event_bus.publish(state_change_event)
        
        return True
    
    def _is_valid_transition(self, from_state: RegistrationState, to_state: RegistrationState) -> bool:
        """检查状态转换是否有效"""
        # 错误状态可以从任何状态转换
        if to_state == RegistrationState.ERROR:
            return True
        
        # 暂停状态可以从任何状态转换（除了完成和错误）
        if to_state == RegistrationState.PAUSED and from_state not in [RegistrationState.COMPLETED, RegistrationState.ERROR]:
            return True
        
        # 从暂停状态可以转换回之前的状态
        if from_state == RegistrationState.PAUSED:
            return True
        
        # 定义有效的状态转换路径
        valid_transitions = {
            RegistrationState.INIT: [RegistrationState.BROWSER_INITIALIZING],
            RegistrationState.BROWSER_INITIALIZING: [RegistrationState.BROWSER_READY],
            RegistrationState.BROWSER_READY: [RegistrationState.FORM_FILLING],
            RegistrationState.FORM_FILLING: [RegistrationState.FORM_SUBMITTED],
            RegistrationState.FORM_SUBMITTED: [RegistrationState.CAPTCHA_PENDING, RegistrationState.EMAIL_VERIFICATION, RegistrationState.COMPLETED],
            RegistrationState.CAPTCHA_PENDING: [RegistrationState.CAPTCHA_SOLVING],
            RegistrationState.CAPTCHA_SOLVING: [RegistrationState.CAPTCHA_COMPLETED, RegistrationState.CAPTCHA_PENDING],  # 可能需要多轮
            RegistrationState.CAPTCHA_COMPLETED: [RegistrationState.EMAIL_VERIFICATION, RegistrationState.COMPLETED],
            RegistrationState.EMAIL_VERIFICATION: [RegistrationState.COMPLETED],
            RegistrationState.COMPLETED: [],  # 终态
            RegistrationState.ERROR: [],  # 终态
        }
        
        allowed_states = valid_transitions.get(from_state, [])
        return to_state in allowed_states
    
    def add_state_listener(self, state: RegistrationState, listener: Callable):
        """添加状态监听器"""
        if state not in self.state_listeners:
            self.state_listeners[state] = []
        self.state_listeners[state].append(listener)
        logger.info(f"添加状态监听器: {state.value} -> {listener.__name__}")
    
    async def _notify_state_listeners(self, state: RegistrationState, transition: StateTransition):
        """通知状态监听器"""
        if state in self.state_listeners:
            for listener in self.state_listeners[state]:
                try:
                    if asyncio.iscoroutinefunction(listener):
                        await listener(transition)
                    else:
                        listener(transition)
                except Exception as e:
                    logger.error(f"状态监听器 {listener.__name__} 执行失败: {e}")
    
    def get_state(self) -> RegistrationState:
        """获取当前状态"""
        return self.current_state
    
    def set_data(self, key: str, value: Any):
        """设置状态数据"""
        self.state_data[key] = value
        logger.debug(f"设置状态数据: {key} = {value}")
    
    def get_data(self, key: str, default=None):
        """获取状态数据"""
        return self.state_data.get(key, default)
    
    def update_data(self, data: Dict[str, Any]):
        """批量更新状态数据"""
        self.state_data.update(data)
        logger.debug(f"批量更新状态数据: {list(data.keys())}")
    
    def remove_data(self, key: str):
        """移除状态数据"""
        if key in self.state_data:
            del self.state_data[key]
            logger.debug(f"移除状态数据: {key}")
    
    def get_all_data(self) -> Dict[str, Any]:
        """获取所有状态数据"""
        return self.state_data.copy()
    
    def get_state_history(self, limit: int = 50) -> List[StateTransition]:
        """获取状态历史"""
        return self.state_history[-limit:]
    
    def get_current_state_duration(self) -> float:
        """获取当前状态持续时间（秒）"""
        if not self.state_history:
            return 0.0
        
        last_transition = self.state_history[-1]
        return (datetime.now() - last_transition.timestamp).total_seconds()
    
    def export_state_data(self) -> str:
        """导出状态数据为JSON"""
        export_data = {
            'current_state': self.current_state.value,
            'state_data': self.state_data,
            'state_history': [
                {
                    'from_state': t.from_state.value,
                    'to_state': t.to_state.value,
                    'timestamp': t.timestamp.isoformat(),
                    'trigger_event': t.trigger_event,
                    'data': t.data
                }
                for t in self.state_history
            ]
        }
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取状态管理器统计信息"""
        return {
            'current_state': self.current_state.value,
            'state_data_keys': list(self.state_data.keys()),
            'transition_count': len(self.state_history),
            'current_state_duration': self.get_current_state_duration(),
            'listeners_count': sum(len(listeners) for listeners in self.state_listeners.values())
        }
