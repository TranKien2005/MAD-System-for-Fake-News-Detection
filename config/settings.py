"""
Centralized configuration for the MAD System.
All configurable parameters are defined here.
"""

from dataclasses import dataclass, field


@dataclass
class ModelConfig:
    """LLM model configuration."""
    # Model cho các agent phức tạp (Defender, Challenger, Judge)
    main_model: str = "llama-3.3-70b-versatile"
    # Model cho agent đơn giản (Claim Parser, Search)
    light_model: str = "llama-3.1-8b-instant"
    # Temperature cho từng loại agent
    debate_temperature: float = 0.7       # Debater: sáng tạo hơn
    parser_temperature: float = 0.2       # Parser: chính xác hơn
    judge_temperature: float = 0.3        # Judge: cân nhắc, ít ngẫu nhiên


@dataclass
class DebateConfig:
    """Debate flow configuration."""
    max_rounds: int = 3                   # Số vòng tranh luận tối đa
    enable_search: bool = False           # Bật/tắt tính năng search thật
    max_search_results: int = 5           # Số kết quả search tối đa


@dataclass
class AppConfig:
    """Main application configuration."""
    model: ModelConfig = field(default_factory=ModelConfig)
    debate: DebateConfig = field(default_factory=DebateConfig)


# Global config instance
config = AppConfig()
