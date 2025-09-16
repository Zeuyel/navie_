"""
任务管理器 - 核心任务调度和管理
"""

import asyncio
import logging
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"          # 等待执行
    RUNNING = "running"          # 正在执行
    COMPLETED = "completed"      # 执行完成
    FAILED = "failed"           # 执行失败
    CANCELLED = "cancelled"      # 已取消
    SKIPPED = "skipped"         # 已跳过

@dataclass
class TaskResult:
    """任务执行结果"""
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    should_retry: bool = False
    next_tasks: List[str] = field(default_factory=list)  # 触发的下一个任务

@dataclass
class Task:
    """任务基类"""
    task_id: str
    name: str
    handler: Callable
    dependencies: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 0  # 生产环境为0，开发环境可设置
    timeout: float = 30.0
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[TaskResult] = None
    error: Optional[str] = None
    is_loop_task: bool = False  # 标记循环任务，防止初始化时自动入队
    
    def __post_init__(self):
        if not self.task_id:
            self.task_id = str(uuid.uuid4())

class TaskManager:
    """任务管理器"""
    
    def __init__(self, event_bus, state_manager, max_concurrent_tasks: int = 3):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.max_concurrent_tasks = max_concurrent_tasks
        
        # 任务存储
        self.tasks: Dict[str, Task] = {}
        self.task_queue = asyncio.Queue()
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.completed_tasks: List[str] = []
        self.failed_tasks: Dict[str, str] = {}
        self.queued_tasks: set = set()  # 跟踪已入队的任务，避免重复
        
        # 依赖关系图
        self.dependency_graph: Dict[str, List[str]] = {}
        self.reverse_dependencies: Dict[str, List[str]] = {}
        
        # 控制标志
        self.is_running = False
        self.is_paused = False
        
        logger.info("TaskManager 初始化完成")

    def reset_all_tasks(self):
        """重置所有任务状态，清理残留状态"""
        logger.info("开始重置所有任务状态...")

        reset_count = 0
        for task_id, task in self.tasks.items():
            if task.status != TaskStatus.PENDING:
                logger.info(f"重置任务状态: {task.name} ({task.status.value} → PENDING)")
                task.status = TaskStatus.PENDING
                task.started_at = None
                task.completed_at = None
                task.result = None
                task.error = None
                task.retry_count = 0
                reset_count += 1

        # 清理运行时状态
        self.running_tasks.clear()
        self.completed_tasks.clear()
        self.failed_tasks.clear()
        self.queued_tasks.clear()

        # 清空任务队列
        while not self.task_queue.empty():
            try:
                self.task_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        logger.info(f"任务状态重置完成，共重置 {reset_count} 个任务")

    async def _safe_enqueue_task(self, task_id: str) -> bool:
        """安全地将任务加入队列，避免重复入队"""
        if task_id not in self.tasks:
            logger.warning(f"尝试入队不存在的任务: {task_id}")
            return False

        task = self.tasks[task_id]

        # 检查任务状态，避免重复入队
        if task.status in [TaskStatus.RUNNING, TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            logger.info(f"任务 {task.name} 状态为 {task.status.value}，跳过入队")
            return False

        # 检查是否已在队列中
        if task_id in self.queued_tasks:
            logger.info(f"任务 {task.name} 已在队列中，跳过重复入队")
            return False

        # 检查是否正在运行
        if task_id in self.running_tasks:
            logger.info(f"任务 {task.name} 正在运行，跳过入队")
            return False

        # 安全入队
        self.queued_tasks.add(task_id)
        await self.task_queue.put(task_id)
        logger.info(f"任务 {task.name} 已成功入队")
        return True

    def register_task(self, task: Task):
        """注册任务"""
        self.tasks[task.task_id] = task

        # 构建依赖关系图
        self.dependency_graph[task.task_id] = task.dependencies.copy()

        # 构建反向依赖关系
        for dep_id in task.dependencies:
            if dep_id not in self.reverse_dependencies:
                self.reverse_dependencies[dep_id] = []
            self.reverse_dependencies[dep_id].append(task.task_id)

        logger.info(f"注册任务: {task.name} (ID: {task.task_id})")

        # 只有非循环任务且无依赖时才立即入队
        if not task.dependencies and not task.is_loop_task:
            asyncio.create_task(self._safe_enqueue_task(task.task_id))
    
    def register_tasks(self, tasks: List[Task]):
        """批量注册任务"""
        for task in tasks:
            self.register_task(task)
    
    async def start(self):
        """启动任务管理器"""
        if self.is_running:
            logger.warning("TaskManager 已在运行中")
            return
        
        self.is_running = True
        logger.info("TaskManager 启动")
        
        # 启动任务执行循环
        await self._task_execution_loop()
    
    async def stop(self):
        """停止任务管理器"""
        self.is_running = False
        
        # 取消所有正在运行的任务
        for task_id, async_task in self.running_tasks.items():
            async_task.cancel()
            logger.info(f"取消任务: {task_id}")
        
        self.running_tasks.clear()
        logger.info("TaskManager 已停止")
    
    async def pause(self):
        """暂停任务执行"""
        self.is_paused = True
        logger.info("TaskManager 已暂停")
    
    async def resume(self):
        """恢复任务执行"""
        self.is_paused = False
        logger.info("TaskManager 已恢复")
    
    async def _task_execution_loop(self):
        """任务执行主循环"""
        while self.is_running:
            try:
                # 如果暂停，等待恢复
                if self.is_paused:
                    await asyncio.sleep(1)
                    continue
                
                # 如果正在运行的任务数量达到上限，等待
                if len(self.running_tasks) >= self.max_concurrent_tasks:
                    await asyncio.sleep(0.5)
                    continue
                
                # 从队列获取任务
                try:
                    task_id = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                    # 从队列跟踪中移除
                    self.queued_tasks.discard(task_id)
                except asyncio.TimeoutError:
                    continue

                # 执行任务
                await self._execute_task(task_id)
                
            except Exception as e:
                logger.error(f"任务执行循环异常: {e}")
                await asyncio.sleep(1)
    
    async def _execute_task(self, task_id: str):
        """执行单个任务"""
        if task_id not in self.tasks:
            logger.error(f"任务不存在: {task_id}")
            return
        
        task = self.tasks[task_id]
        
        # 检查依赖是否满足
        if not self._check_dependencies(task_id):
            logger.warning(f"任务依赖未满足，重新加入队列: {task.name}")
            await self._safe_enqueue_task(task_id)
            return
        
        # 更新任务状态
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        logger.info(f"开始执行任务: {task.name} (ID: {task_id})")
        
        # 创建异步任务执行
        async_task = asyncio.create_task(self._run_task_handler(task))
        self.running_tasks[task_id] = async_task
        
        # 等待任务完成
        try:
            result = await async_task
            await self._handle_task_completion(task, result)
        except asyncio.CancelledError:
            task.status = TaskStatus.CANCELLED
            logger.info(f"任务被取消: {task.name}")
        except Exception as e:
            await self._handle_task_error(task, str(e))
        finally:
            # 清理运行中的任务
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
    
    async def _run_task_handler(self, task: Task) -> TaskResult:
        """运行任务处理器"""
        try:
            # 设置超时
            result = await asyncio.wait_for(
                task.handler(self.state_manager, self.event_bus),
                timeout=task.timeout
            )
            return result
        except asyncio.TimeoutError:
            raise Exception(f"任务超时: {task.timeout}秒")
    
    def _check_dependencies(self, task_id: str) -> bool:
        """检查任务依赖是否满足"""
        dependencies = self.dependency_graph.get(task_id, [])
        
        for dep_id in dependencies:
            if dep_id not in self.completed_tasks:
                return False
        
        return True
    
    async def _handle_task_completion(self, task: Task, result: TaskResult):
        """处理任务完成"""
        task.result = result
        task.completed_at = datetime.now()
        
        if result.success:
            task.status = TaskStatus.COMPLETED
            self.completed_tasks.append(task.task_id)
            logger.info(f"任务完成: {task.name}")

            # 优先处理 next_tasks（编排模式）
            if result.next_tasks:
                await self._trigger_next_tasks(result.next_tasks)
            else:
                # 如果没有指定 next_tasks，则触发依赖此任务的其他任务（依赖模式）
                await self._trigger_dependent_tasks(task.task_id)
        else:
            await self._handle_task_failure(task, result)
    
    async def _handle_task_error(self, task: Task, error: str):
        """处理任务错误"""
        task.error = error
        task.completed_at = datetime.now()
        
        result = TaskResult(success=False, error=error, should_retry=task.retry_count < task.max_retries)
        await self._handle_task_failure(task, result)
    
    async def _handle_task_failure(self, task: Task, result: TaskResult):
        """处理任务失败"""
        logger.info(f"处理任务失败: {task.name}, should_retry={result.should_retry}, retry_count={task.retry_count}, max_retries={task.max_retries}")

        if result.should_retry and task.retry_count < task.max_retries:
            # 重试任务
            task.retry_count += 1
            task.status = TaskStatus.PENDING
            task.started_at = None
            task.completed_at = None
            task.result = None
            task.error = None

            # 确保任务从运行中的任务列表中移除，以便重试
            if task.task_id in self.running_tasks:
                del self.running_tasks[task.task_id]
                logger.info(f"从运行任务列表中移除任务: {task.name}")

            logger.warning(f"任务失败，准备重试 ({task.retry_count}/{task.max_retries}): {task.name}")
            enqueue_result = await self._safe_enqueue_task(task.task_id)
            logger.info(f"重试任务入队结果: {enqueue_result}")
        else:
            # 任务最终失败
            task.status = TaskStatus.FAILED
            self.failed_tasks[task.task_id] = result.error or "未知错误"
            logger.error(f"任务失败: {task.name} - {result.error}")
            
            # 发布任务失败事件
            from .event_bus import create_event
            await self.event_bus.publish(create_event(
                name='task_failed',
                data={
                    'task_id': task.task_id,
                    'task_name': task.name,
                    'error': result.error
                },
                source='TaskManager'
            ))

            # 任务失败后启动调试模式，传递失败任务信息
            await self._start_debug_mode(task)
    
    async def _trigger_next_tasks(self, next_task_ids: List[str]):
        """触发 next_tasks 指定的任务（编排模式）"""
        logger.info(f"触发 next_tasks: {next_task_ids}")

        for task_id in next_task_ids:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if task.status == TaskStatus.PENDING:
                    # 检查该任务的所有依赖是否都已完成
                    if self._check_dependencies(task_id):
                        await self._safe_enqueue_task(task_id)
                    else:
                        logger.warning(f"next_task {task.name} 的依赖未满足，跳过")
                elif task.status == TaskStatus.COMPLETED:
                    # 对于已完成的任务，支持重新执行（用于循环流程）
                    logger.info(f"重置已完成任务状态: {task.name}")
                    self._reset_task_for_rerun(task)
                    if self._check_dependencies(task_id):
                        await self._safe_enqueue_task(task_id)
                    else:
                        logger.warning(f"重置后的next_task {task.name} 依赖未满足，跳过")
                else:
                    logger.warning(f"next_task {task.name} 状态为 {task.status.value}，跳过")
            else:
                logger.error(f"next_task 不存在: {task_id}")

    def _reset_task_for_rerun(self, task: Task):
        """重置任务状态以支持重新执行（用于循环流程）"""
        # 从已完成任务列表中移除
        if task.task_id in self.completed_tasks:
            self.completed_tasks.remove(task.task_id)

        # 重置任务状态
        task.status = TaskStatus.PENDING
        task.started_at = None
        task.completed_at = None
        task.result = None
        task.error = None
        task.retry_count = 0  # 重置重试计数

        logger.info(f"任务 {task.name} 已重置为PENDING状态")

    async def _trigger_dependent_tasks(self, completed_task_id: str):
        """触发依赖已完成任务的其他任务（依赖模式）"""
        dependent_tasks = self.reverse_dependencies.get(completed_task_id, [])
        logger.info(f"触发依赖任务: {dependent_tasks}")

        for task_id in dependent_tasks:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if task.status == TaskStatus.PENDING:
                    # 检查该任务的所有依赖是否都已完成
                    if self._check_dependencies(task_id):
                        await self._safe_enqueue_task(task_id)
                elif task.status == TaskStatus.COMPLETED:
                    # 对于已完成的依赖任务，也支持重新执行（用于循环流程）
                    logger.info(f"重置已完成的依赖任务状态: {task.name}")
                    self._reset_task_for_rerun(task)
                    if self._check_dependencies(task_id):
                        await self._safe_enqueue_task(task_id)
                    else:
                        logger.warning(f"重置后的依赖任务 {task.name} 依赖未满足，跳过")
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        task = self.tasks.get(task_id)
        return task.status if task else None
    
    def get_all_tasks_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有任务状态"""
        status = {}
        for task_id, task in self.tasks.items():
            status[task_id] = {
                'name': task.name,
                'status': task.status.value,
                'retry_count': task.retry_count,
                'created_at': task.created_at.isoformat(),
                'started_at': task.started_at.isoformat() if task.started_at else None,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                'error': task.error
            }
        return status
    
    def is_all_completed(self) -> bool:
        """检查是否所有任务都已完成"""
        return len(self.completed_tasks) == len(self.tasks)
    
    def has_failed_tasks(self) -> bool:
        """检查是否有失败的任务"""
        return len(self.failed_tasks) > 0

    async def _cleanup_on_failure(self):
        """任务失败后的清理操作"""
        logger.info("开始执行任务失败后的清理操作...")

        try:
            # 获取浏览器实例并清理
            browser_instance = self.state_manager.get_data('browser_instance')
            if browser_instance:
                logger.info("清理浏览器实例...")

                # 检查是否是RoxyBrowserManager
                if hasattr(browser_instance, 'roxy_client') and browser_instance.roxy_client:
                    logger.info("检测到RoxyBrowser，执行RoxyBrowser清理...")
                    browser_instance.cleanup()
                else:
                    # 普通浏览器清理
                    logger.info("执行普通浏览器清理...")
                    if hasattr(browser_instance, 'driver') and browser_instance.driver:
                        browser_instance.driver.quit()

                # 清理状态管理器中的浏览器实例
                self.state_manager.set_data('browser_instance', None)
                logger.info("浏览器实例清理完成")

            # 停止TaskManager
            logger.info("停止TaskManager...")
            await self.stop()

        except Exception as e:
            logger.error(f"清理操作失败: {e}")

        logger.info("任务失败清理操作完成")

    async def _start_debug_mode(self, failed_task):
        """启动调试模式，添加debug_task到队列"""
        logger.info("启动调试模式...")

        try:
            # 导入debug_task
            from tasks.initial_tasks import debug_task

            # 找到失败任务的依赖任务
            dependent_tasks = []
            for task_id, task in self.tasks.items():
                if failed_task.task_id in task.dependencies:
                    dependent_tasks.append(task_id)

            logger.info(f"失败任务 {failed_task.name} 的依赖任务: {dependent_tasks}")

            # 创建debug_task
            debug_task_id = "debug_task_" + str(uuid.uuid4())[:8]
            debug_task_obj = Task(
                task_id=debug_task_id,
                name="调试任务",
                handler=debug_task,
                dependencies=[],
                max_retries=0,
                status=TaskStatus.PENDING,
                created_at=datetime.now()
            )

            # 添加到任务列表
            self.tasks[debug_task_id] = debug_task_obj

            # 保存失败任务信息和依赖任务，供debug完成后使用
            self.state_manager.set_data('debug_failed_task_id', failed_task.task_id)
            self.state_manager.set_data('debug_dependent_tasks', dependent_tasks)

            # 立即入队执行
            await self._safe_enqueue_task(debug_task_id)
            logger.info("调试任务已添加到队列")

        except Exception as e:
            logger.error(f"启动调试模式失败: {e}")
            # 如果调试模式启动失败，执行清理
            await self._cleanup_on_failure()
