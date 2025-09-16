"""
智能用户名生成器
支持多种生成策略，生成更自然、多样化的用户名
"""

import random
import string
import json
import logging
from typing import List, Dict, Any
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class UsernameStrategy(Enum):
    """用户名生成策略"""
    WORD_COMBINATION = "word_combination"  # 单词组合
    ADJECTIVE_NOUN = "adjective_noun"      # 形容词+名词
    NAME_BASED = "name_based"              # 基于姓名
    TECH_STYLE = "tech_style"              # 技术风格
    RANDOM_PATTERN = "random_pattern"      # 随机模式
    MIXED_STYLE = "mixed_style"            # 混合风格

@dataclass
class UsernameConfig:
    """用户名生成配置"""
    min_length: int = 6
    max_length: int = 20
    include_numbers: bool = True
    include_hyphens: bool = True
    avoid_consecutive_numbers: bool = True
    preferred_strategies: List[UsernameStrategy] = None
    
    def __post_init__(self):
        if self.preferred_strategies is None:
            self.preferred_strategies = [
                UsernameStrategy.ADJECTIVE_NOUN,
                UsernameStrategy.WORD_COMBINATION,
                UsernameStrategy.TECH_STYLE
            ]

class UsernameGenerator:
    """智能用户名生成器"""
    
    def __init__(self, config: UsernameConfig = None):
        self.config = config or UsernameConfig()
        self._load_word_lists()
        
    def _load_word_lists(self):
        """加载词汇列表"""
        # 形容词列表
        self.adjectives = [
            "swift", "bright", "clever", "quick", "smart", "cool", "fresh", "bold",
            "sharp", "wise", "calm", "brave", "clear", "deep", "fast", "free",
            "happy", "light", "pure", "quiet", "royal", "safe", "true", "warm",
            "young", "active", "agile", "alert", "alive", "amazing", "awesome",
            "cosmic", "cyber", "digital", "dynamic", "electric", "epic", "future",
            "global", "hyper", "infinite", "magic", "modern", "mystic", "neon",
            "nova", "omega", "prime", "quantum", "rapid", "sonic", "stellar",
            "super", "turbo", "ultra", "unique", "vital", "wild", "zen"
        ]
        
        # 名词列表
        self.nouns = [
            "wolf", "eagle", "tiger", "lion", "bear", "fox", "hawk", "shark",
            "dragon", "phoenix", "falcon", "panther", "cobra", "raven", "lynx",
            "storm", "thunder", "lightning", "fire", "ice", "wind", "star",
            "moon", "sun", "ocean", "mountain", "river", "forest", "desert",
            "code", "data", "pixel", "byte", "node", "core", "link", "sync",
            "flow", "wave", "pulse", "spark", "flash", "beam", "ray", "glow",
            "hunter", "warrior", "knight", "ranger", "scout", "pilot", "rider",
            "master", "legend", "hero", "champion", "guardian", "sentinel"
        ]
        
        # 技术相关词汇
        self.tech_words = [
            "dev", "code", "hack", "tech", "cyber", "digital", "pixel", "byte",
            "bit", "net", "web", "app", "sys", "core", "node", "link", "sync",
            "api", "bot", "ai", "ml", "data", "cloud", "edge", "mesh", "grid"
        ]
        
        # 常见姓名
        self.names = [
            "alex", "sam", "jordan", "taylor", "casey", "riley", "morgan", "drew",
            "blake", "sage", "river", "sky", "sage", "phoenix", "rain", "storm"
        ]
        
    def generate(self, strategy: UsernameStrategy = None, attempts: int = 5) -> str:
        """生成用户名"""
        if strategy is None:
            strategy = random.choice(self.config.preferred_strategies)
            
        for attempt in range(attempts):
            try:
                username = self._generate_by_strategy(strategy)
                if self._validate_username(username):
                    logger.info(f"生成用户名成功: {username} (策略: {strategy.value})")
                    return username
            except Exception as e:
                logger.warning(f"用户名生成尝试 {attempt + 1} 失败: {e}")
                
        # 如果所有尝试都失败，使用简单的随机策略
        logger.warning("使用备用策略生成用户名")
        return self._generate_fallback()
        
    def _generate_by_strategy(self, strategy: UsernameStrategy) -> str:
        """根据策略生成用户名"""
        if strategy == UsernameStrategy.ADJECTIVE_NOUN:
            return self._generate_adjective_noun()
        elif strategy == UsernameStrategy.WORD_COMBINATION:
            return self._generate_word_combination()
        elif strategy == UsernameStrategy.NAME_BASED:
            return self._generate_name_based()
        elif strategy == UsernameStrategy.TECH_STYLE:
            return self._generate_tech_style()
        elif strategy == UsernameStrategy.RANDOM_PATTERN:
            return self._generate_random_pattern()
        elif strategy == UsernameStrategy.MIXED_STYLE:
            return self._generate_mixed_style()
        else:
            return self._generate_fallback()
            
    def _generate_adjective_noun(self) -> str:
        """生成形容词+名词组合"""
        adj = random.choice(self.adjectives)
        noun = random.choice(self.nouns)
        
        # 随机决定是否添加数字
        if self.config.include_numbers and random.random() < 0.6:
            if random.random() < 0.5:
                # 数字在末尾
                number = random.randint(1, 999)
                return f"{adj}{noun}{number}"
            else:
                # 数字在中间
                number = random.randint(1, 99)
                return f"{adj}{number}{noun}"
        else:
            # 可能添加连字符
            if self.config.include_hyphens and random.random() < 0.3:
                return f"{adj}-{noun}"
            return f"{adj}{noun}"
            
    def _generate_word_combination(self) -> str:
        """生成单词组合"""
        words = random.sample(self.nouns, 2)
        
        if self.config.include_hyphens and random.random() < 0.4:
            base = "-".join(words)
        else:
            base = "".join(words)
            
        if self.config.include_numbers and random.random() < 0.5:
            number = random.randint(10, 999)
            return f"{base}{number}"
        return base
        
    def _generate_name_based(self) -> str:
        """生成基于姓名的用户名"""
        name = random.choice(self.names)
        
        if random.random() < 0.7:
            # 添加数字
            if random.random() < 0.5:
                year = random.randint(1990, 2010)
                return f"{name}{year}"
            else:
                number = random.randint(100, 9999)
                return f"{name}{number}"
        else:
            # 添加形容词或名词
            suffix = random.choice(self.adjectives + self.nouns)
            if self.config.include_hyphens and random.random() < 0.3:
                return f"{name}-{suffix}"
            return f"{name}{suffix}"
            
    def _generate_tech_style(self) -> str:
        """生成技术风格用户名"""
        tech_word = random.choice(self.tech_words)
        
        if random.random() < 0.5:
            # tech + 形容词/名词
            suffix = random.choice(self.adjectives + self.nouns)
            base = f"{tech_word}{suffix}"
        else:
            # 形容词/名词 + tech
            prefix = random.choice(self.adjectives + self.nouns)
            base = f"{prefix}{tech_word}"
            
        if self.config.include_numbers and random.random() < 0.7:
            number = random.randint(1, 999)
            return f"{base}{number}"
        return base
        
    def _generate_random_pattern(self) -> str:
        """生成随机模式用户名"""
        patterns = [
            lambda: f"{random.choice(self.adjectives)}{random.randint(100, 999)}",
            lambda: f"{random.choice(self.nouns)}{random.randint(10, 99)}{random.choice(self.adjectives)}",
            lambda: f"{random.choice(self.names)}{random.choice(['x', 'z', 'q'])}{random.randint(1, 99)}",
            lambda: f"{random.choice(self.tech_words)}{random.choice(string.ascii_lowercase)}{random.randint(1, 999)}"
        ]
        
        pattern = random.choice(patterns)
        return pattern()
        
    def _generate_mixed_style(self) -> str:
        """生成混合风格用户名"""
        # 随机选择其他策略
        strategies = [s for s in UsernameStrategy if s != UsernameStrategy.MIXED_STYLE]
        strategy = random.choice(strategies)
        return self._generate_by_strategy(strategy)
        
    def _generate_fallback(self) -> str:
        """备用生成方法"""
        prefix = random.choice(["user", "dev", "test", "demo"])
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"{prefix}{suffix}"
        
    def _validate_username(self, username: str) -> bool:
        """验证用户名是否符合要求"""
        if not username:
            return False
            
        # 长度检查
        if len(username) < self.config.min_length or len(username) > self.config.max_length:
            return False
            
        # 字符检查
        allowed_chars = set(string.ascii_lowercase + string.digits)
        if self.config.include_hyphens:
            allowed_chars.add('-')
            
        if not all(c in allowed_chars for c in username.lower()):
            return False
            
        # 避免连续数字
        if self.config.avoid_consecutive_numbers:
            consecutive_digits = 0
            for char in username:
                if char.isdigit():
                    consecutive_digits += 1
                    if consecutive_digits > 3:
                        return False
                else:
                    consecutive_digits = 0
                    
        # 避免全数字或全字母
        has_letter = any(c.isalpha() for c in username)
        has_digit = any(c.isdigit() for c in username)
        
        if not has_letter:  # 全数字
            return False
            
        return True
        
    def generate_batch(self, count: int, unique: bool = True) -> List[str]:
        """批量生成用户名"""
        usernames = []
        attempts = 0
        max_attempts = count * 10
        
        while len(usernames) < count and attempts < max_attempts:
            username = self.generate()
            if not unique or username not in usernames:
                usernames.append(username)
            attempts += 1
            
        if len(usernames) < count:
            logger.warning(f"只生成了 {len(usernames)}/{count} 个用户名")
            
        return usernames
