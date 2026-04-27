"""
Centralized configuration for the MAD System.
All configurable parameters are defined here.
"""

import os
from dataclasses import dataclass, field


@dataclass
class ModelConfig:
    """LLM model configuration."""
    # Model cho các agent phức tạp (Defender, Challenger, Judge, Evaluator)
    main_model: str = field(default_factory=lambda: os.getenv("NINEROUTER_MAIN_MODEL", "llama3"))
    # Model cho agent đơn giản (Search Agent, planner)
    light_model: str = field(default_factory=lambda: os.getenv("NINEROUTER_LIGHT_MODEL", "llama3"))
    # Token giới hạn cho output (Tăng lên để tránh bị cắt output)
    max_tokens: int = 8192
    # Temperature cho từng loại agent
    debate_temperature: float = 0.7       # Debater: sáng tạo hơn
    parser_temperature: float = 0.2       # Parser: chính xác hơn
    judge_temperature: float = 0.3        # Judge: cân nhắc, ít ngẫu nhiên


@dataclass
class DebateConfig:
    """Debate flow configuration."""
    max_rounds: int = 3                   # Số vòng tranh luận tối đa
    enable_search: bool = True            # Bật tìm kiếm
    max_search_results: int = 20          # Tổng số kết quả tối đa toàn bộ KB
    # Wikipedia config
    wikipedia_languages: list = field(default_factory=lambda: ["vi", "en"])
    max_wiki_results_per_query: int = 3   # Đồng bộ với yêu cầu người dùng
    
    # Tavily config
    max_tavily_results_per_query: int = 3 # Đồng bộ với yêu cầu người dùng (tối đa 3 nội dung tốt nhất)
    max_initial_results: int = 3           # Đồng bộ


@dataclass
class AppConfig:
    """Main application configuration."""
    model: ModelConfig = field(default_factory=ModelConfig)
    debate: DebateConfig = field(default_factory=DebateConfig)


# Global config instance
config = AppConfig()
